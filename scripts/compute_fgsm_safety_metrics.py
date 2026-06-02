"""
Compute clean-vs-FGSM fall-vs-non-fall safety-proxy metrics.

Purpose:
    This script reads FGSM prediction results and calculates binary
    fall-vs-non-fall safety-proxy metrics for both clean predictions
    and FGSM-attacked predictions.

Important:
    These are window-level research safety-proxy metrics.
    The FGSM attack is applied to processed CSI tensors.
    This is not physical-layer, packet-level, preamble-level, SDR,
    or over-the-air attack validation.
    This is not clinical validation or medical-device validation.

Expected input:
    results/fgsm_predictions_short_epsilon_0_03.csv

Expected output:
    results/fgsm_safety_proxy_metrics_epsilon_0_03.csv

Command:
    python scripts/compute_fgsm_safety_metrics.py
"""

from pathlib import Path
import csv


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def compute_binary_metrics(rows, prediction_column: str) -> dict:
    tp = 0
    fp = 0
    fn = 0
    tn = 0

    for row in rows:
        true_binary = int(row["fall_true_binary"])
        pred_binary = int(row[prediction_column])

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

    total_windows = tp + fp + fn + tn
    fall_windows = tp + fn
    nonfall_windows = tn + fp

    accuracy = safe_divide(tp + tn, total_windows)
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
        "total_windows": total_windows,
        "fall_windows": fall_windows,
        "nonfall_windows": nonfall_windows,
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


def main() -> None:
    experiment_dir = Path(__file__).resolve().parents[1]

    input_path = experiment_dir / "results" / "fgsm_predictions_short_epsilon_0_03.csv"
    output_path = experiment_dir / "results" / "fgsm_safety_proxy_metrics_epsilon_0_03.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"FGSM prediction CSV not found: {input_path}")

    with input_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    required_columns = {
        "sample_id",
        "epsilon",
        "fall_true_binary",
        "clean_fall_pred_binary",
        "attacked_fall_pred_binary",
    }

    missing_columns = required_columns - set(rows[0].keys())
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    epsilon = rows[0]["epsilon"]

    clean_metrics = compute_binary_metrics(
        rows=rows,
        prediction_column="clean_fall_pred_binary",
    )

    attacked_metrics = compute_binary_metrics(
        rows=rows,
        prediction_column="attacked_fall_pred_binary",
    )

    metric_order = [
        "total_windows",
        "fall_windows",
        "nonfall_windows",
        "true_positive_fall_detected",
        "false_positive_false_fall_alarm",
        "false_negative_missed_fall",
        "true_negative_nonfall_correct",
        "accuracy",
        "recall_sensitivity",
        "missed_fall_rate",
        "specificity",
        "false_positive_rate",
        "precision",
        "f1_score",
        "balanced_accuracy",
        "false_alarm_count",
        "missed_fall_count",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["scenario", "epsilon", "metric", "value"])

        for metric in metric_order:
            value = clean_metrics[metric]
            if isinstance(value, float):
                value = f"{value:.6f}"
            writer.writerow(["clean", epsilon, metric, value])

        for metric in metric_order:
            value = attacked_metrics[metric]
            if isinstance(value, float):
                value = f"{value:.6f}"
            writer.writerow(["fgsm_attacked", epsilon, metric, value])

        for metric in metric_order:
            clean_value = clean_metrics[metric]
            attacked_value = attacked_metrics[metric]

            if isinstance(clean_value, float) or isinstance(attacked_value, float):
                delta_value = attacked_value - clean_value
                writer.writerow(["delta_attacked_minus_clean", epsilon, metric, f"{delta_value:.6f}"])
            else:
                delta_value = attacked_value - clean_value
                writer.writerow(["delta_attacked_minus_clean", epsilon, metric, delta_value])

    print("FGSM fall-vs-non-fall safety-proxy metrics")
    print("-" * 80)
    print(f"Input predictions: {input_path}")
    print(f"Output metrics: {output_path}")
    print(f"FGSM epsilon: {epsilon}")
    print("-" * 80)

    print("Clean binary metrics")
    print("-" * 80)
    print(f"TP / detected falls: {clean_metrics['true_positive_fall_detected']}")
    print(f"FN / missed falls: {clean_metrics['false_negative_missed_fall']}")
    print(f"FP / false fall alarms: {clean_metrics['false_positive_false_fall_alarm']}")
    print(f"TN / correct non-falls: {clean_metrics['true_negative_nonfall_correct']}")
    print(f"Recall / sensitivity: {clean_metrics['recall_sensitivity']:.4f}")
    print(f"Missed fall rate: {clean_metrics['missed_fall_rate']:.4f}")
    print(f"Precision: {clean_metrics['precision']:.4f}")
    print(f"F1-score: {clean_metrics['f1_score']:.4f}")
    print(f"Balanced accuracy: {clean_metrics['balanced_accuracy']:.4f}")

    print("-" * 80)
    print("FGSM-attacked binary metrics")
    print("-" * 80)
    print(f"TP / detected falls: {attacked_metrics['true_positive_fall_detected']}")
    print(f"FN / missed falls: {attacked_metrics['false_negative_missed_fall']}")
    print(f"FP / false fall alarms: {attacked_metrics['false_positive_false_fall_alarm']}")
    print(f"TN / correct non-falls: {attacked_metrics['true_negative_nonfall_correct']}")
    print(f"Recall / sensitivity: {attacked_metrics['recall_sensitivity']:.4f}")
    print(f"Missed fall rate: {attacked_metrics['missed_fall_rate']:.4f}")
    print(f"Precision: {attacked_metrics['precision']:.4f}")
    print(f"F1-score: {attacked_metrics['f1_score']:.4f}")
    print(f"Balanced accuracy: {attacked_metrics['balanced_accuracy']:.4f}")

    print("-" * 80)
    print("Clean-to-FGSM safety degradation")
    print("-" * 80)
    print(
        "Missed fall rate change: "
        f"{attacked_metrics['missed_fall_rate'] - clean_metrics['missed_fall_rate']:.4f}"
    )
    print(
        "False alarm count change: "
        f"{attacked_metrics['false_alarm_count'] - clean_metrics['false_alarm_count']}"
    )
    print(
        "Recall change: "
        f"{attacked_metrics['recall_sensitivity'] - clean_metrics['recall_sensitivity']:.4f}"
    )
    print(
        "F1-score change: "
        f"{attacked_metrics['f1_score'] - clean_metrics['f1_score']:.4f}"
    )
    print("-" * 80)
    print("FGSM safety-proxy metric calculation completed successfully.")


if __name__ == "__main__":
    main()