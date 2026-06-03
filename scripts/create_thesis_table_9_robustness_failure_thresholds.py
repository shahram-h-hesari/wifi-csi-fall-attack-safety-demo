"""
Create Thesis Table 9: Robustness Failure Threshold Table.

This script converts the FGSM/PGD epsilon sweep into threshold-style
robustness evidence.

The goal is to identify the first observed epsilon where each attack crosses
a predefined window-level safety-proxy failure threshold.

Outputs:
    results/thesis_table_9_robustness_failure_thresholds.csv
    notes/thesis_table_9_robustness_failure_thresholds.md

Claim boundary:
    This is a window-level robustness-threshold analysis using processed CSI
    tensors and software-level perturbations. It is not event-level clinical
    validation, medical-device validation, physical-layer validation, or
    over-the-air validation.
"""

from pathlib import Path
import csv


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
NOTES_DIR = ROOT / "notes"

INPUT_CSV = RESULTS_DIR / "fgsm_vs_pgd_epsilon_comparison.csv"
OUTPUT_CSV = RESULTS_DIR / "thesis_table_9_robustness_failure_thresholds.csv"
OUTPUT_NOTE = NOTES_DIR / "thesis_table_9_robustness_failure_thresholds.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level robustness-threshold analysis; "
    "software-level processed-tensor perturbations only; not clinical validation, "
    "not medical-device validation, not diagnostic evidence, not real patient "
    "deployment, not regulatory evaluation, not event-level fall validation, "
    "not long-lie validation, not time-to-alarm validation, and not physical-layer / "
    "packet-level / preamble-level / SDR / over-the-air validation."
)

CRITERIA = [
    {
        "criterion_id": "severe_missed_fall_threshold",
        "failure_category": "Missed-fall risk",
        "metric": "missed_fall_rate",
        "direction": ">=",
        "threshold": 0.75,
        "threshold_rule": "missed_fall_rate >= 0.75",
        "interpretation": (
            "At least 75% of fall windows are missed. This indicates severe "
            "window-level fall-detection degradation."
        ),
        "thesis_use": (
            "Use as an early safety-proxy failure threshold showing when attack "
            "strength becomes unacceptable for fall-window detection."
        ),
    },
    {
        "criterion_id": "near_complete_missed_fall_threshold",
        "failure_category": "Missed-fall risk",
        "metric": "missed_fall_rate",
        "direction": ">=",
        "threshold": 0.95,
        "threshold_rule": "missed_fall_rate >= 0.95",
        "interpretation": (
            "At least 95% of fall windows are missed. This indicates near-complete "
            "window-level fall-detection collapse."
        ),
        "thesis_use": (
            "Use to identify when the fall detector is nearly unusable under attack "
            "at the window level."
        ),
    },
    {
        "criterion_id": "complete_fall_detection_collapse",
        "failure_category": "Missed-fall risk",
        "metric": "missed_fall_rate",
        "direction": ">=",
        "threshold": 1.00,
        "threshold_rule": "missed_fall_rate >= 1.00",
        "interpretation": (
            "All fall windows are missed. This indicates complete window-level "
            "fall-detection collapse."
        ),
        "thesis_use": (
            "Use as the strongest robustness-failure marker for fall-window detection."
        ),
    },
    {
        "criterion_id": "recall_collapse_threshold",
        "failure_category": "Fall recall",
        "metric": "recall_sensitivity",
        "direction": "<=",
        "threshold": 0.05,
        "threshold_rule": "recall_sensitivity <= 0.05",
        "interpretation": (
            "Fall-window recall drops to 5% or lower. This indicates that the model "
            "almost never detects fall windows."
        ),
        "thesis_use": (
            "Use to connect attack strength to collapse of fall-window sensitivity."
        ),
    },
    {
        "criterion_id": "f1_collapse_threshold",
        "failure_category": "Fall precision-recall balance",
        "metric": "f1_score",
        "direction": "<=",
        "threshold": 0.05,
        "threshold_rule": "f1_score <= 0.05",
        "interpretation": (
            "F1-score drops to 5% or lower. This indicates collapse of the combined "
            "fall-window precision/recall balance."
        ),
        "thesis_use": (
            "Use as a compact binary safety-proxy performance-collapse marker."
        ),
    },
    {
        "criterion_id": "seven_class_accuracy_collapse",
        "failure_category": "Multiclass recognition",
        "metric": "seven_class_accuracy",
        "direction": "<=",
        "threshold": 0.25,
        "threshold_rule": "seven_class_accuracy <= 0.25",
        "interpretation": (
            "Seven-class activity accuracy falls to 25% or lower. This indicates "
            "major multiclass recognition collapse."
        ),
        "thesis_use": (
            "Use to show that attacks degrade not only binary fall safety proxies, "
            "but also the underlying seven-class activity model."
        ),
    },
    {
        "criterion_id": "balanced_accuracy_failure_threshold",
        "failure_category": "Balanced binary performance",
        "metric": "balanced_accuracy",
        "direction": "<=",
        "threshold": 0.50,
        "threshold_rule": "balanced_accuracy <= 0.50",
        "interpretation": (
            "Balanced accuracy falls to 50% or lower. This indicates weak or collapsed "
            "binary fall-vs-non-fall discrimination."
        ),
        "thesis_use": (
            "Use as an imbalance-aware binary safety-proxy failure threshold."
        ),
    },
    {
        "criterion_id": "prediction_instability_threshold",
        "failure_category": "Prediction stability",
        "metric": "prediction_change_rate",
        "direction": ">=",
        "threshold": 0.50,
        "threshold_rule": "prediction_change_rate >= 0.50",
        "interpretation": (
            "At least half of predictions change under attack. This indicates strong "
            "model instability under perturbation."
        ),
        "thesis_use": (
            "Use to quantify attack-induced prediction instability across the epsilon sweep."
        ),
    },
    {
        "criterion_id": "high_false_alarm_burden_threshold",
        "failure_category": "False-fall alarm burden",
        "metric": "false_alarm_count",
        "direction": ">=",
        "threshold": 100.0,
        "threshold_rule": "false_alarm_count >= 100",
        "interpretation": (
            "At least 100 non-fall windows are incorrectly predicted as fall. This "
            "indicates high window-level false-fall-alarm burden."
        ),
        "thesis_use": (
            "Use as a window-level false-alert burden threshold. Do not interpret as "
            "false alarms per hour/day because recording duration is unavailable."
        ),
    },
]


