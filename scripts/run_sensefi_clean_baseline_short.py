"""
Run a shortened clean SenseFi UT-HAR LeNet baseline.

Purpose:
    Train LeNet on UT_HAR_data for a small number of epochs to produce an
    initial clean baseline result before adding prediction export and
    fall-vs-non-fall safety-proxy metrics.

Important:
    This is still not the final thesis experiment.
    It is a shortened clean baseline run for local reproducibility testing.

Expected run location:
    experiments/fall_detection_attack_safety_demo/

Command:
    python scripts/run_sensefi_clean_baseline_short.py
"""

from pathlib import Path
import os
import random
import sys
import time

import numpy as np


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

    print("SenseFi UT-HAR LeNet shortened clean baseline")
    print("-" * 70)
    print(f"Experiment directory: {experiment_dir}")
    print(f"Benchmark directory: {benchmark_dir}")
    print(f"Device: {device}")
    print(f"Original SenseFi train epochs: {original_train_epoch}")
    print(f"Short clean baseline epochs: {short_epochs}")
    print("-" * 70)

    metrics_path = results_dir / "clean_baseline_short_metrics.csv"

    with metrics_path.open("w", encoding="utf-8") as f:
        f.write("epoch,train_loss,train_accuracy,test_loss,test_accuracy\n")

    start_time = time.time()

    for epoch in range(1, short_epochs + 1):
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

        print(
            f"Epoch {epoch:02d}/{short_epochs} | "
            f"train_acc={train_acc:.4f}, train_loss={train_loss:.4f} | "
            f"test_acc={test_acc:.4f}, test_loss={test_loss:.4f}"
        )

        with metrics_path.open("a", encoding="utf-8") as f:
            f.write(f"{epoch},{train_loss:.6f},{train_acc:.6f},{test_loss:.6f},{test_acc:.6f}\n")

    elapsed = time.time() - start_time

    print("-" * 70)
    print("Shortened clean baseline completed successfully.")
    print(f"Metrics saved to: {metrics_path}")
    print(f"Elapsed time: {elapsed:.1f} seconds")


if __name__ == "__main__":
    main()