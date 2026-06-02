"""
Train a shortened clean SenseFi UT-HAR LeNet baseline and export predictions.

Purpose:
    This script trains LeNet on UT_HAR_data for a small number of epochs,
    then exports clean model predictions for the SenseFi validation+test loader.

Important:
    This is a window-level machine-learning prediction export.
    It is not clinical validation or medical-device validation.

Expected run location:
    experiments/fall_detection_attack_safety_demo/

Command:
    python scripts/export_clean_predictions_short.py
"""

from pathlib import Path
import csv
import os
import random
import sys
import time

import numpy as np


CLASS_NAMES = {
    0: "lie down",
    1: "fall",
    2: "walk",
    3: "pickup",
    4: "run",
    5: "sit down",
    6: "stand up",
}


def to_fall_binary(label: int) -> int:
    """Map UT-HAR class labels to binary fall/non-fall labels."""
    return 1 if int(label) == 1 else 0


def patch_sensefi_dataset_loader(benchmark_dir: Path) -> None:
    """Apply a local Windows compatibility patch to SenseFi's dataset.py."""
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


def set_seed(seed: int = 42) -> None:
    """Set random seeds for more repeatable local runs."""
    random.seed(seed)
    np.random.seed(seed)

    import torch

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def evaluate(model, loader, criterion, device):
    """Evaluate model and return average loss and accuracy."""
    import torch

    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    with torch.no_grad():
        for inputs, labels in loader:
            inputs = inputs.to(device)
            labels = labels.type(torch.LongTensor).to(device)

            outputs = model(inputs).type(torch.FloatTensor).to(device)
            loss = criterion(outputs, labels)

            preds = torch.argmax(outputs, dim=1)
            total_correct += (preds == labels).sum().item()
            total_loss += loss.item() * inputs.size(0)
            total_samples += inputs.size(0)

    avg_loss = total_loss / total_samples
    accuracy = total_correct / total_samples

    return avg_loss, accuracy


def train_short_baseline(model, train_loader, test_loader, criterion, optimizer, device, epochs: int):
    """Train the clean baseline for a small number of epochs."""
    import torch

    history = []

    for epoch in range(1, epochs + 1):
        model.train()

        total_loss = 0.0
        total_correct = 0
        total_samples = 0

        for inputs, labels in train_loader:
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

        train_loss = total_loss / total_samples
        train_acc = total_correct / total_samples

        test_loss, test_acc = evaluate(model, test_loader, criterion, device)

        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "train_accuracy": train_acc,
                "test_loss": test_loss,
                "test_accuracy": test_acc,
            }
        )

        print(
            f"Epoch {epoch:02d}/{epochs} | "
            f"train_acc={train_acc:.4f}, train_loss={train_loss:.4f} | "
            f"test_acc={test_acc:.4f}, test_loss={test_loss:.4f}"
        )

    return history


def export_predictions(model, loader, device, output_path: Path) -> int:
    """Export clean predictions for all samples in the loader."""
    import torch

    model.eval()
    sample_id = 0

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

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        with torch.no_grad():
            for inputs, labels in loader:
                inputs = inputs.to(device)
                labels = labels.type(torch.LongTensor).to(device)

                outputs = model(inputs).type(torch.FloatTensor).to(device)
                probabilities = torch.softmax(outputs, dim=1)
                confidence, preds = torch.max(probabilities, dim=1)

                labels_cpu = labels.cpu().numpy()
                preds_cpu = preds.cpu().numpy()
                confidence_cpu = confidence.cpu().numpy()

                for true_label, pred_label, pred_conf in zip(labels_cpu, preds_cpu, confidence_cpu):
                    true_label = int(true_label)
                    pred_label = int(pred_label)

                    writer.writerow(
                        {
                            "sample_id": sample_id,
                            "true_label": true_label,
                            "true_class_name": CLASS_NAMES.get(true_label, "unknown"),
                            "predicted_label": pred_label,
                            "predicted_class_name": CLASS_NAMES.get(pred_label, "unknown"),
                            "fall_true_binary": to_fall_binary(true_label),
                            "fall_pred_binary": to_fall_binary(pred_label),
                            "prediction_confidence": f"{float(pred_conf):.6f}",
                            "correct": int(true_label == pred_label),
                        }
                    )

                    sample_id += 1

    return sample_id


def main() -> None:
    experiment_dir = Path(__file__).resolve().parents[1]
    benchmark_dir = experiment_dir / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    data_dir = benchmark_dir / "Data" / "UT_HAR"
    results_dir = experiment_dir / "results"
    results_dir.mkdir(exist_ok=True)

    if not benchmark_dir.exists():
        raise FileNotFoundError(
            "SenseFi benchmark clone not found. Expected folder:\n"
            f"{benchmark_dir}"
        )

    if not data_dir.exists():
        raise FileNotFoundError(
            "UT-HAR data folder not found. Expected folder:\n"
            f"{data_dir}"
        )

    patch_sensefi_dataset_loader(benchmark_dir)

    os.chdir(benchmark_dir)
    sys.path.insert(0, str(benchmark_dir))

    import torch
    import torch.nn as nn
    import torch.optim as optim
    from util import load_data_n_model

    set_seed(42)

    train_loader, test_loader, model, original_train_epoch = load_data_n_model(
        dataset_name="UT_HAR_data",
        model_name="LeNet",
        root="./Data/",
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    short_epochs = 5

    predictions_path = results_dir / "clean_predictions_short.csv"

    print("SenseFi UT-HAR LeNet clean prediction export")
    print("-" * 70)
    print(f"Experiment directory: {experiment_dir}")
    print(f"Benchmark directory: {benchmark_dir}")
    print(f"Device: {device}")
    print(f"Original SenseFi train epochs: {original_train_epoch}")
    print(f"Short clean baseline epochs: {short_epochs}")
    print("Prediction split: SenseFi validation+test loader")
    print("-" * 70)

    start_time = time.time()

    train_short_baseline(
        model=model,
        train_loader=train_loader,
        test_loader=test_loader,
        criterion=criterion,
        optimizer=optimizer,
        device=device,
        epochs=short_epochs,
    )

    exported_count = export_predictions(
        model=model,
        loader=test_loader,
        device=device,
        output_path=predictions_path,
    )

    elapsed = time.time() - start_time

    print("-" * 70)
    print("Clean prediction export completed successfully.")
    print(f"Predictions saved to: {predictions_path}")
    print(f"Rows exported: {exported_count}")
    print(f"Elapsed time: {elapsed:.1f} seconds")


if __name__ == "__main__":
    main()