FIELDNAMES = [
    "rank",
    "attack_type",
    "criterion_id",
    "failure_category",
    "metric",
    "threshold_rule",
    "threshold_epsilon",
    "threshold_metric_value",
    "baseline_epsilon",
    "baseline_metric_value",
    "previous_epsilon",
    "previous_metric_value",
    "status",
    "observed_epsilon_grid",
    "interpretation",
    "thesis_use",
    "claim_boundary",
]


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required input file: {path}")

    with path.open("r", newline="", encoding="utf-8") as csvfile:
        return list(csv.DictReader(csvfile))


def as_float(value):
    return float(str(value).strip())


def fmt(value):
    if value == "NA":
        return "NA"
    return f"{float(value):.4f}"


def criterion_met(value, direction, threshold):
    if direction == ">=":
        return value >= threshold
    if direction == "<=":
        return value <= threshold
    raise ValueError(f"Unsupported direction: {direction}")


def get_attack_rows(rows, attack_type):
    selected = [row for row in rows if row["attack_type"].upper() == attack_type.upper()]
    return sorted(selected, key=lambda row: as_float(row["epsilon"]))


def find_threshold_row(attack_rows, criterion):
    metric = criterion["metric"]
    direction = criterion["direction"]
    threshold = criterion["threshold"]

    baseline_row = attack_rows[0]
    previous_row = None

    for row in attack_rows:
        value = as_float(row[metric])
        if criterion_met(value, direction, threshold):
            return row, previous_row, baseline_row

        previous_row = row

    return None, previous_row, baseline_row


