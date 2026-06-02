"""
Run a PGD epsilon sweep for the WiFi CSI Fall Attack-Safety Demo.

Experiment:
- Baseline: SenseFi / UT-HAR / LeNet
- Task: Seven-class UT-HAR activity recognition
- Safety translation: binary fall vs non-fall window-level proxy metrics
- Attack: PGD, applied to processed UT-HAR CSI tensors

Output:
- results/pgd_epsilon_sweep_summary.csv

Important claim boundary:
This script applies software-level PGD perturbations to processed CSI tensors.
It is not a physical-layer, packet-level, preamble-level, SDR, or over-the-air attack.
It is not clinical validation, medical-device validation, diagnostic evidence, or regulatory evaluation.
"""

from pathlib import Path
import csv
import os
import random
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset


SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = EXPERIMENT_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

SENSEFI_DIR = EXPERIMENT_DIR / "third_party" / "WiFi-CSI-Sensing-Benchmark"

if not SENSEFI_DIR.exists():
    raise FileNotFoundError(
        f"SenseFi folder not found: {SENSEFI_DIR}\n"
        "Expected location: third_party/WiFi-CSI-Sensing-Benchmark"
    )

sys.path.insert(0, str(SENSEFI_DIR))


try:
    from dataset import UT_HAR_dataset
    from UT_HAR_model import UT_HAR_LeNet
except Exception as exc:
    raise ImportError(
        "Could not import SenseFi UT_HAR_dataset or UT_HAR_LeNet.\n"
        "Make sure the SenseFi repository exists under third_party/"
        "WiFi-CSI-Sensing-Benchmark and that the previous smoke test still works."
    ) from exc


CLASS_NAMES = {
    0: "lie down",
    1: "fall",
    2: "walk",
    3: "pickup",
    4: "run",
    5: "sit down",
    6: "stand up",
}

FALL_LABEL = 1


def to_fall_binary(label: int) -> int:
    return 1 if int(label) == FALL_LABEL else 0


def safe_divide(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator


def get_array(data_dict, expected_key: str):
    if expected_key in data_dict:
        return data_dict[expected_key]

    for key, value in data_dict.items():
        normalized_key = str(key).replace("\\", "/").split("/")[-1]
        if normalized_key == expected_key:
            return value

    available_keys = ", ".join(str(k) for k in data_dict.keys())
    raise KeyError(
        f"Could not find key '{expected_key}' in UT-HAR data dictionary.\n"
        f"Available keys: {available_keys}"
    )


def add_channel_dimension(tensor: torch.Tensor) -> torch.Tensor:
    if tensor.ndim == 3:
        return tensor.unsqueeze(1)

    return tensor


def build_dataloaders(data_dict):
    X_train = add_channel_dimension(
        torch.as_tensor(get_array(data_dict, "X_train")).float()
    )
    y_train = torch.as_tensor(get_array(data_dict, "y_train")).long()

    X_val = add_channel_dimension(
        torch.as_tensor(get_array(data_dict, "X_val")).float()
    )
    y_val = torch.as_tensor(get_array(data_dict, "y_val")).long()

    X_test = add_channel_dimension(
        torch.as_tensor(get_array(data_dict, "X_test")).float()
    )
    y_test = torch.as_tensor(get_array(data_dict, "y_test")).long()

    X_eval = torch.cat([X_val, X_test], dim=0)
    y_eval = torch.cat([y_val, y_test], dim=0)

    train_loader = DataLoader(
        TensorDataset(X_train, y_train),
        batch_size=64,
        shuffle=True,
        drop_last=True,
    )

    test_loader = DataLoader(
        TensorDataset(X_eval, y_eval),
        batch_size=256,
        shuffle=False,
    )

    print(f"Training windows:   {len(X_train)}")
    print(f"Validation windows: {len(X_val)}")
    print(f"Test windows:       {len(X_test)}")
    print(f"Evaluation windows: {len(X_eval)}")
    print()

    return train_loader, test_loader


def pgd_attack(
    model: torch.nn.Module,
    inputs: torch.Tensor,
    labels: torch.Tensor,
    epsilon: float,
    alpha: float,
    steps: int,
) -> torch.Tensor:
    """
    Untargeted PGD attack under an L-infinity perturbation limit.

    Because UT-HAR tensors are processed CSI features rather than raw image pixels,
    this implementation does not clamp values to [0, 1].
    """

    if epsilon == 0.0:
        return inputs.detach()

    original_inputs = inputs.detach()
    adv_inputs = original_inputs.clone().detach()

    for _ in range(steps):
        adv_inputs.requires_grad = True

        outputs = model(adv_inputs)
        loss = nn.CrossEntropyLoss()(outputs, labels)

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


def train_one_epoch(model, train_loader, criterion, optimizer, device):
    model.train()

    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    for inputs, labels in train_loader:
        inputs = inputs.to(device).float()
        labels = labels.to(device).long()

        optimizer.zero_grad()

        outputs = model(inputs)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        predictions = outputs.argmax(dim=1)

        total_loss += loss.item() * labels.size(0)
        total_correct += (predictions == labels).sum().item()
        total_samples += labels.size(0)

    average_loss = total_loss / total_samples
    accuracy = total_correct / total_samples

    return average_loss, accuracy


def evaluate_clean(model, test_loader, criterion, device):
    model.eval()

    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device).float()
            labels = labels.to(device).long()

            outputs = model(inputs)
            loss = criterion(outputs, labels)

            predictions = outputs.argmax(dim=1)

            total_loss += loss.item() * labels.size(0)
            total_correct += (predictions == labels).sum().item()
            total_samples += labels.size(0)

    average_loss = total_loss / total_samples
    accuracy = total_correct / total_samples

    return average_loss, accuracy


