"""
Run a shortened FGSM epsilon sweep for SenseFi UT-HAR LeNet.

Purpose:
    This script trains LeNet on UT_HAR_data for a small number of epochs,
    then evaluates how different software-level FGSM perturbation strengths
    change seven-class accuracy and binary fall-vs-non-fall safety-proxy metrics.

Important:
    This is a processed-tensor FGSM attack for research evaluation.
    It is not a physical-layer, packet-level, preamble-level, SDR, or
    over-the-air attack.
    It is not clinical validation or medical-device validation.

Expected run location:
    experiments/fall_detection_attack_safety_demo/

Expected output:
    results/fgsm_epsilon_sweep_summary.csv

Command:
    python scripts/run_fgsm_epsilon_sweep_short.py
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

EPSILONS = [0.0, 0.005, 0.010, 0.020, 0.030]

FALL_LABEL = 1


def set_reproducibility(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def patch_sensefi_dataset_loader(benchmark_dir: Path) -> None:
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


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def empty_metric_tracker() -> dict:
    return {
        "total_windows": 0,
        "seven_class_correct": 0,
        "prediction_changed_count": 0,
        "tp": 0,
        "fp": 0,
        "fn": 0,
        "tn": 0,
    }


def update_binary_counts(tracker: dict, true_binary: int, pred_binary: int) -> None:
    if true_binary == 1 and pred_binary == 1:
        tracker["tp"] += 1
    elif true_binary == 0 and pred_binary == 1:
        tracker["fp"] += 1
    elif true_binary == 1 and pred_binary == 0:
        tracker["fn"] += 1
    elif true_binary == 0 and pred_binary == 0:
        tracker["tn"] += 1
    else:
        raise ValueError(f"Invalid binary labels: true={true_binary}, pred={pred_binary}")


def finalize_metrics(epsilon: float, tracker: dict) -> dict:
    tp = tracker["tp"]
    fp = tracker["fp"]
    fn = tracker["fn"]
    tn = tracker["tn"]

    total_windows = tp + fp + fn + tn
    fall_windows = tp + fn
    nonfall_windows = tn + fp

    seven_class_accuracy = safe_divide(tracker["seven_class_correct"], total_windows)
    prediction_change_rate = safe_divide(tracker["prediction_changed_count"], total_windows)

    binary_accuracy = safe_divide(tp + tn, total_windows)
    recall_sensitivity = safe_divide(tp, tp + fn)
    missed_fall_rate = safe_divide(fn, tp + fn)
    specificity = safe_divide(tn, tn + fp)
    false_positive_rate = safe_divide(fp, fp + tn)
    precision = safe_divide(tp, tp + fp)
    f1_score = safe_divide(
        2 * precision * recall_sensitivity,
        precision + recall_sensitivity,
    )
    balanced_accuracy = (recall_sensitivity + specificity) / 2

    return {
        "epsilon": f"{epsilon:.6f}",
        "total_windows": total_windows,
        "fall_windows": fall_windows,
        "nonfall_windows": nonfall_windows,
        "seven_class_accuracy": f"{seven_class_accuracy:.6f}",
        "true_positive_fall_detected": tp,
        "false_positive_false_fall_alarm": fp,
        "false_negative_missed_fall": fn,
        "true_negative_nonfall_correct": tn,
        "binary_accuracy": f"{binary_accuracy:.6f}",
        "recall_sensitivity": f"{recall_sensitivity:.6f}",
        "missed_fall_rate": f"{missed_fall_rate:.6f}",
        "specificity": f"{specificity:.6f}",
        "false_positive_rate": f"{false_positive_rate:.6f}",
        "precision": f"{precision:.6f}",
        "f1_score": f"{f1_score:.6f}",
        "balanced_accuracy": f"{balanced_accuracy:.6f}",
        "false_alarm_count": fp,
        "missed_fall_count": fn,
        "prediction_changed_count": tracker["prediction_changed_count"],
        "prediction_change_rate": f"{prediction_change_rate:.6f}",
    }


def run_epsilon_sweep(model, tensor_loader, criterion, device):
    model.eval()

    trackers = {epsilon: empty_metric_tracker() for epsilon in EPSILONS}

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

        with torch.no_grad():
            clean_predictions = torch.argmax(clean_outputs.detach(), dim=1)

            for epsilon in EPSILONS:
                attacked_inputs = attack_inputs + epsilon * input_gradient.sign()
                attacked_outputs = model(attacked_inputs.detach()).float()
                attacked_predictions = torch.argmax(attacked_outputs, dim=1)

                tracker = trackers[epsilon]

                for i in range(labels.size(0)):
                    true_label = int(labels[i].item())
                    clean_predicted_label = int(clean_predictions[i].item())
                    attacked_predicted_label = int(attacked_predictions[i].item())

                    true_binary = label_to_binary_fall(true_label)
                    attacked_binary = label_to_binary_fall(attacked_predicted_label)

                    tracker["total_windows"] += 1

                    if attacked_predicted_label == true_label:
                        tracker["seven_class_correct"] += 1

                    if attacked_predicted_label != clean_predicted_label:
                        tracker["prediction_changed_count"] += 1

                    update_binary_counts(
                        tracker=tracker,
                        true_binary=true_binary,
                        pred_binary=attacked_binary,
                    )

    summary_rows = [finalize_metrics(epsilon, trackers[epsilon]) for epsilon in EPSILONS]

    return summary_rows


def main() -> None:
    start_time = time.time()

    set_reproducibility(SEED)

    experiment_dir = Path(__file__).resolve().parents[1]
    results_dir = experiment_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_path = results_dir / "fgsm_epsilon_sweep_summary.csv"

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

    print("SenseFi UT-HAR LeNet FGSM epsilon sweep")
    print("-" * 80)
    print(f"Experiment directory: {experiment_dir}")
    print(f"Benchmark directory: {benchmark_dir}")
    print(f"Device: {device}")
    print(f"Original SenseFi train epochs: {original_train_epoch}")
    print(f"Short clean baseline epochs: {SHORT_EPOCHS}")
    print(f"FGSM epsilons: {EPSILONS}")
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

    summary_rows = run_epsilon_sweep(
        model=model,
        tensor_loader=test_loader,
        criterion=criterion,
        device=device,
    )

    fieldnames = [
        "epsilon",
        "total_windows",
        "fall_windows",
        "nonfall_windows",
        "seven_class_accuracy",
        "true_positive_fall_detected",
        "false_positive_false_fall_alarm",
        "false_negative_missed_fall",
        "true_negative_nonfall_correct",
        "binary_accuracy",
        "recall_sensitivity",
        "missed_fall_rate",
        "specificity",
        "false_positive_rate",
        "precision",
        "f1_score",
        "balanced_accuracy",
        "false_alarm_count",
        "missed_fall_count",
        "prediction_changed_count",
        "prediction_change_rate",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print("-" * 80)
    print("FGSM epsilon sweep completed successfully.")
    print(f"Summary saved to: {output_path}")
    print("-" * 80)

    for row in summary_rows:
        print(
            f"epsilon={row['epsilon']} | "
            f"seven_class_acc={row['seven_class_accuracy']} | "
            f"missed_fall_rate={row['missed_fall_rate']} | "
            f"false_alarms={row['false_alarm_count']} | "
            f"recall={row['recall_sensitivity']} | "
            f"f1={row['f1_score']} | "
            f"prediction_change_rate={row['prediction_change_rate']}"
        )

    elapsed_time = time.time() - start_time
    print("-" * 80)
    print(f"Elapsed time: {elapsed_time:.1f} seconds")


if __name__ == "__main__":
    main()