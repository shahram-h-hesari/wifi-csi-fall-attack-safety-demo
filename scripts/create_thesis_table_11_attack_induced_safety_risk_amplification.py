from pathlib import Path
import csv


BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
NOTES_DIR = BASE_DIR / "notes"

INPUT_CSV = RESULTS_DIR / "defended_vs_undefended_safety_comparison.csv"
OUTPUT_CSV = RESULTS_DIR / "thesis_table_11_attack_induced_safety_risk_amplification.csv"
OUTPUT_NOTE = NOTES_DIR / "thesis_table_11_attack_induced_safety_risk_amplification.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level safety-risk amplification ratios; "
    "software-level processed-tensor perturbations only; not clinical validation, "
    "not medical-device validation, not diagnostic evidence, not real patient deployment, "
    "not regulatory evaluation, not event-level fall validation, not long-lie validation, "
    "not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / "
    "SDR / over-the-air validation."
)

REFERENCE_CONDITION = "undefended_clean"

ORDER = [
    "undefended_clean",
    "undefended_fgsm_epsilon_0_03",
    "undefended_pgd_epsilon_0_03",
    "defended_clean",
    "defended_fgsm_epsilon_0_03",
    "defended_pgd_epsilon_0_03",
]

DISPLAY_NAMES = {
    "undefended_clean": "Undefended clean reference",
    "undefended_fgsm_epsilon_0_03": "Undefended FGSM epsilon 0.03",
    "undefended_pgd_epsilon_0_03": "Undefended PGD epsilon 0.03",
    "defended_clean": "Defended clean",
    "defended_fgsm_epsilon_0_03": "Defended FGSM epsilon 0.03",
    "defended_pgd_epsilon_0_03": "Defended PGD epsilon 0.03",
}


def safe_float(value):
    if value is None or value == "":
        return None
    return float(value)


def safe_int(value):
    if value is None or value == "":
        return 0
    return int(float(value))


def safe_div(numerator, denominator):
    if denominator is None or denominator == 0:
        return None
    if numerator is None:
        return None
    return numerator / denominator


def format_number(value, digits=6):
    if value is None:
        return "NA"
    return f"{value:.{digits}f}"


def load_rows():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_CSV}")

    with INPUT_CSV.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    by_condition = {row["condition"]: row for row in rows}
    missing = [condition for condition in ORDER if condition not in by_condition]

    if missing:
        raise ValueError(f"Missing expected conditions in input CSV: {missing}")

    if REFERENCE_CONDITION not in by_condition:
        raise ValueError(f"Missing reference condition: {REFERENCE_CONDITION}")

    return by_condition


