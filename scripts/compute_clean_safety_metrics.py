"""
Compute clean fall-vs-non-fall safety-proxy metrics.

Purpose:
    This script reads clean window-level predictions exported from the
    SenseFi UT-HAR LeNet baseline and converts them into binary
    fall-vs-non-fall safety-proxy metrics.

Important:
    These are window-level research metrics.
    They are not clinical validation, medical-device validation,
    diagnostic evidence, or regulatory evaluation.

Expected input:
    results/clean_predictions_short.csv

Expected output:
    results/clean_safety_proxy_metrics.csv

Command:
    python scripts/compute_clean_safety_metrics.py
"""

from pathlib import Path
import csv


def safe_divide(numerator: float, denominator: float) -> float:
    """Return numerator / denominator, or 0.0 when denominator is zero."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def main() -> None:
    experiment_dir = Path(__file__).resolve().parents[1]
    predictions_path = experiment_dir / "results" / "clean_predictions_short.csv"
    output_path = experiment_dir / "results" / "clean_safety_proxy_metrics.csv"

    if not predictions_path.exists():
        raise FileNotFoundError(
            "Clean prediction CSV not found. Expected file:\n"
            f"{predictions_path}"
        )

    tp = 0
    fp = 0
    fn = 0
    tn = 0
    total_rows = 0

    with predictions_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required_columns = {
            "sample_id",
            "true_label",
            "predicted_label",
            "fall_true_binary",
            "fall_pred_binary",
        }

        missing_columns = required_columns - set(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

        for row in reader:
            true_binary = int(row["fall_true_binary"])
            pred_binary = int(row["fall_pred_binary"])

            if true_binary == 1 and pred_binary == 1:
                tp += 1
            elif true_binary == 0 and pred_binary == 1:
                fp += 1
            elif true_binary == 1 and pred_binary == 0:
                fn += 1
            elif true_binary == 0 and pred_binary == 0:
                tn += 1
            else:
                raise ValueError(
                    f"Invalid binary labels at sample_id={row.get('sample_id')}: "
                    f"true={true_binary}, pred={pred_binary}"
                )

            total_rows += 1

    total_fall_windows = tp + fn
    total_nonfall_windows = tn + fp

    accuracy = safe_divide(tp + tn, total_rows)
    recall_sensitivity = safe_divide(tp, tp + fn)
    missed_fall_rate = safe_divide(fn, tp + fn)
    specificity = safe_divide(tn, tn + fp)
    false_positive_rate = safe_divide(fp, fp + tn)
    precision = safe_divide(tp, tp + fp)
    f1_score = safe_divide(2 * precision * recall_sensitivity, precision + recall_sensitivity)
    balanced_accuracy = (recall_sensitivity + specificity) / 2

    metrics = {
        "total_windows": total_rows,
        "fall_windows": total_fall_windows,
        "nonfall_windows": total_nonfall_windows,
        "true_positive_fall_detected": tp,
        "false_positive_false_fall_alarm": fp,
        "false_negative_missed_fall": fn,
        "true_negative_nonfall_correct": tn,
        "accuracy": accuracy,
        "recall_sensitivity": recall_sensitivity,
        "missed_fall_rate": missed_fall_rate,
        "specificity": specificity,
        "false_positive_rate": false_positive_rate,
        "precision": precision,
        "f1_score": f1_score,
        "balanced_accuracy": balanced_accuracy,
        "false_alarm_count": fp,
        "missed_fall_count": fn,
    }

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])

        for key, value in metrics.items():
            if isinstance(value, float):
                writer.writerow([key, f"{value:.6f}"])
            else:
                writer.writerow([key, value])

    print("Clean fall-vs-non-fall safety-proxy metrics")
    print("-" * 70)
    print(f"Input predictions: {predictions_path}")
    print(f"Output metrics: {output_path}")
    print("-" * 70)
    print(f"Total windows: {total_rows}")
    print(f"Fall windows: {total_fall_windows}")
    print(f"Non-fall windows: {total_nonfall_windows}")
    print("-" * 70)
    print(f"TP / detected falls: {tp}")
    print(f"FN / missed falls: {fn}")
    print(f"FP / false fall alarms: {fp}")
    print(f"TN / correct non-falls: {tn}")
    print("-" * 70)
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Recall / sensitivity: {recall_sensitivity:.4f}")
    print(f"Missed fall rate: {missed_fall_rate:.4f}")
    print(f"Specificity: {specificity:.4f}")
    print(f"False positive rate: {false_positive_rate:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"F1-score: {f1_score:.4f}")
    print(f"Balanced accuracy: {balanced_accuracy:.4f}")
    print("-" * 70)
    print("Clean safety-proxy metric calculation completed successfully.")


if __name__ == "__main__":
    main()