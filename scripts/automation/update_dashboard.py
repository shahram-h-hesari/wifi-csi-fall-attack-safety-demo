#!/usr/bin/env python
"""Dashboard verifier + renderer for the WiFi-CSI adversarial-defense repo.

Stage 4: RECEIPTS + VERIFY PHASE. Regenerates ../RESEARCH_DASHBOARD.md and automation/status.json
from the source-of-truth (automation/*.yaml, automation/frontier.yaml, automation/receipts/*.json,
automation/dashboard_changelog.md), and COMPUTES verification from evidence:

  three-state ladder (per task, from its latest 'done' receipt):
    CLAIMED-UNVERIFIED         evidence checks failed (rendered loud, never green)
    VERIFIED                   all checks pass, task not gated
    VERIFIED-AWAITING-APPROVAL all checks pass, task gated, no user approval yet
    ACCEPTED                   a user approval receipt exists (actor.kind == user)

Design rule: Claude claims -> scripts verify -> user accepts. Claude can never move a task past
CLAIMED. This script must never: stage/commit/push, edit thesis/Overleaf files, run experiments,
create test authorization tokens, or write anything outside RESEARCH_DASHBOARD.md + automation/status.json.

Usage:
    python scripts/automation/update_dashboard.py            # verify + render (writes)
    python scripts/automation/update_dashboard.py --render   # same (explicit)
    python scripts/automation/update_dashboard.py --verify   # verify + print summary, NO write
    python scripts/automation/update_dashboard.py --check     # idempotency self-test, NO write
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
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML required: pip install pyyaml")

REPO = Path(__file__).resolve().parents[2]
AUT = REPO / "automation"
DASHBOARD_MD = REPO / "RESEARCH_DASHBOARD.md"
STATUS_JSON = AUT / "status.json"

AUTOMATION_ORDER = [
    ("test-split-guard", "test-split-guard.yaml"),
    ("val-pilot-gate", "val-pilot-gate.yaml"),
    ("ledger-sync", "ledger-sync-audit.yaml"),
    ("protocol-freeze", "protocol-freeze.yaml"),
    ("experiment-queue", "experiment-queue.yaml"),
    ("git-stage-check", "git-stage-check.yaml"),
    ("dashboard-refresh", "dashboard-refresh.yaml"),
]

EVIDENCE_TAG = {
    "none": "[research-goal]", "val_only": "[val-only]",
    "val_post_hoc": "[val/post-hoc]", "frozen_test": "[frozen-test]",
}

# (e) forbidden command patterns — a match fails verification.
FORBIDDEN_CMD = [
    (r"--split\s+test", "test-split generation"),
    (r"--split\s+legacy", "legacy-split generation"),
    (r"\bgit\s+commit\b", "git commit"),
    (r"\bgit\s+push\b", "git push"),
    (r"\bgit\s+add\b", "git add"),
    (r"thesis_artifacts", "thesis-artifact path"),
    (r"overleaf", "overleaf path"),
    (r"\brm\b.*\.(pt|pth|ckpt)\b", "checkpoint deletion"),
]
# (f)/(g) integrity gate
MODEL_LOG_EXTS = {".pt", ".pth", ".ckpt", ".log"}
def is_protected(path: str) -> bool:
    p = path.replace("\\", "/")
    return (p.startswith("thesis_artifacts/")
            or "/FROZEN_" in p or p.split("/")[-1].startswith("FROZEN_")
            or p.endswith("defense_attempt_results_long.csv"))


# --------------------------------------------------------------------------- IO
def load_yaml(path: Path):
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_receipts():
    out = []
    rdir = AUT / "receipts"
    if not rdir.exists():
        return out
    for p in sorted(rdir.glob("*.json")):
        try:
            with p.open(encoding="utf-8") as f:
                r = json.load(f)
            r["_file"] = p.name
            out.append(r)
        except (json.JSONDecodeError, OSError):
            continue
    return out


def today_iso():
    return _dt.date.today().isoformat()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_git(args):
    try:
        r = subprocess.run(["git", *args], cwd=str(REPO), capture_output=True, text=True, timeout=20)
        return r.stdout if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def git_head():
    h = run_git(["rev-parse", "--short", "HEAD"])
    return h.strip() if h else "unknown"


# ------------------------------------------------ artifact manifest (Stage 6, read-only)
MANIFEST = AUT / "artifact_manifest.csv"
MANIFEST_META = AUT / "artifact_manifest.meta.json"
_SCAN_ROOTS = ["results", "figures", "tables", "notes"]
_SCAN_EXTS = {".csv", ".png", ".pdf", ".tex", ".md", ".json"}
_SCAN_EXCL = {".git", ".venv", "__pycache__", "checkpoints", ".codex", "thesis_artifacts", "automation"}


def load_manifest():
    if not MANIFEST.exists():
        return None, {}
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    meta = {}
    if MANIFEST_META.exists():
        try:
            meta = json.loads(MANIFEST_META.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            meta = {}
    return rows, meta


def _current_artifact_count():
    n = 0
    for root in _SCAN_ROOTS:
        base = REPO / root
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_dir() or any(part in _SCAN_EXCL for part in p.relative_to(REPO).parts):
                continue
            if p.suffix.lower() in _SCAN_EXTS:
                n += 1
    return n


def manifest_status():
    rows, meta = load_manifest()
    if rows is None:
        return "not generated (run scan_artifacts.py --write)"
    scanned = meta.get("artifact_count", len(rows))
    cur = _current_artifact_count()
    s = f"last scan {str(meta.get('scan_ts','?'))[:10]} ({scanned} artifacts)"
    if cur != scanned:
        s += f" · ⚠️ STALE: {cur} on disk now — re-scan"
    return s


# ------------------------------------------------------------- verification (Stage 4)
def token_valid(token: str, base: Path) -> bool:
    if not token:
        return False
    hits = list((base / "results").rglob(f"*{token}*")) if (base / "results").exists() else []
    return any("AUTH" in h.name.upper() or "TOKEN" in h.name.upper() for h in hits)


def verify_receipt(r: dict, base: Path = REPO) -> dict:
    """Deterministic per-receipt evidence check. Returns {passed, strength, checks:[...]}. Pure."""
    checks = []
    def add(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    claimed = r.get("status_claimed")
    strength = "hash-verified"

    # (a) files_created exist; sha256 match if provided
    for fc in r.get("files_created", []):
        path = base / fc["path"]
        exists = path.exists()
        add(f"exists:{fc['path']}", exists, "" if exists else "missing")
        sha = fc.get("sha256")
        if exists and sha:
            match = (path.is_file() and sha256_file(path) == sha)
            add(f"sha256:{fc['path']}", match, "" if match else "sha mismatch")
        elif exists and not sha:
            strength = "existence-only"   # weak: receipt carried no hash

    # (b) command exit codes (for a 'done' claim, all must be 0)
    if claimed == "done":
        for c in r.get("commands_run", []):
            ok = c.get("exit_code", 0) == 0
            add("cmd_exit0", ok, "" if ok else f"exit={c.get('exit_code')}: {c.get('cmd','')[:50]}")

    # (e) forbidden-command scan
    for c in r.get("commands_run", []):
        cmd = c.get("cmd", "")
        hit = next((label for pat, label in FORBIDDEN_CMD if re.search(pat, cmd, re.I)), None)
        add("no_forbidden_cmd", hit is None, hit or "")

    # (d) split usage: no test read unless authorized
    su = r.get("split_usage", {})
    if su.get("test_read"):
        ok = token_valid(su.get("authorization_token") or "", base)
        add("test_read_authorized", ok, "" if ok else "test_read without valid token")
    else:
        add("no_unauthorized_test_read", True)

    # (c) acceptance-test results declared in the receipt
    for at in r.get("acceptance_tests", []):
        res = at.get("result")
        ep = at.get("evidence_path")
        ok = (res == "pass") and (not ep or (base / ep).exists())
        add(f"acceptance:{at.get('id','?')}", ok, "" if ok else f"result={res}")

    passed = all(c["ok"] for c in checks)
    return {"passed": passed, "strength": strength, "checks": checks}


def integrity_gate() -> dict:
    """(f)/(g) repo-global integrity: no model/log staged; no protected tracked path dirty."""
    staged = run_git(["diff", "--cached", "--name-only"])
    staged_bad = []
    if staged is not None:
        staged_bad = [ln for ln in staged.splitlines()
                      if Path(ln).suffix.lower() in MODEL_LOG_EXTS]
    porcelain = run_git(["status", "--porcelain"])
    protected_dirty = []
    if porcelain is not None:
        for ln in porcelain.splitlines():
            if not ln or ln.startswith("??"):
                continue  # untracked ignored
            path = ln[3:].strip().strip('"')
            if is_protected(path):
                protected_dirty.append(path)
    return {
        "git_available": staged is not None,
        "staged_model_or_log": staged_bad,
        "protected_paths_dirty": protected_dirty,
        "clean": (not staged_bad and not protected_dirty),
    }


def is_gated(task_id, tasks):
    for t in tasks.get("tasks", []):
        if t["id"] == task_id:
            return bool(t.get("gated"))
    return False


def compute_display(claimed, verification, gated, has_user_approval):
    if claimed != "done":
        return (claimed or "unknown").upper()
    # Evidence gates FIRST: an approval can never override failed evidence.
    if not verification["passed"]:
        return "CLAIMED-UNVERIFIED"
    if has_user_approval:
        return "ACCEPTED"
    return "VERIFIED-AWAITING-APPROVAL" if gated else "VERIFIED"


def latest_done_receipt(task_id, receipts):
    rs = [r for r in receipts if r.get("task_id") == task_id]
    return sorted(rs, key=lambda r: r.get("receipt_id", ""))[-1] if rs else None


def has_user_approval(task_id, receipts):
    return any(r.get("task_id") == task_id and r.get("actor", {}).get("kind") == "user"
               for r in receipts)


# ---------------------------------------------------------------- status model
def build_status(roadmap, tasks, frontier, receipts):
    plans = roadmap.get("plans", [])
    plan_id = plans[-1]["plan_id"] if plans else "none"

    task_states = {}
    for t in tasks.get("tasks", []):
        tid = t["id"]
        rs = [r for r in receipts if r.get("task_id") == tid]
        if not rs:
            task_states[tid] = {"display": "not_started", "checks": "0/0"}
            continue
        latest = sorted(rs, key=lambda r: r.get("receipt_id", ""))[-1]
        v = verify_receipt(latest)
        gated_eff = is_gated(tid, tasks) or bool(latest.get("requires_user_approval"))
        disp = compute_display(latest.get("status_claimed"), v,
                               gated_eff, has_user_approval(tid, receipts))
        npass = sum(1 for c in v["checks"] if c["ok"])
        task_states[tid] = {
            "display": disp, "strength": v["strength"],
            "checks": f"{npass}/{len(v['checks'])}",
            "failed": [c["check"] + (f" ({c['detail']})" if c["detail"] else "")
                       for c in v["checks"] if not c["ok"]],
        }

    # verification ledger over ALL done-receipts (incl. tasks not in tasks.yaml, e.g. legacy)
    ledger = []
    seen = set()
    for r in sorted(receipts, key=lambda r: r.get("receipt_id", ""), reverse=True):
        tid = r.get("task_id")
        if r.get("status_claimed") != "done" or tid in seen or r.get("actor", {}).get("kind") == "user":
            continue
        seen.add(tid)
        v = verify_receipt(r)
        gated_eff = is_gated(tid, tasks) or bool(r.get("requires_user_approval"))
        disp = compute_display("done", v, gated_eff, has_user_approval(tid, receipts))
        npass = sum(1 for c in v["checks"] if c["ok"])
        ledger.append({
            "task_id": tid, "automation": r.get("automation"),
            "display": disp, "checks": f"{npass}/{len(v['checks'])}",
            "strength": v["strength"],
            "failed": [c["check"] for c in v["checks"] if not c["ok"]],
        })

    autos = {}
    for name, acc in AUTOMATION_ORDER:
        autos[name] = automation_phase_states(name, (AUT / "acceptance" / acc).exists(), receipts, tasks)

    return {
        "schema_version": 1,
        "generated": today_iso(),
        "stage": 4,
        "verification_active": True,
        "plan_in_effect": plan_id,
        "counters": frontier.get("counters", {}),
        "integrity_gate": integrity_gate(),
        "tasks": task_states,
        "verification_ledger": ledger,
        "automations": autos,
        "frozen_protocols": frontier.get("frozen_protocol_registry", []),
        "receipts_processed": len(receipts),
    }


def automation_phase_states(name, acceptance_exists, receipts, tasks):
    def phase(keyword=None, want_user=False):
        best = "todo"
        for r in receipts:
            if r.get("automation") != name:
                continue
            if want_user:
                if r.get("actor", {}).get("kind") == "user":
                    return "verified"
                continue
            tid = (r.get("task_id") or "").lower()
            if keyword == "impl" and not ("impl" in tid or name == "git-stage-check"):
                continue
            if keyword == "test" and "test" not in tid:
                continue
            if r.get("status_claimed") != "done":
                continue
            v = verify_receipt(r)
            cand = "verified" if v["passed"] else "unverified"
            if cand == "verified":
                best = "verified"
            elif best != "verified":
                best = "unverified"
        return best
    return {
        "design": "verified" if acceptance_exists else "todo",
        "impl": phase("impl"),
        "test": phase("test"),
        "accepted": phase(want_user=True),
        "verification": "active",
    }


# ------------------------------------------------------------------- rendering
PHASE_SYM = {"verified": "✅", "unverified": "⚠️", "todo": "⬜", "na": "➖"}
DISPLAY_SYM = {
    "VERIFIED": "✅ VERIFIED", "ACCEPTED": "✅ ACCEPTED",
    "VERIFIED-AWAITING-APPROVAL": "🟡 VERIFIED · awaiting approval",
    "CLAIMED-UNVERIFIED": "⚠️ CLAIMED-UNVERIFIED", "not_started": "⬜ not started",
    "PARTIAL": "🟡 partial", "FAILED": "⚠️ failed", "BLOCKED": "⛔ blocked",
}


def r_banner(status):
    c = status["counters"]
    ig = status["integrity_gate"]
    ig_line = "✅ clean" if ig["clean"] else (
        "⚠️ " + "; ".join(filter(None, [
            ("staged model/log: " + ", ".join(ig["staged_model_or_log"])) if ig["staged_model_or_log"] else "",
            ("protected dirty: " + ", ".join(ig["protected_paths_dirty"])) if ig["protected_paths_dirty"] else "",
        ])) if ig["git_available"] else "git unavailable")
    return (
        "<!-- GENERATED by scripts/automation/update_dashboard.py. DO NOT HAND-EDIT.\n"
        "     Edit the source-of-truth instead: automation/*.yaml, automation/frontier.yaml,\n"
        "     automation/receipts/*.json. Regenerate: python scripts/automation/update_dashboard.py -->\n\n"
        "# Research Control Dashboard — WiFi-CSI Adversarial Defense\n\n"
        "> **GENERATED FILE** (dashboard Stage 4: verify + render). Source-of-truth is `automation/`.\n"
        "> Verification is **active**: statuses are computed from receipt evidence, not asserted.\n"
        "> Ladder — **CLAIMED** (Claude) → **VERIFIED** (evidence) → **ACCEPTED** (you). A gated task with\n"
        "> passing evidence but no approval shows *VERIFIED · awaiting approval*, never DONE. Failed checks\n"
        "> render loud as **CLAIMED-UNVERIFIED**.\n\n"
        "## ⚡ Status banner\n\n"
        "| | |\n|---|---|\n"
        f"| Generated | {status['generated']} |\n"
        f"| Plan in effect | `{status['plan_in_effect']}` |\n"
        f"| Verification | **active** (Stage 4) |\n"
        f"| Integrity gate (no model/log staged; protected paths clean) | {ig_line} |\n"
        f"| Validation gate-reads consumed | **{c.get('validation_gate_reads_consumed', 'n/a')} logged** |\n"
        f"| Frozen test reads consumed | **{c.get('frozen_test_reads_consumed', 'n/a')}** |\n"
        f"| Artifact manifest | {manifest_status()} |\n"
        f"| Receipts processed | {status['receipts_processed']} |\n"
    )


def r_now_next(roadmap, receipts):
    plans = roadmap.get("plans", [])
    days = plans[-1].get("days", []) if plans else []
    today = today_iso()
    cur = next((d for d in days if str(d.get("date")) == today), None)
    nxt = next((d for d in days if str(d.get("date")) > today), None)
    lines = ["## 1. Now / Next / Blocked\n"]
    if cur:
        lines.append(f"- **Today ({cur['date']}):** {cur.get('primary','')}"
                     + (f" · _secondary:_ {cur['secondary']}" if cur.get("secondary") else ""))
    if nxt:
        lines.append(f"- **Next ({nxt['date']}):** {nxt.get('primary','')}")
    blocked = [r for r in receipts if r.get("status_claimed") == "blocked"]
    approvals = [r for r in receipts
                 if r.get("requires_user_approval") and r.get("actor", {}).get("kind") != "user"
                 and not has_user_approval(r.get("task_id"), receipts)]
    lines.append(f"- **Blockers:** {len(blocked) or 'none'}")
    lines.append(f"- **Awaiting your approval:** {len(approvals) or 'none'}"
                 + (" — " + ", ".join(sorted({r.get('task_id','?') for r in approvals})) if approvals else ""))
    return "\n".join(lines) + "\n"


def r_roadmap(roadmap):
    plans = roadmap.get("plans", [])
    out = ["## 3. 7-day roadmap"]
    if plans:
        p = plans[-1]
        out.append(f"\nPlan `{p['plan_id']}` (created {p.get('created','?')}).\n")
        out.append("| Day | Date | Primary | Secondary |\n|---|---|---|---|")
        for d in p.get("days", []):
            out.append(f"| {d.get('day')} | {d.get('date')} | {d.get('primary','')} | {d.get('secondary') or '—'} |")
    for s in roadmap.get("future_stages", []) or []:
        out.append("")
        out.append(f"- **Future:** `{s['task_id']}` — {s['title']} "
                   f"(depends on: {', '.join(s.get('depends_on', [])) or 'none'})")
    return "\n".join(out) + "\n"


def r_automation_table(status):
    out = ["## 4. Automation status  (evidence-verified; ACCEPTED = your approval receipt)\n"]
    out.append("| Automation | Design | Impl | Test | Accepted |\n|---|---|---|---|---|")
    for name, _ in AUTOMATION_ORDER:
        a = status["automations"][name]
        row = " | ".join(PHASE_SYM.get(a[k], "⬜") for k in ("design", "impl", "test", "accepted"))
        out.append(f"| `{name}` | {row} |")
    out.append("\nLegend: ✅ verified · ⚠️ claimed-unverified · ⬜ not started · ➖ n/a.")
    return "\n".join(out) + "\n"


def r_verification_ledger(status):
    out = ["## 4b. Verification ledger  (per completed task — CLAIMED → VERIFIED → ACCEPTED)\n"]
    ledger = status.get("verification_ledger", [])
    if not ledger:
        out.append("_(no completed receipts yet)_")
        return "\n".join(out) + "\n"
    out.append("| Task | Automation | State | Checks | Strength | Failed |\n|---|---|---|---|---|---|")
    for e in ledger:
        out.append(f"| `{e['task_id']}` | {e['automation']} | {DISPLAY_SYM.get(e['display'], e['display'])} "
                   f"| {e['checks']} | {e['strength']} | {', '.join(e['failed']) or '—'} |")
    out.append("\n> _existence-only_ = the receipt carried no SHA256, so files were checked for existence "
               "only; skill-written receipts should include hashes for hash-verified strength.")
    return "\n".join(out) + "\n"


def r_queue(queue):
    out = ["## 5. Experiment queue\n"]
    entries = queue.get("entries") or []
    if not entries:
        out.append("_(none enqueued)_ — queue opens after `val-pilot-gate` + `test-split-guard` exist. "
                   "See `automation/experiment_queue.yaml`.")
    else:
        out.append("| Entry | Seed | Status | Gate verdict |\n|---|---|---|---|")
        for e in entries:
            out.append(f"| {e.get('entry_id')} | {e.get('seed')} | {e.get('status')} | {e.get('gate_verdict','—')} |")
    return "\n".join(out) + "\n"


def r_frontier(frontier):
    out = ["## 6. Research frontier — toward R90F10 (recall > 90% AND FAR < 10%)\n"]
    out.append(f"**Primary operating point = {frontier.get('primary_operating_point','')}.**\n")
    out.append("| Milestone | Definition | Status | Evidence |\n|---|---|---|---|")
    smap = {"not_met": "❌ not met", "post_hoc_only": "⚠️ post-hoc-only", "pass": "✅ PASS"}
    for m in frontier.get("milestones", []):
        tag = EVIDENCE_TAG.get(m.get("evidence_level", "none"), "[?]")
        out.append(f"| **{m['label']}** | {m['definition']} | {smap.get(m['status'], m['status'])} | `{tag}` |")
    bf = frontier.get("best_validation_frontier", {})
    if bf:
        out.append(f"\n- **Best validation frontier ({bf.get('operating_point','')}):** "
                   f"{bf.get('reference_model','')} PGD-AUROC **{bf.get('val_pgd_auroc','?')}**, "
                   f"recall@FAR≤10% ≈ {bf.get('val_recall_at_far_le_10','?')} `[val-only]`. {bf.get('note','')}")
        if bf.get("advisor_read"):
            out.append(f"- **Advisor read:** {bf['advisor_read']}")
    h15 = next((m for m in frontier.get("milestones", []) if m["id"] == "H15_eps015"), None)
    if h15 and h15.get("detail"):
        out.append(f"\n> **H15@ε=0.015 frozen PASS `[frozen-test]`:** {h15['detail']}. "
                   "Clears recall>90% but **not** FAR<10%, and is at ε=0.015 — **not** R90F10 (ε=0.030).")
    return "\n".join(out) + "\n"


def r_safety(frontier):
    out = ["## 7. Safety, integrity & frozen protocols\n"]
    tsg = frontier.get("test_split_guard", {})
    out.append(f"- **Test-split safety:** {tsg.get('status','?')} — {tsg.get('note','')}")
    vrl = frontier.get("validation_read_log", {})
    out.append(f"- **Validation-read log:** {vrl.get('status','?')} — {vrl.get('note','')}")
    la = frontier.get("ledger_audit", {})
    out.append(f"- **Ledger / audit:** {la.get('status','?')} — {la.get('note','')}")
    out.append("\n**Frozen-protocol registry:**\n")
    out.append("| Protocol ID | ε | Model | Status | Verdict |\n|---|---|---|---|---|")
    for fp in frontier.get("frozen_protocol_registry", []):
        out.append(f"| `{fp['protocol_id']}` | {fp['epsilon']} | {fp['model']} | **{fp['status']}** | "
                   f"**{fp['verdict']}** ({fp.get('detail','')}) |")
    return "\n".join(out) + "\n"


def r_overleaf_claims(frontier):
    out = ["## 8-9. Artifact inventory & Overleaf-ready\n"]
    rows, meta = load_manifest()
    if rows is None:
        out.append("Manifest not generated yet — run `scan_artifacts.py --write`. Interim inventories: "
                   "`EXPERIMENT_EVIDENCE_INDEX.md`, `LOCAL_PROJECT_MAP.md`, "
                   "`results/defense_attempt_inventory/defense_attempt_artifact_inventory.md`.")
        orl = frontier.get("overleaf_ready", {})
        for x in orl.get("eligible_now", []):
            out.append(f"- `[frozen-test]` {x}")
    else:
        byk = Counter(r["kind"] for r in rows)
        bye = Counter(r["evidence_level"] for r in rows)
        byo = Counter(r["overleaf_ready"] for r in rows)
        out.append(f"From `automation/artifact_manifest.csv` — **{len(rows)} artifacts**, "
                   f"{manifest_status()}.")
        out.append("\n- **By kind:** " + ", ".join(f"{k} {v}" for k, v in sorted(byk.items())))
        out.append("- **By evidence level:** " + ", ".join(f"`[{k}]` {v}" for k, v in sorted(bye.items())))
        out.append("- **Overleaf-ready:** " + ", ".join(f"{k} {v}" for k, v in sorted(byo.items())))
        yes = [r["path"] for r in rows if r["overleaf_ready"] == "yes"]
        cand = [r["path"] for r in rows if r["overleaf_ready"] == "candidate"]
        out.append(f"\n**Overleaf-ready = yes ({len(yes)})** — `[thesis-safe]`, committed, admissible evidence:")
        for p in yes[:8]:
            out.append(f"- {p}")
        if len(yes) > 8:
            out.append(f"- …and {len(yes) - 8} more (see manifest)")
        if cand:
            out.append(f"\n**Overleaf-ready = candidate ({len(cand)})** — usable but awaiting your thesis-claim approval:")
            for p in cand[:8]:
                out.append(f"- {p}")
        out.append("\n> Evidence labels are conservative: **frozen-test** is protocol-allowlist only; "
                   "validation-only never shown as frozen; default is diagnostic-internal.")
    cb = frontier.get("claim_boundaries", {})
    out.append("\n## 10. Claim boundaries (thesis-safe vs research-goal-only)\n")
    out.append(f"Sourced from `{cb.get('source','')}` — referenced, not duplicated.")
    if cb.get("thesis_safe_now"):
        out.append("\n**Thesis-safe now** `[thesis-safe]`:")
        for x in cb["thesis_safe_now"]:
            out.append(f"- {x}")
    if cb.get("research_goal_only"):
        out.append("\n**Research/startup-goal only (NOT yet evidenced)** `[research-goal]`:")
        for x in cb["research_goal_only"]:
            out.append(f"- {x}")
    return "\n".join(out) + "\n"


def r_dnb():
    p = AUT / "do_not_build_yet.md"
    return ("## 11. Do-not-build-yet\n\nSee [`automation/do_not_build_yet.md`](automation/do_not_build_yet.md). "
            "Headlines: automated val hyperparameter/threshold search; multi-seed fan-out (43–46); "
            "Overleaf auto-editor; auto-commit hooks; parallel execution; two-way Notion sync; "
            "static HTML dashboard (Stage 8, deferred until status.json + manifest are stable).\n"
            if p.exists() else "")


def r_recent_changes(n=10):
    p = AUT / "dashboard_changelog.md"
    out = ["## 12. Recent changes\n"]
    if not p.exists():
        out.append("_(no changelog yet)_")
        return "\n".join(out) + "\n"
    heads = [ln.strip("# ").strip() for ln in p.read_text(encoding="utf-8").splitlines()
             if ln.startswith("## ")]
    for h in heads[:n]:
        out.append(f"- {h}")
    out.append("\nFull history: [`automation/dashboard_changelog.md`](automation/dashboard_changelog.md).")
    return "\n".join(out) + "\n"


def render(status, roadmap, queue, frontier, receipts):
    parts = [
        r_banner(status),
        r_now_next(roadmap, receipts),
        r_roadmap(roadmap),
        r_automation_table(status),
        r_verification_ledger(status),
        r_queue(queue),
        r_frontier(frontier),
        r_safety(frontier),
        r_overleaf_claims(frontier),
        r_dnb(),
        r_recent_changes(),
    ]
    return "\n---\n\n".join(p.strip() for p in parts if p.strip()) + "\n"


# ------------------------------------------------------------------- commands
def _load_all():
    return (load_yaml(AUT / "roadmap.yaml"), load_yaml(AUT / "tasks.yaml"),
            load_yaml(AUT / "experiment_queue.yaml"), load_yaml(AUT / "frontier.yaml"),
            load_receipts())


def _print_deltas(prev, status):
    prev_tasks = (prev or {}).get("tasks", {})
    new_tasks = status.get("tasks", {})
    changes = []
    for tid, ns in new_tasks.items():
        old = (prev_tasks.get(tid) or {}).get("display")
        new = ns.get("display")
        if old != new:
            changes.append(f"  {tid}: {old or '(new)'} -> {new}")
    if changes:
        print("[delta] task state changes since last refresh:")
        print("\n".join(changes))
    else:
        print("[delta] no task state changes since last refresh.")


def do_render(write=True):
    roadmap, tasks, queue, frontier, receipts = _load_all()
    status = build_status(roadmap, tasks, frontier, receipts)
    md = render(status, roadmap, queue, frontier, receipts)
    status_txt = json.dumps(status, indent=2, ensure_ascii=False) + "\n"
    if write:
        prev = {}
        if STATUS_JSON.exists():
            try:
                prev = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                prev = {}
        DASHBOARD_MD.write_text(md, encoding="utf-8")
        STATUS_JSON.write_text(status_txt, encoding="utf-8")
        ig = status["integrity_gate"]
        print(f"[render] wrote {DASHBOARD_MD.relative_to(REPO)} ({len(md)} chars) + status.json; "
              f"integrity {'CLEAN' if ig['clean'] else 'WARN'}")
        _print_deltas(prev, status)
    return md, status_txt, status


def ledger_display(status, task_id):
    for e in status.get("verification_ledger", []):
        if e["task_id"] == task_id:
            return e["display"]
    return None


def write_approval(task_id, receipts_dir=None, dry_run=False, note=None):
    """Write a user approval receipt (actor.kind == user). The ONLY way a task reaches ACCEPTED.
    Must only ever be invoked by an explicit human `--approve` request — never autonomously."""
    receipts_dir = Path(receipts_dir) if receipts_dir else (AUT / "receipts")
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    rid = f"{ts}_user-approval_{task_id}"
    receipt = {
        "schema_version": 1, "receipt_id": rid, "task_id": task_id,
        "automation": "(user-approval)", "actor": {"kind": "user", "name": "user"},
        "status_claimed": "approved",
        "summary": note or f"User approved {task_id} (evidence was VERIFIED-AWAITING-APPROVAL).",
        "files_created": [], "files_modified": [], "commands_run": [], "artifacts": [],
        "acceptance_tests": [],
        "split_usage": {"splits_touched": [], "test_read": False, "authorization_token": None},
        "git": {"head": git_head(), "expected_dirty": []},
        "requires_user_approval": False, "blocked_on": None, "supersedes": None,
        "next_action": "",
    }
    if not dry_run:
        receipts_dir.mkdir(parents=True, exist_ok=True)
        (receipts_dir / f"{rid}.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return rid, receipt


def do_approve(task_id):
    _, _, status = do_render(write=False)
    disp = (status["tasks"].get(task_id) or {}).get("display") or ledger_display(status, task_id)
    if disp is None:
        print(f"[approve] REFUSED: unknown task '{task_id}'.")
        return 1
    if disp == "ACCEPTED":
        print(f"[approve] {task_id} is already ACCEPTED; nothing to do.")
        return 0
    if disp != "VERIFIED-AWAITING-APPROVAL":
        print(f"[approve] REFUSED: {task_id} is '{disp}', not VERIFIED-AWAITING-APPROVAL. "
              "Only evidence-verified tasks awaiting approval can be accepted.")
        return 1
    rid, _ = write_approval(task_id)
    print(f"[approve] wrote user approval receipt: {rid}")
    do_render(write=True)
    return 0


def do_check():
    a_md, a_js, _ = do_render(write=False)
    b_md, b_js, _ = do_render(write=False)
    ok = (a_md == b_md) and (a_js == b_js)
    print("[check] idempotency:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def do_verify():
    _, _, status = do_render(write=False)
    print(f"[verify] stage={status['stage']} verification_active={status['verification_active']}")
    for e in status["verification_ledger"]:
        print(f"  {e['task_id']:14s} {e['display']:26s} checks {e['checks']} "
              f"({e['strength']})" + (f"  FAILED: {', '.join(e['failed'])}" if e["failed"] else ""))
    ig = status["integrity_gate"]
    print(f"[verify] integrity gate: {'CLEAN' if ig['clean'] else 'WARN ' + json.dumps(ig)}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Dashboard verifier + renderer (Stage 4).")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--render", action="store_true", help="verify + render (writes)")
    g.add_argument("--check", action="store_true", help="idempotency self-test (no write)")
    g.add_argument("--verify", action="store_true", help="verify + print summary (no write)")
    g.add_argument("--approve", metavar="TASK_ID",
                   help="write a USER approval receipt for a VERIFIED-AWAITING-APPROVAL task "
                        "(human-only; never invoke autonomously)")
    args = ap.parse_args()
    if args.check:
        return do_check()
    if args.verify:
        return do_verify()
    if args.approve:
        return do_approve(args.approve)
    do_render(write=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
