"""
Export defended clean, defended FGSM-attacked, and defended PGD-attacked
predictions for the WiFi CSI Fall Attack-Safety Demo.

Purpose:
    This script trains the shortened FGSM adversarial-training defended model,
    then exports prediction-level outputs for:

        defended clean inputs
        defended FGSM-attacked inputs at epsilon 0.03
        defended PGD-attacked inputs at epsilon 0.03

Important:
    This is a software-level processed-tensor defense evaluation.
    It is not clinical validation.
    It is not medical-device validation.
    It is not a physical-layer, packet-level, preamble-level, SDR, or
    over-the-air defense validation.

Expected run location:
    experiments/fall_detection_attack_safety_demo/

Command:
    python scripts/export_defended_predictions_short.py
"""

from pathlib import Path
import csv
import time

import torch
import torch.nn as nn

from export_fgsm_predictions_short import (
    prepare_sensefi_imports,
    patch_sensefi_dataset_loader,
    set_reproducibility,
)

from train_fgsm_adversarial_defense_short import (
    SEED,
    SHORT_EPOCHS,
    LEARNING_RATE,
    FGSM_TRAIN_EPSILON,
    CLEAN_LOSS_WEIGHT,
    ADVERSARIAL_LOSS_WEIGHT,
    load_sensefi_ut_har_lenet,
    train_one_adversarial_epoch,
)


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

FGSM_EVAL_EPSILON = 0.03
PGD_EVAL_EPSILON = 0.03
PGD_STEPS = 10
PGD_ALPHA = 0.005


def to_binary_fall(label: int) -> int:
    """
    Convert UT-HAR seven-class labels into binary fall-vs-non-fall labels.
    """
    return 1 if int(label) == FALL_LABEL else 0


def make_fgsm_eval_batch(model, inputs, labels, criterion, epsilon):
    """
    Create FGSM-attacked inputs for evaluation.

    This is a processed-tensor perturbation, not a physical-layer,
    packet-level, preamble-level, SDR, or over-the-air perturbation.
    """
    attack_inputs = inputs.clone().detach()
    attack_inputs.requires_grad = True

    outputs = model(attack_inputs).float()
    loss = criterion(outputs, labels)

    model.zero_grad()
    loss.backward()

    gradient = attack_inputs.grad.detach()
    attacked_inputs = attack_inputs + epsilon * gradient.sign()

    return attacked_inputs.detach()


def make_pgd_eval_batch(model, inputs, labels, criterion, epsilon, alpha, steps):
    """
    Create PGD-attacked inputs for evaluation.

    This is an iterative processed-tensor perturbation.
    It is not a physical-layer or over-the-air attack.
    """
    original_inputs = inputs.clone().detach()
    attacked_inputs = original_inputs.clone().detach()

    for _ in range(steps):
        attacked_inputs.requires_grad = True

        outputs = model(attacked_inputs).float()
        loss = criterion(outputs, labels)

        model.zero_grad()
        loss.backward()

        gradient = attacked_inputs.grad.detach()
        updated_inputs = attacked_inputs + alpha * gradient.sign()

        perturbation = torch.clamp(
            updated_inputs - original_inputs,
            min=-epsilon,
            max=epsilon,
        )

        attacked_inputs = (original_inputs + perturbation).detach()

    return attacked_inputs


def predict_batch(model, inputs):
    """
    Return predicted labels and confidence scores for one batch.
    """
    with torch.no_grad():
        outputs = model(inputs).float()
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, dim=1)

    return predicted, confidence


def train_defended_model(model, train_loader, criterion, optimizer, device):
    """
    Train the FGSM adversarial-training defended model.
    """
    print("Training defended model")
    print("-" * 80)

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

        print(
            f"Epoch {epoch:02d}/{SHORT_EPOCHS} | "
            f"train_clean_acc={train_metrics['train_clean_accuracy']:.4f}, "
            f"train_adv_acc={train_metrics['train_adversarial_accuracy']:.4f}, "
            f"train_total_loss={train_metrics['train_total_loss']:.4f}"
        )

    print("-" * 80)