def collect_predictions(model, test_loader, device, epsilon, alpha, pgd_steps):
    model.eval()

    true_labels = []
    clean_predictions = []
    attacked_predictions = []

    for inputs, labels in test_loader:
        inputs = inputs.to(device).float()
        labels = labels.to(device).long()

        with torch.no_grad():
            clean_outputs = model(inputs)
            clean_preds = clean_outputs.argmax(dim=1)

        adv_inputs = pgd_attack(
            model=model,
            inputs=inputs,
            labels=labels,
            epsilon=epsilon,
            alpha=alpha,
            steps=pgd_steps,
        )

        with torch.no_grad():
            attacked_outputs = model(adv_inputs)
            attacked_preds = attacked_outputs.argmax(dim=1)

        true_labels.extend(labels.cpu().numpy().tolist())
        clean_predictions.extend(clean_preds.cpu().numpy().tolist())
        attacked_predictions.extend(attacked_preds.cpu().numpy().tolist())

    return true_labels, clean_predictions, attacked_predictions


def compute_metrics(true_labels, clean_predictions, attacked_predictions):
    total_windows = len(true_labels)

    true_binary = [to_fall_binary(label) for label in true_labels]
    attacked_binary = [to_fall_binary(label) for label in attacked_predictions]

    tp = sum(
        1
        for y_true, y_pred in zip(true_binary, attacked_binary)
        if y_true == 1 and y_pred == 1
    )
    fn = sum(
        1
        for y_true, y_pred in zip(true_binary, attacked_binary)
        if y_true == 1 and y_pred == 0
    )
    fp = sum(
        1
        for y_true, y_pred in zip(true_binary, attacked_binary)
        if y_true == 0 and y_pred == 1
    )
    tn = sum(
        1
        for y_true, y_pred in zip(true_binary, attacked_binary)
        if y_true == 0 and y_pred == 0
    )

    fall_windows = tp + fn
    nonfall_windows = fp + tn

    seven_class_accuracy = safe_divide(
        sum(
            1
            for y_true, y_pred in zip(true_labels, attacked_predictions)
            if y_true == y_pred
        ),
        total_windows,
    )

    binary_accuracy = safe_divide(tp + tn, total_windows)

    recall = safe_divide(tp, tp + fn)
    missed_fall_rate = safe_divide(fn, tp + fn)

    specificity = safe_divide(tn, tn + fp)
    false_positive_rate = safe_divide(fp, fp + tn)

    precision = safe_divide(tp, tp + fp)
    f1_score = safe_divide(2 * precision * recall, precision + recall)

    balanced_accuracy = (recall + specificity) / 2

    prediction_change_rate = safe_divide(
        sum(
            1
            for clean_pred, attacked_pred in zip(clean_predictions, attacked_predictions)
            if clean_pred != attacked_pred
        ),
        total_windows,
    )

    return {
        "total_windows": total_windows,
        "fall_windows": fall_windows,
        "nonfall_windows": nonfall_windows,
        "tp_detected_falls": tp,
        "fn_missed_falls": fn,
        "fp_false_fall_alarms": fp,
        "tn_correct_nonfalls": tn,
        "seven_class_accuracy": round(seven_class_accuracy, 6),
        "binary_accuracy": round(binary_accuracy, 6),
        "recall_sensitivity": round(recall, 6),
        "missed_fall_rate": round(missed_fall_rate, 6),
        "specificity": round(specificity, 6),
        "false_positive_rate": round(false_positive_rate, 6),
        "precision": round(precision, 6),
        "f1_score": round(f1_score, 6),
        "balanced_accuracy": round(balanced_accuracy, 6),
        "prediction_change_rate": round(prediction_change_rate, 6),
    }


