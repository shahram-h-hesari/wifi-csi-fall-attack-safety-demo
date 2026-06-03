"""
Create Thesis Table 7: Safety Metric Availability and Data Requirement Table.

This script creates a thesis-ready table that separates:
1. safety-proxy metrics computable from the current SenseFi / UT-HAR
   window-level outputs, and
2. event-level clinical-safety metrics that require additional metadata.

Outputs:
    results/thesis_table_7_metric_availability.csv
    notes/thesis_table_7_metric_availability.md

Claim boundary:
    This is a research implementation using window-level safety-proxy metrics
    and software-level processed-tensor adversarial perturbations.
"""

from pathlib import Path
import csv


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
NOTES_DIR = ROOT / "notes"

OUTPUT_CSV = RESULTS_DIR / "thesis_table_7_metric_availability.csv"
OUTPUT_NOTE = NOTES_DIR / "thesis_table_7_metric_availability.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level safety-proxy evaluation; "
    "software-level processed-tensor perturbations only; not clinical validation, "
    "not medical-device validation, not diagnostic evidence, not real patient deployment, "
    "not regulatory evaluation, not event-level fall validation, not long-lie validation, "
    "not time-to-alarm validation, and not physical-layer / packet-level / "
    "preamble-level / SDR / over-the-air validation."
)