def make_output_rows(by_condition):
    reference = by_condition[REFERENCE_CONDITION]

    ref_missed_fall_rate = safe_float(reference["missed_fall_rate"])
    ref_false_alarm_count = safe_int(reference["FP_false_fall_alarms"])
    ref_recall = safe_float(reference["recall_sensitivity"])
    ref_f1 = safe_float(reference["f1_score"])
    ref_balanced_accuracy = safe_float(reference["balanced_accuracy"])

    output_rows = []

    for condition in ORDER:
        row = by_condition[condition]

        missed_fall_rate = safe_float(row["missed_fall_rate"])
        false_alarm_count = safe_int(row["FP_false_fall_alarms"])
        recall = safe_float(row["recall_sensitivity"])
        f1 = safe_float(row["f1_score"])
        balanced_accuracy = safe_float(row["balanced_accuracy"])

        missed_fall_rate_ratio = safe_div(missed_fall_rate, ref_missed_fall_rate)
        false_alarm_count_ratio = safe_div(false_alarm_count, ref_false_alarm_count)
        recall_retention = safe_div(recall, ref_recall)
        f1_retention = safe_div(f1, ref_f1)
        balanced_accuracy_retention = safe_div(balanced_accuracy, ref_balanced_accuracy)

        output_rows.append(
            {
                "condition": condition,
                "display_condition": DISPLAY_NAMES.get(condition, condition),
                "reference_condition": REFERENCE_CONDITION,
                "model_type": row["model_type"],
                "attack_type": row["attack_type"],
                "epsilon": format_number(safe_float(row["epsilon"])),
                "missed_fall_rate": format_number(missed_fall_rate),
                "reference_missed_fall_rate": format_number(ref_missed_fall_rate),
                "missed_fall_rate_ratio_vs_undefended_clean": format_number(missed_fall_rate_ratio),
                "false_alarm_count": false_alarm_count,
                "reference_false_alarm_count": ref_false_alarm_count,
                "false_alarm_count_ratio_vs_undefended_clean": format_number(false_alarm_count_ratio),
                "recall_sensitivity": format_number(recall),
                "reference_recall_sensitivity": format_number(ref_recall),
                "recall_retention_vs_undefended_clean": format_number(recall_retention),
                "f1_score": format_number(f1),
                "reference_f1_score": format_number(ref_f1),
                "f1_retention_vs_undefended_clean": format_number(f1_retention),
                "balanced_accuracy": format_number(balanced_accuracy),
                "reference_balanced_accuracy": format_number(ref_balanced_accuracy),
                "balanced_accuracy_retention_vs_undefended_clean": format_number(balanced_accuracy_retention),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    return output_rows


def write_csv(output_rows):
    fieldnames = list(output_rows[0].keys())

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)


def write_note(output_rows):
    lines = []

    lines.append("# Thesis Table 11: Attack-Induced Safety Risk Amplification Ratios")
    lines.append("")
    lines.append("This table translates clean-to-attacked and clean-to-defended changes into window-level safety-risk amplification and retention ratios.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Input File")
    lines.append("")
    lines.append("- `results/defended_vs_undefended_safety_comparison.csv`")
    lines.append("")
    lines.append("## Output File")
    lines.append("")
    lines.append("- `results/thesis_table_11_attack_induced_safety_risk_amplification.csv`")
    lines.append("")
    lines.append("## Reference Condition")
    lines.append("")
    lines.append("All ratios are computed relative to the undefended clean baseline.")
    lines.append("")
    lines.append("```text")
    lines.append("reference condition = undefended clean")
    lines.append("reference missed fall rate = 0.359551")
    lines.append("reference false fall alarm count = 32")
    lines.append("reference recall/sensitivity = 0.640449")
    lines.append("reference F1-score = 0.640449")
    lines.append("reference balanced accuracy = 0.802584")
    lines.append("```")
    lines.append("")
    lines.append("## Ratio Definitions")
    lines.append("")
    lines.append("```text")
    lines.append("missed fall rate ratio = condition missed fall rate / clean missed fall rate")
    lines.append("false alarm count ratio = condition false alarm count / clean false alarm count")
    lines.append("recall retention = condition recall / clean recall")
    lines.append("F1 retention = condition F1-score / clean F1-score")
    lines.append("balanced accuracy retention = condition balanced accuracy / clean balanced accuracy")
    lines.append("```")
    lines.append("")
    lines.append("## Table Preview")
    lines.append("")
    lines.append("| Condition | Missed Fall Ratio | False Alarm Ratio | Recall Retention | F1 Retention | Balanced Accuracy Retention |")
    lines.append("|---|---:|---:|---:|---:|---:|")

    for row in output_rows:
        lines.append(
            f"| {row['display_condition']} "
            f"| {row['missed_fall_rate_ratio_vs_undefended_clean']} "
            f"| {row['false_alarm_count_ratio_vs_undefended_clean']} "
            f"| {row['recall_retention_vs_undefended_clean']} "
            f"| {row['f1_retention_vs_undefended_clean']} "
            f"| {row['balanced_accuracy_retention_vs_undefended_clean']} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("Table 11 provides a compact way to describe how much safety-relevant risk increases or useful performance is retained relative to the undefended clean baseline.")
    lines.append("")
    lines.append("A missed fall rate ratio above 1.0 means the condition has more missed fall behavior than the clean baseline. A recall, F1, or balanced accuracy retention below 1.0 means the condition retains less of the clean baseline performance.")
    lines.append("")
    lines.append("The attacked conditions show severe missed-fall amplification because the missed fall rate increases from the clean baseline value of 0.359551 to 1.000000 under FGSM and PGD at epsilon 0.030. The defended attacked conditions reduce false fall alarm burden relative to the undefended attacked conditions, but still do not recover fall recall at epsilon 0.030.")
    lines.append("")
    lines.append("These ratios should be interpreted as window-level safety-proxy ratios, not clinical risk ratios, event-level fall rates, or medical-device validation metrics.")

    OUTPUT_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    by_condition = load_rows()
    output_rows = make_output_rows(by_condition)
    write_csv(output_rows)
    write_note(output_rows)

    print("Created Thesis Table 11 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Table 11 computes ratios relative to:")
    print("  undefended clean baseline")


if __name__ == "__main__":
    main()