def export_predictions(model, test_loader, criterion, device):
    """
    Export defended clean, FGSM-attacked, and PGD-attacked predictions.
    """
    model.eval()

    rows = []
    fgsm_rows = []
    pgd_rows = []

    sample_id = 0

    for inputs, labels in test_loader:
        inputs = inputs.to(device).float()
        labels = labels.to(device).long()

        clean_predicted, clean_confidence = predict_batch(model, inputs)

        fgsm_inputs = make_fgsm_eval_batch(
            model=model,
            inputs=inputs,
            labels=labels,
            criterion=criterion,
            epsilon=FGSM_EVAL_EPSILON,
        )
        fgsm_predicted, fgsm_confidence = predict_batch(model, fgsm_inputs)

        pgd_inputs = make_pgd_eval_batch(
            model=model,
            inputs=inputs,
            labels=labels,
            criterion=criterion,
            epsilon=PGD_EVAL_EPSILON,
            alpha=PGD_ALPHA,
            steps=PGD_STEPS,
        )
        pgd_predicted, pgd_confidence = predict_batch(model, pgd_inputs)

        labels_cpu = labels.detach().cpu()
        clean_predicted_cpu = clean_predicted.detach().cpu()
        fgsm_predicted_cpu = fgsm_predicted.detach().cpu()
        pgd_predicted_cpu = pgd_predicted.detach().cpu()

        clean_confidence_cpu = clean_confidence.detach().cpu()
        fgsm_confidence_cpu = fgsm_confidence.detach().cpu()
        pgd_confidence_cpu = pgd_confidence.detach().cpu()

        for i in range(labels_cpu.size(0)):
            true_label = int(labels_cpu[i].item())

            clean_label = int(clean_predicted_cpu[i].item())
            fgsm_label = int(fgsm_predicted_cpu[i].item())
            pgd_label = int(pgd_predicted_cpu[i].item())

            fall_true_binary = to_binary_fall(true_label)
            fall_clean_binary = to_binary_fall(clean_label)
            fall_fgsm_binary = to_binary_fall(fgsm_label)
            fall_pgd_binary = to_binary_fall(pgd_label)

            row = {
                "sample_id": sample_id,
                "true_label": true_label,
                "true_class_name": CLASS_NAMES.get(true_label, "unknown"),
                "defended_clean_predicted_label": clean_label,
                "defended_clean_predicted_class_name": CLASS_NAMES.get(clean_label, "unknown"),
                "defended_fgsm_predicted_label": fgsm_label,
                "defended_fgsm_predicted_class_name": CLASS_NAMES.get(fgsm_label, "unknown"),
                "defended_pgd_predicted_label": pgd_label,
                "defended_pgd_predicted_class_name": CLASS_NAMES.get(pgd_label, "unknown"),
                "fall_true_binary": fall_true_binary,
                "fall_pred_binary_clean_defended": fall_clean_binary,
                "fall_pred_binary_fgsm_defended": fall_fgsm_binary,
                "fall_pred_binary_pgd_defended": fall_pgd_binary,
                "prediction_confidence_clean_defended": f"{float(clean_confidence_cpu[i].item()):.6f}",
                "prediction_confidence_fgsm_defended": f"{float(fgsm_confidence_cpu[i].item()):.6f}",
                "prediction_confidence_pgd_defended": f"{float(pgd_confidence_cpu[i].item()):.6f}",
                "correct_clean_defended": int(clean_label == true_label),
                "correct_fgsm_defended": int(fgsm_label == true_label),
                "correct_pgd_defended": int(pgd_label == true_label),
            }

            fgsm_row = {
                "sample_id": sample_id,
                "true_label": true_label,
                "true_class_name": CLASS_NAMES.get(true_label, "unknown"),
                "defended_fgsm_predicted_label": fgsm_label,
                "defended_fgsm_predicted_class_name": CLASS_NAMES.get(fgsm_label, "unknown"),
                "fall_true_binary": fall_true_binary,
                "fall_pred_binary_fgsm_defended": fall_fgsm_binary,
                "prediction_confidence_fgsm_defended": f"{float(fgsm_confidence_cpu[i].item()):.6f}",
                "correct_fgsm_defended": int(fgsm_label == true_label),
            }

            pgd_row = {
                "sample_id": sample_id,
                "true_label": true_label,
                "true_class_name": CLASS_NAMES.get(true_label, "unknown"),
                "defended_pgd_predicted_label": pgd_label,
                "defended_pgd_predicted_class_name": CLASS_NAMES.get(pgd_label, "unknown"),
                "fall_true_binary": fall_true_binary,
                "fall_pred_binary_pgd_defended": fall_pgd_binary,
                "prediction_confidence_pgd_defended": f"{float(pgd_confidence_cpu[i].item()):.6f}",
                "correct_pgd_defended": int(pgd_label == true_label),
            }

            rows.append(row)
            fgsm_rows.append(fgsm_row)
            pgd_rows.append(pgd_row)

            sample_id += 1

    return rows, fgsm_rows, pgd_rows