def build_rows():
    input_rows = read_csv(INPUT_CSV)

    attack_types = []
    for row in input_rows:
        attack_type = row["attack_type"]
        if attack_type not in attack_types:
            attack_types.append(attack_type)

    output_rows = []
    rank = 1

    for attack_type in attack_types:
        attack_rows = get_attack_rows(input_rows, attack_type)
        epsilon_grid = "; ".join(fmt(row["epsilon"]) for row in attack_rows)

        for criterion in CRITERIA:
            threshold_row, previous_row, baseline_row = find_threshold_row(
                attack_rows, criterion
            )

            metric = criterion["metric"]

            if threshold_row is None:
                threshold_epsilon = "not reached"
                threshold_metric_value = "not reached"
                status = "not reached in observed epsilon grid"
            else:
                threshold_epsilon = fmt(threshold_row["epsilon"])
                threshold_metric_value = fmt(threshold_row[metric])
                status = "threshold reached"

            if previous_row is None:
                previous_epsilon = "NA"
                previous_metric_value = "NA"
            else:
                previous_epsilon = fmt(previous_row["epsilon"])
                previous_metric_value = fmt(previous_row[metric])

            output_rows.append(
                {
                    "rank": rank,
                    "attack_type": attack_type,
                    "criterion_id": criterion["criterion_id"],
                    "failure_category": criterion["failure_category"],
                    "metric": metric,
                    "threshold_rule": criterion["threshold_rule"],
                    "threshold_epsilon": threshold_epsilon,
                    "threshold_metric_value": threshold_metric_value,
                    "baseline_epsilon": fmt(baseline_row["epsilon"]),
                    "baseline_metric_value": fmt(baseline_row[metric]),
                    "previous_epsilon": previous_epsilon,
                    "previous_metric_value": previous_metric_value,
                    "status": status,
                    "observed_epsilon_grid": epsilon_grid,
                    "interpretation": criterion["interpretation"],
                    "thesis_use": criterion["thesis_use"],
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
            rank += 1

    return output_rows


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


def write_markdown(rows):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Thesis Table 9: Robustness Failure Threshold Table")
    lines.append("")
    lines.append(
        "This table identifies the first observed epsilon where FGSM or PGD crosses "
        "predefined window-level robustness failure thresholds."
    )
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Input File")
    lines.append("")
    lines.append("- `results/fgsm_vs_pgd_epsilon_comparison.csv`")
    lines.append("")
    lines.append("## Threshold Summary")
    lines.append("")
    lines.append(
        "| Attack | Failure Category | Metric | Threshold Rule | First Epsilon Reached | "
        "Metric Value at Threshold | Previous Epsilon | Previous Value | Status |"
    )
    lines.append("|---|---|---|---|---:|---:|---:|---:|---|")

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(row["attack_type"]),
                    md_escape(row["failure_category"]),
                    md_escape(row["metric"]),
                    md_escape(row["threshold_rule"]),
                    md_escape(row["threshold_epsilon"]),
                    md_escape(row["threshold_metric_value"]),
                    md_escape(row["previous_epsilon"]),
                    md_escape(row["previous_metric_value"]),
                    md_escape(row["status"]),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Key Interpretation")
    lines.append("")
    lines.append(
        "Table 9 translates the epsilon sweep into robustness-threshold language. "
        "Instead of only reporting performance at each epsilon, it asks when each "
        "attack first reaches a predefined failure condition."
    )
    lines.append("")
    lines.append(
        "This is useful for thesis writing because it supports statements such as "
        "'FGSM reached near-complete missed-fall behavior by epsilon 0.010' or "
        "'PGD reached severe missed-fall behavior by epsilon 0.005' while keeping "
        "the analysis explicitly window-level."
    )
    lines.append("")
    lines.append(
        "False-alarm thresholds are reported as window counts only. They should not "
        "be converted into false alarms per hour or day because the local UT-HAR "
        "copy does not provide recording duration or monitoring-time metadata."
    )
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `results/thesis_table_9_robustness_failure_thresholds.csv`")
    lines.append("- `notes/thesis_table_9_robustness_failure_thresholds.md`")
    lines.append("")

    OUTPUT_NOTE.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows = build_rows()
    write_csv(rows)
    write_markdown(rows)

    print("Created Thesis Table 9 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Robustness failure threshold summary:")
    for row in rows:
        print(
            f"  {row['attack_type']} | {row['criterion_id']} | "
            f"{row['threshold_rule']} | first epsilon: {row['threshold_epsilon']} | "
            f"value: {row['threshold_metric_value']} | {row['status']}"
        )


if __name__ == "__main__":
    main()