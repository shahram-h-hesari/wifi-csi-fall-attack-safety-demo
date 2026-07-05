"""
############################################################################################
##                                                                                        ##
##   !!!  D14 SINGLE LOCKED HELD-OUT TEST READ  --  DO NOT RUN WITHOUT EXPLICIT APPROVAL  !! ##
##                                                                                        ##
##   This script performs the ONE and ONLY held-out test read authorized for D14, and    ##
##   only if the validation gate has ALREADY PASSED. It is the terminal step of the F20   ##
##   attempt sequence. Running it consumes the single D14 test read; there is no second   ##
##   read, no threshold re-selection, and no test sweep. It applies ONLY the thresholds   ##
##   frozen by the validation gate (primary cap-0.17, secondary cap-0.20 comparison).     ##
##                                                                                        ##
##   Refuses to run unless BOTH:                                                          ##
##     * results/d14_partial_auc_low_far_ranking/d14_frozen_gate_thresholds.json exists   ##
##       (written only on a D14_GATE_PASS_NEEDS_APPROVAL verdict), AND                     ##
##     * the flag --i-understand-this-consumes-the-single-d14-test-read is passed.        ##
##                                                                                        ##
############################################################################################

D14 pre-registration: 20260704_d14_partial_auc_low_far_preregistration.md
(thesis commit 7ee228369052461682741a372a1ac2c3209fecb1).

This file is committed as a STUB/guarded runner in D14 Phase 1. It is NOT to be run during Phase 1.
It exists so the eventual, approved single test read is auditable and impossible to run by accident.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import d14_common as C  # noqa: E402

APPROVAL_FLAG = "--i-understand-this-consumes-the-single-d14-test-read"
FROZEN_JSON = C.D14_RESULTS_ROOT / "d14_frozen_gate_thresholds.json"


def parse_args():
    p = argparse.ArgumentParser(
        description="D14 SINGLE locked held-out test read (guarded; approval required).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument(APPROVAL_FLAG, dest="approved", action="store_true",
                   help="Required acknowledgement that this consumes the single D14 test read.")
    return p.parse_args()


def confusion(y, s, tau):
    tp = fn = fp = tn = 0
    for yi, si in zip(y, s):
        pred = si >= tau
        if yi == 1:
            tp += pred; fn += not pred
        else:
            fp += pred; tn += not pred
    return tp, fn, fp, tn


def load_scores(path: Path):
    import csv
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    y = [int(r["fall_true_binary"]) for r in rows]
    s = [float(r["fall_probability"]) for r in rows]
    return y, s


def main():
    args = parse_args()

    if not FROZEN_JSON.exists():
        raise SystemExit(
            "REFUSED: no frozen-gate-thresholds file found "
            f"({FROZEN_JSON}). The validation gate has not emitted a PASS. "
            "No held-out test read is authorized. Exiting without touching test.")
    if not args.approved:
        raise SystemExit(
            "REFUSED: the single-test-read acknowledgement flag was not provided.\n"
            f"Re-run with {APPROVAL_FLAG} ONLY after explicit human approval.\n"
            "Exiting without touching the held-out test split.")

    frozen = json.loads(FROZEN_JSON.read_text(encoding="utf-8"))
    config = frozen["chosen_config"]
    seed = frozen["median_seed"]
    tau_primary = frozen["primary_frozen_threshold"]
    tau_secondary = frozen["secondary_frozen_threshold"]
    best_ckpt = (C.D14_RESULTS_ROOT / f"config_{config}" / f"seed{seed}"
                 / f"d14_config_{config}_seed{seed}_best.pt")
    if not best_ckpt.exists():
        raise SystemExit(f"REFUSED: chosen best checkpoint not found: {best_ckpt}")

    print("=" * 78)
    print("D14 SINGLE LOCKED HELD-OUT TEST READ -- approval flag present, frozen thresholds loaded.")
    print(f"  config={config} seed={seed} best_ckpt={best_ckpt.name}")
    print(f"  primary cap-0.17 frozen threshold  = {tau_primary}")
    print(f"  secondary cap-0.20 frozen threshold = {tau_secondary}")
    print("  thresholds are FROZEN and applied as-is; no re-selection, no sweep.")
    print("=" * 78)

    # Export TEST scores for the chosen checkpoint (the single authorized test contact).
    test_eval_dir = C.D14_RESULTS_ROOT / f"config_{config}" / f"seed{seed}" / "test_eval"
    run_name = f"d14_config_{config}_seed{seed}"
    cmd = [sys.executable, str(C.REPO / "scripts" / "export_probability_predictions.py"),
           "--checkpoint", str(best_ckpt), "--model", "lenet",
           "--epsilon", str(C.PGD_EPSILON), "--pgd-steps", str(C.PGD_STEPS),
           "--run-name", run_name, "--out-dir", str(test_eval_dir), "--split", "test"]
    subprocess.run(cmd, check=True)

    test_pgd = test_eval_dir / f"{run_name}_pgd_probabilities_test_epsilon_0_03.csv"
    y, s = load_scores(test_pgd)
    if len(y) != 500 or sum(y) != 45:
        raise SystemExit(f"test split sanity failed: expected 500/45, got {len(y)}/{sum(y)}")

    out = {}
    for label, tau in [("primary_cap017", tau_primary), ("secondary_cap020", tau_secondary)]:
        if tau is None:
            continue
        tp, fn, fp, tn = confusion(y, s, tau)
        recall = tp / (tp + fn) if (tp + fn) else float("nan")
        far = fp / (fp + tn) if (fp + tn) else float("nan")
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        f20 = recall >= 0.80 and far <= 0.20
        out[label] = {"threshold": tau, "TP": tp, "FN": fn, "FP": fp, "TN": tn,
                      "recall": recall, "FAR": far, "precision": precision, "F1": f1,
                      "F20_met": f20}
        print(f"[{label}] tau={tau:.6f} TP/FN/FP/TN={tp}/{fn}/{fp}/{tn} "
              f"recall={recall:.4f} FAR={far:.4f} F20={'YES' if f20 else 'no'}")

    result_path = C.D14_RESULTS_ROOT / "D14_LOCKED_TEST_RESULT.json"
    result_path.write_text(json.dumps(
        {"config": config, "seed": seed, "single_test_read": True, "results": out,
         "note": "D14 single locked held-out test read; thresholds frozen from validation gate; "
                 "no re-selection or sweep. F20 chase ends with this read."},
        indent=2), encoding="utf-8")
    print(f"[write] {result_path.relative_to(C.REPO)}")
    print("[done] D14 single locked test read complete. The F20 chase ends here.")


if __name__ == "__main__":
    main()
