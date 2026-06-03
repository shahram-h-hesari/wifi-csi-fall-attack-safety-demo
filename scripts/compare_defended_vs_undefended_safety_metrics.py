"""
Compare defended vs undefended fall-vs-non-fall safety-proxy metrics.

This version computes all comparison rows directly from prediction CSV files,
not from older metric-summary CSV files.

Input files:
    results/clean_predictions_short.csv
    results/fgsm_predictions_short_epsilon_0_03.csv
    results/pgd_predictions_short_epsilon_0_03.csv
    results/defended_predictions_short.csv

Output:
    results/defended_vs_undefended_safety_comparison.csv

Claim boundary:
    This is a window-level software comparison on processed CSI tensors.
    It is not clinical validation, medical-device validation, diagnostic
    evidence, regulatory evaluation, physical-layer validation, packet-level
    validation, preamble-level validation, SDR validation, or over-the-air
    validation.
"""

from pathlib import Path
import csv


OUTPUT_FILE = "defended_vs_undefended_safety_comparison.csv"


def safe_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def safe_divide(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator


def read_rows(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError(f"No rows found in: {path}")

    return rows


def build_binary_lookup(rows, binary_column):
    lookup = {}

    for row in rows:
        sample_id = safe_int(row["sample_id"])
        lookup[sample_id] = safe_int(row[binary_column])

    return lookup


def compute_metrics_from_rows(
    rows,
    condition,
    model_type,
    attack_type,
    epsilon,
    true_binary_column,
    predicted_binary_column,
    seven_class_correct_column,
    reference_binary_column=None,
    reference_binary_lookup=None,
):
    tp = 0
    fn = 0
    fp = 0
    tn = 0
    seven_class_correct = 0
    prediction_changes = 0

    for row in rows:
        true_binary = safe_int(row[true_binary_column])
        pred_binary = safe_int(row[predicted_binary_column])

        if true_binary == 1 and pred_binary == 1:
            tp += 1
        elif true_binary == 1 and pred_binary == 0:
            fn += 1
        elif true_binary == 0 and pred_binary == 1:
            fp += 1
        elif true_binary == 0 and pred_binary == 0:
            tn += 1
        else:
            raise ValueError(
                f"Unexpected binary labels in {condition}: "
                f"true={true_binary}, pred={pred_binary}"
            )

        seven_class_correct += safe_int(row[seven_class_correct_column])

        if reference_binary_column is not None:
            reference_binary = safe_int(row[reference_binary_column])
            if pred_binary != reference_binary:
                prediction_changes += 1

        elif reference_binary_lookup is not None:
            sample_id = safe_int(row["sample_id"])
            if sample_id not in reference_binary_lookup:
                raise KeyError(f"Missing sample_id in reference lookup: {sample_id}")

            reference_binary = reference_binary_lookup[sample_id]
            if pred_binary != reference_binary:
                prediction_changes += 1

    total_windows = len(rows)
    fall_windows = tp + fn
    non_fall_windows = fp + tn

    binary_accuracy = safe_divide(tp + tn, total_windows)
    seven_class_accuracy = safe_divide(seven_class_correct, total_windows)
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

    if reference_binary_column is None and reference_binary_lookup is None:
        prediction_change_rate = 0.0
    else:
        prediction_change_rate = safe_divide(prediction_changes, total_windows)

    if tp + fn + fp + tn != total_windows:
        raise ValueError(
            f"Confusion matrix does not sum to total windows for {condition}."
        )

    return {
        "condition": condition,
        "model_type": model_type,
        "attack_type": attack_type,
        "epsilon": epsilon,
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


def add_delta_columns(rows):
    undefended_by_attack = {
        row["attack_type"]: row
        for row in rows
        if row["model_type"] == "undefended_baseline"
    }

    delta_fields = [
        "missed_fall_rate",
        "FP_false_fall_alarms",
        "recall_sensitivity",
        "precision",
        "f1_score",
        "balanced_accuracy",
        "prediction_change_rate",
    ]

    for row in rows:
        for field in delta_fields:
            row[f"defended_minus_undefended_{field}"] = ""

        if row["model_type"] != "FGSM_adversarial_training_defended":
            continue

        reference = undefended_by_attack.get(row["attack_type"])

        if reference is None:
            continue

        for field in delta_fields:
            delta = float(row[field]) - float(reference[field])
            row[f"defended_minus_undefended_{field}"] = f"{delta:.6f}"

    return rows


def format_for_csv(rows):
    formatted_rows = []

    for row in rows:
        formatted = {}

        for key, value in row.items():
            if isinstance(value, float):
                formatted[key] = f"{value:.6f}"
            else:
                formatted[key] = value

        formatted_rows.append(formatted)

    return formatted_rows


def write_csv(path: Path, rows):
    if not rows:
        raise ValueError("No rows to write.")

    fieldnames = list(rows[0].keys())

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows):
    print("Defended vs undefended comparison completed successfully.")
    print(f"Rows saved: {len(rows)}")
    print("-" * 80)

    for row in rows:
        print(f"Condition: {row['condition']}")
        print(f"  model_type: {row['model_type']}")
        print(f"  attack_type: {row['attack_type']}")
        print(f"  TP: {row['TP_detected_falls']}")
        print(f"  FN: {row['FN_missed_falls']}")
        print(f"  FP: {row['FP_false_fall_alarms']}")
        print(f"  TN: {row['TN_correct_non_falls']}")
        print(f"  missed_fall_rate: {row['missed_fall_rate']}")
        print(f"  recall: {row['recall_sensitivity']}")
        print(f"  f1_score: {row['f1_score']}")
        print(f"  balanced_accuracy: {row['balanced_accuracy']}")
        print(f"  prediction_change_rate: {row['prediction_change_rate']}")
        print(
            "  defended_minus_undefended_missed_fall_rate: "
            f"{row['defended_minus_undefended_missed_fall_rate']}"
        )
        print(
            "  defended_minus_undefended_FP_false_fall_alarms: "
            f"{row['defended_minus_undefended_FP_false_fall_alarms']}"
        )
        print("-" * 80)


def main():
    experiment_dir = Path(__file__).resolve().parents[1]
    results_dir = experiment_dir / "results"

    clean_rows = read_rows(results_dir / "clean_predictions_short.csv")
    fgsm_rows = read_rows(results_dir / "fgsm_predictions_short_epsilon_0_03.csv")
    pgd_rows = read_rows(results_dir / "pgd_predictions_short_epsilon_0_03.csv")
    defended_rows = read_rows(results_dir / "defended_predictions_short.csv")

    clean_binary_lookup = build_binary_lookup(
        rows=clean_rows,
        binary_column="fall_pred_binary",
    )

    output_rows = [
        compute_metrics_from_rows(
            rows=clean_rows,
            condition="undefended_clean",
            model_type="undefended_baseline",
            attack_type="none",
            epsilon="0.000000",
            true_binary_column="fall_true_binary",
            predicted_binary_column="fall_pred_binary",
            seven_class_correct_column="correct",
        ),
        compute_metrics_from_rows(
            rows=fgsm_rows,
            condition="undefended_fgsm_epsilon_0_03",
            model_type="undefended_baseline",
            attack_type="FGSM",
            epsilon="0.030000",
            true_binary_column="fall_true_binary",
            predicted_binary_column="attacked_fall_pred_binary",
            seven_class_correct_column="attacked_correct",
            reference_binary_column="clean_fall_pred_binary",
        ),
        compute_metrics_from_rows(
            rows=pgd_rows,
            condition="undefended_pgd_epsilon_0_03",
            model_type="undefended_baseline",
            attack_type="PGD",
            epsilon="0.030000",
            true_binary_column="fall_true_binary",
            predicted_binary_column="fall_pred_binary",
            seven_class_correct_column="correct",
            reference_binary_lookup=clean_binary_lookup,
        ),
        compute_metrics_from_rows(
            rows=defended_rows,
            condition="defended_clean",
            model_type="FGSM_adversarial_training_defended",
            attack_type="none",
            epsilon="0.000000",
            true_binary_column="fall_true_binary",
            predicted_binary_column="fall_pred_binary_clean_defended",
            seven_class_correct_column="correct_clean_defended",
        ),
        compute_metrics_from_rows(
            rows=defended_rows,
            condition="defended_fgsm_epsilon_0_03",
            model_type="FGSM_adversarial_training_defended",
            attack_type="FGSM",
            epsilon="0.030000",
            true_binary_column="fall_true_binary",
            predicted_binary_column="fall_pred_binary_fgsm_defended",
            seven_class_correct_column="correct_fgsm_defended",
            reference_binary_column="fall_pred_binary_clean_defended",
        ),
        compute_metrics_from_rows(
            rows=defended_rows,
            condition="defended_pgd_epsilon_0_03",
            model_type="FGSM_adversarial_training_defended",
            attack_type="PGD",
            epsilon="0.030000",
            true_binary_column="fall_true_binary",
            predicted_binary_column="fall_pred_binary_pgd_defended",
            seven_class_correct_column="correct_pgd_defended",
            reference_binary_column="fall_pred_binary_clean_defended",
        ),
    ]

    output_rows = add_delta_columns(output_rows)
    output_rows = format_for_csv(output_rows)

    output_path = results_dir / OUTPUT_FILE
    write_csv(output_path, output_rows)

    print(f"Output saved to: {output_path}")
    print_summary(output_rows)


if __name__ == "__main__":
    main()