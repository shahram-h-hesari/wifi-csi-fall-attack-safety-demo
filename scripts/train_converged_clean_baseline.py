"""
Train a converged clean SenseFi UT-HAR LeNet baseline (Stage 1).

Purpose:
    Train LeNet on UT_HAR_data to convergence using a proper train / validation /
    test protocol, then persist a reusable checkpoint plus clean evaluation
    artifacts. Unlike the existing ``*_short`` scripts (which retrain a fresh
    5-epoch model in-process and never save weights), this script:

        * trains on the TRAIN split only,
        * selects the best checkpoint on the VALIDATION split (macro-F1),
        * uses early stopping on validation (never on the test split),
        * reports final metrics on the held-out TEST split,
        * saves best + last checkpoints, training curve, test predictions,
          summary / per-class / fall-binary metrics, and run metadata.

Split note:
    SenseFi's ``util.load_data_n_model`` for UT_HAR_data concatenates X_val and
    X_test into a single "test" loader (see third_party SenseFi util.py). That
    would leak the test set into checkpoint selection / early stopping, which
    violates the Stage 1 protocol. This script therefore reuses the SAME proven
    data loader that passed the local smoke test (``UT_HAR_dataset`` + the
    Windows path patch) but builds three SEPARATE loaders from the raw
    dictionary so that validation and test stay distinct.

Important:
    These are window-level machine-learning research metrics.
    They are not clinical validation, medical-device validation, diagnostic
    evidence, or regulatory evaluation.

Expected run location:
    Repository root (the standalone wifi-csi-fall-attack-safety-demo repo).

Commands:
    python scripts/train_converged_clean_baseline.py --help
    python scripts/train_converged_clean_baseline.py \
        --epochs 100 --patience 15 --seed 42 --lr 1e-3 \
        --batch-size 64 --run-name converged_seed42
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import os
import platform
import random
import subprocess
import sys
import time
from datetime import datetime, timezone

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import precision_recall_fscore_support


# UT-HAR class index -> human-readable name (matches export_clean_predictions_short.py).
CLASS_NAMES = {
    0: "lie down",
    1: "fall",
    2: "walk",
    3: "pickup",
    4: "run",
    5: "sit down",
    6: "stand up",
}
NUM_CLASSES = 7
FALL_CLASS_INDEX = 1


def to_fall_binary(label: int) -> int:
    """Map a UT-HAR class label to a binary fall/non-fall label."""
    return 1 if int(label) == FALL_CLASS_INDEX else 0


def patch_sensefi_dataset_loader(benchmark_dir: Path) -> None:
    """Apply the same local Windows compatibility patch used by the smoke test.

    SenseFi's UT_HAR_dataset parses filenames with ``split('/')`` which, on
    Windows, yields keys such as ``data\\X_train`` instead of ``X_train``. This
    rewrites the parsing to use ``pathlib.Path(...).stem``. The third-party
    SenseFi folder is Git-ignored, so this patch is local only and idempotent.
    """
    dataset_file = benchmark_dir / "dataset.py"
    backup_file = benchmark_dir / "dataset.py.bak"

    if not dataset_file.exists():
        raise FileNotFoundError(f"Could not find SenseFi dataset.py at: {dataset_file}")

    text = dataset_file.read_text(encoding="utf-8")

    if not backup_file.exists():
        backup_file.write_text(text, encoding="utf-8")

    if "from pathlib import Path" not in text:
        text = text.replace("import glob\n", "import glob\nfrom pathlib import Path\n")

    text = text.replace(
        "data_name = data_dir.split('/')[-1].split('.')[0]",
        "data_name = Path(data_dir).stem",
    )
    text = text.replace(
        "label_name = label_dir.split('/')[-1].split('.')[0]",
        "label_name = Path(label_dir).stem",
    )

    dataset_file.write_text(text, encoding="utf-8")


def normalize_key(key) -> str:
    """Normalize SenseFi UT-HAR dict keys to bare stems (defensive, idempotent)."""
    key_text = str(key).replace("\\", "/")
    key_text = key_text.split("/")[-1]
    key_text = key_text.split(".")[0]
    return key_text


def set_seed(seed: int) -> None:
    """Set random seeds for more repeatable local runs."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_command_output(args, cwd=None) -> str:
    """Run a command and return stripped stdout, or 'unknown' on failure."""
    try:
        out = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except Exception:
        return "unknown"