ROWS = [
    {
        "rank": 1,
        "metric_group": "Current window-level metric",
        "metric_name": "Seven-class accuracy",
        "currently_computable": "yes",
        "support_level": "Directly computable",
        "available_data": "true activity labels; predicted activity labels",
        "missing_data": "none for window-level classification",
        "why_it_matters": "Measures overall seven-class activity recognition performance before binary fall translation.",
        "thesis_use": "Use as a standard ML baseline metric, but do not treat it as sufficient for clinical-safety interpretation.",
        "recommended_reporting_status": "Report now",
    },
    {
        "rank": 2,
        "metric_group": "Current window-level metric",
        "metric_name": "Binary fall-vs-non-fall accuracy",
        "currently_computable": "yes",
        "support_level": "Directly computable",
        "available_data": "true labels; predicted labels; fall-vs-non-fall label mapping",
        "missing_data": "none for window-level binary classification",
        "why_it_matters": "Shows how well the model separates fall windows from non-fall windows.",
        "thesis_use": "Use as a bridge from activity recognition to safety-proxy evaluation.",
        "recommended_reporting_status": "Report now",
    },
    {
        "rank": 3,
        "metric_group": "Current window-level metric",
        "metric_name": "TP, FN, FP, TN",
        "currently_computable": "yes",
        "support_level": "Directly computable",
        "available_data": "binary true labels; binary predicted labels",
        "missing_data": "none for window-level confusion matrix",
        "why_it_matters": "Identifies detected falls, missed falls, false fall alarms, and correctly rejected non-falls.",
        "thesis_use": "Use as the foundation for all current safety-proxy metrics.",
        "recommended_reporting_status": "Report now",
    },
    {
        "rank": 4,
        "metric_group": "Current window-level metric",
        "metric_name": "Recall / sensitivity",
        "currently_computable": "yes",
        "support_level": "Directly computable",
        "available_data": "TP and FN",
        "missing_data": "none for window-level fall windows",
        "why_it_matters": "Measures the fraction of fall windows detected as fall.",
        "thesis_use": "Use to quantify fall-detection degradation under FGSM and PGD.",
        "recommended_reporting_status": "Report now",
    },
    {
        "rank": 5,
        "metric_group": "Current window-level metric",
        "metric_name": "Missed fall rate",
        "currently_computable": "yes",
        "support_level": "Directly computable as a window-level proxy",
        "available_data": "FN and total fall windows",
        "missing_data": "event IDs would be needed for event-level missed fall rate",
        "why_it_matters": "Represents the fraction of fall windows misclassified as non-fall.",
        "thesis_use": "Use as the main safety-proxy metric for fall-miss risk under attack.",
        "recommended_reporting_status": "Report now as window-level proxy",
    },
    {
        "rank": 6,
        "metric_group": "Current window-level metric",
        "metric_name": "Specificity",
        "currently_computable": "yes",
        "support_level": "Directly computable",
        "available_data": "TN and FP",
        "missing_data": "none for window-level non-fall windows",
        "why_it_matters": "Measures how well non-fall windows are correctly rejected.",
        "thesis_use": "Use to interpret non-fall stability under clean, attacked, and defended conditions.",
        "recommended_reporting_status": "Report now",
    },
    {
        "rank": 7,
        "metric_group": "Current window-level metric",
        "metric_name": "False positive rate",
        "currently_computable": "yes",
        "support_level": "Directly computable",
        "available_data": "FP and TN",
        "missing_data": "recording duration would be needed for false alarms per hour/day",
        "why_it_matters": "Measures the rate at which non-fall windows are incorrectly flagged as fall.",
        "thesis_use": "Use as a window-level false-alert burden proxy.",
        "recommended_reporting_status": "Report now as window-level proxy",
    },
    {
        "rank": 8,
        "metric_group": "Current window-level metric",
        "metric_name": "Precision / positive predictive value",
        "currently_computable": "yes",
        "support_level": "Directly computable",
        "available_data": "TP and FP",
        "missing_data": "none for window-level predicted fall alerts",
        "why_it_matters": "Shows how trustworthy predicted fall alerts are at the window level.",
        "thesis_use": "Use to explain false-alert burden and alert trustworthiness.",
        "recommended_reporting_status": "Report now",
    },
    {
        "rank": 9,
        "metric_group": "Current window-level metric",
        "metric_name": "F1-score",
        "currently_computable": "yes",
        "support_level": "Directly computable",
        "available_data": "precision and recall",
        "missing_data": "none for window-level binary classification",
        "why_it_matters": "Balances fall-window detection and predicted-alert reliability.",
        "thesis_use": "Use as a compact safety-proxy summary metric.",
        "recommended_reporting_status": "Report now",
    },
    {
        "rank": 10,
        "metric_group": "Current window-level metric",
        "metric_name": "Balanced accuracy",
        "currently_computable": "yes",
        "support_level": "Directly computable",
        "available_data": "sensitivity and specificity",
        "missing_data": "none for window-level binary classification",
        "why_it_matters": "Useful when fall and non-fall windows are imbalanced.",
        "thesis_use": "Use alongside accuracy to avoid hiding poor fall recall behind many non-fall windows.",
        "recommended_reporting_status": "Report now",
    },
    {
        "rank": 11,
        "metric_group": "Current window-level metric",
        "metric_name": "False fall alarm count",
        "currently_computable": "yes",
        "support_level": "Directly computable as FP count",
        "available_data": "FP false fall alarm windows",
        "missing_data": "recording duration would be needed for false alarms per hour/day",
        "why_it_matters": "Shows the number of non-fall windows incorrectly flagged as fall.",
        "thesis_use": "Use as a simple window-level false alarm burden indicator.",
        "recommended_reporting_status": "Report now as count, not rate per time",
    },
    {
        "rank": 12,
        "metric_group": "Current attack/robustness metric",
        "metric_name": "Prediction change rate under attack",
        "currently_computable": "yes",
        "support_level": "Directly computable",
        "available_data": "clean predictions; attacked predictions",
        "missing_data": "none for window-level prediction-change analysis",
        "why_it_matters": "Measures how often adversarial perturbation changes model decisions.",
        "thesis_use": "Use to quantify attack instability alongside safety-proxy metrics.",
        "recommended_reporting_status": "Report now",
    },
    {
        "rank": 13,
        "metric_group": "Current multiclass diagnostic metric",
        "metric_name": "High-risk multiclass confusion pattern",
        "currently_computable": "partial",
        "support_level": "Computable if seven-class predictions are exported for each condition",
        "available_data": "true seven-class labels; predicted seven-class labels",
        "missing_data": "event timing and clinical severity labels are not available",
        "why_it_matters": "Shows whether fall is confused with clinically risky non-fall classes such as lie down or sit down.",
        "thesis_use": "Use for Table 8 / Figure 6 as an error-taxonomy analysis, not clinical validation.",
        "recommended_reporting_status": "Report as window-level error taxonomy",
    },
    {
        "rank": 14,
        "metric_group": "Future event-level metric",
        "metric_name": "Event-level fall detection rate",
        "currently_computable": "no",
        "support_level": "Requires additional metadata",
        "available_data": "fall-window labels only",
        "missing_data": "fall event IDs or trial/event grouping",
        "why_it_matters": "Measures whether each real fall event was detected at least once.",
        "thesis_use": "Use in future event-level dataset or collaboration.",
        "recommended_reporting_status": "Do not report yet",
    },
    {
        "rank": 15,
        "metric_group": "Future event-level metric",
        "metric_name": "Event-level missed fall count",
        "currently_computable": "no",
        "support_level": "Requires additional metadata",
        "available_data": "fall-window labels only",
        "missing_data": "event-level ground truth and event grouping",
        "why_it_matters": "Measures missed fall events rather than missed fall windows.",
        "thesis_use": "Use in future event-level dataset or collaboration.",
        "recommended_reporting_status": "Do not report yet",
    },
    {
        "rank": 16,
        "metric_group": "Future timing metric",
        "metric_name": "Detection latency / time-to-detection",
        "currently_computable": "no",
        "support_level": "Requires additional metadata",
        "available_data": "window-level labels and predictions",
        "missing_data": "timestamps; fall onset time; fall impact time; model detection time",
        "why_it_matters": "Measures how quickly the system detects a fall after it begins or occurs.",
        "thesis_use": "Use in future event-level safety analysis if timing metadata becomes available.",
        "recommended_reporting_status": "Do not report yet",
    },
    {
        "rank": 17,
        "metric_group": "Future timing metric",
        "metric_name": "Delayed detection rate",
        "currently_computable": "no",
        "support_level": "Requires additional metadata and threshold",
        "available_data": "window-level labels and predictions",
        "missing_data": "timestamps; detection time; delay threshold such as 1, 5, 10, or 30 minutes",
        "why_it_matters": "Measures how often falls are detected too late to meet a defined alert-time threshold.",
        "thesis_use": "Use in future clinical-safety translation work with a justified delay threshold.",
        "recommended_reporting_status": "Do not report yet",
    },
    {
        "rank": 18,
        "metric_group": "Future clinical-safety proxy",
        "metric_name": "Long-lie risk proxy",
        "currently_computable": "no",
        "support_level": "Requires additional metadata and threshold",
        "available_data": "window-level labels and predictions",
        "missing_data": "fall time; alert time; time-on-floor threshold; event-level grouping",
        "why_it_matters": "Connects missed or delayed fall detection to delayed-rescue risk.",
        "thesis_use": "Use only with event-level timing data and carefully defined proxy assumptions.",
        "recommended_reporting_status": "Do not report yet",
    },
    {
        "rank": 19,
        "metric_group": "Future alarm-burden metric",
        "metric_name": "False alarms per hour/day",
        "currently_computable": "no",
        "support_level": "Requires additional metadata",
        "available_data": "window-level FP count",
        "missing_data": "recording duration or monitoring time",
        "why_it_matters": "Converts false alarm count into caregiver-facing alarm burden over time.",
        "thesis_use": "Use in future dataset with monitoring duration.",
        "recommended_reporting_status": "Do not report yet; report FP count only for now",
    },
    {
        "rank": 20,
        "metric_group": "Future generalization metric",
        "metric_name": "Subject-level robustness",
        "currently_computable": "no",
        "support_level": "Requires additional metadata",
        "available_data": "window-level labels and predictions",
        "missing_data": "subject IDs",
        "why_it_matters": "Checks whether attack impact differs by participant.",
        "thesis_use": "Use in future subject-annotated dataset.",
        "recommended_reporting_status": "Do not report yet",
    },
    {
        "rank": 21,
        "metric_group": "Future generalization metric",
        "metric_name": "Trial-level robustness",
        "currently_computable": "no",
        "support_level": "Requires additional metadata",
        "available_data": "window-level labels and predictions",
        "missing_data": "trial IDs",
        "why_it_matters": "Checks whether attack impact differs by trial or recording.",
        "thesis_use": "Use in future trial-annotated dataset.",
        "recommended_reporting_status": "Do not report yet",
    },
    {
        "rank": 22,
        "metric_group": "Future generalization metric",
        "metric_name": "Cross-subject generalization",
        "currently_computable": "no",
        "support_level": "Requires additional metadata",
        "available_data": "window-level labels and predictions",
        "missing_data": "subject split metadata",
        "why_it_matters": "Checks whether results generalize across people rather than only across windows.",
        "thesis_use": "Use in future dataset with subject-aware train/test split.",
        "recommended_reporting_status": "Do not report yet",
    },
    {
        "rank": 23,
        "metric_group": "Future context metric",
        "metric_name": "Room/session-level robustness",
        "currently_computable": "no",
        "support_level": "Requires additional metadata",
        "available_data": "window-level labels and predictions",
        "missing_data": "room IDs; session IDs; recording IDs",
        "why_it_matters": "Checks whether attack and defense behavior changes across rooms or sessions.",
        "thesis_use": "Use in future dataset with room/session annotations.",
        "recommended_reporting_status": "Do not report yet",
    },
]


