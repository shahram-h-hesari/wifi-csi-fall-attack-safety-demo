#!/usr/bin/env python
"""Val-pilot scanner (design VAL_PILOT_GATE_DESIGN.md §10 steps 3-4).

Walks a validation-sweep directory, pairs each candidate axis's validation probability export with
its derived metrics, and reports — using the TESTED pure logic in val_pilot_gate_lib.py — whether
each is a COMPLETE val pilot (§2/§3) and what verdict its metrics would earn (§5). With
--write-receipts (§10 step 4), also writes one JSON pilot receipt per VERIFIED pilot.

SAFETY (enforced, not just intended):
  - WRITES NOTHING by default (design §10 step 3: "zero writes in its first iteration"). Only with
    the explicit --write-receipts flag does it write, and only pilot receipts for VERIFIED pilots
    to automation/val_pilot_receipts/ — never inside results/ (write_receipts() refuses on sight if
    ever pointed at a results/ tree; the CLI never exposes that path as configurable).
  - Reads ONLY validation-split artifacts. It refuses to open any path containing a test/legacy
    split token; a would-be test read raises before any file is opened.
  - Runs no experiment, no export, no --split command, no training/eval. Pure file reading + the
    stdlib hashing already in the lib.
  - No verdict printed or receipted authorizes a test read. A STRONG-GO is a proposal, never
    authorization (design §5.2, §9); an incomplete pilot can never authorize anything (§2). A pilot
    receipt is CLAIMED/VERIFIED evidence, not the separate, explicit ACCEPTED approval the design's
    §7 CLAIMED/VERIFIED/ACCEPTED vocabulary requires before any pilot can be cited toward a test read.

Default target: the eps=0.015 validation frontier sweep that the eps015 feasibility audit used.
Usage:
    python scripts/automation/val_pilot_scan.py [--sweep-dir DIR] [--frontier-csv CSV] [--json] [--write-receipts]
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import val_pilot_gate_lib as vpg  # noqa: E402

REPO = HERE.parents[1]
DEFAULT_SWEEP = REPO / "results/defense_attempt_inventory/pgd_epsilon_frontier/val_sweep/eps0015"
DEFAULT_FRONTIER = REPO / "results/defense_attempt_inventory/pgd_epsilon_frontier/val_sweep/eps0015_frontier_results.csv"

# Gate thresholds — mirror automation/acceptance/val-pilot-gate.yaml + design §5. Read here from a
# fixed dict; a future iteration should load them from the acceptance file directly.
THRESHOLDS = {
    "auroc_nogo_below": 0.88, "strong_rfall010_min": 0.70, "strong_auroc_min": 0.90,
    "strong_clean_degrade_max_pp": 5.0, "review_rfall010_lo": 0.50, "review_rfall010_hi": 0.70,
    "review_auroc_lo": 0.88, "review_auroc_hi": 0.90,
}
REFERENCE_FRONTIER = {"val_recall_at_far_le_10": 0.477}

TEST_TOKENS = ("_test_", "_legacy_")


class TestReadRefused(RuntimeError):
    pass


def _assert_not_test(path: Path) -> None:
    low = str(path).lower()
    if any(t in low for t in TEST_TOKENS):
        raise TestReadRefused(f"refused to open a non-validation artifact: {path}")


def _read_frontier_metrics(frontier_csv: Path) -> dict[str, dict]:
    """Map each model axis -> its metric dict, translated to the lib's metric names.
    Only reads the validation frontier results file; refuses a test path."""
    _assert_not_test(frontier_csv)
    out: dict[str, dict] = {}
    if not frontier_csv.exists():
        return out
    with frontier_csv.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if str(row.get("split", "")).lower() != "val":
                continue  # scanner only consumes validation rows, by construction
            model = row["model"]
            out[model] = {
                "auroc": _f(row.get("val_auroc")),
                "recall": _f(row.get("recall_far10")),
                "far": _f(row.get("FAR_far10")),
                "rfall_at_far_010": _f(row.get("recall_far10")),
                "rfall_at_far_020": _f(row.get("recall_far20")),
                "clean_recall_degradation_pp": None,  # not present in this artifact set
                "operating_tau_far10": _f(row.get("tau_far10")),
                "h15_pass_val": row.get("H15_pass_val"),
                "f20_pass_val": row.get("F20_pass_val"),
            }
    return out


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _find_axis_val_csv(sweep_dir: Path, axis: str) -> Path | None:
    """The PGD validation probability CSV for an axis, if present. Never returns a test path."""
    for p in sorted(sweep_dir.glob(f"{axis}_*pgd_probabilities_val_*.csv")):
        _assert_not_test(p)
        return p
    return None


def _find_axis_metadata_path(sweep_dir: Path, axis: str) -> Path | None:
    """Sibling metadata JSON path for an axis, if one exists (design §2). Never returns a test path."""
    for p in sorted(sweep_dir.glob(f"{axis}_*metadata*.json")):
        _assert_not_test(p)
        return p
    return None


def _find_axis_metadata(sweep_dir: Path, axis: str) -> dict | None:
    """Parsed sibling metadata JSON for an axis, if one exists (design §2). Absent here by design
    of the historical artifact set — the scanner reports that honestly rather than inventing one."""
    p = _find_axis_metadata_path(sweep_dir, axis)
    if p is None:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _display_path(p: Path | None) -> str | None:
    """Repo-relative display form of a path, falling back to its resolved absolute form."""
    if p is None:
        return None
    resolved = p.resolve()
    try:
        return str(resolved.relative_to(REPO.resolve()))
    except ValueError:
        return str(resolved)


def scan(sweep_dir: Path, frontier_csv: Path) -> list[dict]:
    metrics_by_axis = _read_frontier_metrics(frontier_csv)
    # Axis list = distinct prefixes of the val PGD CSVs actually on disk.
    axes = sorted({p.name.split("_eps")[0] for p in sweep_dir.glob("*pgd_probabilities_val_*.csv")})
    reports: list[dict] = []
    for axis in axes:
        val_csv = _find_axis_val_csv(sweep_dir, axis)
        metadata_path = _find_axis_metadata_path(sweep_dir, axis)
        metadata = _find_axis_metadata(sweep_dir, axis)
        metrics = metrics_by_axis.get(axis)
        checkpoint_path = Path(metadata["checkpoint"]) if metadata and metadata.get("checkpoint") else None

        verification = vpg.verify_pilot(
            probabilities_csv=val_csv, metadata=metadata,
            checkpoint_path=checkpoint_path, metrics=metrics)

        # Metrics-only verdict, clearly separated from provenance completeness. This tells the user
        # whether the SCIENCE looks strong even when the evidence CHAIN is incomplete — never an
        # authorization.
        metrics_verdict, mv_reasons = (None, [])
        if metrics is not None:
            metrics_verdict, mv_reasons = vpg.compute_verdict(
                metrics=metrics, thresholds=THRESHOLDS,
                reference_frontier=REFERENCE_FRONTIER, integrity_ok=True)

        reports.append({
            "axis": axis,
            "val_csv": _display_path(val_csv),
            "metadata_path": _display_path(metadata_path),
            "has_metadata_json": metadata is not None,
            "has_checkpoint_binding": checkpoint_path is not None,
            "provenance_status": verification.status,
            "provenance_reasons": verification.reasons,
            "checkpoint_sha256": verification.checkpoint_sha256,
            "pilot_fields": verification.fields,
            "metrics": metrics,
            "metrics_only_verdict": metrics_verdict,
            "metrics_only_reasons": mv_reasons,
        })
    return reports


# ---------------------------------------------------------------- receipt writing (design §7/§10.4)
VAL_PILOT_RECEIPTS_DIR = REPO / "automation" / "val_pilot_receipts"
SCANNER_VERSION = "val_pilot_scan.py step4-2026-07-20"


def write_receipts(reports: list[dict], out_dir: Path = VAL_PILOT_RECEIPTS_DIR) -> list[Path]:
    """Write one JSON pilot receipt (design §7, receipt_version 2) per VERIFIED report, to
    `out_dir` ONLY. Writes nothing for NO-GO/NEEDS-REVIEW reports — a receipt asserts a pilot IS
    complete (§7: "VERIFIED — the read-only scanner has confirmed..."), never a failed one.

    `out_dir` is not exposed on the CLI: it is fixed to automation/val_pilot_receipts/ so this can
    never be pointed at results/ (design §9.4: "writes only its own receipts directory ... never
    inside existing result trees").
    """
    if "results" in out_dir.resolve().parts:
        raise RuntimeError(f"refusing to write pilot receipts under a results/ tree: {out_dir}")

    written: list[Path] = []
    verified_utc = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for r in reports:
        if r["provenance_status"] != vpg.VERIFIED:
            continue
        fields = r.get("pilot_fields") or {}
        run_name, seed, epsilon = fields.get("run_name"), fields.get("seed"), fields.get("epsilon")
        if not run_name or seed is None or epsilon is None:
            # verify_pilot() guarantees these for a VERIFIED status; defensive, not expected.
            continue
        m = r.get("metrics") or {}
        receipt = {
            "receipt_version": 2,
            "run_name": run_name, "seed": seed, "epsilon": epsilon,
            "checkpoint_path": fields.get("checkpoint"),
            "checkpoint_sha256": r.get("checkpoint_sha256"),
            "split": fields.get("split"),
            "artifacts": {
                "probabilities_csv": r.get("val_csv"),
                "metadata_json": r.get("metadata_path"),
                "analysis": None,
            },
            "metrics": {
                "recall": m.get("recall"), "far": m.get("far"), "auroc": m.get("auroc"),
                "rfall_at_far_020": m.get("rfall_at_far_020"),
                "rfall_at_far_010": m.get("rfall_at_far_010"),
                "rfall_at_far_005": None,
                "clean_recall_degradation_pp": m.get("clean_recall_degradation_pp"),
            },
            "gate_verdict": r.get("metrics_only_verdict"),
            "novelty_judgment": None,
            "verified_utc": verified_utc,
            "scanner_version": SCANNER_VERSION,
            "acceptance": None,
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{run_name}_{seed}_eps{epsilon}.json".replace("/", "_").replace(" ", "_")
        out_path = out_dir / safe_name
        out_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        written.append(out_path)
    return written


def _print_human(reports: list[dict]) -> None:
    print("Val-pilot scan (read-only; writes nothing; no verdict authorizes a test read)\n")
    for r in reports:
        m = r["metrics"] or {}
        print(f"— {r['axis']}")
        print(f"    provenance : {r['provenance_status']}  ({', '.join(r['provenance_reasons'])})")
        print(f"    metadata/ckpt binding : {'yes' if r['has_metadata_json'] else 'MISSING'}"
              f" / {'yes' if r['has_checkpoint_binding'] else 'MISSING'}")
        if m:
            print(f"    val metrics : AUROC={m.get('auroc')}  recall@FAR10={m.get('rfall_at_far_010')}"
                  f"  FAR={m.get('far')}  recall@FAR20={m.get('rfall_at_far_020')}")
            print(f"    clean-degradation : {m.get('clean_recall_degradation_pp')} "
                  "(not in this artifact set)")
        print(f"    metrics-only verdict : {r['metrics_only_verdict']} "
              f"({', '.join(r['metrics_only_reasons'])})")
        print(f"    -> {_interpretation(r)}\n")


def _interpretation(r: dict) -> str:
    if r["provenance_status"] == vpg.VERIFIED:
        return "COMPLETE pilot; verdict stands (still requires separate human approval for any test read)."
    gaps = []
    if not r["has_metadata_json"]:
        gaps.append("metadata JSON")
    if not r["has_checkpoint_binding"]:
        gaps.append("checkpoint hash-binding")
    gap_str = " + ".join(gaps) if gaps else "provenance"
    return (f"INCOMPLETE for gate purposes (missing {gap_str}). Metrics may look strong, but a "
            "frozen test read cannot be justified until the pilot is regenerated with a metadata "
            "JSON recording the checkpoint path (for hash-binding).")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Val-pilot scanner (read-only by default; --write-receipts writes pilot "
                     "receipts for VERIFIED pilots only, to automation/val_pilot_receipts/).")
    ap.add_argument("--sweep-dir", type=Path, default=DEFAULT_SWEEP)
    ap.add_argument("--frontier-csv", type=Path, default=DEFAULT_FRONTIER)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write-receipts", action="store_true",
                     help="Write one JSON pilot receipt per VERIFIED pilot to "
                          "automation/val_pilot_receipts/ (design §10 step 4). No effect on "
                          "NO-GO/NEEDS-REVIEW pilots; never writes under results/.")
    args = ap.parse_args(argv)
    if not args.sweep_dir.exists():
        print(f"sweep dir not found: {args.sweep_dir}", file=sys.stderr)
        return 2
    reports = scan(args.sweep_dir, args.frontier_csv)
    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        _print_human(reports)
    if args.write_receipts:
        written = write_receipts(reports)
        if written:
            print(f"\nWrote {len(written)} pilot receipt(s) to "
                  f"{VAL_PILOT_RECEIPTS_DIR.relative_to(REPO)}:")
            for p in written:
                print(f"  {p.relative_to(REPO)}")
        else:
            print("\nWrote 0 pilot receipts (no VERIFIED pilots in this scan).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
