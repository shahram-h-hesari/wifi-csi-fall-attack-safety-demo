"""
Export an expanded 18-epsilon prediction sweep for FGSM and PGD.

Purpose:
    Generate prediction-level CSV files for multiple software-level adversarial
    perturbation strengths so the project can later create a true
    attack-severity dose-response analysis.

Important claim boundary:
    This script applies software-level adversarial perturbations to processed
    UT-HAR / SenseFi CSI tensors. It is not a physical-layer, packet-level,
    preamble-level, SDR, over-the-air, clinical, medical-device, diagnostic,
    or regulatory validation experiment.

Why this script exists:
    Earlier prediction export scripts saved only epsilon = 0.03. That is useful
    for Tables/Figures 1-26, but it is not enough for a dose-response curve.
    This script preserves those earlier results and writes a new experiment
    layer under:

        results/epsilon_sweep_predictions/

Expected run location:
    experiments/fall_detection_attack_safety_demo/

Command:
    python scripts/export_attack_prediction_sweep_18eps.py

Outputs:
    results/epsilon_sweep_predictions/
        fgsm_predictions_short_epsilon_0.csv
        fgsm_predictions_short_epsilon_0_001.csv
        ...
        fgsm_predictions_short_epsilon_0_075.csv
        pgd_predictions_short_epsilon_0.csv
        pgd_predictions_short_epsilon_0_001.csv
        ...
        pgd_predictions_short_epsilon_0_075.csv
        attack_prediction_sweep_18eps_summary.csv
"""

from __future__ import annotations

import csv
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn


# =============================================================================
# Experiment configuration
# =============================================================================

SEED = 42
SHORT_EPOCHS = 5
LEARNING_RATE = 1e-3

# Dense near the low-epsilon transition region, with stress-test points later.
EPSILONS = [
    0.000,
    0.001,
    0.002,
    0.003,
    0.004,
    0.005,
    0.0075,
    0.010,
    0.0125,
    0.015,
    0.0175,
    0.020,
    0.025,
    0.030,
    0.035,
    0.040,
    0.050,
    0.075,
]

PGD_STEPS = 10
PGD_ALPHA_DIVISOR = 6.0

FALL_LABEL = 1

CLASS_NAMES = {
    0: "lie down",
    1: "fall",
    2: "walk",
    3: "pickup",
    4: "run",
    5: "sit down",
    6: "stand up",
}

SAFETY_SCORE_WEIGHTS = [
    ("score_1_to_1", 1.0, 1.0),
    ("score_2_to_1", 2.0, 1.0),
    ("score_5_to_1", 5.0, 1.0),
    ("score_10_to_1", 10.0, 1.0),
]


# =============================================================================
# Paths
# =============================================================================

SCRIPT_PATH = Path(__file__).resolve()
EXPERIMENT_DIR = SCRIPT_PATH.parent.parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
SWEEP_DIR = RESULTS_DIR / "epsilon_sweep_predictions"

SUMMARY_PATH = SWEEP_DIR / "attack_prediction_sweep_18eps_summary.csv"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SWEEP_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Reproducibility and SenseFi import helpers
# =============================================================================

