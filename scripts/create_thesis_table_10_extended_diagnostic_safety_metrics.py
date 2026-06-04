from pathlib import Path
import csv
import math

BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
NOTES_DIR = BASE_DIR / "notes"

INPUT_CSV = RESULTS_DIR / "defended_vs_undefended_safety_comparison.csv"
OUTPUT_CSV = RESULTS_DIR / "thesis_table_10_extended_diagnostic_safety_metrics.csv"
OUTPUT_NOTE = NOTES_DIR / "thesis_table_10_extended_diagnostic_safety_metrics.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level diagnostic-style safety-proxy metrics; "
    "software-level processed-tensor perturbations only; not clinical validation, "
    "not medical-device validation, not diagnostic evidence, not real patient deployment, "
    "not regulatory evaluation, not event-level fall validation, not long-lie validation, "
    "not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / "
    "SDR / over-the-air validation."
)

DISPLAY_NAMES = {
    "undefended_clean": "Undefended clean",
    "undefended_fgsm_epsilon_0_03": "Undefended FGSM epsilon 0.03",
    "undefended_pgd_epsilon_0_03": "Undefended PGD epsilon 0.03",
    "defended_clean": "Defended clean",
    "defended_fgsm_epsilon_0_03": "Defended FGSM epsilon 0.03",
    "defended_pgd_epsilon_0_03": "Defended PGD epsilon 0.03",
}

ORDER = [
    "undefended_clean",
    "undefended_fgsm_epsilon_0_03",
    "undefended_pgd_epsilon_0_03",
    "defended_clean",
    "defended_fgsm_epsilon_0_03",
    "defended_pgd_epsilon_0_03",
]


def safe_float(value):
    if value is None or value == "":
        return None
    return float(value)


def safe_int(value):
    if value is None or value == "":
        return 0
    return int(float(value))


