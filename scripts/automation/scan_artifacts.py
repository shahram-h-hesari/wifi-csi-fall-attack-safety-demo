#!/usr/bin/env python
"""Stage 6 artifact scanner for the WiFi-CSI adversarial-defense repo.

Read-only. Walks results/ figures/ tables/ notes/, classifies each artifact, links it to its
generating script, and assigns a CONSERVATIVE evidence level. Emits automation/artifact_manifest.csv
(+ .meta.json sidecar) ONLY when --write is given; default is dry-run.

Hard invariants:
  * frozen-test is a POSITIVE ALLOWLIST built from the frozen-protocol registry — there is no code
    path that assigns frozen-test from a filename. A file literally named FROZEN_TEST that is not in
    a consummated frozen-read directory is NOT frozen-test.
  * validation detection takes precedence over any 'test'-in-filename signal.
  * default evidence level is diagnostic-internal.
  * writes ONLY the manifest + its .meta.json sidecar; never touches results/figures/tables/notes/
    thesis_artifacts/checkpoints/.codex/; no git; no network; no experiments.

Usage:
  python scripts/automation/scan_artifacts.py                         # dry-run (writes nothing)
  python scripts/automation/scan_artifacts.py --write --manifest-out automation/artifact_manifest.csv
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import repo_resolver as rr  # noqa: E402

REPO = rr.governance_repo_root()
SCAN_ROOTS = ["results", "figures", "tables", "notes"]
EXTS = {".csv", ".png", ".pdf", ".tex", ".md", ".json"}
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "checkpoints", ".codex", "thesis_artifacts", "automation"}
LEDGER = "results/defense_attempt_inventory/defense_attempt_results_long.csv"

COLUMNS = ["path", "kind", "sha256", "size_bytes", "generator_script", "link_method",
           "evidence_level", "evidence_provenance", "split", "claim_boundary",
           "overleaf_ready", "overleaf_blockers", "committed"]
COLUMNS_WITH_REPOSITORY = ["repository_id", *COLUMNS]

TOOL_VERSION = "scan_artifacts/1.0"


# --------------------------------------------------------------------------- fs
def rel(p: Path) -> str:
    return p.relative_to(REPO).as_posix()


def iter_files():
    for root in SCAN_ROOTS:
        base = REPO / root
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_dir():
                continue
            if any(part in EXCLUDE_DIRS for part in p.relative_to(REPO).parts):
                continue
            if p.suffix.lower() in EXTS:
                yield p


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_tracked():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=str(REPO), capture_output=True,
                             text=True, timeout=30)
        return set(out.stdout.splitlines()) if out.returncode == 0 else set()
    except (OSError, subprocess.SubprocessError):
        return set()


# ------------------------------------------------------------------- classify
def kind_of(np: str) -> str:
    name = np.rsplit("/", 1)[-1]
    ext = "." + name.rsplit(".", 1)[-1].lower()
    if np.endswith("defense_attempt_results_long.csv"):
        return "ledger"
    if re.search(r"FROZEN_.*PROTOCOL.*\.(md|json)$", name, re.I) or re.search(r"_protocol_.*\.json$", name, re.I):
        return "protocol"
    if name.endswith("_metadata.json"):
        return "metadata"
    if ext == ".tex":
        return "table_tex"
    if ext in (".png", ".pdf"):
        return "figure"
    if ext == ".md":
        return "report"
    if ext == ".csv":
        if name.startswith("thesis_table_"):
            return "table_csv"
        if "_probabilities_" in name or "_predictions_" in name:
            return "predictions"
        return "csv"
    if ext == ".json":
        return "json"
    return "other"


# ------------------------------------------------------------- frozen allowlist
def build_frozen_allowlist():
    """Files physically inside a consummated frozen-read directory (a dir with a
    FROZEN_*_TEST_RESULT.md whose dir or parent also holds a protocol twin)."""
    allow = set()
    for result_md in (REPO / "results").rglob("FROZEN_*_TEST_RESULT.md"):
        d = result_md.parent
        twin = (list(d.glob("FROZEN_*PROTOCOL*")) + list(d.glob("*_protocol_*.json"))
                + list(d.parent.glob("FROZEN_*PROTOCOL*")) + list(d.parent.glob("*_protocol_*.json")))
        if not twin:
            continue  # no pre-registration twin -> do NOT treat as frozen
        for f in d.iterdir():
            if f.is_file() and f.suffix.lower() in EXTS:
                allow.add(rel(f))
    return allow


# ------------------------------------------------------------------- ledger
def load_ledger():
    by_path, by_base = {}, {}
    lp = REPO / LEDGER
    if not lp.exists():
        return by_path, by_base
    with lp.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            src = (row.get("source_file") or "").replace("\\", "/").strip()
            if not src:
                continue
            split = (row.get("split") or "").strip()
            # post-hoc signal lives in result_status (e.g. post_hoc_threshold_sweep_from_saved_scores),
            # NOT source_type (which is per_window_predictions_csv / per_window_score_csv).
            status = (row.get("result_status") or "").strip()
            by_path.setdefault(src, set()).add((split, status))
            by_base.setdefault(src.rsplit("/", 1)[-1], set()).add((split, status))
    return by_path, by_base


# ------------------------------------------------------------- evidence level
VAL_PATH = re.compile(r"/val_eval/|/val_sweep/|_val_|_val\.|/val/", re.I)
TEST_DESC_HINT = re.compile(
    r"(^|/)(converged_baseline|converged_attacks|multiseed_robustness|cross_architecture)/|"
    r"thesis_table_|thesis_figure_|(^|/)ch0\d_|_test_epsilon_|cross_architecture|multiseed", re.I)


def evidence_level(np: str, frozen, by_path, by_base):
    # 1. frozen: allowlist ONLY
    if np in frozen:
        return "frozen-test", "frozen-protocol-allowlist", "test"
    info = by_path.get(np) or by_base.get(np.rsplit("/", 1)[-1])
    splits = {s for s, _ in info} if info else set()
    stypes = {t for _, t in info} if info else set()
    # 2. validation wins over any test-name signal
    if "val" in splits or VAL_PATH.search(np):
        return "validation-only", ("ledger:val" if "val" in splits else "path:val"), "val"
    # 3. test post-hoc distinct from frozen
    if "test" in splits and any("post_hoc" in t for t in stypes):
        return "test-post-hoc", "ledger:test+post_hoc", "test"
    # 4. test (argmax/derived) from ledger
    if "test" in splits:
        return "test-descriptive", "ledger:test", "test"
    # 5. descriptive test evidence by dir/prefix convention (never yields frozen)
    if TEST_DESC_HINT.search(np):
        return "test-descriptive", "path:convention", "test"
    # 6. conservative default
    return "diagnostic-internal", "default", "none"


# ------------------------------------------------------------- claim boundary
THESIS_SAFE = re.compile(
    r"thesis_table_|thesis_figure_|(^|/)tables/|"
    r"(^|/)(converged_baseline|converged_attacks|multiseed_robustness|cross_architecture)/|"
    r"(^|/)ch0\d_|converged_ch0\d_artifacts", re.I)


def claim_boundary(np, evidence):
    if evidence == "frozen-test":
        return "thesis-safe"          # with mandatory disclosures (see dashboard)
    if THESIS_SAFE.search(np):
        return "thesis-safe"
    return "unmapped"


# ------------------------------------------------------------- generator link
_SCRIPTS_CACHE = None


def _scripts():
    global _SCRIPTS_CACHE
    if _SCRIPTS_CACHE is None:
        _SCRIPTS_CACHE = {}
        for p in (REPO / "scripts").rglob("*.py"):
            try:
                _SCRIPTS_CACHE[rel(p)] = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                pass
    return _SCRIPTS_CACHE


def link_generator(p: Path, np: str):
    name = np.rsplit("/", 1)[-1]
    # (1) sibling metadata JSON with a command/script field
    for meta in p.parent.glob("*_metadata.json"):
        try:
            d = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for key in ("script", "command", "generator", "cmd"):
            v = d.get(key)
            if isinstance(v, str):
                m = re.search(r"scripts/[\w/]+\.py", v.replace("\\", "/"))
                if m:
                    return m.group(0), "metadata"
    # (2) naming convention
    m = re.match(r"thesis_table_(\d+)_", name)
    if m:
        for s in _scripts():
            if re.search(rf"create_thesis_table_{m.group(1)}_", s):
                return s, "naming"
    m = re.match(r"thesis_figure_(\d+)_", name)
    if m:
        for s in _scripts():
            if re.search(rf"create_thesis_figure_{m.group(1)}_", s):
                return s, "naming"
    m = re.search(r"ch0(\d)_", name)
    if m:
        for s in _scripts():
            if re.search(rf"generate_ch0{m.group(1)}_converged_artifacts", s):
                return s, "naming"
    # (3) literal basename search in scripts
    for spath, text in _scripts().items():
        if name in text:
            return spath, "literal"
    return "unknown", "none"


# ------------------------------------------------------------- overleaf ready
def overleaf_ready(kind, evidence, claim, generator, committed_artifact, tracked):
    if kind not in ("figure", "table_tex"):
        return "no", "not-a-figure-or-table-float"
    blockers = []
    if generator == "unknown":
        blockers.append("generator-unknown")
    elif generator not in tracked:
        blockers.append("generator-not-committed")
    if not committed_artifact:
        blockers.append("artifact-not-committed")
    if evidence in ("diagnostic-internal", "test-post-hoc"):
        blockers.append("evidence-not-admissible")
    if claim != "thesis-safe":
        blockers.append("claim-not-approved")
    if not blockers:
        return "yes", ""
    if blockers == ["claim-not-approved"]:
        return "candidate", "claim-not-approved"
    return "no", ";".join(blockers)


# ------------------------------------------------------------------- build
def build_rows(repository_id=None):
    frozen = build_frozen_allowlist()
    by_path, by_base = load_ledger()
    tracked = git_tracked()
    rows = []
    for p in iter_files():
        np = rel(p)
        kind = kind_of(np)
        ev, prov, split = evidence_level(np, frozen, by_path, by_base)
        claim = claim_boundary(np, ev)
        gen, method = link_generator(p, np)
        committed = np in tracked
        orl, blk = overleaf_ready(kind, ev, claim, gen, committed, tracked)
        row = {
            "path": np, "kind": kind, "sha256": sha256_file(p), "size_bytes": p.stat().st_size,
            "generator_script": gen, "link_method": method,
            "evidence_level": ev, "evidence_provenance": prov, "split": split,
            "claim_boundary": claim, "overleaf_ready": orl, "overleaf_blockers": blk,
            "committed": "yes" if committed else "no",
        }
        if repository_id:
            row["repository_id"] = repository_id
        rows.append(row)
    rows.sort(key=lambda r: r["path"])
    return rows, frozen


# ------------------------------------------------------------------- output
def summarize(rows):
    def counts(key):
        c = {}
        for r in rows:
            c[r[key]] = c.get(r[key], 0) + 1
        return dict(sorted(c.items()))
    return {"total": len(rows), "by_kind": counts("kind"),
            "by_evidence_level": counts("evidence_level"),
            "by_overleaf_ready": counts("overleaf_ready")}


def write_manifest(rows, out_path: Path, include_repository_id=False):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = COLUMNS_WITH_REPOSITORY if include_repository_id else COLUMNS
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    meta = out_path.with_suffix(".meta.json")
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(REPO),
                          capture_output=True, text=True)
    meta.write_text(json.dumps({
        "scan_ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "artifact_count": len(rows), "tool_version": TOOL_VERSION,
        "repo_head": head.stdout.strip() if head.returncode == 0 else "unknown",
    }, indent=2) + "\n", encoding="utf-8")
    return meta


def main():
    ap = argparse.ArgumentParser(description="Stage 6 artifact scanner (dry-run by default).")
    ap.add_argument("--write", action="store_true", help="write the manifest (otherwise dry-run)")
    ap.add_argument("--manifest-out", default="automation/artifact_manifest.csv",
                    help="manifest output path (only used with --write)")
    ap.add_argument("--repository-id", default=None,
                    help="optional repository_id column value for explicit cross-repository manifests")
    args = ap.parse_args()

    rows, frozen = build_rows(repository_id=args.repository_id)
    s = summarize(rows)
    print(f"[scan] {s['total']} artifacts | frozen-allowlist size {len(frozen)}")
    print(f"[scan] by_kind={s['by_kind']}")
    print(f"[scan] by_evidence_level={s['by_evidence_level']}")
    print(f"[scan] by_overleaf_ready={s['by_overleaf_ready']}")

    if not args.write:
        print(f"[dry-run] wrote NOTHING. Use --write --manifest-out {args.manifest_out} to emit.")
        return 0

    out = (REPO / args.manifest_out).resolve()
    # safety: refuse to write outside automation/
    if (REPO / "automation") not in out.parents and out.parent != (REPO / "automation"):
        # allow scratchpad/absolute for tests, but never into protected repo trees
        for guard in ("results", "figures", "tables", "notes", "thesis_artifacts", "checkpoints"):
            if (REPO / guard) in out.parents:
                sys.exit(f"[refused] will not write into protected tree: {guard}/")
    meta = write_manifest(rows, out, include_repository_id=bool(args.repository_id))
    print(f"[write] {out.relative_to(REPO) if REPO in out.parents else out} ({len(rows)} rows) + {meta.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