def set_reproducibility(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # Keep reproducibility as stable as possible without making the script brittle.
    torch.backends.cudnn.deterministic = False
    torch.backends.cudnn.benchmark = False


def patch_sensefi_dataset_loader(benchmark_dir: Path) -> None:
    """
    Patch the local ignored SenseFi dataset loader for Windows path separators.

    The original SenseFi loader can extract keys using split('/'), which may
    create keys like data\\X_train on Windows. The patch uses Path(...).stem so
    keys become X_train, y_train, etc.
    """
    dataset_path = benchmark_dir / "dataset.py"
    backup_path = benchmark_dir / "dataset.py.bak"

    if not dataset_path.exists():
        raise FileNotFoundError(f"Could not find SenseFi dataset.py at: {dataset_path}")

    text = dataset_path.read_text(encoding="utf-8")

    if not backup_path.exists():
        backup_path.write_text(text, encoding="utf-8")

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

    dataset_path.write_text(text, encoding="utf-8")


def prepare_sensefi_imports(experiment_dir: Path) -> Path:
    benchmark_dir = experiment_dir / "third_party" / "WiFi-CSI-Sensing-Benchmark"

    if not benchmark_dir.exists():
        raise FileNotFoundError(
            "SenseFi benchmark clone not found. Expected folder:\n"
            f"{benchmark_dir}"
        )

    patch_sensefi_dataset_loader(benchmark_dir)

    os.chdir(benchmark_dir)
    sys.path.insert(0, str(benchmark_dir))

    return benchmark_dir


# =============================================================================
# Model training and clean evaluation
# =============================================================================

def train_one_epoch(model, tensor_loader, optimizer, criterion, device):
    model.train()

    running_loss = 0.0
    running_correct = 0
    running_total = 0

    for inputs, labels in tensor_loader:
        inputs = inputs.to(device).float()
        labels = labels.to(device).long()

        optimizer.zero_grad()

        outputs = model(inputs).float()
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        predicted = torch.argmax(outputs, dim=1)

        running_loss += loss.item() * inputs.size(0)
        running_correct += (predicted == labels).sum().item()
        running_total += labels.size(0)

    return running_loss / running_total, running_correct / running_total


def evaluate_clean(model, tensor_loader, criterion, device):
    model.eval()

    running_loss = 0.0
    running_correct = 0
    running_total = 0

    with torch.no_grad():
        for inputs, labels in tensor_loader:
            inputs = inputs.to(device).float()
            labels = labels.to(device).long()

            outputs = model(inputs).float()
            loss = criterion(outputs, labels)

            predicted = torch.argmax(outputs, dim=1)

            running_loss += loss.item() * inputs.size(0)
            running_correct += (predicted == labels).sum().item()
            running_total += labels.size(0)

    return running_loss / running_total, running_correct / running_total


# =============================================================================
# Attack helpers
# =============================================================================

def label_to_binary_fall(label: int) -> int:
    return 1 if int(label) == FALL_LABEL else 0


def epsilon_to_file_token(epsilon: float) -> str:
    """
    Convert epsilon to filename token.

    Examples:
        0.000  -> 0
        0.001  -> 0_001
        0.0075 -> 0_0075
        0.030  -> 0_03
        0.075  -> 0_075
    """
    text = f"{epsilon:.6f}".rstrip("0").rstrip(".")
    if text == "-0":
        text = "0"
    return text.replace(".", "_")


def pgd_alpha_for_epsilon(epsilon: float) -> float:
    if epsilon == 0.0:
        return 0.0
    return epsilon / PGD_ALPHA_DIVISOR


def pgd_attack(
    model: torch.nn.Module,
    inputs: torch.Tensor,
    labels: torch.Tensor,
    criterion,
    epsilon: float,
    alpha: float,
    steps: int,
) -> torch.Tensor:
    """
    Untargeted PGD attack under an L-infinity perturbation limit.

    Because UT-HAR tensors are processed CSI features rather than raw image
    pixels, this implementation does not clamp values to [0, 1].
    """
    if epsilon == 0.0:
        return inputs.detach()

    original_inputs = inputs.detach()
    adv_inputs = original_inputs.clone().detach()

    for _ in range(steps):
        adv_inputs.requires_grad = True

        outputs = model(adv_inputs).float()
        loss = criterion(outputs, labels)

        model.zero_grad()
        loss.backward()

        with torch.no_grad():
            gradient_sign = adv_inputs.grad.sign()
            adv_inputs = adv_inputs + alpha * gradient_sign

            perturbation = torch.clamp(
                adv_inputs - original_inputs,
                min=-epsilon,
                max=epsilon,
            )

            adv_inputs = original_inputs + perturbation

        adv_inputs = adv_inputs.detach()

    return adv_inputs


# =============================================================================
# Row generation and metrics
# =============================================================================

def build_prediction_row(
    sample_id: int,
    attack_type: str,
    epsilon: float,
    alpha: float,
    pgd_steps: int,
    true_label: int,
    clean_predicted_label: int,
    attacked_predicted_label: int,
    clean_confidence: float,
    attacked_confidence: float,
) -> dict[str, Any]:
    true_class_name = CLASS_NAMES.get(true_label, f"unknown_{true_label}")
    clean_predicted_class_name = CLASS_NAMES.get(
        clean_predicted_label,
        f"unknown_{clean_predicted_label}",
    )
    attacked_predicted_class_name = CLASS_NAMES.get(
        attacked_predicted_label,
        f"unknown_{attacked_predicted_label}",
    )

    fall_true_binary = label_to_binary_fall(true_label)
    clean_fall_pred_binary = label_to_binary_fall(clean_predicted_label)
    attacked_fall_pred_binary = label_to_binary_fall(attacked_predicted_label)

    return {
        "sample_id": sample_id,
        "attack_type": attack_type,
        "epsilon": f"{epsilon:.6f}",
        "alpha": f"{alpha:.6f}" if attack_type == "PGD" else "",
        "pgd_steps": pgd_steps if attack_type == "PGD" else "",
        "true_label": true_label,
        "true_class_name": true_class_name,
        "clean_predicted_label": clean_predicted_label,
        "clean_predicted_class_name": clean_predicted_class_name,
        "attacked_predicted_label": attacked_predicted_label,
        "attacked_predicted_class_name": attacked_predicted_class_name,
        "fall_true_binary": fall_true_binary,
        "clean_fall_pred_binary": clean_fall_pred_binary,
        "attacked_fall_pred_binary": attacked_fall_pred_binary,
        "clean_prediction_confidence": f"{clean_confidence:.6f}",
        "attacked_prediction_confidence": f"{attacked_confidence:.6f}",
        "clean_correct": int(clean_predicted_label == true_label),
        "attacked_correct": int(attacked_predicted_label == true_label),
        "prediction_changed": int(clean_predicted_label != attacked_predicted_label),
    }


def confusion_counts_from_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    tp = fn = fp = tn = 0

    for row in rows:
        true_binary = int(row["fall_true_binary"])
        pred_binary = int(row["attacked_fall_pred_binary"])

        if true_binary == 1 and pred_binary == 1:
            tp += 1
        elif true_binary == 1 and pred_binary == 0:
            fn += 1
        elif true_binary == 0 and pred_binary == 1:
            fp += 1
        elif true_binary == 0 and pred_binary == 0:
            tn += 1
        else:
            raise ValueError(f"Unexpected binary values: {true_binary}, {pred_binary}")

    return {"tp": tp, "fn": fn, "fp": fp, "tn": tn}


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return float("nan")
    return numerator / denominator


def metrics_from_rows(
    rows: list[dict[str, Any]],
    attack_type: str,
    epsilon: float,
    alpha: float,
    output_path: Path,
) -> dict[str, Any]:
    counts = confusion_counts_from_rows(rows)

    tp = counts["tp"]
    fn = counts["fn"]
    fp = counts["fp"]
    tn = counts["tn"]

    total_rows = len(rows)
    total_fall = tp + fn
    total_nonfall = fp + tn

    clean_correct = sum(int(row["clean_correct"]) for row in rows)
    attacked_correct = sum(int(row["attacked_correct"]) for row in rows)
    prediction_changed = sum(int(row["prediction_changed"]) for row in rows)

    fnr = safe_divide(fn, total_fall)
    fpr = safe_divide(fp, total_nonfall)
    tpr = safe_divide(tp, total_fall)
    tnr = safe_divide(tn, total_nonfall)
    precision = safe_divide(tp, tp + fp)
    f1 = safe_divide(2 * precision * tpr, precision + tpr)

    summary = {
        "attack_type": attack_type,
        "epsilon": f"{epsilon:.6f}",
        "epsilon_file_token": epsilon_to_file_token(epsilon),
        "alpha": f"{alpha:.6f}" if attack_type == "PGD" else "",
        "pgd_steps": PGD_STEPS if attack_type == "PGD" else "",
        "prediction_file": str(output_path),
        "total_windows": total_rows,
        "total_fall_windows": total_fall,
        "total_nonfall_windows": total_nonfall,
        "clean_accuracy": safe_divide(clean_correct, total_rows),
        "attacked_accuracy": safe_divide(attacked_correct, total_rows),
        "accuracy_drop": safe_divide(clean_correct, total_rows) - safe_divide(attacked_correct, total_rows),
        "prediction_changed_count": prediction_changed,
        "prediction_change_rate": safe_divide(prediction_changed, total_rows),
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "missed_fall_rate_fnr": fnr,
        "false_positive_rate_fpr": fpr,
        "fall_recall_tpr": tpr,
        "specificity_tnr": tnr,
        "precision_ppv": precision,
        "f1_score": f1,
    }

    for score_name, fn_weight, fp_weight in SAFETY_SCORE_WEIGHTS:
        summary[score_name] = fn_weight * fnr + fp_weight * fpr

    return summary


def format_summary_value(value: Any) -> str:
    if isinstance(value, float):
        if np.isnan(value):
            return "nan"
        return f"{value:.6f}"
    return str(value)


def write_prediction_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "sample_id",
        "attack_type",
        "epsilon",
        "alpha",
        "pgd_steps",
        "true_label",
        "true_class_name",
        "clean_predicted_label",
        "clean_predicted_class_name",
        "attacked_predicted_label",
        "attacked_predicted_class_name",
        "fall_true_binary",
        "clean_fall_pred_binary",
        "attacked_fall_pred_binary",
        "clean_prediction_confidence",
        "attacked_prediction_confidence",
        "clean_correct",
        "attacked_correct",
        "prediction_changed",
    ]

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "attack_type",
        "epsilon",
        "epsilon_file_token",
        "alpha",
        "pgd_steps",
        "prediction_file",
        "total_windows",
        "total_fall_windows",
        "total_nonfall_windows",
        "clean_accuracy",
        "attacked_accuracy",
        "accuracy_drop",
        "prediction_changed_count",
        "prediction_change_rate",
        "tp",
        "fn",
        "fp",
        "tn",
        "missed_fall_rate_fnr",
        "false_positive_rate_fpr",
        "fall_recall_tpr",
        "specificity_tnr",
        "precision_ppv",
        "f1_score",
        "score_1_to_1",
        "score_2_to_1",
        "score_5_to_1",
        "score_10_to_1",
    ]

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({key: format_summary_value(row[key]) for key in fieldnames})


