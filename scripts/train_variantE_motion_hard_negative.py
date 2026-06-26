"""
Variant E: motion-class-aware hard-negative adversarial-training defense (seed 42 pilot).

Motivation:
    The seed-42/43 false-alarm decision analysis showed that the frozen Variant D
    safety-guided defense raises PGD fall recall but at the cost of many false-fall
    alarms, ~74-76% of which come from the MOTION classes walk (2) and run (4), and
    those false alarms are HIGH-confidence (median fall-probability ~0.8-0.9, far above
    the true falls' ~0.27-0.35). Threshold calibration therefore cannot fix them; the
    fix must change the TRAINING OBJECTIVE.

What this is:
    Variant E = the FROZEN Variant D recipe (FGSM+PGD multi-epsilon {0.005,0.015,0.030}
    adversarial training, fall-weighted CE loss, safety-guided checkpoint selection with
    the clean-collapse guard, macro-F1 selection kept as comparison) PLUS a
    motion-class hard-negative penalty on the adversarial sub-batch.

    The frozen Variant D script (train_safety_guided_defense.py) is NOT modified; this
    script imports its building blocks (perturbations, validation bundle, presets) and
    only adds the extra loss term.

Objective (documented exactly):
    Per training batch (batch-split mixing: 50% clean / 25% FGSM / 25% PGD), the loss is

        loss = fall_weighted_CE(outputs, labels)                         # Variant D term
             + lambda_motion * mean( softmax(outputs_adv_motion)[:, FALL] )

    where ``outputs_adv_motion`` are the model outputs for the ADVERSARIAL sub-batch
    samples whose TRUE label is walk or run. The penalty is the mean fall-class
    PROBABILITY assigned to adversarial walk/run windows; minimizing it pushes the model
    to stop calling adversarial motion windows "fall".

    Why the probability form (not a logit-margin): it directly targets the diagnosed
    failure (high fall-PROBABILITY on adversarial walk/run), it is bounded in [0,1] so
    the penalty scale is stable across batches and lambda values, and it needs no extra
    reference logit. If no adversarial walk/run sample is present in a batch, the penalty
    is 0 for that batch. The adversary that GENERATES the perturbations is unchanged
    (untargeted, unweighted CE) -- only the defender's training loss gains the term.

Scope/claims: window-level, digital-domain, white-box, processed CSI only. Seed 42 only,
    LeNet only. NOT solved robustness, NOT clinical, NOT certified, NOT over-the-air.

Commands:
    python scripts/train_variantE_motion_hard_negative.py --lambda-motion 0.5 --seed 42 --dry-run
    python scripts/train_variantE_motion_hard_negative.py --lambda-motion 0.5 --seed 42 \
        --epochs 70 --patience 15 --min-epochs 35
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

WALK_CLASS_INDEX = 2
RUN_CLASS_INDEX = 4


def import_variantD():
    """Import the frozen Variant D module to reuse its building blocks unchanged."""
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import train_safety_guided_defense as tsg
    return tsg


def train_one_epoch_motion(model, loader, train_criterion, atk_criterion, optimizer, device,
                           train_epsilons, train_pgd_steps, rng, tsg, lambda_motion,
                           fall_idx):
    """FGSM+PGD batch-split adversarial training (Variant D) + motion hard-negative penalty.

    Mirrors train_safety_guided_defense.train_one_epoch for attack_mode='fgsm_pgd', then
    adds lambda_motion * mean(fall-probability) over adversarial walk/run samples.
    """
    model.train()
    total_loss = 0.0
    total = 0
    clean_correct = 0
    adv_correct = 0
    adv_total = 0
    motion_penalty_sum = 0.0
    motion_batches = 0

    for inputs, labels in loader:
        inputs = inputs.to(device).float()
        labels = labels.type(torch.LongTensor).to(device)
        bs = labels.size(0)

        eps = float(rng.choice(train_epsilons))
        pgd_alpha = eps / 4.0  # training PGD step size (smaller-step; identical to Variant D)

        n_clean = bs // 2
        n_fgsm = (bs - n_clean) // 2
        clean_x = inputs[:n_clean]
        fgsm_src = inputs[n_clean:n_clean + n_fgsm]
        fgsm_lbl = labels[n_clean:n_clean + n_fgsm]
        pgd_src = inputs[n_clean + n_fgsm:]
        pgd_lbl = labels[n_clean + n_fgsm:]

        model.eval()
        fgsm_adv = tsg.fgsm_perturb(model, fgsm_src, fgsm_lbl, atk_criterion, eps)
        pgd_adv = tsg.pgd_perturb(model, pgd_src, pgd_lbl, atk_criterion, eps,
                                  train_pgd_steps, pgd_alpha)
        model.train()
        batch_x = torch.cat([clean_x, fgsm_adv, pgd_adv], dim=0)
        batch_y = labels  # order preserved: [clean | fgsm | pgd]
        adv_count = fgsm_src.size(0) + pgd_src.size(0)
        n_clean = clean_x.size(0)

        optimizer.zero_grad()
        outputs = model(batch_x).float()
        base_loss = train_criterion(outputs, batch_y)

        # --- motion hard-negative penalty on the ADVERSARIAL sub-batch ---
        adv_outputs = outputs[n_clean:]
        adv_labels = batch_y[n_clean:]
        motion_mask = (adv_labels == WALK_CLASS_INDEX) | (adv_labels == RUN_CLASS_INDEX)
        if motion_mask.any():
            adv_motion_probs = torch.softmax(adv_outputs[motion_mask], dim=1)[:, fall_idx]
            motion_penalty = adv_motion_probs.mean()
            motion_penalty_sum += float(motion_penalty.item())
            motion_batches += 1
        else:
            motion_penalty = torch.zeros((), device=device)

        loss = base_loss + lambda_motion * motion_penalty
        loss.backward()
        optimizer.step()

        preds = torch.argmax(outputs, dim=1)
        total_loss += loss.item() * bs
        total += bs
        clean_correct += (preds[:n_clean] == batch_y[:n_clean]).sum().item()
        adv_correct += (preds[n_clean:] == batch_y[n_clean:]).sum().item()
        adv_total += adv_count

    return {
        "train_loss": total_loss / total,
        "train_clean_accuracy": clean_correct / max(n_clean, 1) if total else 0.0,
        "train_adv_accuracy": adv_correct / adv_total if adv_total else 0.0,
        "mean_motion_penalty": motion_penalty_sum / motion_batches if motion_batches else 0.0,
    }


def parse_args():
    p = argparse.ArgumentParser(
        description="Variant E: motion-class hard-negative adversarial-training defense.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--lambda-motion", type=float, required=True,
                   help="Weight of the walk/run adversarial fall-probability penalty (E1=0.5, E2=1.0, E3=2.0).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=70)
    p.add_argument("--patience", type=int, default=15)
    p.add_argument("--min-epochs", type=int, default=35)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--train-pgd-steps", type=int, default=7)
    p.add_argument("--fall-weight", type=float, default=3.0)
    p.add_argument("--min-clean-accuracy", type=float, default=0.60)
    p.add_argument("--min-clean-macro-f1", type=float, default=0.50)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    tsg = import_variantD()

    # Variant E inherits the Variant D 'D' preset (fgsm_pgd, multi-eps, fw3, 50/25/25 mix).
    preset = tsg.VARIANT_PRESETS["D"]
    train_epsilons = list(preset["train_epsilons"])
    mix = preset["mix"]
    fall_weight = args.fall_weight
    fall_idx = tsg.FALL_CLASS_INDEX
    num_classes = tsg.NUM_CLASSES

    exp = Path(__file__).resolve().parents[1]
    benchmark = exp / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    data_dir = benchmark / "Data" / "UT_HAR"
    seed_tag = f"seed{args.seed}"
    base = exp / "results" / "safety_guided_defense" / "variantE_motion_hard_negative" / seed_tag
    ck_dir = exp / "checkpoints" / "safety_guided_defense" / "variantE_motion_hard_negative" / seed_tag
    logs_dir = base / "logs"
    meta_dir = base / "metadata"

    if not benchmark.exists():
        raise FileNotFoundError(f"SenseFi clone not found: {benchmark}")
    if not data_dir.exists():
        raise FileNotFoundError(f"UT-HAR data not found: {data_dir}")

    s1 = tsg.import_stage1()  # stage-1 module: loaders/metrics/seed/io helpers live here
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

    lam_tag = f"lam{str(args.lambda_motion).replace('.', 'p')}"
    run_name = f"{seed_tag}_variantE_motion_hardneg_fw{int(fall_weight)}_{lam_tag}_{mix}"
    ckpt_safety = ck_dir / f"{run_name}_bySafetyScore_best.pt"
    ckpt_f1 = ck_dir / f"{run_name}_byValMacroF1_best.pt"
    ckpt_last = ck_dir / f"{run_name}_last.pt"
    log_path = logs_dir / f"{run_name}_training_log.csv"
    meta_path = logs_dir / f"{run_name}_metadata.json"

    selection_def = ("SafetyScore = 0.35*clean_fall_recall + 0.45*pgd_fall_recall "
                     "+ 0.10*fgsm_fall_recall - 0.10*normalized_false_alarm_burden (validation only)")

    print("Variant E: motion-class hard-negative adversarial-training defense")
    print("-" * 72)
    print(f"Run name:        {run_name}")
    print(f"lambda_motion:   {args.lambda_motion}")
    print(f"Base recipe:     Variant D (fgsm_pgd, multi-eps {train_epsilons}, fw{fall_weight}, mix {mix})")
    print(f"Motion penalty:  lambda*mean(fall_prob of adversarial walk/run samples)")
    print(f"Device:          {device} | Seed: {args.seed}")
    print(f"Max epochs:      {args.epochs} | patience {args.patience} | min-epochs {args.min_epochs}")
    print(f"Guard:           clean_acc>={args.min_clean_accuracy} AND clean_macro_f1>={args.min_clean_macro_f1}")
    print(f"Split sizes:     {split_sizes}")
    print("-" * 72)

    if args.dry_run:
        print("[dry-run] model+loaders built; no training/files.")
        for lbl, pth in [("ckpt_safety", ckpt_safety), ("ckpt_f1", ckpt_f1),
                         ("ckpt_last", ckpt_last), ("log", log_path), ("meta", meta_path)]:
            print(f"    {lbl}: {pth}")
        return

    ck_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    log_fields = ["epoch", "train_loss", "mean_motion_penalty", "train_clean_accuracy",
                  "train_adv_accuracy", "val_clean_accuracy", "val_clean_macro_f1",
                  "val_clean_fall_recall", "val_fgsm_fall_recall", "val_pgd_fall_recall",
                  "val_fgsm_false_fall_alarms", "val_pgd_false_fall_alarms",
                  "val_normalized_false_alarm_burden", "safety_score",
                  "selected_by_safety_score", "selected_by_val_macro_f1"]

    history = []
    best_safety = -1e9; best_safety_epoch = -1; best_safety_record = None
    best_f1 = -1e9; best_f1_epoch = -1; best_f1_record = None
    best_raw_safety = -1e9; best_raw_epoch = -1; best_raw_bundle = None
    no_improve = 0
    start = time.time()

    for epoch in range(1, args.epochs + 1):
        tr = train_one_epoch_motion(model, train_loader, train_criterion, atk_criterion,
                                    optimizer, device, train_epsilons, args.train_pgd_steps,
                                    rng, tsg, args.lambda_motion, fall_idx)
        vb = tsg.compute_validation_bundle(s1, model, val_loader, atk_criterion, device)

        eligible = (vb["val_clean_accuracy"] >= args.min_clean_accuracy
                    and vb["val_clean_macro_f1"] >= args.min_clean_macro_f1)
        improved_safety = eligible and vb["safety_score"] > best_safety
        improved_f1 = vb["val_clean_macro_f1"] > best_f1

        if vb["safety_score"] > best_raw_safety:
            best_raw_safety = vb["safety_score"]; best_raw_epoch = epoch; best_raw_bundle = vb

        if improved_safety:
            best_safety = vb["safety_score"]; best_safety_epoch = epoch; no_improve = 0
            torch.save({"epoch": epoch, "model_state_dict": model.state_dict(),
                        "selection_method": "safety_score_clean_guarded", "val_bundle": vb,
                        "lambda_motion": args.lambda_motion, "run_name": run_name,
                        "args": vars(args)}, ckpt_safety)
        elif best_safety_epoch > 0:
            no_improve += 1

        if improved_f1:
            best_f1 = vb["val_clean_macro_f1"]; best_f1_epoch = epoch
            torch.save({"epoch": epoch, "model_state_dict": model.state_dict(),
                        "selection_method": "val_macro_f1", "val_bundle": vb,
                        "lambda_motion": args.lambda_motion, "run_name": run_name,
                        "args": vars(args)}, ckpt_f1)

        rec = {"epoch": epoch, "train_loss": tr["train_loss"],
               "mean_motion_penalty": tr["mean_motion_penalty"],
               "train_clean_accuracy": tr["train_clean_accuracy"],
               "train_adv_accuracy": tr["train_adv_accuracy"],
               "selected_by_safety_score": int(improved_safety),
               "selected_by_val_macro_f1": int(improved_f1)}
        rec.update({k: vb[k] for k in ("val_clean_accuracy", "val_clean_macro_f1",
                    "val_clean_fall_recall", "val_fgsm_fall_recall", "val_pgd_fall_recall",
                    "val_fgsm_false_fall_alarms", "val_pgd_false_fall_alarms",
                    "val_normalized_false_alarm_burden", "safety_score")})
        history.append(rec)
        if improved_safety:
            best_safety_record = rec
        if improved_f1:
            best_f1_record = rec

        flags = (("S" if improved_safety else " ") + ("F" if improved_f1 else " ")
                 + ("g" if not eligible else " "))
        print(f"Epoch {epoch:03d}/{args.epochs} | loss={tr['train_loss']:.4f} "
              f"mpen={tr['mean_motion_penalty']:.3f} | clean_fr={vb['val_clean_fall_recall']:.3f} "
              f"pgd_fr={vb['val_pgd_fall_recall']:.3f} fgsm_fr={vb['val_fgsm_fall_recall']:.3f} | "
              f"pgd_FP={vb['val_pgd_false_fall_alarms']} | score={vb['safety_score']:.4f} "
              f"f1={vb['val_clean_macro_f1']:.4f} [{flags}]")

        if args.patience > 0 and epoch >= args.min_epochs and no_improve >= args.patience:
            print(f"Early stopping at epoch {epoch} (best safety epoch {best_safety_epoch}).")
            break

    elapsed = time.time() - start
    last_epoch = history[-1]["epoch"]
    torch.save({"epoch": last_epoch, "model_state_dict": model.state_dict(),
                "selection_method": "last", "run_name": run_name, "args": vars(args)}, ckpt_last)

    with log_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=log_fields)
        w.writeheader()
        for r in history:
            w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in log_fields})

    metadata = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "variantE_motion_hard_negative_seed42_pilot",
        "run_name": run_name,
        "seed": args.seed,
        "base_recipe": "frozen Variant D (fgsm_pgd multi-eps fw3, safety-guided + clean-collapse guard)",
        "motion_penalty_definition": (
            "loss += lambda_motion * mean(softmax(outputs)[:, fall] for adversarial samples "
            "whose true label is walk(2) or run(4)); 0 if none in batch"),
        "lambda_motion": args.lambda_motion,
        "train_epsilons": train_epsilons,
        "fall_weight": fall_weight,
        "train_pgd_steps": args.train_pgd_steps,
        "eval_protocol": {"epsilon": tsg.EVAL_EPSILON, "pgd_steps": tsg.EVAL_PGD_STEPS,
                          "pgd_alpha_rule": tsg.EVAL_PGD_ALPHA_RULE},
        "selection_score_definition": selection_def,
        "clean_collapse_guard": {"min_clean_accuracy": args.min_clean_accuracy,
                                 "min_clean_macro_f1": args.min_clean_macro_f1},
        "raw_ungated_safety_best": {"epoch": best_raw_epoch, "safety_score": best_raw_safety,
            "val_clean_accuracy": (best_raw_bundle or {}).get("val_clean_accuracy"),
            "val_pgd_fall_recall": (best_raw_bundle or {}).get("val_pgd_fall_recall")},
        "best_safety_epoch": best_safety_epoch, "best_safety_score": best_safety,
        "best_safety_record": best_safety_record,
        "best_val_macro_f1_epoch": best_f1_epoch, "best_val_macro_f1": best_f1,
        "best_val_macro_f1_record": best_f1_record,
        "epochs_run": last_epoch, "max_epochs": args.epochs, "patience": args.patience,
        "min_epochs": args.min_epochs, "learning_rate": args.lr, "batch_size": args.batch_size,
        "split_sizes": split_sizes,
        "checkpoint_bySafetyScore": str(ckpt_safety), "checkpoint_byValMacroF1": str(ckpt_f1),
        "checkpoint_last": str(ckpt_last),
        "claim_boundary": ("Digital-domain white-box on processed CSI; seed 42 / LeNet only; "
                           "NOT solved/certified/clinical/over-the-air."),
        "device": str(device), "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "git_branch": s1.get_command_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(exp)),
        "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(exp)),
        "elapsed_seconds": elapsed,
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("-" * 72)
    print(f"Variant E (lambda={args.lambda_motion}) done in {elapsed:.1f}s ({last_epoch} epochs).")
    print(f"  best-by-SafetyScore : epoch {best_safety_epoch} score={best_safety:.4f}")
    if best_safety_record:
        print(f"     val clean_fr={best_safety_record['val_clean_fall_recall']:.3f} "
              f"pgd_fr={best_safety_record['val_pgd_fall_recall']:.3f} "
              f"pgd_FP={best_safety_record['val_pgd_false_fall_alarms']}")
    print(f"  best-by-ValMacroF1  : epoch {best_f1_epoch} f1={best_f1:.4f}")
    print(f"  checkpoints -> {ck_dir}")


if __name__ == "__main__":
    main()
