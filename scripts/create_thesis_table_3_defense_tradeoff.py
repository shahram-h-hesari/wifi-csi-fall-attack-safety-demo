from pathlib import Path
import csv


# ============================================================
# Thesis Table 3: Defense Tradeoff Table
#
# Purpose:
# Compare defended and undefended conditions using existing
# window-level fall-vs-non-fall safety-proxy results.
#
# This table summarizes the tradeoff from the first short
# 5-epoch FGSM adversarial-training defense.
#
# Main interpretation:
# The defense reduced false fall alarms under FGSM and PGD
# attack, but it did not recover fall recall at epsilon 0.030.
#
# Scope:
# Window-level fall-vs-non-fall safety-proxy evaluation only.
# Software-level processed-tensor adversarial perturbation only.
#
# Claim boundary:
# This is not clinical validation, medical-device validation,
# diagnostic evidence, regulatory evaluation, real patient
# deployment, event-level fall validation, long-lie validation,
# or physical-layer / packet-level / preamble-level / SDR /
# over-the-air validation.
# ============================================================


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
NOTES_DIR = ROOT / "notes"

RESULTS_DIR.mkdir(exist_ok=True)
NOTES_DIR.mkdir(exist_ok=True)

INPUT_FILE = RESULTS_DIR / "defended_vs_undefended_safety_comparison.csv"

OUTPUT_CSV = RESULTS_DIR / "thesis_table_3_defense_tradeoff.csv"
OUTPUT_MD = NOTES_DIR / "thesis_table_3_defense_tradeoff.md"


PAIRINGS = [
    {
        "comparison_label": "Clean: defended vs undefended",
        "undefended_condition": "undefended_clean",
        "defended_condition": "defended_clean",
    },
    {
        "comparison_label": "FGSM epsilon 0.030: defended vs undefended",
        "undefended_condition": "undefended_fgsm_epsilon_0_03",
        "defended_condition": "defended_fgsm_epsilon_0_03",
    },
    {
        "comparison_label": "PGD epsilon 0.030: defended vs undefended",
        "undefended_condition": "undefended_pgd_epsilon_0_03",
        "defended_condition": "defended_pgd_epsilon_0_03",
    },
]


def to_float(value):
    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    try:
        return float(value)
    except ValueError:
        return None


def to_int(value):
    number = to_float(value)

    if number is None:
        return None

    return int(round(number))


def fmt_decimal(value, digits=4):
    if value is None:
        return "NA"

    return f"{value:.{digits}f}"


def fmt_integer(value):
    if value is None:
        return "NA"

    return str(int(round(value)))


