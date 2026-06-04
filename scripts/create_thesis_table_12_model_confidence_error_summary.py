from pathlib import Path
import csv
import statistics


BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
NOTES_DIR = BASE_DIR / "notes"

OUTPUT_CSV = RESULTS_DIR / "thesis_table_12_model_confidence_error_summary.csv"
OUTPUT_NOTE = NOTES_DIR / "thesis_table_12_model_confidence_error_summary.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level model-reported prediction-confidence summary; "
    "confidence means predicted-class probability/confidence from the model output, not calibrated "
    "clinical confidence; software-level processed-tensor perturbations only; not clinical validation, "
    "not medical-device validation, not diagnostic evidence, not real patient deployment, "
    "not regulatory evaluation, not event-level fall validation, not long-lie validation, "
    "not time-to-alarm validation, not false alarms per hour/day, and not physical-layer / "
    "packet-level / preamble-level / SDR / over-the-air validation."
)

HIGH_CONFIDENCE_THRESHOLD = 0.80
LOW_CONFIDENCE_THRESHOLD = 0.50

CONDITIONS = [
    {
        "condition": "undefended_clean",
        "display_condition": "Undefended clean",
        "model_type": "undefended_baseline",
        "attack_type": "none",
        "epsilon": "0.000000",
        "source_file": "clean_predictions_short.csv",
        "prediction_label_column": "predicted_label",
        "prediction_class_column": "predicted_class_name",
        "fall_pred_column": "fall_pred_binary",
        "confidence_column": "prediction_confidence",
        "correct_column": "correct",
    },
    {
        "condition": "undefended_fgsm_epsilon_0_03",
        "display_condition": "Undefended FGSM epsilon 0.03",
        "model_type": "undefended_baseline",
        "attack_type": "FGSM",
        "epsilon": "0.030000",
        "source_file": "fgsm_predictions_short_epsilon_0_03.csv",
        "prediction_label_column": "attacked_predicted_label",
        "prediction_class_column": "attacked_predicted_class_name",
        "fall_pred_column": "attacked_fall_pred_binary",
        "confidence_column": "attacked_prediction_confidence",
        "correct_column": "attacked_correct",
    },
    {
        "condition": "undefended_pgd_epsilon_0_03",
        "display_condition": "Undefended PGD epsilon 0.03",
        "model_type": "undefended_baseline",
        "attack_type": "PGD",
        "epsilon": "0.030000",
        "source_file": "pgd_predictions_short_epsilon_0_03.csv",
        "prediction_label_column": "predicted_label",
        "prediction_class_column": "predicted_class_name",
        "fall_pred_column": "fall_pred_binary",
        "confidence_column": "prediction_confidence",
        "correct_column": "correct",
    },
    {
        "condition": "defended_clean",
        "display_condition": "Defended clean",
        "model_type": "FGSM_adversarial_training_defended",
        "attack_type": "none",
        "epsilon": "0.000000",
        "source_file": "defended_predictions_short.csv",
        "prediction_label_column": "defended_clean_predicted_label",
        "prediction_class_column": "defended_clean_predicted_class_name",
        "fall_pred_column": "fall_pred_binary_clean_defended",
        "confidence_column": "prediction_confidence_clean_defended",
        "correct_column": "correct_clean_defended",
    },
    {
        "condition": "defended_fgsm_epsilon_0_03",
        "display_condition": "Defended FGSM epsilon 0.03",
        "model_type": "FGSM_adversarial_training_defended",
        "attack_type": "FGSM",
        "epsilon": "0.030000",
        "source_file": "defended_predictions_short.csv",
        "prediction_label_column": "defended_fgsm_predicted_label",
        "prediction_class_column": "defended_fgsm_predicted_class_name",
        "fall_pred_column": "fall_pred_binary_fgsm_defended",
        "confidence_column": "prediction_confidence_fgsm_defended",
        "correct_column": "correct_fgsm_defended",
    },
    {
        "condition": "defended_pgd_epsilon_0_03",
        "display_condition": "Defended PGD epsilon 0.03",
        "model_type": "FGSM_adversarial_training_defended",
        "attack_type": "PGD",
        "epsilon": "0.030000",
        "source_file": "defended_predictions_short.csv",
        "prediction_label_column": "defended_pgd_predicted_label",
        "prediction_class_column": "defended_pgd_predicted_class_name",
        "fall_pred_column": "fall_pred_binary_pgd_defended",
        "confidence_column": "prediction_confidence_pgd_defended",
        "correct_column": "correct_pgd_defended",
    },
]