def write_csv(path, rows):
    """
    Write a list of dictionary rows to CSV.
    """
    if not rows:
        raise ValueError(f"No rows to write for {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    start_time = time.time()

    set_reproducibility(SEED)

    experiment_dir = Path(__file__).resolve().parents[1]
    results_dir = experiment_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    benchmark_dir = prepare_sensefi_imports(experiment_dir)
    patch_sensefi_dataset_loader(benchmark_dir)

    train_loader, test_loader, model, original_train_epoch = load_sensefi_ut_har_lenet(
        benchmark_dir
    )

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    print("Defended prediction export")
    print("-" * 80)
    print(f"Experiment directory: {experiment_dir}")
    print(f"Benchmark directory: {benchmark_dir}")
    print(f"Device: {device}")
    print(f"Original SenseFi train epochs: {original_train_epoch}")
    print(f"Defense epochs: {SHORT_EPOCHS}")
    print(f"FGSM training epsilon: {FGSM_TRAIN_EPSILON}")
    print(f"FGSM evaluation epsilon: {FGSM_EVAL_EPSILON}")
    print(f"PGD evaluation epsilon: {PGD_EVAL_EPSILON}")
    print(f"PGD alpha: {PGD_ALPHA}")
    print(f"PGD steps: {PGD_STEPS}")
    print("Evaluation split: SenseFi validation+test loader")
    print("-" * 80)

    train_defended_model(
        model=model,
        train_loader=train_loader,
        criterion=criterion,
        optimizer=optimizer,
        device=device,
    )

    combined_rows, fgsm_rows, pgd_rows = export_predictions(
        model=model,
        test_loader=test_loader,
        criterion=criterion,
        device=device,
    )

    combined_output_path = results_dir / "defended_predictions_short.csv"
    fgsm_output_path = results_dir / "defended_fgsm_predictions_short_epsilon_0_03.csv"
    pgd_output_path = results_dir / "defended_pgd_predictions_short_epsilon_0_03.csv"

    write_csv(combined_output_path, combined_rows)
    write_csv(fgsm_output_path, fgsm_rows)
    write_csv(pgd_output_path, pgd_rows)

    elapsed_seconds = time.time() - start_time

    print("-" * 80)
    print("Defended prediction export completed successfully.")
    print(f"Combined predictions saved to: {combined_output_path}")
    print(f"Defended FGSM predictions saved to: {fgsm_output_path}")
    print(f"Defended PGD predictions saved to: {pgd_output_path}")
    print(f"Rows saved: {len(combined_rows)}")
    print(f"Elapsed time: {elapsed_seconds:.1f} seconds")
    print("-" * 80)


if __name__ == "__main__":
    main()