"""
Train a shortened clean SenseFi UT-HAR LeNet baseline and export FGSM attacked predictions.

Purpose:
    This script trains LeNet on UT_HAR_data for a small number of epochs,
    then applies a software-level FGSM adversarial perturbation to the
    processed CSI tensors from the SenseFi validation+test loader.

Important:
    This is a processed-tensor FGSM attack for research evaluation.
    It is not a physical-layer, packet-level, preamble-level, SDR, or
    over-the-air attack.
    It is not clinical validation or medical-device validation.

Expected run location:
    experiments/fall_detection_attack_safety_demo/

Command:
    python scripts/export_fgsm_predictions_short.py
"""

from pathlib import Path
import csv
import os
import random
import sys
import time

import numpy as np
import torch
import torch.nn as nn


SEED = 42
SHORT_EPOCHS = 5
LEARNING_RATE = 1e-3
FGSM_EPSILON = 0.03

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


def set_reproducibility(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def patch_sensefi_dataset_loader(benchmark_dir: Path) -> None:
    """
    Patch the local ignored SenseFi dataset loader for Windows path separators.

    The original SenseFi loader extracts keys using split('/'), which can create
    keys like data\\X_train on Windows. The patch uses Path(...).stem so keys
    become X_train, y_train, etc.
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

    avg_loss = running_loss / running_total
    avg_accuracy = running_correct / running_total

    return avg_loss, avg_accuracy


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

    avg_loss = running_loss / running_total
    avg_accuracy = running_correct / running_total

    return avg_loss, avg_accuracy


def label_to_binary_fall(label: int) -> int:
    return 1 if label == FALL_LABEL else 0


def make_fgsm_predictions(model, tensor_loader, criterion, device, epsilon: float):
    model.eval()

    rows = []
    sample_id = 0

    clean_correct_total = 0
    attacked_correct_total = 0
    prediction_changed_total = 0

    for inputs, labels in tensor_loader:
        inputs = inputs.to(device).float()
        labels = labels.to(device).long()

        # FGSM needs gradient with respect to the input tensor.
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

            clean_predictions = torch.argmax(clean_probs, dim=1)
            attacked_predictions = torch.argmax(attacked_probs, dim=1)

            clean_confidences = torch.max(clean_probs, dim=1).values
            attacked_confidences = torch.max(attacked_probs, dim=1).values

        for i in range(labels.size(0)):
            true_label = int(labels[i].item())
            clean_predicted_label = int(clean_predictions[i].item())
            attacked_predicted_label = int(attacked_predictions[i].item())

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

            clean_correct = int(clean_predicted_label == true_label)
            attacked_correct = int(attacked_predicted_label == true_label)
            prediction_changed = int(clean_predicted_label != attacked_predicted_label)

            clean_correct_total += clean_correct
            attacked_correct_total += attacked_correct
            prediction_changed_total += prediction_changed

            rows.append(
                {
                    "sample_id": sample_id,
                    "epsilon": f"{epsilon:.6f}",
                    "true_label": true_label,
                    "true_class_name": true_class_name,
                    "clean_predicted_label": clean_predicted_label,
                    "clean_predicted_class_name": clean_predicted_class_name,
                    "attacked_predicted_label": attacked_predicted_label,
                    "attacked_predicted_class_name": attacked_predicted_class_name,
                    "fall_true_binary": fall_true_binary,
                    "clean_fall_pred_binary": clean_fall_pred_binary,
                    "attacked_fall_pred_binary": attacked_fall_pred_binary,
                    "clean_prediction_confidence": f"{clean_confidences[i].item():.6f}",
                    "attacked_prediction_confidence": f"{attacked_confidences[i].item():.6f}",
                    "clean_correct": clean_correct,
                    "attacked_correct": attacked_correct,
                    "prediction_changed": prediction_changed,
                }
            )

            sample_id += 1

    total_rows = len(rows)
    clean_accuracy = clean_correct_total / total_rows
    attacked_accuracy = attacked_correct_total / total_rows
    prediction_change_rate = prediction_changed_total / total_rows

    summary = {
        "total_rows": total_rows,
        "clean_accuracy": clean_accuracy,
        "attacked_accuracy": attacked_accuracy,
        "accuracy_drop": clean_accuracy - attacked_accuracy,
        "prediction_changed_count": prediction_changed_total,
        "prediction_change_rate": prediction_change_rate,
    }

    return rows, summary


def main() -> None:
    start_time = time.time()

    set_reproducibility(SEED)

    experiment_dir = Path(__file__).resolve().parents[1]
    results_dir = experiment_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_path = results_dir / "fgsm_predictions_short_epsilon_0_03.csv"

    benchmark_dir = prepare_sensefi_imports(experiment_dir)

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

    print("SenseFi UT-HAR LeNet FGSM attacked prediction export")
    print("-" * 80)
    print(f"Experiment directory: {experiment_dir}")
    print(f"Benchmark directory: {benchmark_dir}")
    print(f"Device: {device}")
    print(f"Original SenseFi train epochs: {original_train_epoch}")
    print(f"Short clean baseline epochs: {SHORT_EPOCHS}")
    print(f"FGSM epsilon: {FGSM_EPSILON}")
    print("Prediction split: SenseFi validation+test loader")
    print("-" * 80)

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

    rows, summary = make_fgsm_predictions(
        model=model,
        tensor_loader=test_loader,
        criterion=criterion,
        device=device,
        epsilon=FGSM_EPSILON,
    )

    fieldnames = [
        "sample_id",
        "epsilon",
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

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    elapsed_time = time.time() - start_time

    print("-" * 80)
    print("FGSM attacked prediction export completed successfully.")
    print(f"Predictions saved to: {output_path}")
    print(f"Rows exported: {summary['total_rows']}")
    print(f"Clean accuracy: {summary['clean_accuracy']:.4f}")
    print(f"Attacked accuracy: {summary['attacked_accuracy']:.4f}")
    print(f"Accuracy drop: {summary['accuracy_drop']:.4f}")
    print(f"Prediction changed count: {summary['prediction_changed_count']}")
    print(f"Prediction change rate: {summary['prediction_change_rate']:.4f}")
    print(f"Elapsed time: {elapsed_time:.1f} seconds")


if __name__ == "__main__":
    main()