FIELDNAMES = [
    "rank",
    "metric_group",
    "metric_name",
    "currently_computable",
    "support_level",
    "available_data",
    "missing_data",
    "why_it_matters",
    "thesis_use",
    "recommended_reporting_status",
    "claim_boundary",
]


def md_escape(value) -> str:
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
            output_row = dict(row)
            output_row["claim_boundary"] = CLAIM_BOUNDARY
            writer.writerow(output_row)


def write_markdown(rows):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Thesis Table 7: Safety Metric Availability and Data Requirement Table")
    lines.append("")
    lines.append(
        "This table separates metrics that are computable from the current "
        "SenseFi / UT-HAR window-level outputs from metrics that require "
        "additional event-level, timing, subject, trial, or recording metadata."
    )
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Key Finding")
    lines.append("")
    lines.append(
        "The current local UT-HAR dataset supports window-level fall-vs-non-fall "
        "safety-proxy metrics, but it does not support event-level clinical-safety "
        "metrics such as detection latency, time-to-detection, delayed detection "
        "rate, long-lie proxy, or false alarms per hour/day without additional "
        "metadata."
    )
    lines.append("")
    lines.append("## Table")
    lines.append("")

    headers = [
        "Rank",
        "Metric Group",
        "Metric",
        "Computable Now?",
        "Support Level",
        "Available Data",
        "Missing Data",
        "Why It Matters",
        "Thesis Use",
        "Reporting Status",
    ]

    display_fields = [
        "rank",
        "metric_group",
        "metric_name",
        "currently_computable",
        "support_level",
        "available_data",
        "missing_data",
        "why_it_matters",
        "thesis_use",
        "recommended_reporting_status",
    ]

    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in rows:
        lines.append(
            "| " + " | ".join(md_escape(row[field]) for field in display_fields) + " |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Table 7 helps prevent overclaiming by making the metric boundary explicit. "
        "The current experiment can defensibly report window-level safety-proxy "
        "metrics, including missed fall rate, false fall alarm count, recall, "
        "precision, F1-score, specificity, false positive rate, balanced accuracy, "
        "and prediction change rate under attack."
    )
    lines.append("")
    lines.append(
        "Metrics that require event timing, fall onset, alert time, subject IDs, "
        "trial IDs, or recording duration should be treated as future work until "
        "a richer dataset or collaboration provides those fields."
    )
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `results/thesis_table_7_metric_availability.csv`")
    lines.append("- `notes/thesis_table_7_metric_availability.md`")
    lines.append("")

    OUTPUT_NOTE.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows = ROWS
    write_csv(rows)
    write_markdown(rows)

    print("Created Thesis Table 7 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Metric availability summary:")
    for status in ["yes", "partial", "no"]:
        count = sum(1 for row in rows if row["currently_computable"] == status)
        print(f"  {status}: {count}")


if __name__ == "__main__":
    main()