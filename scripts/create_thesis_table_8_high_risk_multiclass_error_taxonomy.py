"""
Create Thesis Table 8: High-Risk Multiclass Error Taxonomy.

This script uses existing seven-class prediction CSVs to identify fall-relevant
multiclass error patterns:

1. missed fall multiclass errors:
   true class = fall, predicted class = non-fall activity

2. false fall alarm multiclass errors:
   true class = non-fall activity, predicted class = fall

Outputs:
    results/thesis_table_8_high_risk_multiclass_error_taxonomy.csv
    notes/thesis_table_8_high_risk_multiclass_error_taxonomy.md

Claim boundary:
    This is a window-level error-taxonomy analysis. It is not event-level
    fall validation, clinical validation, or medical-device evaluation.
"""

from pathlib import Path
import csv
from collections import Counter


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
NOTES_DIR = ROOT / "notes"

OUTPUT_CSV = RESULTS_DIR / "thesis_table_8_high_risk_multiclass_error_taxonomy.csv"
OUTPUT_NOTE = NOTES_DIR / "thesis_table_8_high_risk_multiclass_error_taxonomy.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level multiclass error-taxonomy "
    "analysis; software-level processed-tensor perturbations only; not clinical "
    "validation, not medical-device validation, not diagnostic evidence, not real "
    "patient deployment, not regulatory evaluation, not event-level fall validation, "
    "not long-lie validation, not time-to-alarm validation, and not physical-layer / "
    "packet-level / preamble-level / SDR / over-the-air validation."
)

CLASS_NAMES = {
    0: "lie down",
    1: "fall",
    2: "walk",
    3: "pickup",
    4: "run",
    5: "sit down",
    6: "stand up",
}

CONDITIONS = [
    {
        "condition_id": "undefended_clean",
        "condition_name": "Undefended clean baseline",
        "defense_state": "undefended",
        "attack_type": "none",
        "epsilon": "NA",
        "file": RESULTS_DIR / "clean_predictions_short.csv",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "pred_label_col": "predicted_label",
        "pred_class_col": "predicted_class_name",
    },
    {
        "condition_id": "undefended_fgsm_epsilon_0_03",
        "condition_name": "Undefended FGSM attack, epsilon 0.030",
        "defense_state": "undefended",
        "attack_type": "FGSM",
        "epsilon": "0.030",
        "file": RESULTS_DIR / "fgsm_predictions_short_epsilon_0_03.csv",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "pred_label_col": "attacked_predicted_label",
        "pred_class_col": "attacked_predicted_class_name",
    },
    {
        "condition_id": "undefended_pgd_epsilon_0_03",
        "condition_name": "Undefended PGD attack, epsilon 0.030",
        "defense_state": "undefended",
        "attack_type": "PGD",
        "epsilon": "0.030",
        "file": RESULTS_DIR / "pgd_predictions_short_epsilon_0_03.csv",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "pred_label_col": "predicted_label",
        "pred_class_col": "predicted_class_name",
    },
    {
        "condition_id": "defended_clean",
        "condition_name": "Defended clean baseline",
        "defense_state": "FGSM adversarial-training defense",
        "attack_type": "none",
        "epsilon": "NA",
        "file": RESULTS_DIR / "defended_predictions_short.csv",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "pred_label_col": "defended_clean_predicted_label",
        "pred_class_col": "defended_clean_predicted_class_name",
    },
    {
        "condition_id": "defended_fgsm_epsilon_0_03",
        "condition_name": "Defended FGSM attack, epsilon 0.030",
        "defense_state": "FGSM adversarial-training defense",
        "attack_type": "FGSM",
        "epsilon": "0.030",
        "file": RESULTS_DIR / "defended_predictions_short.csv",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "pred_label_col": "defended_fgsm_predicted_label",
        "pred_class_col": "defended_fgsm_predicted_class_name",
    },
    {
        "condition_id": "defended_pgd_epsilon_0_03",
        "condition_name": "Defended PGD attack, epsilon 0.030",
        "defense_state": "FGSM adversarial-training defense",
        "attack_type": "PGD",
        "epsilon": "0.030",
        "file": RESULTS_DIR / "defended_predictions_short.csv",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "pred_label_col": "defended_pgd_predicted_label",
        "pred_class_col": "defended_pgd_predicted_class_name",
    },
]