def read_rows_by_condition(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required input file: {path}")

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError(f"No rows found in input file: {path}")

    by_condition = {}

    for row in rows:
        condition = row.get("condition", "").strip()

        if condition:
            by_condition[condition] = row

    return by_condition


def build_tradeoff_row(comparison_label, undefended_row, defended_row):
    attack_type = defended_row["attack_type"]
    epsilon = to_float(defended_row["epsilon"])

    undefended_false_alarms = to_int(undefended_row["FP_false_fall_alarms"])
    defended_false_alarms = to_int(defended_row["FP_false_fall_alarms"])

    false_alarm_reduction = undefended_false_alarms - defended_false_alarms
    defended_minus_undefended_false_alarms = defended_false_alarms - undefended_false_alarms

    undefended_recall = to_float(undefended_row["recall_sensitivity"])
    defended_recall = to_float(defended_row["recall_sensitivity"])
    recall_recovery = defended_recall - undefended_recall

    undefended_missed_fall_rate = to_float(undefended_row["missed_fall_rate"])
    defended_missed_fall_rate = to_float(defended_row["missed_fall_rate"])
    missed_fall_rate_change = defended_missed_fall_rate - undefended_missed_fall_rate

    undefended_precision = to_float(undefended_row["precision"])
    defended_precision = to_float(defended_row["precision"])
    precision_change = defended_precision - undefended_precision

    undefended_f1 = to_float(undefended_row["f1_score"])
    defended_f1 = to_float(defended_row["f1_score"])
    f1_score_change = defended_f1 - undefended_f1

    undefended_balanced_accuracy = to_float(undefended_row["balanced_accuracy"])
    defended_balanced_accuracy = to_float(defended_row["balanced_accuracy"])
    balanced_accuracy_change = defended_balanced_accuracy - undefended_balanced_accuracy

    undefended_prediction_change_rate = to_float(undefended_row["prediction_change_rate"])
    defended_prediction_change_rate = to_float(defended_row["prediction_change_rate"])
    prediction_change_rate_change = defended_prediction_change_rate - undefended_prediction_change_rate

    return {
        "comparison": comparison_label,
        "attack_type": attack_type,
        "epsilon": epsilon,
        "undefended_false_alarm_count": undefended_false_alarms,
        "defended_false_alarm_count": defended_false_alarms,
        "false_alarm_reduction": false_alarm_reduction,
        "defended_minus_undefended_false_alarm_count": defended_minus_undefended_false_alarms,
        "undefended_recall_sensitivity": undefended_recall,
        "defended_recall_sensitivity": defended_recall,
        "recall_recovery": recall_recovery,
        "undefended_missed_fall_rate": undefended_missed_fall_rate,
        "defended_missed_fall_rate": defended_missed_fall_rate,
        "missed_fall_rate_change": missed_fall_rate_change,
        "undefended_precision": undefended_precision,
        "defended_precision": defended_precision,
        "precision_change": precision_change,
        "undefended_f1_score": undefended_f1,
        "defended_f1_score": defended_f1,
        "f1_score_change": f1_score_change,
        "undefended_balanced_accuracy": undefended_balanced_accuracy,
        "defended_balanced_accuracy": defended_balanced_accuracy,
        "balanced_accuracy_change": balanced_accuracy_change,
        "undefended_prediction_change_rate": undefended_prediction_change_rate,
        "defended_prediction_change_rate": defended_prediction_change_rate,
        "prediction_change_rate_change": prediction_change_rate_change,
    }


def write_csv(rows):
    fieldnames = [
        "comparison",
        "attack_type",
        "epsilon",
        "undefended_false_alarm_count",
        "defended_false_alarm_count",
        "false_alarm_reduction",
        "defended_minus_undefended_false_alarm_count",
        "undefended_recall_sensitivity",
        "defended_recall_sensitivity",
        "recall_recovery",
        "undefended_missed_fall_rate",
        "defended_missed_fall_rate",
        "missed_fall_rate_change",
        "undefended_precision",
        "defended_precision",
        "precision_change",
        "undefended_f1_score",
        "defended_f1_score",
        "f1_score_change",
        "undefended_balanced_accuracy",
        "defended_balanced_accuracy",
        "balanced_accuracy_change",
        "undefended_prediction_change_rate",
        "defended_prediction_change_rate",
        "prediction_change_rate_change",
    ]

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    "comparison": row["comparison"],
                    "attack_type": row["attack_type"],
                    "epsilon": fmt_decimal(row["epsilon"], digits=3),
                    "undefended_false_alarm_count": fmt_integer(row["undefended_false_alarm_count"]),
                    "defended_false_alarm_count": fmt_integer(row["defended_false_alarm_count"]),
                    "false_alarm_reduction": fmt_integer(row["false_alarm_reduction"]),
                    "defended_minus_undefended_false_alarm_count": fmt_integer(row["defended_minus_undefended_false_alarm_count"]),
                    "undefended_recall_sensitivity": fmt_decimal(row["undefended_recall_sensitivity"]),
                    "defended_recall_sensitivity": fmt_decimal(row["defended_recall_sensitivity"]),
                    "recall_recovery": fmt_decimal(row["recall_recovery"]),
                    "undefended_missed_fall_rate": fmt_decimal(row["undefended_missed_fall_rate"]),
                    "defended_missed_fall_rate": fmt_decimal(row["defended_missed_fall_rate"]),
                    "missed_fall_rate_change": fmt_decimal(row["missed_fall_rate_change"]),
                    "undefended_precision": fmt_decimal(row["undefended_precision"]),
                    "defended_precision": fmt_decimal(row["defended_precision"]),
                    "precision_change": fmt_decimal(row["precision_change"]),
                    "undefended_f1_score": fmt_decimal(row["undefended_f1_score"]),
                    "defended_f1_score": fmt_decimal(row["defended_f1_score"]),
                    "f1_score_change": fmt_decimal(row["f1_score_change"]),
                    "undefended_balanced_accuracy": fmt_decimal(row["undefended_balanced_accuracy"]),
                    "defended_balanced_accuracy": fmt_decimal(row["defended_balanced_accuracy"]),
                    "balanced_accuracy_change": fmt_decimal(row["balanced_accuracy_change"]),
                    "undefended_prediction_change_rate": fmt_decimal(row["undefended_prediction_change_rate"]),
                    "defended_prediction_change_rate": fmt_decimal(row["defended_prediction_change_rate"]),
                    "prediction_change_rate_change": fmt_decimal(row["prediction_change_rate_change"]),
                }
            )