WINDOW_GROUPS = [
    "all_windows",
    "correct_predictions",
    "incorrect_predictions",
    "true_fall_windows",
    "true_nonfall_windows",
    "detected_fall_windows",
    "missed_fall_windows",
    "false_fall_alarm_windows",
    "correct_nonfall_windows",
]


def safe_int(value):
    if value is None or value == "":
        return 0
    return int(float(value))


def safe_float(value):
    if value is None or value == "":
        return None
    return float(value)


def format_float(value, digits=6):
    if value is None:
        return "NA"
    return f"{value:.{digits}f}"


def read_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")

    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_group_name(row, fall_pred_column, correct_column):
    fall_true = safe_int(row["fall_true_binary"])
    fall_pred = safe_int(row[fall_pred_column])
    correct = safe_int(row[correct_column])

    group_flags = {
        "all_windows": True,
        "correct_predictions": correct == 1,
        "incorrect_predictions": correct == 0,
        "true_fall_windows": fall_true == 1,
        "true_nonfall_windows": fall_true == 0,
        "detected_fall_windows": fall_true == 1 and fall_pred == 1,
        "missed_fall_windows": fall_true == 1 and fall_pred == 0,
        "false_fall_alarm_windows": fall_true == 0 and fall_pred == 1,
        "correct_nonfall_windows": fall_true == 0 and fall_pred == 0,
    }

    return group_flags


def summarize_confidences(confidences):
    confidences = [value for value in confidences if value is not None]
    n = len(confidences)

    if n == 0:
        return {
            "n_windows": 0,
            "mean_prediction_confidence": "NA",
            "median_prediction_confidence": "NA",
            "min_prediction_confidence": "NA",
            "max_prediction_confidence": "NA",
            "high_confidence_count": 0,
            "high_confidence_rate": "NA",
            "low_confidence_count": 0,
            "low_confidence_rate": "NA",
        }

    high_count = sum(1 for value in confidences if value >= HIGH_CONFIDENCE_THRESHOLD)
    low_count = sum(1 for value in confidences if value <= LOW_CONFIDENCE_THRESHOLD)

    return {
        "n_windows": n,
        "mean_prediction_confidence": format_float(statistics.mean(confidences)),
        "median_prediction_confidence": format_float(statistics.median(confidences)),
        "min_prediction_confidence": format_float(min(confidences)),
        "max_prediction_confidence": format_float(max(confidences)),
        "high_confidence_count": high_count,
        "high_confidence_rate": format_float(high_count / n),
        "low_confidence_count": low_count,
        "low_confidence_rate": format_float(low_count / n),
    }


def build_output_rows():
    output_rows = []

    for condition_config in CONDITIONS:
        source_path = RESULTS_DIR / condition_config["source_file"]
        rows = read_rows(source_path)

        group_confidences = {group: [] for group in WINDOW_GROUPS}

        for row in rows:
            confidence = safe_float(row[condition_config["confidence_column"]])
            group_flags = get_group_name(
                row,
                condition_config["fall_pred_column"],
                condition_config["correct_column"],
            )

            for group_name, include_row in group_flags.items():
                if include_row:
                    group_confidences[group_name].append(confidence)

        for group_name in WINDOW_GROUPS:
            summary = summarize_confidences(group_confidences[group_name])

            output_row = {
                "condition": condition_config["condition"],
                "display_condition": condition_config["display_condition"],
                "model_type": condition_config["model_type"],
                "attack_type": condition_config["attack_type"],
                "epsilon": condition_config["epsilon"],
                "source_file": condition_config["source_file"],
                "window_group": group_name,
                "high_confidence_threshold": format_float(HIGH_CONFIDENCE_THRESHOLD),
                "low_confidence_threshold": format_float(LOW_CONFIDENCE_THRESHOLD),
                "claim_boundary": CLAIM_BOUNDARY,
            }
            output_row.update(summary)
            output_rows.append(output_row)

    return output_rows


