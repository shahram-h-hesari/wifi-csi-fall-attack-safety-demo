"""
Variant E selection-v2 pilot (seeds 42 & 43): CHANGE ONLY CHECKPOINT SELECTION.

Motivation:
    The cross-seed decision analysis found the mixed seed-43 Variant E result was caused by
    checkpoint-selection sensitivity + a too-weak clean-performance guard (the recall-heavy
    safety score picked an early, clean-weak, high-false-alarm epoch on seed 43), NOT the
    motion hard-negative loss. This pilot tests that: it keeps the Variant E training
    objective byte-identical and changes only the selection/saving.

What is unchanged (imported from the committed Variant E script; nothing modified there):
    LeNet, same UT-HAR split, FGSM+PGD multi-ε {0.005,0.015,0.030} adversarial training,
    fall-weighted CE, motion hard-negative penalty λ=1.0 (train_one_epoch_motion).

What changes (selection only):
    * Stronger clean-performance guard for safety-score eligibility:
        val clean accuracy >= 0.70  AND  val clean macro-F1 >= 0.65   (was 0.60 / 0.50).
    * Save TOP-k candidate checkpoints (not just safety-best + macro-F1-best):
        - v2_safety   : guard-eligible, max SafetyScore
        - v2_maxrec   : guard-eligible, max (val PGD recall, then min val PGD FP)
        - v2_lowFA    : guard-eligible AND val PGD recall >= 0.10, min (val PGD FP, then max recall)
        - v2_macroF1  : max val clean macro-F1 (no guard; reference)
    * Record validation metrics for ALL epochs (analysis/selection_candidates.csv).

Run-length fidelity (so the SAME epochs/weights as the prior run are visited):
    The optimizer / data RNG are seeded identically, so per-epoch weights are deterministic
    and independent of selection. Early stopping is kept IDENTICAL to the prior Variant E run
    (patience on the ORIGINAL guard-0.60 safety score, patience=15, min-epochs=35) so the run
    stops at the same epoch as before (seed 42 -> 70, seed 43 -> 35). v2 candidates are then
    selected from the same visited epoch range.

Scope: window-level, digital-domain, white-box; seeds 42/43 only; λ=1.0 only; LeNet only.
    Selection-v2 pilot, NOT independent validation (the guard was motivated on these seeds).
    Not solved/certified/clinical/over-the-air.

Command:
    python scripts/train_variantE_selection_v2.py --seed 43 --epochs 70 --patience 15 --min-epochs 35
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import platform
import sys
import time
from datetime import datetime, timezone

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

# Stronger clean-performance guard (selection-v2).
V2_GUARD_ACC = 0.70
V2_GUARD_F1 = 0.65
LOWFA_RECALL_FLOOR = 0.10
# Original guard, used ONLY to replicate the prior run's early-stopping length.
ORIG_GUARD_ACC = 0.60
ORIG_GUARD_F1 = 0.50


def import_variantE():
    sd = Path(__file__).resolve().parent
    if str(sd) not in sys.path:
        sys.path.insert(0, str(sd))
    import train_variantE_motion_hard_negative as tve
    return tve


def parse_args():
    p = argparse.ArgumentParser(description="Variant E selection-v2 (selection change only).")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--epochs", type=int, default=70)
    p.add_argument("--patience", type=int, default=15)
    p.add_argument("--min-epochs", type=int, default=35)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--train-pgd-steps", type=int, default=7)
    p.add_argument("--lambda-motion", type=float, default=1.0)
    p.add_argument("--fall-weight", type=float, default=3.0)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def safety_score(vb):
    return (0.35 * vb["val_clean_fall_recall"] + 0.45 * vb["val_pgd_fall_recall"]
            + 0.10 * vb["val_fgsm_fall_recall"] - 0.10 * vb["val_normalized_false_alarm_burden"])


def main():
    args = parse_args()
    tve = import_variantE()
    tsg = tve.import_variantD()
    s1 = tsg.import_stage1()

    preset = tsg.VARIANT_PRESETS["D"]
    train_epsilons = list(preset["train_epsilons"])
    mix = preset["mix"]
    fall_weight = args.fall_weight
    fall_idx = tsg.FALL_CLASS_INDEX
    num_classes = tsg.NUM_CLASSES

    exp = Path(__file__).resolve().parents[1]
    benchmark = exp / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    seed_tag = f"seed{args.seed}"
    base = exp / "results" / "safety_guided_defense" / "variantE_motion_hard_negative" / "selection_v2" / seed_tag
    ck_dir = exp / "checkpoints" / "safety_guided_defense" / "variantE_motion_hard_negative" / "selection_v2" / seed_tag
    logs_dir = base / "logs"
    ana_dir = base / "analysis"

    s1.patch_sensefi_dataset_loader(benchmark)
    if str(benchmark) not in sys.path:
        sys.path.insert(0, str(benchmark))
    from model_factory import build_model

    s1.set_seed(args.seed)
    data = s1.load_raw_ut_har(benchmark)
    train_loader, val_loader, test_loader, split_sizes = s1.build_loaders(data, args.batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model("lenet").to(device)
    class_weights = torch.ones(num_classes, device=device)
    class_weights[fall_idx] = fall_weight
    train_criterion = nn.CrossEntropyLoss(weight=class_weights)
    atk_criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    rng = np.random.default_rng(args.seed)

    run = f"{seed_tag}_variantE_selv2_lam1p0"
    ck = {k: ck_dir / f"{run}_{k}_best.pt" for k in ("v2safety", "v2maxrec", "v2lowFA", "v2macroF1")}
    ck_last = ck_dir / f"{run}_last.pt"
    log_path = logs_dir / f"{run}_training_log.csv"
    cand_path = ana_dir / f"{run}_selection_candidates.csv"
    meta_path = logs_dir / f"{run}_metadata.json"

    print("Variant E selection-v2 (selection change only)")
    print("-" * 70)
    print(f"Run: {run} | seed {args.seed} | lambda 1.0 | fw{fall_weight}")
    print(f"V2 guard: clean_acc>={V2_GUARD_ACC} AND clean_macro_f1>={V2_GUARD_F1}")
    print(f"Early-stop replicates prior run (orig guard {ORIG_GUARD_ACC}/{ORIG_GUARD_F1}, "
          f"patience {args.patience}, min-epochs {args.min_epochs})")
    print(f"Saves candidates: {list(ck.keys())}")
    print("-" * 70)
    if args.dry_run:
        for k, v in ck.items():
            print(f"  {k}: {v}")
        print(f"  log: {log_path}"); print(f"  candidates: {cand_path}")
        return

    ck_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    ana_dir.mkdir(parents=True, exist_ok=True)

    history = []
    # selection-v2 best trackers (key, epoch)
    best = {"v2safety": (-1e9, -1), "v2maxrec": ((-1e9, 1e9), -1),
            "v2lowFA": ((1e9, -1e9), -1), "v2macroF1": (-1e9, -1)}
    best_records = {}
    # original-guard safety best, ONLY for early-stop length fidelity
    orig_best_safety = -1e9
    orig_best_epoch = -1
    orig_no_improve = 0
    start = time.time()

    for epoch in range(1, args.epochs + 1):
        tr = tve.train_one_epoch_motion(model, train_loader, train_criterion, atk_criterion,
                                        optimizer, device, train_epsilons, args.train_pgd_steps,
                                        rng, tsg, args.lambda_motion, fall_idx)
        vb = tsg.compute_validation_bundle(s1, model, val_loader, atk_criterion, device)
        sc = safety_score(vb)
        acc = vb["val_clean_accuracy"]; f1 = vb["val_clean_macro_f1"]
        rec = vb["val_pgd_fall_recall"]; fpv = vb["val_pgd_false_fall_alarms"]
        v2_eligible = (acc >= V2_GUARD_ACC and f1 >= V2_GUARD_F1)

        def save(key):
            torch.save({"epoch": epoch, "model_state_dict": model.state_dict(),
                        "selection_method": key, "val_bundle": vb, "safety_score": sc,
                        "lambda_motion": args.lambda_motion, "run_name": run, "args": vars(args)},
                       ck[key])

        sel_flags = {k: 0 for k in ck}
        if v2_eligible:
            if sc > best["v2safety"][0]:
                best["v2safety"] = (sc, epoch); best_records["v2safety"] = vb; save("v2safety"); sel_flags["v2safety"] = 1
            if (rec, -fpv) > best["v2maxrec"][0]:
                best["v2maxrec"] = ((rec, -fpv), epoch); best_records["v2maxrec"] = vb; save("v2maxrec"); sel_flags["v2maxrec"] = 1
            if rec >= LOWFA_RECALL_FLOOR and (fpv, -rec) < best["v2lowFA"][0]:
                best["v2lowFA"] = ((fpv, -rec), epoch); best_records["v2lowFA"] = vb; save("v2lowFA"); sel_flags["v2lowFA"] = 1
        if f1 > best["v2macroF1"][0]:
            best["v2macroF1"] = (f1, epoch); best_records["v2macroF1"] = vb; save("v2macroF1"); sel_flags["v2macroF1"] = 1

        rec_row = {"epoch": epoch, "train_loss": tr["train_loss"],
                   "mean_motion_penalty": tr["mean_motion_penalty"],
                   "val_clean_accuracy": acc, "val_clean_macro_f1": f1,
                   "val_clean_fall_recall": vb["val_clean_fall_recall"],
                   "val_fgsm_fall_recall": vb["val_fgsm_fall_recall"], "val_pgd_fall_recall": rec,
                   "val_fgsm_false_fall_alarms": vb["val_fgsm_false_fall_alarms"],
                   "val_pgd_false_fall_alarms": fpv,
                   "val_normalized_false_alarm_burden": vb["val_normalized_false_alarm_burden"],
                   "safety_score": sc, "v2_eligible": int(v2_eligible),
                   "sel_v2safety": sel_flags["v2safety"], "sel_v2maxrec": sel_flags["v2maxrec"],
                   "sel_v2lowFA": sel_flags["v2lowFA"], "sel_v2macroF1": sel_flags["v2macroF1"]}
        history.append(rec_row)

        # early-stop length fidelity: track ORIGINAL guard-0.60 safety best
        orig_eligible = (acc >= ORIG_GUARD_ACC and f1 >= ORIG_GUARD_F1)
        if orig_eligible and sc > orig_best_safety:
            orig_best_safety = sc; orig_best_epoch = epoch; orig_no_improve = 0
        elif orig_best_epoch > 0:
            orig_no_improve += 1

        print(f"Epoch {epoch:03d}/{args.epochs} | acc={acc:.3f} f1={f1:.3f} pgd_fr={rec:.3f} "
              f"pgd_FP={fpv} score={sc:.3f} v2elig={int(v2_eligible)} "
              f"[{''.join(k[3:5] if sel_flags[k] else '..' for k in ck)}]")

        if args.patience > 0 and epoch >= args.min_epochs and orig_no_improve >= args.patience:
            print(f"Early stopping at epoch {epoch} (replicates prior run; orig-guard best epoch {orig_best_epoch}).")
            break

    elapsed = time.time() - start
    last_epoch = history[-1]["epoch"]
    torch.save({"epoch": last_epoch, "model_state_dict": model.state_dict(),
                "selection_method": "last", "run_name": run, "args": vars(args)}, ck_last)

    log_fields = list(history[0].keys())
    with log_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=log_fields)
        w.writeheader()
        for r in history:
            w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in log_fields})

    # selection candidates summary
    with cand_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["selection", "selected_epoch", "val_clean_acc", "val_clean_macro_f1",
                    "val_pgd_recall", "val_pgd_false_alarms", "safety_score"])
        for k in ck:
            ep = best[k][1]
            vb = best_records.get(k, {})
            w.writerow([k, ep, f"{vb.get('val_clean_accuracy', float('nan')):.4f}",
                        f"{vb.get('val_clean_macro_f1', float('nan')):.4f}",
                        f"{vb.get('val_pgd_fall_recall', float('nan')):.4f}",
                        vb.get('val_pgd_false_fall_alarms', ''),
                        f"{safety_score(vb):.4f}" if vb else ""])

    metadata = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "variantE_selection_v2_pilot",
        "run_name": run, "seed": args.seed, "lambda_motion": args.lambda_motion,
        "note": ("Selection-v2 pilot: Variant E training objective UNCHANGED; only checkpoint "
                 "selection/saving changed. NOT independent validation (guard motivated on seeds 42/43)."),
        "v2_guard": {"min_clean_accuracy": V2_GUARD_ACC, "min_clean_macro_f1": V2_GUARD_F1},
        "lowfa_recall_floor": LOWFA_RECALL_FLOOR,
        "early_stop_fidelity": {"orig_guard_acc": ORIG_GUARD_ACC, "orig_guard_f1": ORIG_GUARD_F1,
                                "patience": args.patience, "min_epochs": args.min_epochs,
                                "orig_best_safety_epoch": orig_best_epoch},
        "selected_epochs": {k: best[k][1] for k in ck},
        "train_epsilons": train_epsilons, "fall_weight": fall_weight,
        "epochs_run": last_epoch, "split_sizes": split_sizes,
        "checkpoints": {k: str(v) for k, v in ck.items()},
        "device": str(device), "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(exp)),
        "elapsed_seconds": elapsed,
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("-" * 70)
    print(f"Selection-v2 seed {args.seed} done in {elapsed:.1f}s ({last_epoch} epochs).")
    for k in ck:
        ep = best[k][1]; vb = best_records.get(k, {})
        print(f"  {k:9s} epoch {ep}: acc={vb.get('val_clean_accuracy', float('nan')):.3f} "
              f"pgd_fr={vb.get('val_pgd_fall_recall', float('nan')):.3f} "
              f"pgd_FP={vb.get('val_pgd_false_fall_alarms', '?')}")


if __name__ == "__main__":
    main()
