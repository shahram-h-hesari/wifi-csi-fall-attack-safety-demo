from pathlib import Path
import csv


BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
NOTES_DIR = BASE_DIR / "notes"

SAFETY_INPUT_CSV = RESULTS_DIR / "defended_vs_undefended_safety_comparison.csv"
CONFIDENCE_INPUT_CSV = RESULTS_DIR / "thesis_table_12_model_confidence_error_summary.csv"
RANKING_INPUT_CSV = RESULTS_DIR / "thesis_table_13_confidence_safety_failure_ranking.csv"

OUTPUT_CSV = RESULTS_DIR / "thesis_table_14_matched_attack_defense_effect_summary.csv"
OUTPUT_NOTE = NOTES_DIR / "thesis_table_14_matched_attack_defense_effect_summary.md"

CLAIM_BOUNDARY = (
    "Research implementation only; matched window-level attack-defense effect summary; "
    "defense effects are descriptive clean-to-attacked and undefended-to-defended comparisons, "
    "not clinical effectiveness claims; model confidence means predicted-class probability/confidence "
    "from the model output, not calibrated clinical confidence; software-level processed-tensor "
    "perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, "
    "not real patient deployment, not regulatory evaluation, not event-level fall validation, "
    "not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, "
    "and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation."
)

MATCHED_ATTACK_PAIRS = [
    {
        "attack_type": "FGSM",
        "epsilon": "0.030000",
        "undefended_condition": "undefended_fgsm_epsilon_0_03",
        "defended_condition": "defended_fgsm_epsilon_0_03",
        "display_pair": "Undefended FGSM vs Defended FGSM",
    },
    {
        "attack_type": "PGD",
        "epsilon": "0.030000",
        "undefended_condition": "undefended_pgd_epsilon_0_03",
        "defended_condition": "defended_pgd_epsilon_0_03",
        "display_pair": "Undefended PGD vs Defended PGD",
    },
]


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


def fmt_percent(value):
    if value is None:
        return "NA"
    return f"{value:.2f}%"


def fmt_count(value):
    if value is None:
        return "NA"
    return str(int(round(value)))


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")

    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def percent_reduction(original_value, new_value):
    if original_value is None or new_value is None:
        return None
    if original_value == 0:
        return None
    return ((original_value - new_value) / original_value) * 100.0


def absolute_reduction(original_value, new_value):
    if original_value is None or new_value is None:
        return None
    return original_value - new_value


def absolute_change(new_value, original_value):
    if original_value is None or new_value is None:
        return None
    return new_value - original_value


def build_lookup_tables():
    safety_rows = read_csv(SAFETY_INPUT_CSV)
    confidence_rows = read_csv(CONFIDENCE_INPUT_CSV)
    ranking_rows = read_csv(RANKING_INPUT_CSV)

    safety_by_condition = {row["condition"]: row for row in safety_rows}

    missed_confidence_by_condition = {
        row["condition"]: row
        for row in confidence_rows
        if row["window_group"] == "missed_fall_windows"
    }

    ranking_by_condition = {
        row["condition"]: row
        for row in ranking_rows
    }

    return safety_by_condition, missed_confidence_by_condition, ranking_by_condition


def get_condition_metrics(condition, safety_by_condition, missed_confidence_by_condition, ranking_by_condition):
    if condition not in safety_by_condition:
        raise ValueError(f"Missing safety row for {condition}")
    if condition not in missed_confidence_by_condition:
        raise ValueError(f"Missing missed-fall confidence row for {condition}")
    if condition not in ranking_by_condition:
        raise ValueError(f"Missing confidence-safety ranking row for {condition}")

    safety_row = safety_by_condition[condition]
    confidence_row = missed_confidence_by_condition[condition]
    ranking_row = ranking_by_condition[condition]

    return {
        "condition": condition,
        "display_condition": ranking_row["display_condition"],
        "missed_fall_rate": safe_float(safety_row["missed_fall_rate"]),
        "missed_fall_windows": safe_int(confidence_row["n_windows"]),
        "false_fall_alarm_count": safe_int(safety_row["FP_false_fall_alarms"]),
        "recall_sensitivity": safe_float(safety_row["recall_sensitivity"]),
        "f1_score": safe_float(safety_row["f1_score"]),
        "balanced_accuracy": safe_float(safety_row["balanced_accuracy"]),
        "mean_missed_fall_confidence": safe_float(confidence_row["mean_prediction_confidence"]),
        "median_missed_fall_confidence": safe_float(confidence_row["median_prediction_confidence"]),
        "high_confidence_missed_fall_count": safe_int(confidence_row["high_confidence_count"]),
        "high_confidence_missed_fall_rate": safe_float(confidence_row["high_confidence_rate"]),
        "confidence_safety_failure_score": safe_float(ranking_row["confidence_safety_failure_score"]),
    }


