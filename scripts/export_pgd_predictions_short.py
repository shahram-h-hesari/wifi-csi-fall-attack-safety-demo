"""
Export PGD attacked predictions for the WiFi CSI Fall Attack-Safety Demo.

Experiment:
- Baseline: SenseFi / UT-HAR / LeNet
- Task: Seven-class UT-HAR activity recognition
- Safety translation: binary fall vs non-fall window-level proxy metrics
- Attack: PGD, applied to processed UT-HAR CSI tensors

Important claim boundary:
This script applies a software-level adversarial perturbation to processed CSI tensors.
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


# -----------------------------
# Reproducibility settings
# -----------------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


# -----------------------------
# Experiment paths
# -----------------------------
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


# -----------------------------
# Import SenseFi components
# -----------------------------
try:
    from dataset import UT_HAR_dataset
    from UT_HAR_model import UT_HAR_LeNet
except Exception as exc:
    raise ImportError(
        "Could not import SenseFi UT_HAR_dataset or UT_HAR_LeNet.\n"
        "Make sure the SenseFi repository exists under third_party/"
        "WiFi-CSI-Sensing-Benchmark and that the previous smoke test still works."
    ) from exc


# -----------------------------
# Label mapping
# -----------------------------
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
    """Map UT-HAR multiclass label to binary fall/non-fall."""
    return 1 if int(label) == FALL_LABEL else 0


# -----------------------------
# Dataset helpers
# -----------------------------
def get_array(data_dict, expected_key: str):
    """
    Return an array from the SenseFi UT-HAR dictionary.

    This helper supports both clean keys such as 'X_train' and Windows-style
    keys such as 'data\\X_train' or 'label\\y_train'.
    """

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
    """
    LeNet expects data shaped as:
        batch, channel, height, width

    UT-HAR processed tensors are usually:
        batch, 250, 90

    This function converts them to:
        batch, 1, 250, 90
    """

    if tensor.ndim == 3:
        return tensor.unsqueeze(1)

    return tensor


def build_dataloaders(data_dict):
    """
    Build PyTorch DataLoaders from the SenseFi UT-HAR dictionary.

    Evaluation combines validation and test windows to match the previous
    clean and FGSM workflow:
        496 validation windows + 500 test windows = 996 evaluation windows
    """

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


# -----------------------------
# PGD attack
# -----------------------------
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

    The adversarial tensor is projected after each step so that:
        x_adv stays within [x_original - epsilon, x_original + epsilon]

    Because UT-HAR tensors are processed CSI features rather than raw image pixels,
    this implementation does not clamp values to [0, 1].
    """

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


# -----------------------------
# Training and clean evaluation
# -----------------------------
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


# -----------------------------
# PGD prediction export
# -----------------------------
def export_pgd_predictions(
    model,
    test_loader,
    device,
    epsilon: float,
    alpha: float,
    steps: int,
    output_path: Path,
):
    model.eval()

    rows = []
    sample_id = 0

    for inputs, labels in test_loader:
        inputs = inputs.to(device).float()
        labels = labels.to(device).long()

        adv_inputs = pgd_attack(
            model=model,
            inputs=inputs,
            labels=labels,
            epsilon=epsilon,
            alpha=alpha,
            steps=steps,
        )

        with torch.no_grad():
            outputs = model(adv_inputs)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predictions = probabilities.max(dim=1)

        labels_cpu = labels.cpu().numpy()
        predictions_cpu = predictions.cpu().numpy()
        confidence_cpu = confidence.cpu().numpy()

        for true_label, predicted_label, pred_confidence in zip(
            labels_cpu,
            predictions_cpu,
            confidence_cpu,
        ):
            true_label = int(true_label)
            predicted_label = int(predicted_label)

            fall_true_binary = to_fall_binary(true_label)
            fall_pred_binary = to_fall_binary(predicted_label)

            rows.append(
                {
                    "sample_id": sample_id,
                    "true_label": true_label,
                    "true_class_name": CLASS_NAMES.get(true_label, "unknown"),
                    "predicted_label": predicted_label,
                    "predicted_class_name": CLASS_NAMES.get(predicted_label, "unknown"),
                    "fall_true_binary": fall_true_binary,
                    "fall_pred_binary": fall_pred_binary,
                    "prediction_confidence": round(float(pred_confidence), 6),
                    "correct": int(true_label == predicted_label),
                    "attack_type": "PGD",
                    "epsilon": epsilon,
                    "alpha": alpha,
                    "pgd_steps": steps,
                }
            )

            sample_id += 1

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
        "attack_type",
        "epsilon",
        "alpha",
        "pgd_steps",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main():
    device = torch.device("cpu")

    epochs = 5
    epsilon = 0.030
    alpha = 0.005
    pgd_steps = 10

    output_path = RESULTS_DIR / "pgd_predictions_short_epsilon_0_03.csv"

    print("WiFi CSI Fall Attack-Safety Demo")
    print("PGD attacked prediction export")
    print("--------------------------------")
    print(f"Experiment directory: {EXPERIMENT_DIR}")
    print(f"SenseFi directory:    {SENSEFI_DIR}")
    print(f"Device:               {device}")
    print(f"Epochs:               {epochs}")
    print(f"Attack:               PGD")
    print(f"Epsilon:              {epsilon}")
    print(f"Alpha:                {alpha}")
    print(f"PGD steps:            {pgd_steps}")
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

    print("Training clean baseline model before PGD export...")

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
    print("Exporting PGD attacked predictions...")

    row_count = export_pgd_predictions(
        model=model,
        test_loader=test_loader,
        device=device,
        epsilon=epsilon,
        alpha=alpha,
        steps=pgd_steps,
        output_path=output_path,
    )

    print()
    print("PGD prediction export completed.")
    print(f"Rows exported: {row_count}")
    print(f"Output file:   {output_path}")


if __name__ == "__main__":
    main()