def load_raw_ut_har(benchmark_dir: Path) -> dict:
    """Load the raw UT-HAR tensor dictionary using the smoke-test-proven loader.

    Returns a dict with normalized keys: X_train/X_val/X_test, y_train/y_val/y_test.
    Tensors are already reshaped to (N, 1, 250, 90) and min-max normalized by
    SenseFi's loader.
    """
    if str(benchmark_dir) not in sys.path:
        sys.path.insert(0, str(benchmark_dir))

    from dataset import UT_HAR_dataset  # provided by the SenseFi clone

    data_root = str(benchmark_dir / "Data") + "/"
    print("UT-HAR loader root:", data_root)
    raw = UT_HAR_dataset(data_root)

    normalized = {normalize_key(k): v for k, v in raw.items()}
    print("Normalized UT-HAR keys:", sorted(normalized.keys()))

    required = {"X_train", "X_val", "X_test", "y_train", "y_val", "y_test"}
    missing = required - set(normalized.keys())
    if missing:
        raise KeyError(f"UT-HAR data is missing expected keys: {sorted(missing)}")

    return normalized


def build_loaders(data: dict, batch_size: int):
    """Build three SEPARATE train / val / test loaders from the raw dict.

    Train uses batch_size with shuffle + drop_last=True (matching SenseFi's
    UT_HAR train loader). Validation and test use a fixed eval batch size with
    shuffle=False and drop_last=False so every sample is evaluated exactly once.
    """
    eval_batch_size = 256

    train_set = torch.utils.data.TensorDataset(data["X_train"], data["y_train"])
    val_set = torch.utils.data.TensorDataset(data["X_val"], data["y_val"])
    test_set = torch.utils.data.TensorDataset(data["X_test"], data["y_test"])

    train_loader = torch.utils.data.DataLoader(
        train_set, batch_size=batch_size, shuffle=True, drop_last=True
    )
    val_loader = torch.utils.data.DataLoader(
        val_set, batch_size=eval_batch_size, shuffle=False, drop_last=False
    )
    test_loader = torch.utils.data.DataLoader(
        test_set, batch_size=eval_batch_size, shuffle=False, drop_last=False
    )

    split_sizes = {
        "train": int(len(train_set)),
        "val": int(len(val_set)),
        "test": int(len(test_set)),
        "train_batches_per_epoch": int(len(train_loader)),
        "train_batch_size": int(batch_size),
        "eval_batch_size": int(eval_batch_size),
        "train_drop_last": True,
    }
    return train_loader, val_loader, test_loader, split_sizes


def train_one_epoch(model, loader, criterion, optimizer, device):
    """Train for one epoch; return (avg_loss, accuracy)."""
    model.train()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    for inputs, labels in loader:
        inputs = inputs.to(device)
        labels = labels.type(torch.LongTensor).to(device)

        optimizer.zero_grad()
        outputs = model(inputs).type(torch.FloatTensor).to(device)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        preds = torch.argmax(outputs, dim=1)
        total_correct += (preds == labels).sum().item()
        total_loss += loss.item() * inputs.size(0)
        total_samples += inputs.size(0)

    return total_loss / total_samples, total_correct / total_samples


