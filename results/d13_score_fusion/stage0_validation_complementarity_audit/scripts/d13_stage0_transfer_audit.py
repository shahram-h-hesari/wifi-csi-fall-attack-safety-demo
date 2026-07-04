"""
D13 Step 0B - VALIDATION-ONLY shared-input transfer audit.

Purpose: Step 0A's saved-score complementarity was computed from INDEPENDENTLY per-model PGD
adversarial examples (each model attacked with its own gradients). A real fused rule would see one
shared attacked input. This script crafts PGD (epsilon=0.030, 10 steps, alpha=eps/6) adversarial
validation examples against each of the three source models in turn, then evaluates all three
models on each source's adversarial batch, producing a 3x3 transfer matrix.

VALIDATION SPLIT ONLY. No test-split path exists anywhere in this file (grep-verifiable). No
training. No fusion-weight fitting. Regenerates validation-only adversarial examples (byte-
identical attack settings to every other committed eval in this repo) since none were cached in a
form usable for cross-model transfer; original attack config (epsilon, steps, alpha rule) is
reused from run_converged_attacks.generate_attacked_batch, the same delegate used by
export_probability_predictions.py for all previously committed validation/test exports.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import torch

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "d13_score_fusion" / "stage0_validation_complementarity_audit"
BENCH_DIR = REPO / "third_party" / "WiFi-CSI-Sensing-Benchmark"

CHECKPOINTS = {
    "AFAC": REPO / "checkpoints/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/seed42_optionB_maxscore_best.pt",
    "D10": REPO / "checkpoints/safety_guided_defense/boundary_aware_selective_at/gairat/seed42/GR1/seed42_basat_gairat_GR1_v2macroF1_best.pt",
    "D11b": REPO / "checkpoints/safety_guided_defense/boundary_aware_selective_at/sat/seed42/SA1/seed42_basat_sat_SA1_v2lowFA_best.pt",
}
MODEL_ORDER = ["AFAC", "D10", "D11b"]

EPSILON = 0.03
PGD_STEPS = 10
PGD_ALPHA = EPSILON / 6.0

# FAR<=0.18 thresholds selected in Step 0A (frozen; must match d13_stage0_model_metrics.csv exactly)
THRESHOLDS_018 = {
    "AFAC": 0.168743,
    "D10": 0.087853,
    "D11b": 0.055186,
}
# Step 0A diagonal reference confusion counts at FAR<=0.18 (for the +/-2 validity check)
STEP0A_DIAGONAL_REFERENCE = {
    "AFAC": {"TP": 34, "FN": 10, "FP": 71, "TN": 381},
    "D10": {"TP": 32, "FN": 12, "FP": 81, "TN": 371},
    "D11b": {"TP": 36, "FN": 8, "FP": 80, "TN": 372},
}


def import_modules():
    scripts_dir = REPO / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import train_converged_clean_baseline as s1
    s1.patch_sensefi_dataset_loader(BENCH_DIR)
    if str(BENCH_DIR) not in sys.path:
        sys.path.insert(0, str(BENCH_DIR))
    import run_converged_attacks as rca
    from model_factory import build_model
    return s1, rca, build_model


def load_model(build_model, ckpt_path, device):
    state = torch.load(ckpt_path, map_location=device, weights_only=False)
    model = build_model("lenet").to(device)
    model.load_state_dict(state["model_state_dict"], strict=True)
    model.eval()
    return model


def confusion(y, s, tau):
    tp = fn = fp = tn = 0
    for yi, si in zip(y, s):
        pred = si >= tau
        if yi == 1:
            tp += pred
            fn += not pred
        else:
            fp += pred
            tn += not pred
    return tp, fn, fp, tn


def rates(tp, fn, fp, tn):
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    far = fp / (fp + tn) if (fp + tn) else float("nan")
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return recall, far, precision, f1


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s1, rca, build_model = import_modules()

    s1.set_seed(1337)
    data = s1.load_raw_ut_har(BENCH_DIR)
    _, val_loader, _, split_sizes = s1.build_loaders(data, 64)
    assert split_sizes["val"] == 496, f"expected 496 validation windows, got {split_sizes['val']}"

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    models = {name: load_model(build_model, path, device) for name, path in CHECKPOINTS.items()}
    criterion = torch.nn.CrossEntropyLoss()
    fall_idx = s1.FALL_CLASS_INDEX

    # Collect all validation windows once (deterministic order: shuffle=False, drop_last=False)
    all_inputs, all_labels = [], []
    for inputs, labels in val_loader:
        all_inputs.append(inputs.to(device).float())
        all_labels.append(labels.to(device).long())
    all_inputs = torch.cat(all_inputs, dim=0)
    all_labels = torch.cat(all_labels, dim=0)
    n_total = all_inputs.shape[0]
    y_np = all_labels.cpu().numpy().tolist()
    y_bin = [1 if yy == fall_idx else 0 for yy in y_np]
    n_fall = sum(y_bin)
    assert n_total == 496 and n_fall == 44, f"split mismatch: n={n_total} fall={n_fall}"
    print(f"[check] validation split loaded fresh for Step 0B: {n_total} windows, {n_fall} fall - OK")

    # Craft adversarial examples ONCE per source model (batched for memory/robustness)
    adv_batches = {}
    batch_size = 64
    for src_name, src_model in models.items():
        adv_chunks = []
        for start in range(0, n_total, batch_size):
            end = min(start + batch_size, n_total)
            chunk_in = all_inputs[start:end]
            chunk_lbl = all_labels[start:end]
            adv = rca.generate_attacked_batch(
                src_model, chunk_in, chunk_lbl, criterion, "pgd", EPSILON, PGD_ALPHA, PGD_STEPS)
            adv_chunks.append(adv.detach())
        adv_batches[src_name] = torch.cat(adv_chunks, dim=0)
        print(f"[attack] crafted PGD adversarial validation batch against source={src_name} "
              f"({adv_batches[src_name].shape[0]} windows)")

    # Evaluate every model on every source's adversarial batch -> 3x3 matrix
    matrix_rows = []
    fall_probs_cache = {}
    for eval_name, eval_model in models.items():
        for src_name in MODEL_ORDER:
            adv = adv_batches[src_name]
            with torch.no_grad():
                logits = eval_model(adv).float()
                probs = torch.softmax(logits, dim=1)
            fall_probs = probs[:, fall_idx].cpu().numpy().tolist()
            fall_probs_cache[(eval_name, src_name)] = fall_probs
            tau = THRESHOLDS_018[eval_name]
            tp, fn, fp, tn = confusion(y_bin, fall_probs, tau)
            recall, far, precision, f1 = rates(tp, fn, fp, tn)
            matrix_rows.append({
                "eval_model": eval_name, "source_model_(adv_crafted_against)": src_name,
                "threshold_FAR0.18": f"{tau:.6f}",
                "TP": tp, "FN": fn, "FP": fp, "TN": tn,
                "recall": f"{recall:.6f}", "FAR": f"{far:.6f}",
                "precision": f"{precision:.6f}", "F1": f"{f1:.6f}",
                "is_diagonal": eval_name == src_name,
            })

    with (OUT / "d13_stage0_transfer_matrix.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(matrix_rows[0].keys()))
        w.writeheader()
        w.writerows(matrix_rows)
    print(f"[write] {(OUT / 'd13_stage0_transfer_matrix.csv').relative_to(REPO)} ({len(matrix_rows)} rows)")

    # Validity check: diagonal cells vs Step 0A saved-score reference, +/-2 per confusion cell
    validity_report = {}
    step0b_valid = True
    for name in MODEL_ORDER:
        row = next(r for r in matrix_rows if r["eval_model"] == name and r["source_model_(adv_crafted_against)"] == name)
        ref = STEP0A_DIAGONAL_REFERENCE[name]
        diffs = {k: row[k] - ref[k] for k in ["TP", "FN", "FP", "TN"]}
        within_tol = all(abs(v) <= 2 for v in diffs.values())
        validity_report[name] = {"regenerated": {k: row[k] for k in ["TP", "FN", "FP", "TN"]},
                                  "step0A_reference": ref, "diff": diffs, "within_tolerance_2": within_tol}
        if not within_tol:
            step0b_valid = False

    diag_recalls = [float(r["recall"]) for r in matrix_rows if r["is_diagonal"]]
    offdiag_recalls = [float(r["recall"]) for r in matrix_rows if not r["is_diagonal"]]
    mean_diag = sum(diag_recalls) / len(diag_recalls)
    mean_offdiag = sum(offdiag_recalls) / len(offdiag_recalls)
    transfer_veto_pass = mean_offdiag >= mean_diag + 0.15

    if not step0b_valid:
        print("STEP0B_INVALID")

    summary = {
        "step0b_valid": step0b_valid,
        "validity_report": validity_report,
        "mean_diagonal_fall_recall": mean_diag,
        "mean_offdiagonal_fall_recall": mean_offdiag,
        "transfer_veto_condition": "mean_offdiag >= mean_diag + 0.15",
        "transfer_veto_pass": transfer_veto_pass,
        "epsilon": EPSILON, "pgd_steps": PGD_STEPS, "pgd_alpha": PGD_ALPHA,
        "seed": 1337,
    }
    with (OUT / "d13_stage0_transfer_validity_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    print(f"[write] {(OUT / 'd13_stage0_transfer_validity_summary.json').relative_to(REPO)}")
    print(f"[info] step0b_valid={step0b_valid} mean_diag={mean_diag:.4f} "
          f"mean_offdiag={mean_offdiag:.4f} transfer_veto_pass={transfer_veto_pass}")
    print("[done] Step 0B complete. NO test file was read at any point.")


if __name__ == "__main__":
    main()
