"""
DS-SGE Stage D (run within Stage A): adaptive full-gate PGD attack on S(x).

Mandatory evaluation-integrity step (Athalye et al.). The defense is the GATED
PIPELINE x -> (f_R, f_B) -> S(x) -> decision, so we attack the continuous gate
score S directly, not the individual specialists and not the hard threshold tau.

    S(x) = alpha * p_R(fall|x) + (1 - alpha) * p_B(fall|x)

Attacker objective (untargeted, safety-aware):
    true fall (y == fall):  push S DOWN  -> missed fall   (maximize -S)
    non-fall  (y != fall):  push S UP    -> false alarm   (maximize  S)
    batch loss = mean( where(y==fall, -S, S) );  PGD does gradient ASCENT.

The decision threshold tau is applied only AFTER the attack, to score the
adversarial windows (the attack itself never sees tau -> no hard-threshold
gradient masking). alpha, tau are the validation-locked values from
gate_config.json; this script performs NO selection.

Diagnostics emitted for the gradient-masking checklist:
    * adaptive-gate recall/FAR vs the per-specialist PGD points (the gate's
      adaptive recall should be <= the standard-PGD gate recall; if adaptive
      is *weaker* than standard PGD, suspect masking).

Scope: window-level, digital-domain, white-box, processed CSI (no value clamp);
    eps=0.030, steps=10, step=eps/6, random start. NOT certified/clinical/OTA.

Command:
    python scripts/adaptive_gate_attack.py \
        --recall-ckpt checkpoints/.../seed42_variantG_G1_v2maxrec_best.pt \
        --far-ckpt    checkpoints/.../seed42_variantG_G1_v2lowFA_best.pt \
        --gate-config results/.../A1/seed42/gate_config.json \
        --out-dir     results/.../A1/seed42 --split test \
        --epsilon 0.03 --steps 10
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import sys

import numpy as np
import torch
import torch.nn as nn


FALL_CLASS_INDEX = 1


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
    from model_factory import build_model
    return experiment_dir, benchmark_dir, s1, build_model


def gate_score(f_R, f_B, x, alpha):
    """Continuous, differentiable safety score S(x) in [0,1]."""
    p_R = torch.softmax(f_R(x).float(), dim=1)[:, FALL_CLASS_INDEX]
    p_B = torch.softmax(f_B(x).float(), dim=1)[:, FALL_CLASS_INDEX]
    return alpha * p_R + (1.0 - alpha) * p_B


def adaptive_gate_pgd(f_R, f_B, x, y, alpha, epsilon, steps, step_size, fall_idx):
    """L-inf PGD ascent on the safety loss mean(where(y==fall, -S, S)). No value clamp."""
    original = x.detach()
    # random start
    adv = original + torch.empty_like(original).uniform_(-epsilon, epsilon)
    adv = adv.detach()
    is_fall = (y == fall_idx)
    sign = torch.where(is_fall, torch.tensor(-1.0, device=x.device),
                       torch.tensor(1.0, device=x.device))  # -S for falls, +S for non-falls
    for _ in range(steps):
        adv.requires_grad = True
        S = gate_score(f_R, f_B, adv, alpha)
        loss = (sign * S).mean()
        grad = torch.autograd.grad(loss, adv)[0]
        with torch.no_grad():
            adv = adv + step_size * grad.sign()
            adv = original + torch.clamp(adv - original, min=-epsilon, max=epsilon)
        adv = adv.detach()
    return adv


def binary_metrics(fall_true, fall_pred):
    fall_true = fall_true.astype(bool); fall_pred = fall_pred.astype(bool)
    tp = int((fall_true & fall_pred).sum()); fn = int((fall_true & ~fall_pred).sum())
    fp = int((~fall_true & fall_pred).sum()); tn = int((~fall_true & ~fall_pred).sum())
    nf = tp + fn; nn_ = fp + tn
    recall = tp / nf if nf else 0.0
    far = fp / nn_ if nn_ else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = 2 * prec * recall / (prec + recall) if (prec + recall) else 0.0
    return {"TP": tp, "FN": fn, "FP": fp, "TN": tn, "n_fall": nf, "n_nonfall": nn_,
            "fall_recall": recall, "missed_fall_rate": 1 - recall, "false_alarm_rate": far,
            "fall_precision": prec, "fall_f1": f1, "binary_accuracy": (tp + tn) / (nf + nn_)}


def parse_args():
    p = argparse.ArgumentParser(description="Adaptive full-gate PGD attack on S(x).")
    p.add_argument("--recall-ckpt", required=True)
    p.add_argument("--far-ckpt", required=True)
    p.add_argument("--gate-config", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--model", default="lenet")
    p.add_argument("--split", choices=["test", "val"], default="test")
    p.add_argument("--epsilon", type=float, default=0.03)
    p.add_argument("--steps", type=int, default=10)
    p.add_argument("--step-size", type=float, default=None, help="Default epsilon/6.")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--tag", default="adaptive_gate")
    return p.parse_args()


def main():
    args = parse_args()
    experiment_dir, benchmark_dir, s1, build_model = import_modules()

    with open(args.gate_config, encoding="utf-8") as f:
        cfg = json.load(f)
    alpha, tau = float(cfg["alpha"]), float(cfg["tau"])
    step_size = args.step_size if args.step_size is not None else args.epsilon / 6.0

    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    s1.set_seed(args.seed)
    data = s1.load_raw_ut_har(benchmark_dir)
    _, val_loader, test_loader, _ = s1.build_loaders(data, 64)
    loader = test_loader if args.split == "test" else val_loader

    def load(ckpt):
        st = torch.load(Path(ckpt) if Path(ckpt).is_absolute() else experiment_dir / ckpt,
                        map_location=device, weights_only=False)
        m = build_model(args.model).to(device)
        m.load_state_dict(st["model_state_dict"], strict=True)
        m.eval()
        return m

    f_R, f_B = load(args.recall_ckpt), load(args.far_ckpt)

    rows = []
    y_all, S_all = [], []
    sid = 0
    for inputs, labels in loader:
        inputs = inputs.to(device).float(); labels = labels.to(device).long()
        adv = adaptive_gate_pgd(f_R, f_B, inputs, labels, alpha, args.epsilon,
                                args.steps, step_size, FALL_CLASS_INDEX)
        with torch.no_grad():
            S = gate_score(f_R, f_B, adv, alpha)
        S_np = S.cpu().numpy(); y_np = labels.cpu().numpy()
        for i in range(len(y_np)):
            t = int(y_np[i]); s_val = float(S_np[i])
            rows.append({"sample_id": sid, "true_label": t,
                         "fall_true_binary": 1 if t == FALL_CLASS_INDEX else 0,
                         "gate_score_S": f"{s_val:.6f}",
                         "fall_pred_binary": 1 if s_val >= tau else 0})
            sid += 1
        y_all.append(y_np); S_all.append(S_np)

    y_all = np.concatenate(y_all); S_all = np.concatenate(S_all)
    fall_true = (y_all == FALL_CLASS_INDEX).astype(int)
    fall_pred = (S_all >= tau).astype(int)
    metrics = binary_metrics(fall_true, fall_pred)
    metrics.update({"system": "DS_SGE_adaptive_gate_pgd", "attack": "adaptive_gate_pgd",
                    "alpha": alpha, "tau": tau, "epsilon": args.epsilon, "steps": args.steps,
                    "split": args.split})

    perwin = out_dir / f"{args.tag}_perwindow_{args.split}_epsilon_{str(args.epsilon).replace('.', '_')}.csv"
    with perwin.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["sample_id", "true_label", "fall_true_binary",
                                          "gate_score_S", "fall_pred_binary"])
        w.writeheader(); w.writerows(rows)

    metrics_path = out_dir / "metrics_adaptive_gate_pgd_eps003.csv"
    import pandas as pd
    pd.DataFrame([metrics]).to_csv(metrics_path, index=False)

    print("=" * 70)
    print(f"Adaptive full-gate PGD on S(x)  alpha={alpha:.2f} tau={tau:.2f} "
          f"eps={args.epsilon} steps={args.steps} split={args.split}")
    print(f"  recall={metrics['fall_recall']:.3f}  FAR={metrics['false_alarm_rate']:.3f}  "
          f"TP={metrics['TP']} FP={metrics['FP']} FN={metrics['FN']} TN={metrics['TN']}")
    print(f"  -> {metrics_path.name}, {perwin.name}")
    print("=" * 70)


if __name__ == "__main__":
    main()