def safe_div(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator


def safe_round(value, digits=6):
    if value is None:
        return "NA"
    if isinstance(value, float):
        if math.isinf(value):
            return "INF"
        if math.isnan(value):
            return "NA"
    return f"{value:.{digits}f}"


def compute_metrics(row):
    tp = safe_int(row["TP_detected_falls"])
    fn = safe_int(row["FN_missed_falls"])
    fp = safe_int(row["FP_false_fall_alarms"])
    tn = safe_int(row["TN_correct_non_falls"])

    total = tp + fn + fp + tn
    actual_fall = tp + fn
    actual_nonfall = fp + tn
    predicted_fall = tp + fp
    predicted_nonfall = fn + tn

    sensitivity = safe_div(tp, actual_fall)
    specificity = safe_div(tn, actual_nonfall)
    false_positive_rate = safe_div(fp, actual_nonfall)

    negative_predictive_value = safe_div(tn, tn + fn)
    false_omission_rate = safe_div(fn, fn + tn)
    false_discovery_rate = safe_div(fp, fp + tp)

    positive_likelihood_ratio = None
    if sensitivity is not None and false_positive_rate is not None:
        if false_positive_rate == 0:
            positive_likelihood_ratio = math.inf if sensitivity > 0 else None
        else:
            positive_likelihood_ratio = sensitivity / false_positive_rate

    negative_likelihood_ratio = None
    if sensitivity is not None and specificity is not None:
        if specificity == 0:
            negative_likelihood_ratio = math.inf if (1 - sensitivity) > 0 else None
        else:
            negative_likelihood_ratio = (1 - sensitivity) / specificity

    diagnostic_odds_ratio = None
    dor_denominator = fp * fn
    if dor_denominator == 0:
        if tp * tn > 0:
            diagnostic_odds_ratio = math.inf
        else:
            diagnostic_odds_ratio = None
    else:
        diagnostic_odds_ratio = (tp * tn) / dor_denominator

    mcc_denominator = math.sqrt(
        (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    )
    matthews_correlation_coefficient = safe_div(
        (tp * tn) - (fp * fn),
        mcc_denominator,
    )

    observed_agreement = safe_div(tp + tn, total)

    expected_agreement = None
    if total > 0:
        expected_agreement = (
            ((actual_fall / total) * (predicted_fall / total))
            + ((actual_nonfall / total) * (predicted_nonfall / total))
        )

    cohens_kappa = None
    if observed_agreement is not None and expected_agreement is not None:
        if (1 - expected_agreement) != 0:
            cohens_kappa = (observed_agreement - expected_agreement) / (1 - expected_agreement)

    fall_window_prevalence = safe_div(actual_fall, total)
    false_alarm_to_detected_fall_ratio = safe_div(fp, tp)
    missed_fall_to_detected_fall_ratio = safe_div(fn, tp)

    return {
        "condition": row["condition"],
        "display_condition": DISPLAY_NAMES.get(row["condition"], row["condition"]),
        "model_type": row["model_type"],
        "attack_type": row["attack_type"],
        "epsilon": safe_round(safe_float(row["epsilon"]), 6),
        "total_windows": total,
        "fall_windows": actual_fall,
        "non_fall_windows": actual_nonfall,
        "TP_detected_falls": tp,
        "FN_missed_falls": fn,
        "FP_false_fall_alarms": fp,
        "TN_correct_non_falls": tn,
        "negative_predictive_value": safe_round(negative_predictive_value),
        "false_omission_rate": safe_round(false_omission_rate),
        "false_discovery_rate": safe_round(false_discovery_rate),
        "positive_likelihood_ratio": safe_round(positive_likelihood_ratio),
        "negative_likelihood_ratio": safe_round(negative_likelihood_ratio),
        "diagnostic_odds_ratio": safe_round(diagnostic_odds_ratio),
        "matthews_correlation_coefficient": safe_round(matthews_correlation_coefficient),
        "cohens_kappa": safe_round(cohens_kappa),
        "fall_window_prevalence": safe_round(fall_window_prevalence),
        "false_alarm_to_detected_fall_ratio": safe_round(false_alarm_to_detected_fall_ratio),
        "missed_fall_to_detected_fall_ratio": safe_round(missed_fall_to_detected_fall_ratio),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_CSV}")

    with INPUT_CSV.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    by_condition = {row["condition"]: row for row in rows}

    missing = [condition for condition in ORDER if condition not in by_condition]
    if missing:
        raise ValueError(f"Missing expected conditions in input CSV: {missing}")

    output_rows = [compute_metrics(by_condition[condition]) for condition in ORDER]

    fieldnames = list(output_rows[0].keys())

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    markdown_lines = []
    markdown_lines.append("# Thesis Table 10: Extended Window-Level Diagnostic Safety Metrics")
    markdown_lines.append("")
    markdown_lines.append("This table reports additional diagnostic-style safety-proxy metrics computed from the binary fall-vs-non-fall confusion matrix for clean, attacked, and defended conditions.")
    markdown_lines.append("")
    markdown_lines.append("## Claim Boundary")
    markdown_lines.append("")
    markdown_lines.append(CLAIM_BOUNDARY)
    markdown_lines.append("")
    markdown_lines.append("## Input File")
    markdown_lines.append("")
    markdown_lines.append("- `results/defended_vs_undefended_safety_comparison.csv`")
    markdown_lines.append("")
    markdown_lines.append("## Output File")
    markdown_lines.append("")
    markdown_lines.append("- `results/thesis_table_10_extended_diagnostic_safety_metrics.csv`")
    markdown_lines.append("")
    markdown_lines.append("## Metrics")
    markdown_lines.append("")
    markdown_lines.append("The table includes:")
    markdown_lines.append("")
    markdown_lines.append("```text")
    markdown_lines.append("negative predictive value")
    markdown_lines.append("false omission rate")
    markdown_lines.append("false discovery rate")
    markdown_lines.append("positive likelihood ratio")
    markdown_lines.append("negative likelihood ratio")
    markdown_lines.append("diagnostic odds ratio")
    markdown_lines.append("Matthews correlation coefficient")
    markdown_lines.append("Cohen's kappa")
    markdown_lines.append("fall-window prevalence")
    markdown_lines.append("false-alarm-to-detected-fall ratio")
    markdown_lines.append("missed-fall-to-detected-fall ratio")
    markdown_lines.append("```")
    markdown_lines.append("")
    markdown_lines.append("## Interpretation")
    markdown_lines.append("")
    markdown_lines.append("Table 10 strengthens the thesis by adding diagnostic-style window-level metrics beyond recall, precision, F1-score, and balanced accuracy. These metrics help explain whether the model is becoming less trustworthy when it predicts non-fall, whether fall alerts are more likely to be false, and whether attacks cause asymmetric safety burden.")
    markdown_lines.append("")
    markdown_lines.append("These values should be described as window-level diagnostic-style safety-proxy metrics. They should not be described as clinical diagnostic validation.")
    markdown_lines.append("")
    markdown_lines.append("`NA` means the ratio is undefined because the denominator is zero, commonly because there were no detected fall windows in that condition.")
    markdown_lines.append("")
    markdown_lines.append("## Table Preview")
    markdown_lines.append("")
    markdown_lines.append("| Condition | NPV | FOR | FDR | PLR | NLR | DOR | MCC | Kappa | Fall Prevalence | FP/TP | FN/TP |")
    markdown_lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for row in output_rows:
        markdown_lines.append(
            f"| {row['display_condition']} "
            f"| {row['negative_predictive_value']} "
            f"| {row['false_omission_rate']} "
            f"| {row['false_discovery_rate']} "
            f"| {row['positive_likelihood_ratio']} "
            f"| {row['negative_likelihood_ratio']} "
            f"| {row['diagnostic_odds_ratio']} "
            f"| {row['matthews_correlation_coefficient']} "
            f"| {row['cohens_kappa']} "
            f"| {row['fall_window_prevalence']} "
            f"| {row['false_alarm_to_detected_fall_ratio']} "
            f"| {row['missed_fall_to_detected_fall_ratio']} |"
        )

    OUTPUT_NOTE.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")

    print("Created Thesis Table 10 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Computed window-level diagnostic-style safety-proxy metrics for:")
    for row in output_rows:
        print(f"  {row['display_condition']}")


if __name__ == "__main__":
    main()
