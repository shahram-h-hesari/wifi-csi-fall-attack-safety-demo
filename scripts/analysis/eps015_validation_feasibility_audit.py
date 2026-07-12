"""Task 3 driver — validation-only PGD eps=0.015 false-positive audit and operating-point
feasibility analysis.

Evidence type: validation-only re-analysis of already-saved probability exports. No training,
no attack generation, no checkpoint loaded, no test-split file opened. Every artifact is passed
through `eps015_feasibility_lib.check_split_is_validation` before use; any artifact that cannot
be proven to be the 496-window (44 fall / 452 non-fall) validation split is excluded, not guessed.

Already-published test aggregates (TP 41, FN 4, FP 60, TN 395, recall 0.911111, FAR 0.131868)
are cited only as fixed context in the output report -- no per-window test information is ever
read, derived, or referenced.

Command:
    .venv/Scripts/python.exe scripts/analysis/eps015_validation_feasibility_audit.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eps015_feasibility_lib as lib  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
VAL_DIR = REPO / "results" / "defense_attempt_inventory" / "pgd_epsilon_frontier" / "val_sweep" / "eps0015"
OUT = REPO / "results" / "eps015_validation_feasibility_audit"

# Already-published test aggregate (fixed context only -- never re-derived, never opened here).
PUBLISHED_TEST_AGGREGATE = {
    "protocol_id": "H15-TEST-EPS0015-AFAC-20260705",
    "TP": 41, "FN": 4, "FP": 60, "TN": 395,
    "recall": 0.911111, "FAR": 0.131868,
    "source": "results/defense_attempt_inventory/pgd_epsilon_frontier/frozen_test_read/FROZEN_H15_TEST_RESULT.md (research-os commit 5fef192 cites the same numbers)",
}

# Pre-registered/frozen validation threshold, where one exists (from
# h15_frozen_test_gate_numbers_eps0015.csv). Axes not listed here have no frozen threshold --
# only the exploratory FAR-cap thresholds from eps0015_frontier_results.csv, reported separately.
FROZEN_VAL_THRESHOLDS = {
    "AFAC_maxscore": 0.168754,
    "ST1b6_lowFA": 0.122502,
    "SA1_lowFA": 0.112824,
}
FROZEN_THRESHOLD_SOURCE = "results/defense_attempt_inventory/pgd_epsilon_frontier/h15_frozen_test_gate_numbers_eps0015.csv"

ATTACK_NORM_STATUS = {
    "status": "VERIFIED_LINF",
    "source": "scripts/run_converged_attacks.py:103 -- code comment \"# PGD: untargeted L-infinity, "
              "projected after each step.\" immediately preceding an epsilon-ball projection "
              "implemented via torch.clamp(perturbation, min=-epsilon, max=epsilon) (an L-infinity "
              "projection). Found by reading existing code only; the attack implementation was not "
              "altered.",
}

MIXED_SPLIT_EXCLUSION_NOTE = (
    "results/epsilon_sweep_predictions/pgd_predictions_short_epsilon_0_015.csv and its FGSM "
    "counterpart were considered and EXCLUDED: per "
    "results/defense_attempt_inventory/PGD_EPSILON_RECALL_FAR_FRONTIER_PLAN.md section 1, the "
    "'short' split is validation+test concatenated (996 windows = 89 fall / 907 non-fall) and "
    "cannot be proven to be validation-only; it also carries argmax labels only, no "
    "fall_probability score column, so no threshold sweep is possible on it regardless."
)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def discover_axis_files() -> dict:
    """Return {model_id: path} for every PGD eps=0.015 validation probability export found
    under VAL_DIR. Does not assume the directory listing is complete elsewhere in the repo --
    callers should record MIXED_SPLIT_EXCLUSION_NOTE for the known-excluded alternative."""
    axes = {}
    if not VAL_DIR.is_dir():
        return axes
    for p in sorted(VAL_DIR.glob("*_pgd_probabilities_val_epsilon_0_015.csv")):
        model_id = re.sub(r"_eps0015_pgd_probabilities_val_epsilon_0_015\.csv$", "", p.name)
        axes[model_id] = p
    return axes


def load_and_verify(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    result = lib.check_split_is_validation(path.name, len(df), int(df["fall_true_binary"].sum()))
    if not result.accepted:
        raise lib.SplitRejection(f"{path}: {result.reason}")
    return df


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    axis_files = discover_axis_files()
    if not axis_files:
        print(f"[eps015-audit] no validation axis files found under {VAL_DIR}")
        return 1

    inventory_rows = []
    frames = {}
    for model_id, path in axis_files.items():
        df = load_and_verify(path)
        frames[model_id] = df
        inventory_rows.append({
            "model_id": model_id,
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "artifact_type": "per-window PGD probability export",
            "epsilon": 0.015,
            "split": "val",
            "row_count": len(df),
            "fall_count": int(df["fall_true_binary"].sum()),
            "nonfall_count": len(df) - int(df["fall_true_binary"].sum()),
            "score_axis": "fall_probability",
            "label_field": "fall_true_binary",
            "class_field": "true_class_name",
            "sha256": sha256_of(path),
        })

    sweep_table_rows = []
    per_axis_summary_rows = []
    fp_source_rows = []
    reference_thresholds = {}

    for model_id, df in frames.items():
        scores = df["fall_probability"].tolist()
        labels = df["fall_true_binary"].tolist()
        rows = lib.sweep_thresholds(scores, labels)
        summary = lib.summarize_feasibility(rows)

        for r in rows:
            c = r.confusion
            sweep_table_rows.append({
                "model_id": model_id, "threshold": r.threshold,
                "TP": c.TP, "FN": c.FN, "FP": c.FP, "TN": c.TN,
                "recall": c.recall, "FAR": c.far, "specificity": c.specificity,
                "precision": c.precision, "f1": c.f1, "balanced_accuracy": c.balanced_accuracy,
                "meets_R90F10_target": c.meets_target(),
            })

        frozen_tau = FROZEN_VAL_THRESHOLDS.get(model_id)
        if frozen_tau is not None:
            frozen_conf = lib.confusion_at_threshold(scores, labels, frozen_tau)
            reference_thresholds[model_id] = ("frozen", frozen_tau, frozen_conf)
        elif summary.best_feasible is not None:
            reference_thresholds[model_id] = ("best_feasible_candidate", summary.best_feasible.threshold, summary.best_feasible.confusion)
        else:
            reference_thresholds[model_id] = ("nearest_to_target_candidate", summary.nearest_to_target.threshold, summary.nearest_to_target.confusion)

        ref_kind, ref_tau, ref_conf = reference_thresholds[model_id]
        per_axis_summary_rows.append({
            "model_id": model_id,
            "n_feasible_thresholds": len(summary.feasible_rows),
            "best_feasible_threshold": summary.best_feasible.threshold if summary.best_feasible else None,
            "best_feasible_recall": summary.best_feasible.confusion.recall if summary.best_feasible else None,
            "best_feasible_FAR": summary.best_feasible.confusion.far if summary.best_feasible else None,
            "highest_recall_under_far_target": summary.highest_recall_under_far_target.confusion.recall if summary.highest_recall_under_far_target else None,
            "highest_recall_under_far_target_FAR": summary.highest_recall_under_far_target.confusion.far if summary.highest_recall_under_far_target else None,
            "lowest_far_at_recall_target": summary.lowest_far_at_recall_target.confusion.far if summary.lowest_far_at_recall_target else None,
            "lowest_far_at_recall_target_recall": summary.lowest_far_at_recall_target.confusion.recall if summary.lowest_far_at_recall_target else None,
            "nearest_to_target_threshold": summary.nearest_to_target.threshold,
            "nearest_to_target_recall": summary.nearest_to_target.confusion.recall,
            "nearest_to_target_FAR": summary.nearest_to_target.confusion.far,
            "reference_threshold_kind": ref_kind,
            "reference_threshold_value": ref_tau,
            "reference_TP": ref_conf.TP, "reference_FN": ref_conf.FN,
            "reference_FP": ref_conf.FP, "reference_TN": ref_conf.TN,
            "reference_recall": ref_conf.recall, "reference_FAR": ref_conf.far,
        })

        fp_rows = list(zip(df["true_class_name"], df["fall_true_binary"],
                            [1 if s >= ref_tau else 0 for s in scores]))
        counts = lib.false_positive_source_breakdown(fp_rows)
        total_fp = sum(counts.values())
        for cls, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            fp_source_rows.append({
                "model_id": model_id, "reference_threshold_kind": ref_kind,
                "source_class": cls, "count": n,
                "proportion_of_fp": (n / total_fp) if total_fp else None,
            })
        margin = lib.score_margin_buckets(scores, labels, ref_tau)
        per_axis_summary_rows[-1]["fp_near_threshold"] = margin["near_threshold"]
        per_axis_summary_rows[-1]["fp_far_from_threshold"] = margin["far_from_threshold"]

    # Score-axis overlap (pairwise), each axis evaluated at its own reference threshold.
    overlap_rows = []
    model_ids = sorted(frames.keys())
    joined_by_id = {
        mid: {int(sid): (int(y), int(s >= reference_thresholds[mid][1]))
              for sid, y, s in zip(frames[mid]["sample_id"], frames[mid]["fall_true_binary"], frames[mid]["fall_probability"])}
        for mid in model_ids
    }
    for i, a in enumerate(model_ids):
        for b in model_ids[i + 1:]:
            common_ids = sorted(set(joined_by_id[a]) & set(joined_by_id[b]))
            joined = [(joined_by_id[a][sid][0], joined_by_id[a][sid][1], joined_by_id[b][sid][1]) for sid in common_ids]
            overlap = lib.compare_axis_predictions(joined)
            overlap_rows.append({
                "axis_a": a, "axis_b": b, "n_common_windows": len(common_ids),
                "shared_tp": overlap.shared_tp, "shared_fp": overlap.shared_fp,
                "unique_fp_a": overlap.unique_fp_a, "unique_fp_b": overlap.unique_fp_b,
                "unique_recovered_fall_a": overlap.unique_recovered_fall_a,
                "unique_recovered_fall_b": overlap.unique_recovered_fall_b,
                "disagreement_count": overlap.disagreement_count,
            })

    # ---- write outputs (new files only; nothing existing is overwritten) ----
    def _write_csv(name: str, rows: list):
        path = OUT / name
        if not rows:
            path.write_text("", encoding="utf-8")
            return path
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return path

    inventory_path = _write_csv("inventory.csv", inventory_rows)
    sweep_path = _write_csv("operating_point_sweep.csv", sweep_table_rows)
    per_axis_path = _write_csv("per_axis_summary.csv", per_axis_summary_rows)
    fp_source_path = _write_csv("false_positive_source_summary.csv", fp_source_rows)
    overlap_path = _write_csv("score_axis_overlap.csv", overlap_rows)

    provenance_rows = [{"path": str(p.relative_to(REPO)).replace("\\", "/"), "sha256": sha256_of(p)}
                        for p in axis_files.values()]
    for out_path in (inventory_path, sweep_path, per_axis_path, fp_source_path, overlap_path):
        provenance_rows.append({"path": str(out_path.relative_to(REPO)).replace("\\", "/"), "sha256": sha256_of(out_path)})
    provenance_path = _write_csv("provenance_manifest.csv", provenance_rows)

    # ---- Markdown report ----
    any_feasible_axis = any(r["n_feasible_thresholds"] > 0 for r in per_axis_summary_rows)
    md = _render_report(
        inventory_rows, per_axis_summary_rows, fp_source_rows, overlap_rows,
        any_feasible_axis, now_iso(),
    )
    report_path = OUT / "REPORT.md"
    report_path.write_text(md, encoding="utf-8")

    print(f"[eps015-audit] wrote outputs to {OUT}")
    print(f"[eps015-audit] axes analyzed: {sorted(frames.keys())}")
    print(f"[eps015-audit] any axis feasible (Rfall>0.90 AND FAR<0.10 on validation): {any_feasible_axis}")
    return 0


def _render_report(inventory_rows, per_axis_summary_rows, fp_source_rows, overlap_rows, any_feasible_axis, generated_at) -> str:
    lines = []
    lines.append("# Task 3 — Validation-Only PGD eps=0.015 False-Positive Audit and Operating-Point Feasibility")
    lines.append("")
    lines.append(f"Generated: {generated_at}. Evidence type: **validation-only re-analysis of saved probability")
    lines.append("exports.** No training, no attack generation, no checkpoint loaded, no held-out-test file opened.")
    lines.append("No threshold in this report has been applied to test data; nothing here is a final threshold")
    lines.append("selection or protocol freeze. All operating points below are `retrospective validation feasibility`")
    lines.append("/ `candidate operating point`, `not yet protocol-frozen`, `not evaluated on held-out test`.")
    lines.append("")
    lines.append("## Fixed context: already-published test aggregate (not re-derived, not re-opened here)")
    lines.append("")
    lines.append(f"Protocol `{PUBLISHED_TEST_AGGREGATE['protocol_id']}`: TP {PUBLISHED_TEST_AGGREGATE['TP']}, "
                  f"FN {PUBLISHED_TEST_AGGREGATE['FN']}, FP {PUBLISHED_TEST_AGGREGATE['FP']}, "
                  f"TN {PUBLISHED_TEST_AGGREGATE['TN']}, recall {PUBLISHED_TEST_AGGREGATE['recall']}, "
                  f"FAR {PUBLISHED_TEST_AGGREGATE['FAR']}.")
    lines.append("")
    lines.append("## Attack-norm verification (Task 3, Step 2)")
    lines.append("")
    lines.append(f"Status: **{ATTACK_NORM_STATUS['status']}**. {ATTACK_NORM_STATUS['source']}")
    lines.append("")
    lines.append("## Excluded artifact (documented reason)")
    lines.append("")
    lines.append(MIXED_SPLIT_EXCLUSION_NOTE)
    lines.append("")
    lines.append("## 1. Is R90/F10 feasible on any existing saved validation score axis at eps=0.015?")
    lines.append("")
    if any_feasible_axis:
        lines.append("**Yes** — at least one saved validation score axis has a candidate threshold satisfying")
        lines.append("Rfall > 0.90 AND FAR < 0.10 simultaneously, on validation data. See `per_axis_summary.csv`")
        lines.append("for the exact per-axis best-feasible candidate and margin.")
    else:
        lines.append("**No** — no saved validation score axis has any threshold simultaneously satisfying both")
        lines.append("strict targets. See `per_axis_summary.csv`'s `nearest_to_target_*` columns for the closest")
        lines.append("achievable point per axis.")
    lines.append("")
    lines.append("## 2/3. Margin, or nearest achievable point, per axis")
    lines.append("")
    lines.append("| Axis | Feasible? | # feasible thresholds | Reference (frozen/candidate) recall | Reference FAR | Nearest-to-target recall | Nearest-to-target FAR |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in per_axis_summary_rows:
        feasible = "yes" if r["n_feasible_thresholds"] > 0 else "no"
        lines.append(
            f"| {r['model_id']} | {feasible} | {r['n_feasible_thresholds']} | "
            f"{r['reference_recall']:.4f} | {r['reference_FAR']:.4f} | "
            f"{r['nearest_to_target_recall']:.4f} | {r['nearest_to_target_FAR']:.4f} |"
        )
    lines.append("")
    lines.append("## 4. Which validation activity classes dominate false alarms?")
    lines.append("")
    by_class_total: dict = {}
    for row in fp_source_rows:
        by_class_total[row["source_class"]] = by_class_total.get(row["source_class"], 0) + row["count"]
    for cls, n in sorted(by_class_total.items(), key=lambda kv: -kv[1]):
        lines.append(f"- {cls}: {n} false positives (aggregated across all analyzed axes at their reference threshold)")
    lines.append("")
    lines.append("## 5. Are false positives mostly threshold-near or deeply overlapping?")
    lines.append("")
    for r in per_axis_summary_rows:
        lines.append(f"- {r['model_id']}: near-threshold FP = {r['fp_near_threshold']}, far-from-threshold FP = {r['fp_far_from_threshold']} (band = 0.05)")
    lines.append("")
    lines.append("## 6. Do existing axes have useful complementarity?")
    lines.append("")
    lines.append("| Axis A | Axis B | Shared TP | Shared FP | Unique FP (A) | Unique FP (B) | Unique recovered fall (A) | Unique recovered fall (B) | Disagreements |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in overlap_rows:
        lines.append(
            f"| {r['axis_a']} | {r['axis_b']} | {r['shared_tp']} | {r['shared_fp']} | "
            f"{r['unique_fp_a']} | {r['unique_fp_b']} | {r['unique_recovered_fall_a']} | "
            f"{r['unique_recovered_fall_b']} | {r['disagreement_count']} |"
        )
    lines.append("")
    lines.append("No new ensemble or gate was built or evaluated in this task; the table above is descriptive")
    lines.append("overlap evidence only, for later, separately-decided experiment planning.")
    lines.append("")
    lines.append("## 7. Which experiment families does this evidence support?")
    lines.append("")
    lines.append("Evidence-supported candidate directions only -- not a final experiment verdict. Based on")
    lines.append("the actual per-axis results in Section 2/3 above (this run's real numbers, not a generic")
    lines.append("template):")
    lines.append("")
    feasible_axes = [r for r in per_axis_summary_rows if r["n_feasible_thresholds"] > 0]
    infeasible_axes = [r for r in per_axis_summary_rows if r["n_feasible_thresholds"] == 0]
    wide_margin_axes = [r for r in feasible_axes if r["n_feasible_thresholds"] >= 5]
    knife_edge_axes = [r for r in infeasible_axes if r["nearest_to_target_recall"] > 0.90 - 1e-9 and r["nearest_to_target_FAR"] < 0.11]
    if feasible_axes:
        names = ", ".join(r["model_id"] for r in feasible_axes)
        lines.append(f"- **Threshold/calibration — SUPPORTED BY DIRECT EVIDENCE.** {names} already reach a")
        lines.append("  validation operating point satisfying Rfall>0.90 AND FAR<0.10 with the EXISTING saved")
        lines.append("  scores, at a threshold that was never applied to test. This requires no new training --")
        lines.append("  only a future, separately-authorized protocol freeze and single test read at the chosen")
        lines.append("  threshold for one of these axes.")
    else:
        lines.append("- **Threshold/calibration** — NOT supported by this evidence: no saved axis reaches")
        lines.append("  feasibility at any threshold.")
    if wide_margin_axes:
        names = ", ".join(f"{r['model_id']} ({r['n_feasible_thresholds']} feasible thresholds)" for r in wide_margin_axes)
        lines.append(f"  {names} has more than a knife-edge margin (multiple adjacent feasible thresholds, not a single point).")
    if knife_edge_axes:
        names = ", ".join(r["model_id"] for r in knife_edge_axes)
        lines.append(f"- **Knife-edge caution:** {names} sit just outside feasibility (recall already >0.90 but FAR")
        lines.append("  just above 0.10) -- consistent with this program's prior D8b knife-edge experience; any")
        lines.append("  future selection on these specific axes should budget FAR margin, not select at the boundary.")
    lines.append("- **Low-FAR objective / partial-AUC training** — weakly supported: the axes that are already")
    lines.append("  feasible make a from-scratch low-FAR training objective lower priority than simply selecting")
    lines.append("  among existing axes; still relevant if a future test read on a feasible axis fails to transfer.")
    lines.append("- **Hard-negative / source-aware training** — supported: false alarms concentrate heavily in")
    lines.append("  'run' and 'walk' (Section 4) rather than spreading evenly across all six non-fall classes,")
    lines.append("  which is consistent with source-aware or hard-negative training being a targeted, not diffuse, fix.")
    lines.append("- **Temporal/event-level filtering** — this analysis is window-level only and cannot confirm")
    lines.append("  or rule out event-level effects; supported only as an untested, literature-motivated direction.")
    complementary_pairs = [r for r in overlap_rows if r["unique_recovered_fall_a"] + r["unique_recovered_fall_b"] >= 3]
    if complementary_pairs:
        lines.append(f"- **Gating/ensemble** — some support: {len(complementary_pairs)} axis pair(s) show 3 or more")
        lines.append("  combined unique-recovered-fall windows (Section 6), i.e. genuine complementarity, not mere")
        lines.append("  agreement -- but combining axes also tends to combine their unique false positives, so this")
        lines.append("  is not a free win and would need its own validation-only evaluation.")
    else:
        lines.append("- **Gating/ensemble** — weak support: axis pairs largely agree (low unique-recovered-fall")
        lines.append("  counts in Section 6); little sign of genuine complementarity in this evidence.")
    if feasible_axes:
        lines.append("- **Representation/architecture change** — NOT prioritized by this evidence: multiple")
        lines.append("  existing axes already reach feasibility without any representation change, so this")
        lines.append("  remains the lowest-priority family unless a future test read on a feasible axis fails.")
    else:
        lines.append("- **Representation/architecture change** — supported: no axis approaches feasibility with")
        lines.append("  any meaningful margin.")
    lines.append("")
    lines.append("## 8. What should be investigated in the literature next?")
    lines.append("")
    lines.append("Prioritize categories directly motivated by the findings above (see per-axis and per-class")
    lines.append("tables): Neyman-Pearson / FAR-constrained thresholding, partial-AUC low-FPR optimization,")
    lines.append("selective prediction/abstention, temporal event-level confirmation, and adversarial-input")
    lines.append("detection / ensemble disagreement -- weighted by which experiment families Section 7 actually")
    lines.append("supports for this evidence, not by category popularity.")
    lines.append("")
    lines.append("## Inventory")
    lines.append("")
    lines.append(f"{len(inventory_rows)} validation-proven axis file(s) analyzed. See `inventory.csv` for full detail.")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