FIELDNAMES = [
    "condition_id",
    "condition_name",
    "defense_state",
    "attack_type",
    "epsilon",
    "error_family",
    "risk_priority",
    "true_label",
    "true_class_name",
    "predicted_label",
    "predicted_class_name",
    "count",
    "total_windows",
    "percent_of_total_windows",
    "safety_proxy_interpretation",
    "thesis_use",
    "claim_boundary",
]


def read_csv_rows(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required prediction file: {path}")

    with path.open("r", newline="", encoding="utf-8") as csvfile:
        return list(csv.DictReader(csvfile))


def require_columns(rows, path: Path, columns):
    if not rows:
        raise ValueError(f"No rows found in file: {path}")

    missing = [col for col in columns if col not in rows[0]]
    if missing:
        raise ValueError(f"Missing columns in {path}: {missing}")


def as_int(value):
    return int(float(str(value).strip()))


def format_percent(count, total):
    if total == 0:
        return "0.0000"
    return f"{100.0 * count / total:.4f}"


def error_metadata(true_label, predicted_label):
    if true_label == 1 and predicted_label != 1:
        return {
            "error_family": "missed_fall_multiclass_error",
            "risk_priority": "highest",
            "safety_proxy_interpretation": (
                "Fall window predicted as a non-fall activity; contributes to "
                "window-level missed fall rate."
            ),
            "thesis_use": (
                "Use to explain which non-fall classes absorb fall windows under "
                "clean, attacked, or defended conditions."
            ),
        }

    if true_label != 1 and predicted_label == 1:
        return {
            "error_family": "false_fall_alarm_multiclass_error",
            "risk_priority": "high",
            "safety_proxy_interpretation": (
                "Non-fall window predicted as fall; contributes to window-level "
                "false fall alarm count."
            ),
            "thesis_use": (
                "Use to explain which non-fall activities are converted into "
                "false fall alarms under clean, attacked, or defended conditions."
            ),
        }

    raise ValueError("Table 8 only includes fall-relevant high-risk error pairs.")


def all_high_risk_pairs():
    pairs = []

    # Missed fall patterns: true fall -> predicted non-fall.
    for predicted_label in [0, 2, 3, 4, 5, 6]:
        pairs.append((1, predicted_label))

    # False fall alarm patterns: true non-fall -> predicted fall.
    for true_label in [0, 2, 3, 4, 5, 6]:
        pairs.append((true_label, 1))

    return pairs


def build_taxonomy_rows():
    output_rows = []
    summary_rows = []

    for condition in CONDITIONS:
        rows = read_csv_rows(condition["file"])
        required_columns = [
            condition["true_label_col"],
            condition["true_class_col"],
            condition["pred_label_col"],
            condition["pred_class_col"],
        ]
        require_columns(rows, condition["file"], required_columns)

        total_windows = len(rows)
        pair_counter = Counter()

        for row in rows:
            true_label = as_int(row[condition["true_label_col"]])
            predicted_label = as_int(row[condition["pred_label_col"]])

            if true_label == predicted_label:
                continue

            if true_label == 1 or predicted_label == 1:
                pair_counter[(true_label, predicted_label)] += 1

        missed_fall_count = sum(
            pair_counter[(1, predicted_label)] for predicted_label in [0, 2, 3, 4, 5, 6]
        )
        false_fall_alarm_count = sum(
            pair_counter[(true_label, 1)] for true_label in [0, 2, 3, 4, 5, 6]
        )

        summary_rows.append(
            {
                "condition_id": condition["condition_id"],
                "condition_name": condition["condition_name"],
                "total_windows": total_windows,
                "missed_fall_multiclass_error_count": missed_fall_count,
                "false_fall_alarm_multiclass_error_count": false_fall_alarm_count,
                "total_high_risk_multiclass_error_count": (
                    missed_fall_count + false_fall_alarm_count
                ),
            }
        )

        for true_label, predicted_label in all_high_risk_pairs():
            count = pair_counter[(true_label, predicted_label)]
            meta = error_metadata(true_label, predicted_label)

            output_rows.append(
                {
                    "condition_id": condition["condition_id"],
                    "condition_name": condition["condition_name"],
                    "defense_state": condition["defense_state"],
                    "attack_type": condition["attack_type"],
                    "epsilon": condition["epsilon"],
                    "error_family": meta["error_family"],
                    "risk_priority": meta["risk_priority"],
                    "true_label": true_label,
                    "true_class_name": CLASS_NAMES[true_label],
                    "predicted_label": predicted_label,
                    "predicted_class_name": CLASS_NAMES[predicted_label],
                    "count": count,
                    "total_windows": total_windows,
                    "percent_of_total_windows": format_percent(count, total_windows),
                    "safety_proxy_interpretation": meta["safety_proxy_interpretation"],
                    "thesis_use": meta["thesis_use"],
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    return output_rows, summary_rows


def md_escape(value):
    text = str(value)
    text = text.replace("|", "\\|")
    text = text.replace("\n", " ")
    return text


def write_csv(rows):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(rows, summary_rows):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Thesis Table 8: High-Risk Multiclass Error Taxonomy")
    lines.append("")
    lines.append(
        "This table identifies fall-relevant seven-class error patterns from the "
        "existing prediction CSV files. It separates missed-fall multiclass errors "
        "from false-fall-alarm multiclass errors."
    )
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Key Finding")
    lines.append("")
    lines.append(
        "The current prediction files support a window-level multiclass error-taxonomy "
        "analysis because they include true seven-class labels and predicted seven-class "
        "labels for clean, FGSM, PGD, defended clean, defended FGSM, and defended PGD "
        "conditions."
    )
    lines.append("")
    lines.append("This is not an event-level clinical-safety analysis.")
    lines.append("")
    lines.append("## Summary by Condition")
    lines.append("")
    lines.append(
        "| Condition | Total Windows | Missed-Fall Multiclass Errors | "
        "False-Fall-Alarm Multiclass Errors | Total High-Risk Errors |"
    )
    lines.append("|---|---:|---:|---:|---:|")

    for row in summary_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(row["condition_name"]),
                    md_escape(row["total_windows"]),
                    md_escape(row["missed_fall_multiclass_error_count"]),
                    md_escape(row["false_fall_alarm_multiclass_error_count"]),
                    md_escape(row["total_high_risk_multiclass_error_count"]),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Detailed Taxonomy")
    lines.append("")
    lines.append(
        "| Condition | Error Family | True Class | Predicted Class | Count | "
        "Percent of Windows | Interpretation |"
    )
    lines.append("|---|---|---|---|---:|---:|---|")

    for row in rows:
        # Keep the Markdown readable by including only nonzero taxonomy rows.
        if int(row["count"]) == 0:
            continue

        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(row["condition_name"]),
                    md_escape(row["error_family"]),
                    md_escape(row["true_class_name"]),
                    md_escape(row["predicted_class_name"]),
                    md_escape(row["count"]),
                    md_escape(row["percent_of_total_windows"]),
                    md_escape(row["safety_proxy_interpretation"]),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Table 8 provides the multiclass explanation behind the binary fall-vs-non-fall "
        "safety-proxy metrics. A missed-fall multiclass error occurs when a true fall "
        "window is predicted as a non-fall activity. A false-fall-alarm multiclass "
        "error occurs when a true non-fall activity is predicted as fall."
    )
    lines.append("")
    lines.append(
        "This table is useful because two conditions may have similar binary safety-proxy "
        "metrics while failing through different seven-class confusion pathways. For "
        "example, attacks may convert fall windows into specific non-fall classes, or "
        "convert specific non-fall activities into false fall alarms."
    )
    lines.append("")
    lines.append(
        "The result should be reported as a window-level multiclass error-taxonomy "
        "analysis. It should not be described as event-level fall validation or "
        "clinical fall validation."
    )
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `results/thesis_table_8_high_risk_multiclass_error_taxonomy.csv`")
    lines.append("- `notes/thesis_table_8_high_risk_multiclass_error_taxonomy.md`")
    lines.append("")

    OUTPUT_NOTE.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows, summary_rows = build_taxonomy_rows()
    write_csv(rows)
    write_markdown(rows, summary_rows)

    print("Created Thesis Table 8 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("High-risk multiclass error summary:")
    for row in summary_rows:
        print(
            f"  {row['condition_name']}: "
            f"missed_fall_errors={row['missed_fall_multiclass_error_count']}, "
            f"false_fall_alarm_errors={row['false_fall_alarm_multiclass_error_count']}, "
            f"total_high_risk_errors={row['total_high_risk_multiclass_error_count']}"
        )


if __name__ == "__main__":
    main()