def run_inference(model, loader, criterion, device):
    """Evaluate model on a loader.

    Returns (avg_loss, y_true, y_pred, confidence) where the last three are
    numpy arrays aligned by sample.
    """
    model.eval()
    total_loss = 0.0
    total_samples = 0
    y_true_all = []
    y_pred_all = []
    conf_all = []

    with torch.no_grad():
        for inputs, labels in loader:
            inputs = inputs.to(device)
            labels = labels.type(torch.LongTensor).to(device)

            outputs = model(inputs).type(torch.FloatTensor).to(device)
            loss = criterion(outputs, labels)

            probs = torch.softmax(outputs, dim=1)
            confidence, preds = torch.max(probs, dim=1)

            total_loss += loss.item() * inputs.size(0)
            total_samples += inputs.size(0)

            y_true_all.append(labels.cpu().numpy())
            y_pred_all.append(preds.cpu().numpy())
            conf_all.append(confidence.cpu().numpy())

    avg_loss = total_loss / total_samples
    y_true = np.concatenate(y_true_all)
    y_pred = np.concatenate(y_pred_all)
    confidence = np.concatenate(conf_all)
    return avg_loss, y_true, y_pred, confidence


def accuracy_of(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float((y_true == y_pred).mean()) if len(y_true) else 0.0


def macro_f1_of(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    _, _, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(NUM_CLASSES)), average="macro", zero_division=0
    )
    return float(f1)


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def compute_fall_binary_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute fall (class 1) vs non-fall binary safety-proxy metrics."""
    true_bin = (y_true == FALL_CLASS_INDEX).astype(int)
    pred_bin = (y_pred == FALL_CLASS_INDEX).astype(int)

    tp = int(np.sum((true_bin == 1) & (pred_bin == 1)))
    fp = int(np.sum((true_bin == 0) & (pred_bin == 1)))
    fn = int(np.sum((true_bin == 1) & (pred_bin == 0)))
    tn = int(np.sum((true_bin == 0) & (pred_bin == 0)))

    recall = safe_divide(tp, tp + fn)
    precision = safe_divide(tp, tp + fp)
    f1 = safe_divide(2 * precision * recall, precision + recall)
    specificity = safe_divide(tn, tn + fp)

    return {
        "fall_true_positive": tp,
        "fall_false_negative": fn,
        "fall_false_positive": fp,
        "fall_true_negative": tn,
        "fall_windows": tp + fn,
        "nonfall_windows": tn + fp,
        "fall_recall": recall,
        "missed_fall_rate": safe_divide(fn, tp + fn),
        "fall_precision": precision,
        "fall_f1": f1,
        "specificity": specificity,
        "false_positive_rate": safe_divide(fp, fp + tn),
    }


def write_metric_value_csv(path: Path, metrics: dict) -> None:
    """Write a {metric: value} dict as a two-column metric,value CSV."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for key, value in metrics.items():
            if isinstance(value, float):
                writer.writerow([key, f"{value:.6f}"])
            else:
                writer.writerow([key, value])


def write_per_class_csv(path: Path, y_true: np.ndarray, y_pred: np.ndarray) -> None:
    """Write per-class precision / recall / F1 / support."""
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(NUM_CLASSES)), zero_division=0
    )
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["class_index", "class_name", "precision", "recall", "f1", "support"])
        for idx in range(NUM_CLASSES):
            writer.writerow(
                [
                    idx,
                    CLASS_NAMES.get(idx, "unknown"),
                    f"{precision[idx]:.6f}",
                    f"{recall[idx]:.6f}",
                    f"{f1[idx]:.6f}",
                    int(support[idx]),
                ]
            )


