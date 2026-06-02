"""
Run a one-epoch SenseFi UT-HAR LeNet smoke test.

Purpose:
    This script verifies that the local SenseFi benchmark clone, UT-HAR data,
    PyTorch environment, model, training loop, and test loop can run.

Important:
    This is not a final baseline experiment.
    It is only a smoke test for reproducibility and setup validation.

Expected run location:
    experiments/fall_detection_attack_safety_demo/

Command:
    python scripts/run_sensefi_smoke_test.py
"""

from pathlib import Path
import os
import sys


def patch_sensefi_dataset_loader(benchmark_dir: Path) -> None:
    """
    Apply a small local Windows compatibility patch to SenseFi's dataset.py.

    The original SenseFi UT_HAR_dataset loader can return keys like:
        data\\X_train
        label\\y_train

    on Windows, while util.py expects:
        X_train
        y_train

    This patch changes filename parsing to use pathlib.Path(...).stem.
    The third-party SenseFi folder is ignored by Git, so this patch is local only.
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


def main() -> None:
    experiment_dir = Path(__file__).resolve().parents[1]
    benchmark_dir = experiment_dir / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    data_dir = benchmark_dir / "Data" / "UT_HAR"

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
    from util import load_data_n_model
    from run import train, test

    train_loader, test_loader, model, original_train_epoch = load_data_n_model(
        dataset_name="UT_HAR_data",
        model_name="LeNet",
        root="./Data/",
    )

    criterion = nn.CrossEntropyLoss()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    print("SenseFi UT-HAR LeNet clean-baseline smoke test")
    print("-" * 60)
    print(f"Experiment directory: {experiment_dir}")
    print(f"Benchmark directory: {benchmark_dir}")
    print(f"Device: {device}")
    print(f"Original SenseFi train epochs: {original_train_epoch}")
    print("Smoke test epochs: 1")
    print("-" * 60)

    train(
        model=model,
        tensor_loader=train_loader,
        num_epochs=1,
        learning_rate=1e-3,
        criterion=criterion,
        device=device,
    )

    test(
        model=model,
        tensor_loader=test_loader,
        criterion=criterion,
        device=device,
    )

    print("-" * 60)
    print("Smoke test completed successfully.")


if __name__ == "__main__":
    main()