# =============================================================================
# Attack export functions
# =============================================================================

def export_fgsm_for_epsilon(
    model,
    tensor_loader,
    criterion,
    device,
    epsilon: float,
    output_path: Path,
) -> dict[str, Any]:
    model.eval()

    rows: list[dict[str, Any]] = []
    sample_id = 0

    for inputs, labels in tensor_loader:
        inputs = inputs.to(device).float()
        labels = labels.to(device).long()

        attack_inputs = inputs.clone().detach()
        attack_inputs.requires_grad = True

        clean_outputs = model(attack_inputs).float()
        clean_loss = criterion(clean_outputs, labels)

        model.zero_grad()
        clean_loss.backward()

        input_gradient = attack_inputs.grad.detach()
        attacked_inputs = attack_inputs + epsilon * input_gradient.sign()
        attacked_inputs = attacked_inputs.detach()

        with torch.no_grad():
            attacked_outputs = model(attacked_inputs).float()

            clean_probs = torch.softmax(clean_outputs.detach(), dim=1)
            attacked_probs = torch.softmax(attacked_outputs, dim=1)

            clean_confidences, clean_predictions = clean_probs.max(dim=1)
            attacked_confidences, attacked_predictions = attacked_probs.max(dim=1)

        for i in range(labels.size(0)):
            rows.append(
                build_prediction_row(
                    sample_id=sample_id,
                    attack_type="FGSM",
                    epsilon=epsilon,
                    alpha=0.0,
                    pgd_steps=0,
                    true_label=int(labels[i].item()),
                    clean_predicted_label=int(clean_predictions[i].item()),
                    attacked_predicted_label=int(attacked_predictions[i].item()),
                    clean_confidence=float(clean_confidences[i].item()),
                    attacked_confidence=float(attacked_confidences[i].item()),
                )
            )
            sample_id += 1

    write_prediction_csv(output_path, rows)
    return metrics_from_rows(
        rows=rows,
        attack_type="FGSM",
        epsilon=epsilon,
        alpha=0.0,
        output_path=output_path,
    )