def write_csv(output_rows):
    fieldnames = list(output_rows[0].keys())

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)


def find_row(output_rows, condition, group):
    for row in output_rows:
        if row["condition"] == condition and row["window_group"] == group:
            return row
    raise ValueError(f"Missing row for {condition} / {group}")


def write_note(output_rows):
    lines = []

    lines.append("# Thesis Table 12: Model Confidence and Error Confidence Summary")
    lines.append("")
    lines.append("This table summarizes model-reported prediction confidence for correct predictions, incorrect predictions, missed fall windows, false fall alarm windows, and other clinically motivated window groups.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Output File")
    lines.append("")
    lines.append("- `results/thesis_table_12_model_confidence_error_summary.csv`")
    lines.append("")
    lines.append("## Input Files")
    lines.append("")
    lines.append("- `results/clean_predictions_short.csv`")
    lines.append("- `results/fgsm_predictions_short_epsilon_0_03.csv`")
    lines.append("- `results/pgd_predictions_short_epsilon_0_03.csv`")
    lines.append("- `results/defended_predictions_short.csv`")
    lines.append("")
    lines.append("## Confidence Meaning")
    lines.append("")
    lines.append("The confidence values are model-reported predicted-class confidence values exported from the prediction files. They should be interpreted as model output confidence, not calibrated clinical certainty.")
    lines.append("")
    lines.append("## Thresholds")
    lines.append("")
    lines.append("```text")
    lines.append(f"high-confidence threshold = {HIGH_CONFIDENCE_THRESHOLD:.2f}")
    lines.append(f"low-confidence threshold = {LOW_CONFIDENCE_THRESHOLD:.2f}")
    lines.append("```")
    lines.append("")
    lines.append("## Main Confidence Summary")
    lines.append("")
    lines.append("| Condition | Group | N | Mean Confidence | Median Confidence | High-Confidence Rate | Low-Confidence Rate |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")

    summary_groups = [
        "all_windows",
        "correct_predictions",
        "incorrect_predictions",
        "missed_fall_windows",
        "false_fall_alarm_windows",
    ]

    for condition_config in CONDITIONS:
        for group in summary_groups:
            row = find_row(output_rows, condition_config["condition"], group)
            lines.append(
                f"| {row['display_condition']} "
                f"| {row['window_group']} "
                f"| {row['n_windows']} "
                f"| {row['mean_prediction_confidence']} "
                f"| {row['median_prediction_confidence']} "
                f"| {row['high_confidence_rate']} "
                f"| {row['low_confidence_rate']} |"
            )

    lines.append("")
    lines.append("## Missed-Fall Confidence Focus")
    lines.append("")
    lines.append("| Condition | Missed Fall Windows | Mean Confidence | Median Confidence | High-Confidence Missed-Fall Rate |")
    lines.append("|---|---:|---:|---:|---:|")

    for condition_config in CONDITIONS:
        row = find_row(output_rows, condition_config["condition"], "missed_fall_windows")
        lines.append(
            f"| {row['display_condition']} "
            f"| {row['n_windows']} "
            f"| {row['mean_prediction_confidence']} "
            f"| {row['median_prediction_confidence']} "
            f"| {row['high_confidence_rate']} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("Table 12 adds a confidence dimension to the safety-proxy analysis. It helps identify whether the model is merely wrong, or wrong with high model-reported confidence.")
    lines.append("")
    lines.append("This is important for thesis discussion because high-confidence missed fall windows may be more concerning than low-confidence missed fall windows in a safety-monitoring context. Similarly, high-confidence false fall alarms may reduce trust in alerts.")
    lines.append("")
    lines.append("The table should not be interpreted as clinical confidence, calibrated uncertainty, diagnostic certainty, or medical-device reliability. It is a window-level summary of model-reported predicted-class confidence.")

    OUTPUT_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    output_rows = build_output_rows()
    write_csv(output_rows)
    write_note(output_rows)

    print("Created Thesis Table 12 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Table 12 summarizes model-reported prediction confidence for:")
    for condition_config in CONDITIONS:
        print(f"  {condition_config['display_condition']}")


if __name__ == "__main__":
    main()