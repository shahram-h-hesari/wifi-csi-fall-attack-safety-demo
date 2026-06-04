from pathlib import Path
import csv


BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
NOTES_DIR = BASE_DIR / "notes"

SAFETY_INPUT_CSV = RESULTS_DIR / "defended_vs_undefended_safety_comparison.csv"
CONFIDENCE_INPUT_CSV = RESULTS_DIR / "thesis_table_12_model_confidence_error_summary.csv"

OUTPUT_CSV = RESULTS_DIR / "thesis_table_13_confidence_safety_failure_ranking.csv"
OUTPUT_NOTE = NOTES_DIR / "thesis_table_13_confidence_safety_failure_ranking.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level confidence-safety failure ranking; "
    "the confidence-safety failure score is a descriptive product of missed fall rate and "
    "high-confidence missed-fall rate, not a clinical risk score; model confidence means "
    "predicted-class probability/confidence from the model output, not calibrated clinical confidence; "
    "software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, "
    "not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, "
    "not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, and not physical-layer / "
    "packet-level / preamble-level / SDR / over-the-air validation."
)

CONDITION_ORDER = [
    "undefended_clean",
    "undefended_fgsm_epsilon_0_03",
    "undefended_pgd_epsilon_0_03",
    "defended_clean",
    "defended_fgsm_epsilon_0_03",
    "defended_pgd_epsilon_0_03",
]

DISPLAY_NAMES = {
    "undefended_clean": "Undefended clean",
    "undefended_fgsm_epsilon_0_03": "Undefended FGSM epsilon 0.03",
    "undefended_pgd_epsilon_0_03": "Undefended PGD epsilon 0.03",
    "defended_clean": "Defended clean",
    "defended_fgsm_epsilon_0_03": "Defended FGSM epsilon 0.03",
    "defended_pgd_epsilon_0_03": "Defended PGD epsilon 0.03",
}


def safe_float(value):
    if value is None or value == "" or value == "NA":
        return None
    return float(value)


def safe_int(value):
    if value is None or value == "" or value == "NA":
        return 0
    return int(float(value))


