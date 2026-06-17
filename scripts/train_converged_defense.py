"""
Stage 3: converged FGSM adversarial-training defense (no PGD training yet).

Purpose:
    Train a defended UT-HAR LeNet using mixed clean + FGSM adversarial training,
    with the same SenseFi loader/preprocessing as Stage 1 and proper
    train/validation/test separation. The defended model is trained from
    random initialization (adversarial training from scratch), selected on a
    robustness-aware validation score, and saved as a reusable checkpoint.

    Unlike the old `*_short` defense scripts (5 epochs, val+test merged, no
    checkpoint, retrain on every export), this script trains to convergence,
    keeps validation/test distinct, and persists best + last checkpoints.

Selection:
    selection_score = 0.5 * val_clean_macro_f1 + 0.5 * val_fgsm_adv_macro_f1
    (computed on the validation split only; the test split is never used for
    selection, and the legacy val+test pool is comparison-only.)

Scope:
    This is FGSM adversarial training, NOT PGD adversarial training. It is a
    window-level, software-tensor defense. It is not a physical-layer / over-
    the-air defense and not clinical or medical-device validation.

    Defended FGSM/PGD attack evaluation and the defended epsilon sweep are done
    separately via scripts/run_converged_attacks.py pointed at the defended
    checkpoint; this script only trains and reports CLEAN defended metrics.

Commands:
    python scripts/train_converged_defense.py --help
    python scripts/train_converged_defense.py --dry-run --run-name defended_fgsm_at_seed42
    python scripts/train_converged_defense.py --epochs 100 --patience 15 \
        --seed 42 --train-epsilon 0.03 --run-name defended_fgsm_at_seed42
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import platform
import sys
from datetime import datetime, timezone
import time

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim


def import_stage1():
    """Import the Stage 1 module so loader/preprocessing/metrics are identical."""
    experiment_dir = Path(__file__).resolve().parents[1]
    scripts_dir = experiment_dir / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import train_converged_clean_baseline as s1  # noqa: E402

    return s1


def fgsm_perturb(model, inputs, labels, criterion, epsilon):
    """Single-step FGSM perturbation on processed CSI tensors (no [0,1] clamp)."""
    if epsilon == 0.0:
        return inputs.detach()
    x = inputs.clone().detach()
    x.requires_grad = True
    outputs = model(x).float()
    loss = criterion(outputs, labels)
    model.zero_grad()
    loss.backward()
    adv = x + epsilon * x.grad.detach().sign()
    return adv.detach()


def train_one_adv_epoch(model, loader, criterion, optimizer, device, epsilon, clean_w, adv_w):
    """Mixed clean + FGSM adversarial training for one epoch."""
    model.train()
    total_loss = 0.0
    clean_correct = 0
    adv_correct = 0
    total = 0

    for inputs, labels in loader:
        inputs = inputs.to(device).float()
        labels = labels.type(torch.LongTensor).to(device)

        adv_inputs = fgsm_perturb(model, inputs, labels, criterion, epsilon)

        optimizer.zero_grad()
        clean_out = model(inputs).float()
        adv_out = model(adv_inputs).float()
        loss = clean_w * criterion(clean_out, labels) + adv_w * criterion(adv_out, labels)
        loss.backward()
        optimizer.step()

        bs = labels.size(0)
        total_loss += loss.item() * bs
        clean_correct += (torch.argmax(clean_out, dim=1) == labels).sum().item()
        adv_correct += (torch.argmax(adv_out, dim=1) == labels).sum().item()
        total += bs

    return {
        "train_total_loss": total_loss / total,
        "train_clean_accuracy": clean_correct / total,
        "train_adv_accuracy": adv_correct / total,
    }


def eval_fgsm(model, loader, criterion, device, epsilon):
    """Evaluate FGSM-attacked predictions; return (y_true, y_pred) numpy arrays."""
    model.eval()
    y_true_all, y_pred_all = [], []
    for inputs, labels in loader:
        inputs = inputs.to(device).float()
        labels = labels.type(torch.LongTensor).to(device)
        adv = fgsm_perturb(model, inputs, labels, criterion, epsilon)
        with torch.no_grad():
            preds = torch.argmax(model(adv).float(), dim=1)
        y_true_all.append(labels.cpu().numpy())
        y_pred_all.append(preds.cpu().numpy())
    return np.concatenate(y_true_all), np.concatenate(y_pred_all)


def clean_metric_dict(s1, split, y_true, y_pred, n):
    """Build a clean defended metric dict for a split."""
    fb = s1.compute_fall_binary_metrics(y_true, y_pred)
    return {
        "split": split,
        "n_windows": int(n),
        "accuracy": s1.accuracy_of(y_true, y_pred),
        "macro_f1": s1.macro_f1_of(y_true, y_pred),
        "fall_recall": fb["fall_recall"],
        "missed_fall_rate": fb["missed_fall_rate"],
        "fall_precision": fb["fall_precision"],
        "fall_f1": fb["fall_f1"],
        "fall_true_positive": fb["fall_true_positive"],
        "fall_false_negative": fb["fall_false_negative"],
        "fall_false_positive": fb["fall_false_positive"],
        "fall_true_negative": fb["fall_true_negative"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 3: converged FGSM adversarial-training defense for UT-HAR LeNet.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--epochs", type=int, default=100, help="Maximum training epochs.")
    parser.add_argument(
        "--patience", type=int, default=15,
        help="Early-stopping patience on the validation selection score. 0 disables.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Adam learning rate.")
    parser.add_argument("--batch-size", type=int, default=64, help="Training batch size.")
    parser.add_argument("--train-epsilon", type=float, default=0.03, help="FGSM training epsilon.")
    parser.add_argument("--clean-loss-weight", type=float, default=0.5, help="Clean loss weight.")
    parser.add_argument("--adv-loss-weight", type=float, default=0.5, help="Adversarial loss weight.")
    parser.add_argument(
        "--run-name", type=str, default="defended_fgsm_at_seed42", help="Output filename prefix."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Build loaders + model and print planned output paths WITHOUT training or writing files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    experiment_dir = Path(__file__).resolve().parents[1]
    benchmark_dir = experiment_dir / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    data_dir = benchmark_dir / "Data" / "UT_HAR"

    checkpoints_dir = experiment_dir / "checkpoints" / "converged_defense"
    results_dir = experiment_dir / "results" / "converged_defense"

    if not benchmark_dir.exists():
        raise FileNotFoundError(f"SenseFi clone not found: {benchmark_dir}")
    if not data_dir.exists():
        raise FileNotFoundError(f"UT-HAR data not found: {data_dir}")

    s1 = import_stage1()
    s1.patch_sensefi_dataset_loader(benchmark_dir)
    if str(benchmark_dir) not in sys.path:
        sys.path.insert(0, str(benchmark_dir))
    from UT_HAR_model import UT_HAR_LeNet

    s1.set_seed(args.seed)

    data = s1.load_raw_ut_har(benchmark_dir)
    train_loader, val_loader, test_loader, split_sizes = s1.build_loaders(data, args.batch_size)

    legacy_X = torch.cat((data["X_val"], data["X_test"]), 0)
    legacy_y = torch.cat((data["y_val"], data["y_test"]), 0)
    legacy_loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(legacy_X, legacy_y),
        batch_size=256, shuffle=False, drop_last=False,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = UT_HAR_LeNet().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    # Output paths (new namespaces only).
    best_ckpt = checkpoints_dir / f"{args.run_name}_best.pt"
    last_ckpt = checkpoints_dir / f"{args.run_name}_last.pt"
    curve_path = results_dir / f"{args.run_name}_training_curve.csv"
    clean_test_path = results_dir / f"{args.run_name}_clean_metrics_test.csv"
    clean_legacy_path = results_dir / f"{args.run_name}_clean_metrics_legacy.csv"
    metadata_path = results_dir / f"{args.run_name}_metadata.json"

    selection_def = "0.5 * val_clean_macro_f1 + 0.5 * val_fgsm_adv_macro_f1"

    print("Stage 3: converged FGSM adversarial-training defense")
    print("-" * 70)
    print(f"Run name:          {args.run_name}")
    print(f"Device:            {device}")
    print(f"Seed:              {args.seed}")
    print(f"Max epochs:        {args.epochs}  | patience: {args.patience}")
    print(f"LR:                {args.lr}  | batch size: {args.batch_size}")
    print(f"FGSM train epsilon:{args.train_epsilon}")
    print(f"Loss weights:      clean={args.clean_loss_weight} adv={args.adv_loss_weight}")
    print(f"Split sizes:       {split_sizes}")
    print(f"Selection score:   {selection_def}")
    print("-" * 70)

    if args.dry_run:
        print("[dry-run] model + loaders built; no training, no files written.")
        print("[dry-run] planned output files:")
        for label, p in [
            ("best_checkpoint", best_ckpt), ("last_checkpoint", last_ckpt),
            ("training_curve", curve_path), ("clean_metrics_test", clean_test_path),
            ("clean_metrics_legacy", clean_legacy_path), ("metadata_json", metadata_path),
        ]:
            print(f"    {label}: {p}")
        return

    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    history = []
    best_score = -1.0
    best_epoch = -1
    best_record = None
    no_improve = 0
    start = time.time()

    for epoch in range(1, args.epochs + 1):
        tr = train_one_adv_epoch(
            model, train_loader, criterion, optimizer, device,
            args.train_epsilon, args.clean_loss_weight, args.adv_loss_weight,
        )

        # Validation: clean + FGSM-attacked (at training epsilon).
        _, v_true, v_pred, _ = s1.run_inference(model, val_loader, criterion, device)
        val_clean_acc = s1.accuracy_of(v_true, v_pred)
        val_clean_f1 = s1.macro_f1_of(v_true, v_pred)
        val_clean_fall = s1.compute_fall_binary_metrics(v_true, v_pred)["fall_recall"]

        va_true, va_pred = eval_fgsm(model, val_loader, criterion, device, args.train_epsilon)
        val_fgsm_acc = s1.accuracy_of(va_true, va_pred)
        val_fgsm_f1 = s1.macro_f1_of(va_true, va_pred)
        val_fgsm_fall = s1.compute_fall_binary_metrics(va_true, va_pred)["fall_recall"]

        selection_score = 0.5 * val_clean_f1 + 0.5 * val_fgsm_f1

        record = {
            "epoch": epoch,
            "train_total_loss": tr["train_total_loss"],
            "train_clean_accuracy": tr["train_clean_accuracy"],
            "train_adv_accuracy": tr["train_adv_accuracy"],
            "val_clean_accuracy": val_clean_acc,
            "val_clean_macro_f1": val_clean_f1,
            "val_clean_fall_recall": val_clean_fall,
            "val_fgsm_accuracy": val_fgsm_acc,
            "val_fgsm_macro_f1": val_fgsm_f1,
            "val_fgsm_fall_recall": val_fgsm_fall,
            "selection_score": selection_score,
        }
        history.append(record)

        flag = ""
        if selection_score > best_score:
            best_score = selection_score
            best_epoch = epoch
            best_record = record
            no_improve = 0
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "selection_score": selection_score,
                    "val_clean_macro_f1": val_clean_f1,
                    "val_fgsm_macro_f1": val_fgsm_f1,
                    "args": vars(args),
                },
                best_ckpt,
            )
            flag = " *best (checkpoint saved)"
        else:
            no_improve += 1

        print(
            f"Epoch {epoch:03d}/{args.epochs} | "
            f"train_clean={tr['train_clean_accuracy']:.4f} train_adv={tr['train_adv_accuracy']:.4f} | "
            f"val_clean_f1={val_clean_f1:.4f} val_fgsm_f1={val_fgsm_f1:.4f} "
            f"score={selection_score:.4f}{flag}"
        )

        if args.patience > 0 and no_improve >= args.patience:
            print(f"Early stopping at epoch {epoch}: no selection-score improvement "
                  f"for {args.patience} epochs (best epoch {best_epoch}).")
            break

    elapsed = time.time() - start
    last_epoch = history[-1]["epoch"]

    torch.save(
        {
            "epoch": last_epoch,
            "model_state_dict": model.state_dict(),
            "selection_score": history[-1]["selection_score"],
            "args": vars(args),
        },
        last_ckpt,
    )

    # Training curve CSV.
    curve_fields = [
        "epoch", "train_total_loss", "train_clean_accuracy", "train_adv_accuracy",
        "val_clean_accuracy", "val_clean_macro_f1", "val_clean_fall_recall",
        "val_fgsm_accuracy", "val_fgsm_macro_f1", "val_fgsm_fall_recall", "selection_score",
    ]
    with curve_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=curve_fields)
        writer.writeheader()
        for r in history:
            writer.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in curve_fields})

    # Final CLEAN defended metrics from the BEST checkpoint.
    best_state = torch.load(best_ckpt, map_location=device, weights_only=False)
    model.load_state_dict(best_state["model_state_dict"])

    _, t_true, t_pred, _ = s1.run_inference(model, test_loader, criterion, device)
    _, l_true, l_pred, _ = s1.run_inference(model, legacy_loader, criterion, device)
    test_metrics = clean_metric_dict(s1, "test", t_true, t_pred, split_sizes["test"])
    legacy_metrics = clean_metric_dict(s1, "legacy_val_plus_test", l_true, l_pred, len(legacy_y))
    s1.write_metric_value_csv(clean_test_path, test_metrics)
    s1.write_metric_value_csv(clean_legacy_path, legacy_metrics)

    metadata = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "stage3_converged_fgsm_adversarial_training_defense",
        "run_name": args.run_name,
        "defense_type": "FGSM adversarial training (mixed clean + FGSM); NOT PGD adversarial training",
        "train_epsilon": args.train_epsilon,
        "clean_loss_weight": args.clean_loss_weight,
        "adv_loss_weight": args.adv_loss_weight,
        "selection_score_definition": selection_def,
        "best_epoch": best_epoch,
        "epochs_run": last_epoch,
        "max_epochs": args.epochs,
        "patience": args.patience,
        "learning_rate": args.lr,
        "batch_size": args.batch_size,
        "seed": args.seed,
        "best_selection_score": best_record["selection_score"],
        "best_val_clean_macro_f1": best_record["val_clean_macro_f1"],
        "best_val_fgsm_macro_f1": best_record["val_fgsm_macro_f1"],
        "clean_defended_test_metrics": test_metrics,
        "clean_defended_legacy_metrics": legacy_metrics,
        "checkpoint_best": str(best_ckpt),
        "checkpoint_last": str(last_ckpt),
        "split_sizes": split_sizes,
        "legacy_note": (
            "legacy val+test (996 windows) is comparison-only; it was not used "
            "for training or checkpoint selection."
        ),
        "defense_note": (
            "This is FGSM adversarial training, not PGD adversarial training. "
            "Defended FGSM/PGD attack evaluation is performed separately via "
            "scripts/run_converged_attacks.py with --checkpoint pointing at the "
            "defended checkpoint."
        ),
        "device": str(device),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "sensefi_commit_sha": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(benchmark_dir)),
        "git_branch": s1.get_command_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(experiment_dir)),
        "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(experiment_dir)),
        "elapsed_seconds": elapsed,
    }
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("-" * 70)
    print("Converged FGSM adversarial-training defense completed.")
    print(f"Best epoch:        {best_epoch} (selection score {best_score:.4f})")
    print(f"Clean defended TEST:   acc={test_metrics['accuracy']:.4f} "
          f"fall_recall={test_metrics['fall_recall']:.4f}")
    print(f"Clean defended LEGACY: acc={legacy_metrics['accuracy']:.4f} "
          f"fall_recall={legacy_metrics['fall_recall']:.4f}")
    print(f"Elapsed: {elapsed:.1f} s")
    print(f"Metadata: {metadata_path}")


if __name__ == "__main__":
    main()
