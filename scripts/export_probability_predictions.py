"""
Per-window probability / logit export for safety-guided defense checkpoints.

Purpose:
    LOGGING/EXPORT ONLY. Loads a frozen checkpoint and, for the clean / FGSM /
    PGD conditions at a fixed evaluation epsilon, writes a per-window CSV that
    includes the full seven-class softmax probabilities and raw logits in
    addition to the argmax prediction. This is the data needed for later binary
    fall-alert threshold calibration and class-source analysis; the existing
    `run_converged_attacks.py` only saves the argmax confidence.

    This script does NOT train, does NOT modify the model, and does NOT change
    the attack/eval protocol. Attack generation is delegated to
    `run_converged_attacks.generate_attacked_batch` so the perturbations are
    byte-identical to the frozen evaluation pipeline (FGSM single-step; PGD
    L-infinity, steps=10, alpha=epsilon/6; no value clamp on processed CSI).

Scope: window-level, digital-domain, white-box; processed CSI tensors only.

Commands:
    python scripts/export_probability_predictions.py \
        --checkpoint checkpoints/safety_guided_defense/seed43/<ckpt>.pt \
        --model lenet --epsilon 0.03 --run-name variantD_bySafetyScore \
        --out-dir results/safety_guided_defense/seed43/test_eval --split test
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import sys

import numpy as np
import torch
import torch.nn as nn


def import_modules():
    experiment_dir = Path(__file__).resolve().parents[1]
    scripts_dir = experiment_dir / "scripts"
    benchmark_dir = experiment_dir / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import train_converged_clean_baseline as s1
    s1.patch_sensefi_dataset_loader(benchmark_dir)
    if str(benchmark_dir) not in sys.path:
        sys.path.insert(0, str(benchmark_dir))
    import run_converged_attacks as rca
    from model_factory import build_model
    return experiment_dir, benchmark_dir, s1, rca, build_model


def parse_args():
    p = argparse.ArgumentParser(description="Per-window probability/logit export (logging only).")
    p.add_argument("--checkpoint", required=True, help="Path to the frozen checkpoint (.pt).")
    p.add_argument("--model", default="lenet")
    p.add_argument("--epsilon", type=float, default=0.03)
    p.add_argument("--pgd-steps", type=int, default=10)
    p.add_argument("--pgd-alpha", type=float, default=None, help="Default epsilon/6.")
    p.add_argument("--run-name", required=True, help="Output filename prefix.")
    p.add_argument("--out-dir", required=True, help="Output directory for the probability CSVs.")
    p.add_argument("--split", choices=["test", "legacy"], default="test")
    p.add_argument("--seed", type=int, default=0, help="Loader batching seed only (no effect on attacks).")
    return p.parse_args()


def main():
    args = parse_args()
    experiment_dir, benchmark_dir, s1, rca, build_model = import_modules()

    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.is_absolute():
        checkpoint_path = experiment_dir / checkpoint_path
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = experiment_dir / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    s1.set_seed(args.seed)
    data = s1.load_raw_ut_har(benchmark_dir)
    _, _, test_loader, split_sizes = s1.build_loaders(data, 64)
    if args.split == "test":
        loader = test_loader
    else:
        legacy_X = torch.cat((data["X_val"], data["X_test"]), 0)
        legacy_y = torch.cat((data["y_val"], data["y_test"]), 0)
        loader = torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(legacy_X, legacy_y),
            batch_size=256, shuffle=False, drop_last=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    state = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model = build_model(args.model).to(device)
    model.load_state_dict(state["model_state_dict"], strict=True)
    model.eval()
    criterion = nn.CrossEntropyLoss()

    alpha = args.pgd_alpha if args.pgd_alpha is not None else args.epsilon / 6.0
    eps_token = rca.epsilon_to_token(args.epsilon)
    class_names = s1.CLASS_NAMES
    n_classes = s1.NUM_CLASSES
    fall_idx = s1.FALL_CLASS_INDEX

    # condition -> (attack, epsilon, alpha, steps)
    conditions = [
        ("clean", "fgsm", 0.0, 0.0, 0),       # epsilon 0 => no perturbation
        ("fgsm", "fgsm", args.epsilon, 0.0, 0),
        ("pgd", "pgd", args.epsilon, alpha, args.pgd_steps),
    ]

    prob_cols = [f"prob_{class_names[i].replace(' ', '_')}" for i in range(n_classes)]
    logit_cols = [f"logit_{class_names[i].replace(' ', '_')}" for i in range(n_classes)]
    fieldnames = (["sample_id", "condition", "epsilon", "true_label", "true_class_name",
                   "predicted_label", "predicted_class_name", "fall_true_binary",
                   "fall_pred_binary", "max_confidence", "fall_probability"]
                  + prob_cols + logit_cols)

    written = []
    for cond_name, attack, eps, a, steps in conditions:
        out_path = out_dir / f"{args.run_name}_{cond_name}_probabilities_{args.split}_epsilon_{eps_token}.csv"
        sample_id = 0
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for inputs, labels in loader:
                inputs = inputs.to(device).float()
                labels = labels.to(device).long()
                if eps == 0.0:
                    adv = inputs.detach()
                else:
                    adv = rca.generate_attacked_batch(model, inputs, labels, criterion,
                                                      attack, eps, a, steps)
                with torch.no_grad():
                    logits = model(adv).float()
                    probs = torch.softmax(logits, dim=1)
                    conf, preds = torch.max(probs, dim=1)
                logits_np = logits.cpu().numpy()
                probs_np = probs.cpu().numpy()
                labels_np = labels.cpu().numpy()
                preds_np = preds.cpu().numpy()
                conf_np = conf.cpu().numpy()
                for i in range(len(labels_np)):
                    t = int(labels_np[i]); pr = int(preds_np[i])
                    row = {
                        "sample_id": sample_id, "condition": cond_name,
                        "epsilon": f"{eps:.6f}", "true_label": t,
                        "true_class_name": class_names.get(t, f"unknown_{t}"),
                        "predicted_label": pr,
                        "predicted_class_name": class_names.get(pr, f"unknown_{pr}"),
                        "fall_true_binary": 1 if t == fall_idx else 0,
                        "fall_pred_binary": 1 if pr == fall_idx else 0,
                        "max_confidence": f"{float(conf_np[i]):.6f}",
                        "fall_probability": f"{float(probs_np[i][fall_idx]):.6f}",
                    }
                    for c in range(n_classes):
                        row[prob_cols[c]] = f"{float(probs_np[i][c]):.6f}"
                        row[logit_cols[c]] = f"{float(logits_np[i][c]):.6f}"
                    writer.writerow(row)
                    sample_id += 1
        written.append(out_path)
        print(f"[export] {cond_name:5s} split={args.split} eps={eps:.3f} -> {out_path.name} ({sample_id} windows)")

    print(f"[done] {args.run_name} probability/logit export complete ({len(written)} files).")


if __name__ == "__main__":
    main()
