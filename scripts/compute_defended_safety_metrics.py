"""
Compute defended clean, defended FGSM-attacked, and defended PGD-attacked
fall-vs-non-fall safety-proxy metrics.

Purpose:
    This script reads defended prediction outputs and computes window-level
    fall-vs-non-fall safety-proxy metrics for:

        defended clean model outputs
        defended FGSM-attacked model outputs at epsilon 0.03
        defended PGD-attacked model outputs at epsilon 0.03

Important:
    This is a window-level software evaluation on processed CSI tensors.
    It is not clinical validation.
    It is not medical-device validation.
    It is not physical-layer, packet-level, preamble-level, SDR, or
    over-the-air defense validation.

Expected run location:
    experiments/fall_detection_attack_safety_demo/

Command:
    python scripts/compute_defended_safety_metrics.py
"""

from pathlib import Path
import csv


INPUT_FILE = "defended_predictions_short.csv"
OUTPUT_FILE = "defended_safety_proxy_metrics.csv"


def safe_divide(numerator, denominator):
    """
    Divide safely and return 0.0 when denominator is zero.
    """
    if denominator == 0:
        return 0.0
    return numerator / denominator


def compute_binary_metrics(rows, prediction_column, seven_class_correct_column, clean_reference_column=None):
    """
    Compute binary fall-vs-non-fall safety-proxy metrics.

    Positive class:
        fall = 1

    Negative class:
        non-fall = 0
    """
    total_windows = len(rows)

    tp = 0
    fn = 0
    fp = 0
    tn = 0

    seven_class_correct = 0
    prediction_changes = 0

    for row in rows:
        true_binary = int(row["fall_true_binary"])
        pred_binary = int(row[prediction_column])

        if true_binary == 1 and pred_binary == 1:
            tp += 1
        elif true_binary == 1 and pred_binary == 0:
            fn += 1
        elif true_binary == 0 and pred_binary == 1:
            fp += 1
        elif true_binary == 0 and pred_binary == 0:
            tn += 1

        seven_class_correct += int(row[seven_class_correct_column])

        if clean_reference_column is not None:
            if int(row[prediction_column]) != int(row[clean_reference_column]):
                prediction_changes += 1

    fall_windows = tp + fn
    non_fall_windows = fp + tn

    binary_accuracy = safe_divide(tp + tn, total_windows)
    recall = safe_divide(tp, tp + fn)
    missed_fall_rate = safe_divide(fn, tp + fn)
    specificity = safe_divide(tn, tn + fp)
    false_positive_rate = safe_divide(fp, fp + tn)
    precision = safe_divide(tp, tp + fp)

    if precision + recall == 0:
        f1_score = 0.0
    else:
        f1_score = 2 * precision * recall / (precision + recall)

    balanced_accuracy = (recall + specificity) / 2
    seven_class_accuracy = safe_divide(seven_class_correct, total_windows)

    if clean_reference_column is None:
        prediction_change_rate = 0.0
    else:
        prediction_change_rate = safe_divide(prediction_changes, total_windows)

    return {
        "total_windows": total_windows,
        "fall_windows": fall_windows,
        "non_fall_windows": non_fall_windows,
        "TP_detected_falls": tp,
        "FN_missed_falls": fn,
        "FP_false_fall_alarms": fp,
        "TN_correct_non_falls": tn,
        "seven_class_accuracy": seven_class_accuracy,
        "binary_accuracy": binary_accuracy,
        "recall_sensitivity": recall,
        "missed_fall_rate": missed_fall_rate,
        "specificity": specificity,
        "false_positive_rate": false_positive_rate,
        "precision": precision,
        "f1_score": f1_score,
        "balanced_accuracy": balanced_accuracy,
        "prediction_change_rate": prediction_change_rate,
    }


def format_metric_row(condition_name, attack_type, epsilon, metrics):
    """
    Format one output row for CSV.
    """
    row = {
        "condition": condition_name,
        "model_type": "FGSM_adversarial_training_defended",
        "attack_type": attack_type,
        "epsilon": epsilon,
    }

    for key, value in metrics.items():
        if isinstance(value, float):
            row[key] = f"{value:.6f}"
        else:
            row[key] = value

    return row


def main():
    experiment_dir = Path(__file__).resolve().parents[1]
    results_dir = experiment_dir / "results"

    input_path = results_dir / INPUT_FILE
    output_path = results_dir / OUTPUT_FILE

    if not input_path.exists():
        raise FileNotFoundError(f"Missing input file: {input_path}")

    with input_path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    if not rows:
        raise ValueError(f"No rows found in: {input_path}")

    print("Computing defended fall-vs-non-fall safety-proxy metrics")
    print("-" * 80)
    print(f"Input file: {input_path}")
    print(f"Rows loaded: {len(rows)}")
    print("-" * 80)

    defended_clean_metrics = compute_binary_metrics(
        rows=rows,
        prediction_column="fall_pred_binary_clean_defended",
        seven_class_correct_column="correct_clean_defended",
        clean_reference_column=None,
    )

    defended_fgsm_metrics = compute_binary_metrics(
        rows=rows,
        prediction_column="fall_pred_binary_fgsm_defended",
        seven_class_correct_column="correct_fgsm_defended",
        clean_reference_column="fall_pred_binary_clean_defended",
    )

    defended_pgd_metrics = compute_binary_metrics(
        rows=rows,
        prediction_column="fall_pred_binary_pgd_defended",
        seven_class_correct_column="correct_pgd_defended",
        clean_reference_column="fall_pred_binary_clean_defended",
    )

    output_rows = [
        format_metric_row(
            condition_name="defended_clean",
            attack_type="none",
            epsilon="0.000000",
            metrics=defended_clean_metrics,
        ),
        format_metric_row(
            condition_name="defended_fgsm_epsilon_0_03",
            attack_type="FGSM",
            epsilon="0.030000",
            metrics=defended_fgsm_metrics,
        ),
        format_metric_row(
            condition_name="defended_pgd_epsilon_0_03",
            attack_type="PGD",
            epsilon="0.030000",
            metrics=defended_pgd_metrics,
        ),
    ]

    fieldnames = list(output_rows[0].keys())

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    for row in output_rows:
        print(f"Condition: {row['condition']}")
        print(f"  TP detected falls: {row['TP_detected_falls']}")
        print(f"  FN missed falls: {row['FN_missed_falls']}")
        print(f"  FP false fall alarms: {row['FP_false_fall_alarms']}")
        print(f"  TN correct non-falls: {row['TN_correct_non_falls']}")
        print(f"  Seven-class accuracy: {row['seven_class_accuracy']}")
        print(f"  Recall / sensitivity: {row['recall_sensitivity']}")
        print(f"  Missed fall rate: {row['missed_fall_rate']}")
        print(f"  Precision: {row['precision']}")
        print(f"  F1-score: {row['f1_score']}")
        print(f"  Balanced accuracy: {row['balanced_accuracy']}")
        print(f"  Prediction change rate: {row['prediction_change_rate']}")
        print("-" * 80)

    print("Defended safety-proxy metrics completed successfully.")
    print(f"Metrics saved to: {output_path}")
    print(f"Rows saved: {len(output_rows)}")


if __name__ == "__main__":
    main()