def fmt(value):
    if value is None:
        return "NA"
    return f"{value:.6f}"


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")

    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_rows():
    safety_rows = read_csv(SAFETY_INPUT_CSV)
    confidence_rows = read_csv(CONFIDENCE_INPUT_CSV)

    safety_by_condition = {row["condition"]: row for row in safety_rows}

    missed_confidence_by_condition = {
        row["condition"]: row
        for row in confidence_rows
        if row["window_group"] == "missed_fall_windows"
    }

    output_rows = []

    for condition in CONDITION_ORDER:
        if condition not in safety_by_condition:
            raise ValueError(f"Missing safety row for {condition}")

        if condition not in missed_confidence_by_condition:
            raise ValueError(f"Missing missed-fall confidence row for {condition}")

        safety_row = safety_by_condition[condition]
        confidence_row = missed_confidence_by_condition[condition]

        missed_fall_rate = safe_float(safety_row["missed_fall_rate"])
        false_alarm_count = safe_int(safety_row["FP_false_fall_alarms"])
        recall = safe_float(safety_row["recall_sensitivity"])
        f1_score = safe_float(safety_row["f1_score"])
        balanced_accuracy = safe_float(safety_row["balanced_accuracy"])

        missed_fall_windows = safe_int(confidence_row["n_windows"])
        mean_confidence = safe_float(confidence_row["mean_prediction_confidence"])
        median_confidence = safe_float(confidence_row["median_prediction_confidence"])
        high_confidence_count = safe_int(confidence_row["high_confidence_count"])
        high_confidence_rate = safe_float(confidence_row["high_confidence_rate"])

        confidence_safety_failure_score = None
        if missed_fall_rate is not None and high_confidence_rate is not None:
            confidence_safety_failure_score = missed_fall_rate * high_confidence_rate

        output_rows.append(
            {
                "condition": condition,
                "display_condition": DISPLAY_NAMES[condition],
                "missed_fall_rate": fmt(missed_fall_rate),
                "missed_fall_windows": missed_fall_windows,
                "high_confidence_missed_fall_count": high_confidence_count,
                "high_confidence_missed_fall_rate": fmt(high_confidence_rate),
                "mean_missed_fall_confidence": fmt(mean_confidence),
                "median_missed_fall_confidence": fmt(median_confidence),
                "confidence_safety_failure_score": fmt(confidence_safety_failure_score),
                "false_fall_alarm_count": false_alarm_count,
                "recall_sensitivity": fmt(recall),
                "f1_score": fmt(f1_score),
                "balanced_accuracy": fmt(balanced_accuracy),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    ranked_rows = sorted(
        output_rows,
        key=lambda row: (
            -safe_float(row["confidence_safety_failure_score"]),
            -safe_float(row["missed_fall_rate"]),
            -safe_float(row["high_confidence_missed_fall_rate"]),
        ),
    )

    for rank, row in enumerate(ranked_rows, start=1):
        row["rank_by_confidence_safety_failure_score"] = rank

    field_order = [
        "rank_by_confidence_safety_failure_score",
        "condition",
        "display_condition",
        "missed_fall_rate",
        "missed_fall_windows",
        "high_confidence_missed_fall_count",
        "high_confidence_missed_fall_rate",
        "mean_missed_fall_confidence",
        "median_missed_fall_confidence",
        "confidence_safety_failure_score",
        "false_fall_alarm_count",
        "recall_sensitivity",
        "f1_score",
        "balanced_accuracy",
        "claim_boundary",
    ]

    return [
        {field: row[field] for field in field_order}
        for row in ranked_rows
    ]


def write_csv(rows):
    fieldnames = list(rows[0].keys())

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_note(rows):
    lines = []

    lines.append("# Thesis Table 13: Confidence-Safety Failure Ranking")
    lines.append("")
    lines.append("This table ranks clean, attacked, and defended conditions by a descriptive window-level confidence-safety failure score.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Output File")
    lines.append("")
    lines.append("- `results/thesis_table_13_confidence_safety_failure_ranking.csv`")
    lines.append("")
    lines.append("## Input Files")
    lines.append("")
    lines.append("- `results/defended_vs_undefended_safety_comparison.csv`")
    lines.append("- `results/thesis_table_12_model_confidence_error_summary.csv`")
    lines.append("")
    lines.append("## Descriptive Score Definition")
    lines.append("")
    lines.append("```text")
    lines.append("confidence-safety failure score = missed fall rate * high-confidence missed-fall rate")
    lines.append("```")
    lines.append("")
    lines.append("This score is a descriptive ranking score only. It is not a clinical risk score, diagnostic score, regulatory score, calibrated confidence score, or medical-device safety score.")
    lines.append("")
    lines.append("## Ranked Table Preview")
    lines.append("")
    lines.append("| Rank | Condition | Missed Fall Rate | High-Confidence Missed-Fall Rate | Failure Score | Recall | F1-score | Balanced Accuracy |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|---:|")

    for row in rows:
        lines.append(
            f"| {row['rank_by_confidence_safety_failure_score']} "
            f"| {row['display_condition']} "
            f"| {row['missed_fall_rate']} "
            f"| {row['high_confidence_missed_fall_rate']} "
            f"| {row['confidence_safety_failure_score']} "
            f"| {row['recall_sensitivity']} "
            f"| {row['f1_score']} "
            f"| {row['balanced_accuracy']} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("Table 13 provides a ranked numeric companion to Figure 12. It identifies conditions that combine missed-fall safety failure with high model-reported confidence in the wrong prediction.")
    lines.append("")
    lines.append("The undefended PGD condition ranks highest because it has missed fall rate 1.000000 and high-confidence missed-fall rate 0.820225, producing the largest confidence-safety failure score.")
    lines.append("")
    lines.append("The undefended FGSM condition ranks second because it also misses all 89 fall windows but has a lower high-confidence missed-fall rate than PGD.")
    lines.append("")
    lines.append("The defended attacked conditions still miss all 89 fall windows, but they rank lower because their high-confidence missed-fall rates are much lower than the undefended attacked conditions. This supports the careful interpretation that the short defended model reduced overconfident missed-fall behavior but did not restore fall-detection safety performance.")
    lines.append("")
    lines.append("This table should be interpreted as a window-level descriptive ranking only. It does not estimate clinical risk, event-level fall risk, long-lie risk, time-to-alarm risk, or medical-device safety.")

    OUTPUT_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rows = build_rows()
    write_csv(rows)
    write_note(rows)

    print("Created Thesis Table 13 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Table 13 ranks conditions by:")
    print("  confidence-safety failure score = missed fall rate * high-confidence missed-fall rate")


if __name__ == "__main__":
    main()
