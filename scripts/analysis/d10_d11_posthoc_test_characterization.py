"""
POST-HOC test operating-region characterization for D10/D11 (labeling: this is
NOT frozen-threshold evidence; it sweeps held-out test scores after the fact,
exactly the same evidence type as the D8b AFAC-score post-hoc row). Purpose:
separate threshold-transfer failure from score-separability failure, and give
an apples-to-apples comparison against the D8b post-hoc reference.
"""

from __future__ import annotations

import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from d10_d11_locked_test_followup import (  # noqa: E402
    METHODS, OUT, TEST_EVAL, FAR_CAPS, load_rows, extract, confusion, rates,
    select_threshold, auroc, REPO)


def main():
    rows_out = []
    for m in METHODS:
        test_csv = TEST_EVAL / (
            f"{m['run_name']}_pgd_probabilities_test_epsilon_0_03.csv")
        ty, ts, _, _ = extract(load_rows(test_csv))
        a = auroc(ty, ts)
        for cap in FAR_CAPS:
            # identical sweep rule as validation selection, but ON TEST (post hoc)
            tau, tp, fn, fp, tn, rec, far = select_threshold(ty, ts, cap)
            rows_out.append({
                "method_id": m["id"], "run_name": m["run_name"],
                "evidence_type": "test post-hoc FAR sweep (characterization only)",
                "far_cap": cap, "posthoc_threshold": f"{tau:.6f}",
                "test_TP": tp, "test_FN": fn, "test_FP": fp, "test_TN": tn,
                "test_recall": f"{rec:.6f}", "test_FAR": f"{far:.6f}",
                "test_AUROC": f"{a:.6f}",
            })
    out_path = OUT / "d10_d11_posthoc_test_characterization.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    print(f"[write] {out_path.relative_to(REPO)} ({len(rows_out)} rows)")


if __name__ == "__main__":
    main()