def write_predictions_csv(
    path: Path, y_true: np.ndarray, y_pred: np.ndarray, confidence: np.ndarray
) -> None:
    """Write per-sample test predictions (same column schema as the short export)."""
    fieldnames = [
        "sample_id",
        "true_label",
        "true_class_name",
        "predicted_label",
        "predicted_class_name",
        "fall_true_binary",
        "fall_pred_binary",
        "prediction_confidence",
        "correct",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for sample_id, (t, p, c) in enumerate(zip(y_true, y_pred, confidence)):
            t = int(t)
            p = int(p)
            writer.writerow(
                {
                    "sample_id": sample_id,
                    "true_label": t,
                    "true_class_name": CLASS_NAMES.get(t, "unknown"),
                    "predicted_label": p,
                    "predicted_class_name": CLASS_NAMES.get(p, "unknown"),
                    "fall_true_binary": to_fall_binary(t),
                    "fall_pred_binary": to_fall_binary(p),
                    "prediction_confidence": f"{float(c):.6f}",
                    "correct": int(t == p),
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a converged clean SenseFi UT-HAR LeNet baseline (Stage 1).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--epochs", type=int, default=100, help="Maximum training epochs.")
    parser.add_argument(
        "--patience",
        type=int,
        default=15,
        help="Early-stopping patience: stop after this many epochs without "
        "validation macro-F1 improvement. Use 0 to disable early stopping.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Adam learning rate.")
    parser.add_argument(
        "--batch-size", type=int, default=64, help="Training batch size (SenseFi default: 64)."
    )
    parser.add_argument(
        "--run-name",
        type=str,
        default="converged_clean_baseline",
        help="Run name; used as the output filename prefix.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="lenet",
        help="Architecture to train (default: lenet, identical to prior behavior). "
        "Cross-architecture choices, e.g. resnet18, are resolved via model_factory.",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default=None,
        help="Override the results output directory (default: results/converged_baseline).",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default=None,
        help="Override the checkpoint output directory "
        "(default: checkpoints/converged_clean_baseline).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    experiment_dir = Path(__file__).resolve().parents[1]
    benchmark_dir = experiment_dir / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    data_dir = benchmark_dir / "Data" / "UT_HAR"

    checkpoints_dir = (
        Path(args.checkpoint_dir)
        if args.checkpoint_dir
        else experiment_dir / "checkpoints" / "converged_clean_baseline"
    )
    results_dir = (
        Path(args.results_dir)
        if args.results_dir
        else experiment_dir / "results" / "converged_baseline"
    )

    if not benchmark_dir.exists():
        raise FileNotFoundError(
            f"SenseFi benchmark clone not found. Expected folder:\n{benchmark_dir}"
        )
    if not data_dir.exists():
        raise FileNotFoundError(
            f"UT-HAR data folder not found. Expected folder:\n{data_dir}"
        )

    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Output paths (all namespaced by run name; never overwrite the short artifacts).
    best_ckpt_path = checkpoints_dir / f"{args.run_name}_best.pt"
    last_ckpt_path = checkpoints_dir / f"{args.run_name}_last.pt"
    curve_path = results_dir / f"{args.run_name}_training_curve.csv"
    predictions_path = results_dir / f"{args.run_name}_test_predictions.csv"
    summary_path = results_dir / f"{args.run_name}_summary_metrics.csv"
    per_class_path = results_dir / f"{args.run_name}_per_class_metrics.csv"
    fall_binary_path = results_dir / f"{args.run_name}_fall_binary_metrics.csv"
    metadata_path = results_dir / f"{args.run_name}_metadata.json"

    # Legacy comparison outputs: combined validation+test pool (996 windows),
    # used ONLY to compare against prior 996-window thesis artifacts. This pool
    # is never used for training, early stopping, or checkpoint selection.
    legacy_predictions_path = results_dir / f"{args.run_name}_legacy_eval_predictions.csv"
    legacy_summary_path = results_dir / f"{args.run_name}_legacy_eval_summary_metrics.csv"
    legacy_per_class_path = results_dir / f"{args.run_name}_legacy_eval_per_class_metrics.csv"
    legacy_fall_binary_path = results_dir / f"{args.run_name}_legacy_eval_fall_binary_metrics.csv"

    # Prepare SenseFi imports (apply Windows patch, then make the clone importable).
    patch_sensefi_dataset_loader(benchmark_dir)
    if str(benchmark_dir) not in sys.path:
        sys.path.insert(0, str(benchmark_dir))
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from model_factory import build_model

    set_seed(args.seed)

    data = load_raw_ut_har(benchmark_dir)
    train_loader, val_loader, test_loader, split_sizes = build_loaders(data, args.batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(args.model).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    # Junction / link provenance for metadata.
    resolved_data_path = os.path.realpath(data_dir)
    via_junction = os.path.normcase(resolved_data_path) != os.path.normcase(str(data_dir))

    sensefi_sha = get_command_output(["git", "rev-parse", "HEAD"], cwd=str(benchmark_dir))
    git_branch = get_command_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(experiment_dir)
    )
    git_commit = get_command_output(["git", "rev-parse", "HEAD"], cwd=str(experiment_dir))

    print("SenseFi UT-HAR LeNet converged clean baseline (Stage 1)")
    print("-" * 70)
    print(f"Run name:             {args.run_name}")
    print(f"Model:                {args.model}")
    print(f"Experiment directory: {experiment_dir}")
    print(f"Benchmark directory:  {benchmark_dir}")
    print(f"Data path:            {data_dir}")
    print(f"Resolved data path:   {resolved_data_path}")
    print(f"Accessed via junction:{via_junction}")
    print(f"Device:               {device}")
    print(f"Seed:                 {args.seed}")
    print(f"Max epochs:           {args.epochs}")
    print(f"Patience:             {args.patience}")
    print(f"Learning rate:        {args.lr}")
    print(f"Train batch size:     {args.batch_size}")
    print(f"Split sizes:          {split_sizes}")
    print(f"Checkpoint selection: validation macro-F1 (test split never used for selection)")
    print("-" * 70)

    history = []
    best_val_macro_f1 = -1.0
    best_epoch = -1
    best_record = None
    epochs_without_improvement = 0
    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_true, val_pred, _ = run_inference(model, val_loader, criterion, device)
        val_acc = accuracy_of(val_true, val_pred)
        val_macro_f1 = macro_f1_of(val_true, val_pred)

        record = {
            "epoch": epoch,
            "train_loss": train_loss,
            "train_accuracy": train_acc,
            "val_loss": val_loss,
            "val_accuracy": val_acc,
            "val_macro_f1": val_macro_f1,
        }
        history.append(record)

        improved = val_macro_f1 > best_val_macro_f1
        flag = ""
        if improved:
            best_val_macro_f1 = val_macro_f1
            best_epoch = epoch
            best_record = record
            epochs_without_improvement = 0
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "val_macro_f1": val_macro_f1,
                    "val_accuracy": val_acc,
                    "val_loss": val_loss,
                    "args": vars(args),
                },
                best_ckpt_path,
            )
            flag = " *best (checkpoint saved)"
        else:
            epochs_without_improvement += 1

        print(
            f"Epoch {epoch:03d}/{args.epochs} | "
            f"train_acc={train_acc:.4f}, train_loss={train_loss:.4f} | "
            f"val_acc={val_acc:.4f}, val_loss={val_loss:.4f}, val_macroF1={val_macro_f1:.4f}"
            f"{flag}"
        )

        if args.patience > 0 and epochs_without_improvement >= args.patience:
            print(
                f"Early stopping at epoch {epoch}: no validation macro-F1 "
                f"improvement for {args.patience} epochs (best epoch {best_epoch})."
            )
            break

    elapsed = time.time() - start_time
    last_epoch = history[-1]["epoch"]

    # Always save the last checkpoint (final epoch trained).
    torch.save(
        {
            "epoch": last_epoch,
            "model_state_dict": model.state_dict(),
            "val_macro_f1": history[-1]["val_macro_f1"],
            "val_accuracy": history[-1]["val_accuracy"],
            "val_loss": history[-1]["val_loss"],
            "args": vars(args),
        },
        last_ckpt_path,
    )

    # Training curve CSV.
    with curve_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "epoch",
                "train_loss",
                "train_accuracy",
                "val_loss",
                "val_accuracy",
                "val_macro_f1",
            ],
        )
        writer.writeheader()
        for row in history:
            writer.writerow(
                {
                    "epoch": row["epoch"],
                    "train_loss": f"{row['train_loss']:.6f}",
                    "train_accuracy": f"{row['train_accuracy']:.6f}",
                    "val_loss": f"{row['val_loss']:.6f}",
                    "val_accuracy": f"{row['val_accuracy']:.6f}",
                    "val_macro_f1": f"{row['val_macro_f1']:.6f}",
                }
            )

    # Final TEST reporting uses the BEST (validation-selected) checkpoint.
    best_state = torch.load(best_ckpt_path, map_location=device)
    model.load_state_dict(best_state["model_state_dict"])

    test_loss, test_true, test_pred, test_conf = run_inference(
        model, test_loader, criterion, device
    )
    test_acc = accuracy_of(test_true, test_pred)
    test_macro_f1 = macro_f1_of(test_true, test_pred)
    fall_metrics = compute_fall_binary_metrics(test_true, test_pred)

    write_predictions_csv(predictions_path, test_true, test_pred, test_conf)
    write_per_class_csv(per_class_path, test_true, test_pred)
    write_metric_value_csv(fall_binary_path, fall_metrics)

    summary_metrics = {
        "run_name": args.run_name,
        "best_epoch": best_epoch,
        "epochs_run": last_epoch,
        "max_epochs": args.epochs,
        "early_stopped": bool(args.patience > 0 and last_epoch < args.epochs),
        "best_val_macro_f1": best_record["val_macro_f1"],
        "best_val_accuracy": best_record["val_accuracy"],
        "best_val_loss": best_record["val_loss"],
        "best_train_accuracy": best_record["train_accuracy"],
        "best_train_loss": best_record["train_loss"],
        "test_loss": test_loss,
        "test_accuracy": test_acc,
        "test_macro_f1": test_macro_f1,
        "fall_recall": fall_metrics["fall_recall"],
        "missed_fall_rate": fall_metrics["missed_fall_rate"],
        "fall_precision": fall_metrics["fall_precision"],
        "fall_f1": fall_metrics["fall_f1"],
        "elapsed_seconds": elapsed,
    }
    write_metric_value_csv(summary_path, summary_metrics)

    # ------------------------------------------------------------------
    # Legacy comparison evaluation: combined validation + test (996 windows).
    # This reuses the BEST (validation-selected) checkpoint already loaded into
    # `model`. It exists ONLY to compare against prior 996-window thesis
    # artifacts and is NOT used for training, early stopping, or checkpoint
    # selection. Built from the raw dict so the pool exactly matches SenseFi's
    # original concatenation order (X_val followed by X_test).
    # ------------------------------------------------------------------
    legacy_X = torch.cat((data["X_val"], data["X_test"]), 0)
    legacy_y = torch.cat((data["y_val"], data["y_test"]), 0)
    legacy_set = torch.utils.data.TensorDataset(legacy_X, legacy_y)
    legacy_loader = torch.utils.data.DataLoader(
        legacy_set, batch_size=256, shuffle=False, drop_last=False
    )

    legacy_loss, legacy_true, legacy_pred, legacy_conf = run_inference(
        model, legacy_loader, criterion, device
    )
    legacy_acc = accuracy_of(legacy_true, legacy_pred)
    legacy_macro_f1 = macro_f1_of(legacy_true, legacy_pred)
    legacy_fall_metrics = compute_fall_binary_metrics(legacy_true, legacy_pred)

    write_predictions_csv(legacy_predictions_path, legacy_true, legacy_pred, legacy_conf)
    write_per_class_csv(legacy_per_class_path, legacy_true, legacy_pred)
    write_metric_value_csv(legacy_fall_binary_path, legacy_fall_metrics)

    legacy_summary_metrics = {
        "run_name": args.run_name,
        "eval_split": "legacy_val_plus_test",
        "eval_windows": int(len(legacy_set)),
        "checkpoint_used": "best (validation-selected)",
        "legacy_loss": legacy_loss,
        "legacy_accuracy": legacy_acc,
        "legacy_macro_f1": legacy_macro_f1,
        "fall_recall": legacy_fall_metrics["fall_recall"],
        "missed_fall_rate": legacy_fall_metrics["missed_fall_rate"],
        "fall_precision": legacy_fall_metrics["fall_precision"],
        "fall_f1": legacy_fall_metrics["fall_f1"],
    }
    write_metric_value_csv(legacy_summary_path, legacy_summary_metrics)

    metadata = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "run_name": args.run_name,
        "model": args.model,
        "seed": args.seed,
        "max_epochs": args.epochs,
        "epochs_run": last_epoch,
        "best_epoch": best_epoch,
        "patience": args.patience,
        "learning_rate": args.lr,
        "train_batch_size": args.batch_size,
        "checkpoint_selection_metric": "validation_macro_f1",
        "device": str(device),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "sensefi_commit_sha": sensefi_sha,
        "data_path": str(data_dir),
        "resolved_data_path": resolved_data_path,
        "data_accessed_via_junction": via_junction,
        "data_junction_note": (
            "UT-HAR data is accessed via a local Windows directory junction "
            "pointing at the main repo's copy; data is not stored in this repo."
        ),
        "git_branch": git_branch,
        "git_commit": git_commit,
        "split_sizes": split_sizes,
        "class_names": CLASS_NAMES,
        "fall_class_index": FALL_CLASS_INDEX,
        "legacy_eval_note": (
            "legacy_eval_val_plus_test is for comparison to prior 996-window "
            "thesis artifacts only and was not used for training, early stopping, "
            "or checkpoint selection."
        ),
        "legacy_eval_val_plus_test": {
            "eval_windows": int(len(legacy_set)),
            "accuracy": legacy_acc,
            "macro_f1": legacy_macro_f1,
            "fall_recall": legacy_fall_metrics["fall_recall"],
            "missed_fall_rate": legacy_fall_metrics["missed_fall_rate"],
            "fall_precision": legacy_fall_metrics["fall_precision"],
            "fall_f1": legacy_fall_metrics["fall_f1"],
        },
        "outputs": {
            "best_checkpoint": str(best_ckpt_path),
            "last_checkpoint": str(last_ckpt_path),
            "training_curve_csv": str(curve_path),
            "test_predictions_csv": str(predictions_path),
            "summary_metrics_csv": str(summary_path),
            "per_class_metrics_csv": str(per_class_path),
            "fall_binary_metrics_csv": str(fall_binary_path),
            "legacy_eval_predictions_csv": str(legacy_predictions_path),
            "legacy_eval_summary_metrics_csv": str(legacy_summary_path),
            "legacy_eval_per_class_metrics_csv": str(legacy_per_class_path),
            "legacy_eval_fall_binary_metrics_csv": str(legacy_fall_binary_path),
        },
    }
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("-" * 70)
    print("Converged clean baseline completed successfully.")
    print(f"Best epoch:        {best_epoch} (val macro-F1 {best_val_macro_f1:.4f})")
    print(f"Test accuracy:     {test_acc:.4f}")
    print(f"Test macro-F1:     {test_macro_f1:.4f}")
    print(f"Fall recall:       {fall_metrics['fall_recall']:.4f}")
    print(f"Missed-fall rate:  {fall_metrics['missed_fall_rate']:.4f}")
    print(
        f"[legacy val+test]  acc={legacy_acc:.4f}, macroF1={legacy_macro_f1:.4f} "
        f"(comparison only; not used for selection)"
    )
    print(f"Elapsed:           {elapsed:.1f} s")
    print("-" * 70)
    print("Artifacts:")
    for key, value in metadata["outputs"].items():
        print(f"  {key}: {value}")
    print(f"  run_metadata_json: {metadata_path}")


if __name__ == "__main__":
    main()