def main():
    device = torch.device("cpu")

    epochs = 5
    pgd_steps = 10

    epsilon_values = [
        0.000,
        0.005,
        0.010,
        0.020,
        0.030,
    ]

    output_path = RESULTS_DIR / "pgd_epsilon_sweep_summary.csv"

    print("WiFi CSI Fall Attack-Safety Demo")
    print("PGD epsilon sweep")
    print("-----------------")
    print(f"Experiment directory: {EXPERIMENT_DIR}")
    print(f"SenseFi directory:    {SENSEFI_DIR}")
    print(f"Device:               {device}")
    print(f"Epochs:               {epochs}")
    print(f"PGD steps:            {pgd_steps}")
    print(f"Epsilon values:       {epsilon_values}")
    print()

    original_cwd = Path.cwd()
    os.chdir(SENSEFI_DIR)

    try:
        data = UT_HAR_dataset("./Data/")
    finally:
        os.chdir(original_cwd)

    train_loader, test_loader = build_dataloaders(data)

    model = UT_HAR_LeNet().to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    print("Training clean baseline model before PGD epsilon sweep...")

    for epoch in range(1, epochs + 1):
        train_loss, train_accuracy = train_one_epoch(
            model=model,
            train_loader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
        )

        test_loss, test_accuracy = evaluate_clean(
            model=model,
            test_loader=test_loader,
            criterion=criterion,
            device=device,
        )

        print(
            f"Epoch {epoch:02d}/{epochs} | "
            f"train_acc={train_accuracy:.4f} | "
            f"train_loss={train_loss:.4f} | "
            f"test_acc={test_accuracy:.4f} | "
            f"test_loss={test_loss:.4f}"
        )

    print()
    print("Running PGD epsilon sweep...")

    rows = []

    for epsilon in epsilon_values:
        if epsilon == 0.0:
            alpha = 0.0
        else:
            alpha = epsilon / 6.0

        true_labels, clean_predictions, attacked_predictions = collect_predictions(
            model=model,
            test_loader=test_loader,
            device=device,
            epsilon=epsilon,
            alpha=alpha,
            pgd_steps=pgd_steps,
        )

        metrics = compute_metrics(
            true_labels=true_labels,
            clean_predictions=clean_predictions,
            attacked_predictions=attacked_predictions,
        )

        row = {
            "attack_type": "PGD",
            "epsilon": round(epsilon, 6),
            "alpha": round(alpha, 6),
            "pgd_steps": pgd_steps,
            **metrics,
        }

        rows.append(row)

        print(
            f"epsilon={epsilon:.3f} | "
            f"alpha={alpha:.6f} | "
            f"seven_class_acc={row['seven_class_accuracy']:.6f} | "
            f"missed_fall_rate={row['missed_fall_rate']:.6f} | "
            f"false_alarms={row['fp_false_fall_alarms']} | "
            f"recall={row['recall_sensitivity']:.6f} | "
            f"f1={row['f1_score']:.6f} | "
            f"prediction_change_rate={row['prediction_change_rate']:.6f}"
        )

    fieldnames = list(rows[0].keys())

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print()
    print("PGD epsilon sweep completed.")
    print(f"Output file: {output_path}")


if __name__ == "__main__":
    main()