def write_markdown(rows):
    lines = []

    lines.append("# Thesis Table 3: Defense Tradeoff Table")
    lines.append("")
    lines.append("This table summarizes the tradeoff between the undefended baseline and the first short 5-epoch FGSM adversarial-training defense using window-level fall-vs-non-fall safety-proxy metrics.")
    lines.append("")
    lines.append("The table compares clean, FGSM-attacked, and PGD-attacked conditions.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append("This is a research implementation using window-level safety-proxy metrics and software-level processed-tensor adversarial perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.")
    lines.append("")
    lines.append("## Table")
    lines.append("")
    lines.append("| Comparison | Epsilon | False Alarm Reduction | Recall Recovery | Missed Fall Rate Change | F1-Score Change | Balanced Accuracy Change |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")

    for row in rows:
        lines.append(
            "| "
            f"{row['comparison']} | "
            f"{fmt_decimal(row['epsilon'], digits=3)} | "
            f"{fmt_integer(row['false_alarm_reduction'])} | "
            f"{fmt_decimal(row['recall_recovery'])} | "
            f"{fmt_decimal(row['missed_fall_rate_change'])} | "
            f"{fmt_decimal(row['f1_score_change'])} | "
            f"{fmt_decimal(row['balanced_accuracy_change'])} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The defended model reduced false fall alarms compared with the undefended model in all three comparisons. Under FGSM attack, false fall alarms decreased from 119 to 72. Under PGD attack, false fall alarms decreased from 115 to 56.")
    lines.append("")
    lines.append("However, the defense did not recover fall recall under the attacked conditions at epsilon 0.030. Both defended FGSM and defended PGD still had recall/sensitivity of 0.0000 and missed fall rate of 1.0000. This suggests that the first short 5-epoch FGSM adversarial-training defense reduced alarm burden but did not solve the missed-fall safety-proxy failure under attack.")
    lines.append("")
    lines.append("For the clean condition, the defended model reduced false fall alarms but also reduced fall recall and F1-score compared with the undefended clean baseline. This shows a clean-performance tradeoff that should be evaluated carefully before interpreting the defense as beneficial.")
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `results/thesis_table_3_defense_tradeoff.csv`")
    lines.append("- `notes/thesis_table_3_defense_tradeoff.md`")
    lines.append("- Input: `results/defended_vs_undefended_safety_comparison.csv`")
    lines.append("")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows_by_condition = read_rows_by_condition(INPUT_FILE)

    output_rows = []

    for pairing in PAIRINGS:
        undefended_condition = pairing["undefended_condition"]
        defended_condition = pairing["defended_condition"]

        if undefended_condition not in rows_by_condition:
            raise KeyError(f"Missing condition in input file: {undefended_condition}")

        if defended_condition not in rows_by_condition:
            raise KeyError(f"Missing condition in input file: {defended_condition}")

        output_rows.append(
            build_tradeoff_row(
                pairing["comparison_label"],
                rows_by_condition[undefended_condition],
                rows_by_condition[defended_condition],
            )
        )

    write_csv(output_rows)
    write_markdown(output_rows)

    print("Created Thesis Table 3 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_MD}")
    print("")
    print("Summary:")
    for row in output_rows:
        print(
            f"  {row['comparison']}: "
            f"false_alarm_reduction={fmt_integer(row['false_alarm_reduction'])}, "
            f"recall_recovery={fmt_decimal(row['recall_recovery'])}, "
            f"missed_fall_rate_change={fmt_decimal(row['missed_fall_rate_change'])}, "
            f"f1_score_change={fmt_decimal(row['f1_score_change'])}, "
            f"balanced_accuracy_change={fmt_decimal(row['balanced_accuracy_change'])}"
        )


if __name__ == "__main__":
    main()