def build_output_rows():
    safety_by_condition, missed_confidence_by_condition, ranking_by_condition = build_lookup_tables()

    output_rows = []

    for pair in MATCHED_ATTACK_PAIRS:
        undefended = get_condition_metrics(
            pair["undefended_condition"],
            safety_by_condition,
            missed_confidence_by_condition,
            ranking_by_condition,
        )

        defended = get_condition_metrics(
            pair["defended_condition"],
            safety_by_condition,
            missed_confidence_by_condition,
            ranking_by_condition,
        )

        missed_fall_rate_change = absolute_change(
            defended["missed_fall_rate"],
            undefended["missed_fall_rate"],
        )

        high_confidence_rate_reduction = absolute_reduction(
            undefended["high_confidence_missed_fall_rate"],
            defended["high_confidence_missed_fall_rate"],
        )

        high_confidence_rate_percent_reduction = percent_reduction(
            undefended["high_confidence_missed_fall_rate"],
            defended["high_confidence_missed_fall_rate"],
        )

        score_reduction = absolute_reduction(
            undefended["confidence_safety_failure_score"],
            defended["confidence_safety_failure_score"],
        )

        score_percent_reduction = percent_reduction(
            undefended["confidence_safety_failure_score"],
            defended["confidence_safety_failure_score"],
        )

        mean_confidence_reduction = absolute_reduction(
            undefended["mean_missed_fall_confidence"],
            defended["mean_missed_fall_confidence"],
        )

        median_confidence_reduction = absolute_reduction(
            undefended["median_missed_fall_confidence"],
            defended["median_missed_fall_confidence"],
        )

        false_alarm_reduction = absolute_reduction(
            undefended["false_fall_alarm_count"],
            defended["false_fall_alarm_count"],
        )

        recall_change = absolute_change(
            defended["recall_sensitivity"],
            undefended["recall_sensitivity"],
        )

        f1_change = absolute_change(
            defended["f1_score"],
            undefended["f1_score"],
        )

        balanced_accuracy_change = absolute_change(
            defended["balanced_accuracy"],
            undefended["balanced_accuracy"],
        )

        if (
            undefended["missed_fall_rate"] == defended["missed_fall_rate"]
            and defended["missed_fall_rate"] == 1.0
            and high_confidence_rate_reduction is not None
            and high_confidence_rate_reduction > 0
        ):
            interpretation = (
                "Defense reduced overconfident missed-fall behavior but did not restore fall recall."
            )
        else:
            interpretation = (
                "Defense effect requires careful condition-specific interpretation."
            )

        output_rows.append(
            {
                "attack_type": pair["attack_type"],
                "epsilon": pair["epsilon"],
                "matched_pair": pair["display_pair"],
                "undefended_condition": undefended["display_condition"],
                "defended_condition": defended["display_condition"],
                "undefended_missed_fall_rate": fmt(undefended["missed_fall_rate"]),
                "defended_missed_fall_rate": fmt(defended["missed_fall_rate"]),
                "missed_fall_rate_change_defended_minus_undefended": fmt(missed_fall_rate_change),
                "undefended_missed_fall_windows": undefended["missed_fall_windows"],
                "defended_missed_fall_windows": defended["missed_fall_windows"],
                "undefended_high_confidence_missed_fall_rate": fmt(undefended["high_confidence_missed_fall_rate"]),
                "defended_high_confidence_missed_fall_rate": fmt(defended["high_confidence_missed_fall_rate"]),
                "high_confidence_missed_fall_rate_reduction": fmt(high_confidence_rate_reduction),
                "high_confidence_missed_fall_rate_percent_reduction": fmt_percent(high_confidence_rate_percent_reduction),
                "undefended_confidence_safety_failure_score": fmt(undefended["confidence_safety_failure_score"]),
                "defended_confidence_safety_failure_score": fmt(defended["confidence_safety_failure_score"]),
                "confidence_safety_failure_score_reduction": fmt(score_reduction),
                "confidence_safety_failure_score_percent_reduction": fmt_percent(score_percent_reduction),
                "undefended_mean_missed_fall_confidence": fmt(undefended["mean_missed_fall_confidence"]),
                "defended_mean_missed_fall_confidence": fmt(defended["mean_missed_fall_confidence"]),
                "mean_missed_fall_confidence_reduction": fmt(mean_confidence_reduction),
                "undefended_median_missed_fall_confidence": fmt(undefended["median_missed_fall_confidence"]),
                "defended_median_missed_fall_confidence": fmt(defended["median_missed_fall_confidence"]),
                "median_missed_fall_confidence_reduction": fmt(median_confidence_reduction),
                "undefended_false_fall_alarm_count": undefended["false_fall_alarm_count"],
                "defended_false_fall_alarm_count": defended["false_fall_alarm_count"],
                "false_fall_alarm_count_reduction": fmt_count(false_alarm_reduction),
                "undefended_recall_sensitivity": fmt(undefended["recall_sensitivity"]),
                "defended_recall_sensitivity": fmt(defended["recall_sensitivity"]),
                "recall_change_defended_minus_undefended": fmt(recall_change),
                "undefended_f1_score": fmt(undefended["f1_score"]),
                "defended_f1_score": fmt(defended["f1_score"]),
                "f1_score_change_defended_minus_undefended": fmt(f1_change),
                "undefended_balanced_accuracy": fmt(undefended["balanced_accuracy"]),
                "defended_balanced_accuracy": fmt(defended["balanced_accuracy"]),
                "balanced_accuracy_change_defended_minus_undefended": fmt(balanced_accuracy_change),
                "interpretation": interpretation,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    return output_rows


def write_csv(rows):
    fieldnames = list(rows[0].keys())

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_note(rows):
    lines = []

    lines.append("# Thesis Table 14: Matched Attack Defense Effect Summary")
    lines.append("")
    lines.append("This table compares matched undefended and defended attack conditions to summarize the observed defense effect.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Output File")
    lines.append("")
    lines.append("- `results/thesis_table_14_matched_attack_defense_effect_summary.csv`")
    lines.append("")
    lines.append("## Input Files")
    lines.append("")
    lines.append("- `results/defended_vs_undefended_safety_comparison.csv`")
    lines.append("- `results/thesis_table_12_model_confidence_error_summary.csv`")
    lines.append("- `results/thesis_table_13_confidence_safety_failure_ranking.csv`")
    lines.append("")
    lines.append("## Matched Comparisons")
    lines.append("")
    lines.append("```text")
    lines.append("Undefended FGSM epsilon 0.03 vs Defended FGSM epsilon 0.03")
    lines.append("Undefended PGD epsilon 0.03 vs Defended PGD epsilon 0.03")
    lines.append("```")
    lines.append("")
    lines.append("## Summary Table")
    lines.append("")
    lines.append("| Attack | Missed Fall Rate Undefended -> Defended | High-Confidence Missed-Fall Rate Undefended -> Defended | Failure Score Undefended -> Defended | False Fall Alarms Undefended -> Defended | Interpretation |")
    lines.append("|---|---:|---:|---:|---:|---|")

    for row in rows:
        lines.append(
            f"| {row['attack_type']} "
            f"| {row['undefended_missed_fall_rate']} -> {row['defended_missed_fall_rate']} "
            f"| {row['undefended_high_confidence_missed_fall_rate']} -> {row['defended_high_confidence_missed_fall_rate']} "
            f"| {row['undefended_confidence_safety_failure_score']} -> {row['defended_confidence_safety_failure_score']} "
            f"| {row['undefended_false_fall_alarm_count']} -> {row['defended_false_fall_alarm_count']} "
            f"| {row['interpretation']} |"
        )

    lines.append("")
    lines.append("## Main Defense-Effect Details")
    lines.append("")

    for row in rows:
        lines.append(f"### {row['attack_type']} epsilon 0.03")
        lines.append("")
        lines.append("```text")
        lines.append(f"missed fall rate change = {row['missed_fall_rate_change_defended_minus_undefended']}")
        lines.append(f"high-confidence missed-fall rate reduction = {row['high_confidence_missed_fall_rate_reduction']}")
        lines.append(f"high-confidence missed-fall rate percent reduction = {row['high_confidence_missed_fall_rate_percent_reduction']}")
        lines.append(f"confidence-safety failure score reduction = {row['confidence_safety_failure_score_reduction']}")
        lines.append(f"confidence-safety failure score percent reduction = {row['confidence_safety_failure_score_percent_reduction']}")
        lines.append(f"mean missed-fall confidence reduction = {row['mean_missed_fall_confidence_reduction']}")
        lines.append(f"median missed-fall confidence reduction = {row['median_missed_fall_confidence_reduction']}")
        lines.append(f"false fall alarm count reduction = {row['false_fall_alarm_count_reduction']}")
        lines.append(f"recall change = {row['recall_change_defended_minus_undefended']}")
        lines.append(f"F1-score change = {row['f1_score_change_defended_minus_undefended']}")
        lines.append(f"balanced accuracy change = {row['balanced_accuracy_change_defended_minus_undefended']}")
        lines.append("```")
        lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append("Table 14 directly compares matched attack conditions. In both FGSM and PGD cases, the defended model does not restore fall recall because missed fall rate remains 1.000000. However, the defended attacked conditions have much lower high-confidence missed-fall rates and lower confidence-safety failure scores than the corresponding undefended attacked conditions.")
    lines.append("")
    lines.append("This supports a careful thesis statement: the short defended model reduced overconfident missed-fall behavior, but it did not restore window-level fall-detection safety performance.")
    lines.append("")
    lines.append("This table should not be interpreted as clinical defense effectiveness, medical-device validation, event-level fall-risk reduction, time-to-alarm improvement, or physical-world attack mitigation.")

    OUTPUT_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rows = build_output_rows()
    write_csv(rows)
    write_note(rows)

    print("Created Thesis Table 14 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Table 14 summarizes matched attack-defense effects for:")
    print("  FGSM epsilon 0.03")
    print("  PGD epsilon 0.03")


if __name__ == "__main__":
    main()