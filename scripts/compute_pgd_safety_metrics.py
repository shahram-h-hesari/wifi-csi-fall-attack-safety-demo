"""
Compute PGD safety-proxy metrics for the WiFi CSI Fall Attack-Safety Demo.

Input:
- results/pgd_predictions_short_epsilon_0_03.csv

Output:
- results/pgd_safety_proxy_metrics_epsilon_0_03.csv

Important claim boundary:
These are window-level fall-vs-non-fall safety-proxy metrics derived from model predictions.
They are not clinical validation, medical-device validation, diagnostic evidence, or regulatory evaluation.
"""

from pathlib import Path
import csv


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = EXPERIMENT_DIR / "results"

INPUT_FILE = RESULTS_DIR / "pgd_predictions_short_epsilon_0_03.csv"
OUTPUT_FILE = RESULTS_DIR / "pgd_safety_proxy_metrics_epsilon_0_03.csv"


def safe_divide(numerator, denominator):
    """Avoid division-by-zero errors."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    with INPUT_FILE.open("r", newline="", encoding="utf-8") as csvfile:
        rows = list(csv.DictReader(csvfile))

    if not rows:
        raise ValueError(f"No rows found in input file: {INPUT_FILE}")

    total_windows = len(rows)

    true_binary = [int(row["fall_true_binary"]) for row in rows]
    pred_binary = [int(row["fall_pred_binary"]) for row in rows]

    true_labels = [int(row["true_label"]) for row in rows]
    pred_labels = [int(row["predicted_label"]) for row in rows]

    attack_type = rows[0].get("attack_type", "PGD")
    epsilon = rows[0].get("epsilon", "0.03")
    alpha = rows[0].get("alpha", "0.005")
    pgd_steps = rows[0].get("pgd_steps", "10")

    tp = sum(1 for y_true, y_pred in zip(true_binary, pred_binary) if y_true == 1 and y_pred == 1)
    fn = sum(1 for y_true, y_pred in zip(true_binary, pred_binary) if y_true == 1 and y_pred == 0)
    fp = sum(1 for y_true, y_pred in zip(true_binary, pred_binary) if y_true == 0 and y_pred == 1)
    tn = sum(1 for y_true, y_pred in zip(true_binary, pred_binary) if y_true == 0 and y_pred == 0)

    fall_windows = tp + fn
    nonfall_windows = fp + tn

    binary_accuracy = safe_divide(tp + tn, total_windows)
    seven_class_accuracy = safe_divide(
        sum(1 for y_true, y_pred in zip(true_labels, pred_labels) if y_true == y_pred),
        total_windows,
    )

    recall = safe_divide(tp, tp + fn)
    sensitivity = recall
    missed_fall_rate = safe_divide(fn, tp + fn)

    specificity = safe_divide(tn, tn + fp)
    false_positive_rate = safe_divide(fp, fp + tn)

    precision = safe_divide(tp, tp + fp)
    f1_score = safe_divide(2 * precision * recall, precision + recall)

    balanced_accuracy = (sensitivity + specificity) / 2

    false_alarm_count = fp
    missed_fall_count = fn
    detected_fall_count = tp
    correct_nonfall_count = tn

    output_row = {
        "attack_type": attack_type,
        "epsilon": epsilon,
        "alpha": alpha,
        "pgd_steps": pgd_steps,
        "total_windows": total_windows,
        "fall_windows": fall_windows,
        "nonfall_windows": nonfall_windows,
        "tp_detected_falls": tp,
        "fn_missed_falls": fn,
        "fp_false_fall_alarms": fp,
        "tn_correct_nonfalls": tn,
        "detected_fall_count": detected_fall_count,
        "missed_fall_count": missed_fall_count,
        "false_alarm_count": false_alarm_count,
        "correct_nonfall_count": correct_nonfall_count,
        "seven_class_accuracy": round(seven_class_accuracy, 6),
        "binary_accuracy": round(binary_accuracy, 6),
        "recall_sensitivity": round(recall, 6),
        "missed_fall_rate": round(missed_fall_rate, 6),
        "specificity": round(specificity, 6),
        "false_positive_rate": round(false_positive_rate, 6),
        "precision": round(precision, 6),
        "f1_score": round(f1_score, 6),
        "balanced_accuracy": round(balanced_accuracy, 6),
    }

    fieldnames = list(output_row.keys())

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(output_row)

    print("PGD safety-proxy metrics computed.")
    print(f"Input file:  {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print()
    print("Summary")
    print("-------")
    print(f"Attack type:          {attack_type}")
    print(f"Epsilon:              {epsilon}")
    print(f"Alpha:                {alpha}")
    print(f"PGD steps:            {pgd_steps}")
    print(f"Total windows:        {total_windows}")
    print(f"Fall windows:         {fall_windows}")
    print(f"Non-fall windows:     {nonfall_windows}")
    print(f"TP detected falls:    {tp}")
    print(f"FN missed falls:      {fn}")
    print(f"FP false alarms:      {fp}")
    print(f"TN correct non-falls: {tn}")
    print(f"Seven-class accuracy: {seven_class_accuracy:.4f}")
    print(f"Binary accuracy:      {binary_accuracy:.4f}")
    print(f"Recall/sensitivity:   {recall:.4f}")
    print(f"Missed fall rate:     {missed_fall_rate:.4f}")
    print(f"Specificity:          {specificity:.4f}")
    print(f"False positive rate:  {false_positive_rate:.4f}")
    print(f"Precision:            {precision:.4f}")
    print(f"F1-score:             {f1_score:.4f}")
    print(f"Balanced accuracy:    {balanced_accuracy:.4f}")


if __name__ == "__main__":
    main()