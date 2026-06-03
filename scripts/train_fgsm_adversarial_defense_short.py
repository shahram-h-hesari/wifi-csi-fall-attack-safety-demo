"""
Train a shortened FGSM adversarial-training defense baseline for the
WiFi CSI Fall Attack-Safety Demo.

Purpose:
    This script trains LeNet on UT_HAR_data using a simple software-level
    FGSM adversarial training loop. Each batch is trained using both clean
    CSI tensors and FGSM-perturbed CSI tensors.

Important:
    This is a processed-tensor adversarial training baseline for research
    evaluation.
    It is not a physical-layer defense.
    It is not a packet-level, preamble-level, SDR, or over-the-air defense.
    It is not clinical validation or medical-device validation.

Expected run location:
    experiments/fall_detection_attack_safety_demo/

Command:
    python scripts/train_fgsm_adversarial_defense_short.py
"""

from pathlib import Path
import csv
import sys
import time

import torch
import torch.nn as nn

from export_fgsm_predictions_short import (
    prepare_sensefi_imports,
    patch_sensefi_dataset_loader,
    set_reproducibility,
    evaluate_clean,
)


SEED = 42
SHORT_EPOCHS = 5
LEARNING_RATE = 1e-3

FGSM_TRAIN_EPSILON = 0.005
CLEAN_LOSS_WEIGHT = 0.5
ADVERSARIAL_LOSS_WEIGHT = 0.5


def normalize_key(key) -> str:
    """
    Normalize SenseFi UT-HAR keys.

    On Windows, SenseFi can sometimes return keys such as:
        data\\X_train
        label\\y_train

    This function converts them to:
        X_train
        y_train
    """
    key_text = str(key).replace("\\", "/")
    key_text = key_text.split("/")[-1]
    key_text = key_text.split(".")[0]
    return key_text


def load_sensefi_ut_har_lenet(benchmark_dir: Path):
    """
    Load SenseFi UT-HAR LeNet while normalizing UT-HAR dictionary keys.

    This avoids the Windows path-separator issue that causes:
        KeyError: 'X_train'
    """
    if str(benchmark_dir) not in sys.path:
        sys.path.insert(0, str(benchmark_dir))

    from dataset import UT_HAR_dataset as original_ut_har_dataset
    import util

    def normalized_ut_har_dataset(data_root):
        data_root = str(benchmark_dir / "Data") + "/"
        print("UT-HAR loader root:", data_root)
        raw_data = original_ut_har_dataset(data_root)

        normalized_data = {}
        for key, value in raw_data.items():
            normalized_data[normalize_key(key)] = value

        print("Normalized UT-HAR keys:", sorted(normalized_data.keys()))

        return normalized_data

    util.UT_HAR_dataset = normalized_ut_har_dataset

    root_path = str(benchmark_dir) + "/"

    return util.load_data_n_model(
        dataset_name="UT_HAR_data",
        model_name="LeNet",
        root=root_path,
    )


def make_fgsm_training_batch(model, inputs, labels, criterion, epsilon):
    """
    Create FGSM adversarial examples for one training batch.

    This uses a processed-tensor FGSM perturbation:

        attacked_inputs = inputs + epsilon * sign(input_gradient)

    No physical-layer, packet-level, preamble-level, SDR, or over-the-air
    perturbation is created here.
    """
    attack_inputs = inputs.clone().detach()
    attack_inputs.requires_grad = True

    outputs = model(attack_inputs).float()
    loss = criterion(outputs, labels)

    model.zero_grad()
    loss.backward()

    input_gradient = attack_inputs.grad.detach()
    attacked_inputs = attack_inputs + epsilon * input_gradient.sign()
    attacked_inputs = attacked_inputs.detach()

    return attacked_inputs


def train_one_adversarial_epoch(
    model,
    tensor_loader,
    optimizer,
    criterion,
    device,
    epsilon,
    clean_loss_weight,
    adversarial_loss_weight,
):
    """
    Train one epoch using clean loss plus FGSM adversarial loss.
    """
    model.train()

    running_total_loss = 0.0
    running_clean_loss = 0.0
    running_adversarial_loss = 0.0

    running_clean_correct = 0
    running_adversarial_correct = 0
    running_total = 0

    for inputs, labels in tensor_loader:
        inputs = inputs.to(device).float()
        labels = labels.to(device).long()

        adversarial_inputs = make_fgsm_training_batch(
            model=model,
            inputs=inputs,
            labels=labels,
            criterion=criterion,
            epsilon=epsilon,
        )

        optimizer.zero_grad()

        clean_outputs = model(inputs).float()
        adversarial_outputs = model(adversarial_inputs).float()

        clean_loss = criterion(clean_outputs, labels)
        adversarial_loss = criterion(adversarial_outputs, labels)

        total_loss = (
            clean_loss_weight * clean_loss
            + adversarial_loss_weight * adversarial_loss
        )

        total_loss.backward()
        optimizer.step()

        clean_predicted = torch.argmax(clean_outputs, dim=1)
        adversarial_predicted = torch.argmax(adversarial_outputs, dim=1)

        batch_size = labels.size(0)

        running_total_loss += total_loss.item() * batch_size
        running_clean_loss += clean_loss.item() * batch_size
        running_adversarial_loss += adversarial_loss.item() * batch_size

        running_clean_correct += (clean_predicted == labels).sum().item()
        running_adversarial_correct += (adversarial_predicted == labels).sum().item()
        running_total += batch_size

    avg_total_loss = running_total_loss / running_total
    avg_clean_loss = running_clean_loss / running_total
    avg_adversarial_loss = running_adversarial_loss / running_total
    clean_accuracy = running_clean_correct / running_total
    adversarial_accuracy = running_adversarial_correct / running_total

    return {
        "train_total_loss": avg_total_loss,
        "train_clean_loss": avg_clean_loss,
        "train_adversarial_loss": avg_adversarial_loss,
        "train_clean_accuracy": clean_accuracy,
        "train_adversarial_accuracy": adversarial_accuracy,
    }