def export_pgd_for_epsilon(
    model,
    tensor_loader,
    criterion,
    device,
    epsilon: float,
    output_path: Path,
) -> dict[str, Any]:
    model.eval()

    rows: list[dict[str, Any]] = []
    sample_id = 0
    alpha = pgd_alpha_for_epsilon(epsilon)

    for inputs, labels in tensor_loader:
        inputs = inputs.to(device).float()
        labels = labels.to(device).long()

        with torch.no_grad():
            clean_outputs = model(inputs).float()
            clean_probs = torch.softmax(clean_outputs, dim=1)
            clean_confidences, clean_predictions = clean_probs.max(dim=1)

        attacked_inputs = pgd_attack(
            model=model,
            inputs=inputs,
            labels=labels,
            criterion=criterion,
            epsilon=epsilon,
            alpha=alpha,
            steps=PGD_STEPS,
        )

        with torch.no_grad():
            attacked_outputs = model(attacked_inputs).float()
            attacked_probs = torch.softmax(attacked_outputs, dim=1)
            attacked_confidences, attacked_predictions = attacked_probs.max(dim=1)

        for i in range(labels.size(0)):
            rows.append(
                build_prediction_row(
                    sample_id=sample_id,
                    attack_type="PGD",
                    epsilon=epsilon,
                    alpha=alpha,
                    pgd_steps=PGD_STEPS,
                    true_label=int(labels[i].item()),
                    clean_predicted_label=int(clean_predictions[i].item()),
                    attacked_predicted_label=int(attacked_predictions[i].item()),
                    clean_confidence=float(clean_confidences[i].item()),
                    attacked_confidence=float(attacked_confidences[i].item()),
                )
            )
            sample_id += 1

    write_prediction_csv(output_path, rows)
    return metrics_from_rows(
        rows=rows,
        attack_type="PGD",
        epsilon=epsilon,
        alpha=alpha,
        output_path=output_path,
    )


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    start_time = time.time()

    set_reproducibility(SEED)

    benchmark_dir = prepare_sensefi_imports(EXPERIMENT_DIR)

    from util import load_data_n_model

    train_loader, test_loader, model, original_train_epoch = load_data_n_model(
        dataset_name="UT_HAR_data",
        model_name="LeNet",
        root="./Data/",
    )

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    print("SenseFi UT-HAR LeNet expanded attack prediction sweep")
    print("-" * 80)
    print(f"Experiment directory: {EXPERIMENT_DIR}")
    print(f"Benchmark directory:  {benchmark_dir}")
    print(f"Output directory:     {SWEEP_DIR}")
    print(f"Device:               {device}")
    print(f"Original train epochs:{original_train_epoch}")
    print(f"Short clean epochs:   {SHORT_EPOCHS}")
    print(f"Epsilon count:        {len(EPSILONS)}")
    print(f"Epsilons:             {EPSILONS}")
    print(f"PGD steps:            {PGD_STEPS}")
    print(f"PGD alpha rule:       alpha = epsilon / {PGD_ALPHA_DIVISOR}")
    print("Prediction split:     SenseFi validation+test loader")
    print("-" * 80)

    print("Training one clean baseline model used for all epsilon exports...")
    for epoch in range(1, SHORT_EPOCHS + 1):
        train_loss, train_accuracy = train_one_epoch(
            model=model,
            tensor_loader=train_loader,
            optimizer=optimizer,
            criterion=criterion,
            device=device,
        )

        test_loss, test_accuracy = evaluate_clean(
            model=model,
            tensor_loader=test_loader,
            criterion=criterion,
            device=device,
        )

        print(
            f"Epoch {epoch:02d}/{SHORT_EPOCHS} | "
            f"train_acc={train_accuracy:.4f}, train_loss={train_loss:.4f} | "
            f"test_acc={test_accuracy:.4f}, test_loss={test_loss:.4f}"
        )

    summary_rows: list[dict[str, Any]] = []

    print("-" * 80)
    print("Exporting FGSM and PGD prediction files...")
    for epsilon in EPSILONS:
        token = epsilon_to_file_token(epsilon)

        fgsm_output_path = SWEEP_DIR / f"fgsm_predictions_short_epsilon_{token}.csv"
        pgd_output_path = SWEEP_DIR / f"pgd_predictions_short_epsilon_{token}.csv"

        fgsm_summary = export_fgsm_for_epsilon(
            model=model,
            tensor_loader=test_loader,
            criterion=criterion,
            device=device,
            epsilon=epsilon,
            output_path=fgsm_output_path,
        )
        summary_rows.append(fgsm_summary)

        pgd_summary = export_pgd_for_epsilon(
            model=model,
            tensor_loader=test_loader,
            criterion=criterion,
            device=device,
            epsilon=epsilon,
            output_path=pgd_output_path,
        )
        summary_rows.append(pgd_summary)

        print(
            f"epsilon={epsilon:.6f} | "
            f"FGSM: acc={fgsm_summary['attacked_accuracy']:.4f}, "
            f"FNR={fgsm_summary['missed_fall_rate_fnr']:.4f}, "
            f"FPR={fgsm_summary['false_positive_rate_fpr']:.4f}, "
            f"score10={fgsm_summary['score_10_to_1']:.4f} | "
            f"PGD: acc={pgd_summary['attacked_accuracy']:.4f}, "
            f"FNR={pgd_summary['missed_fall_rate_fnr']:.4f}, "
            f"FPR={pgd_summary['false_positive_rate_fpr']:.4f}, "
            f"score10={pgd_summary['score_10_to_1']:.4f}"
        )

    write_summary_csv(SUMMARY_PATH, summary_rows)

    elapsed_time = time.time() - start_time

    print("-" * 80)
    print("Expanded attack prediction sweep completed successfully.")
    print(f"Prediction files directory: {SWEEP_DIR}")
    print(f"Summary CSV:                {SUMMARY_PATH}")
    print(f"Rows in summary:            {len(summary_rows)}")
    print(f"Elapsed time:               {elapsed_time:.1f} seconds")
    print()
    print("Next suggested artifact:")
    print("  Table/Figure 27: Attack-Severity Dose Response of Fall-Safety Metrics")


if __name__ == "__main__":
    main()