def main() -> None:
    start_time = time.time()

    set_reproducibility(SEED)

    experiment_dir = Path(__file__).resolve().parents[1]
    results_dir = experiment_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_path = results_dir / "fgsm_adversarial_training_short_metrics.csv"

    benchmark_dir = prepare_sensefi_imports(experiment_dir)

    # Required on Windows:
    # The original SenseFi dataset loader can create keys like data\\X_train
    # instead of X_train. This local ignored patch makes UT_HAR load correctly.
    patch_sensefi_dataset_loader(benchmark_dir)

    train_loader, test_loader, model, original_train_epoch = load_sensefi_ut_har_lenet(
        benchmark_dir
    )

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    print("SenseFi UT-HAR LeNet FGSM adversarial training defense")
    print("-" * 80)
    print(f"Experiment directory: {experiment_dir}")
    print(f"Benchmark directory: {benchmark_dir}")
    print(f"Device: {device}")
    print(f"Original SenseFi train epochs: {original_train_epoch}")
    print(f"Short defense epochs: {SHORT_EPOCHS}")
    print(f"FGSM training epsilon: {FGSM_TRAIN_EPSILON}")
    print(f"Clean loss weight: {CLEAN_LOSS_WEIGHT}")
    print(f"Adversarial loss weight: {ADVERSARIAL_LOSS_WEIGHT}")
    print("Evaluation split: SenseFi validation+test loader")
    print("-" * 80)

    rows = []

    for epoch in range(1, SHORT_EPOCHS + 1):
        train_metrics = train_one_adversarial_epoch(
            model=model,
            tensor_loader=train_loader,
            optimizer=optimizer,
            criterion=criterion,
            device=device,
            epsilon=FGSM_TRAIN_EPSILON,
            clean_loss_weight=CLEAN_LOSS_WEIGHT,
            adversarial_loss_weight=ADVERSARIAL_LOSS_WEIGHT,
        )

        test_loss, test_accuracy = evaluate_clean(
            model=model,
            tensor_loader=test_loader,
            criterion=criterion,
            device=device,
        )

        row = {
            "epoch": epoch,
            "train_total_loss": f"{train_metrics['train_total_loss']:.6f}",
            "train_clean_loss": f"{train_metrics['train_clean_loss']:.6f}",
            "train_adversarial_loss": f"{train_metrics['train_adversarial_loss']:.6f}",
            "train_clean_accuracy": f"{train_metrics['train_clean_accuracy']:.6f}",
            "train_adversarial_accuracy": f"{train_metrics['train_adversarial_accuracy']:.6f}",
            "test_clean_loss": f"{test_loss:.6f}",
            "test_clean_accuracy": f"{test_accuracy:.6f}",
            "fgsm_train_epsilon": f"{FGSM_TRAIN_EPSILON:.6f}",
            "clean_loss_weight": f"{CLEAN_LOSS_WEIGHT:.2f}",
            "adversarial_loss_weight": f"{ADVERSARIAL_LOSS_WEIGHT:.2f}",
        }

        rows.append(row)

        print(
            f"Epoch {epoch:02d}/{SHORT_EPOCHS} | "
            f"train_clean_acc={train_metrics['train_clean_accuracy']:.4f}, "
            f"train_adv_acc={train_metrics['train_adversarial_accuracy']:.4f}, "
            f"train_total_loss={train_metrics['train_total_loss']:.4f} | "
            f"test_clean_acc={test_accuracy:.4f}, "
            f"test_clean_loss={test_loss:.4f}"
        )

    fieldnames = [
        "epoch",
        "train_total_loss",
        "train_clean_loss",
        "train_adversarial_loss",
        "train_clean_accuracy",
        "train_adversarial_accuracy",
        "test_clean_loss",
        "test_clean_accuracy",
        "fgsm_train_epsilon",
        "clean_loss_weight",
        "adversarial_loss_weight",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    elapsed_seconds = time.time() - start_time

    print("-" * 80)
    print("FGSM adversarial training defense completed successfully.")
    print(f"Metrics saved to: {output_path}")
    print(f"Rows saved: {len(rows)}")
    print(f"Elapsed time: {elapsed_seconds:.1f} seconds")
    print("-" * 80)


if __name__ == "__main__":
    main()

