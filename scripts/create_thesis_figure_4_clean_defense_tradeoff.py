from pathlib import Path
import csv
import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# Thesis Figure 4: Clean vs Defended Clean Tradeoff
#
# Purpose:
# Compare the undefended clean baseline against the defended
# clean model to show the clean-performance cost of the first
# short 5-epoch FGSM adversarial-training defense.
#
# Metrics:
# - Recall/sensitivity
# - Missed fall rate
# - Precision
# - F1-score
# - Balanced accuracy
# - False fall alarm count
#
# Input:
# - results/defended_vs_undefended_safety_comparison.csv
#
# Outputs:
# - figures/thesis_figure_4_clean_defense_tradeoff.png
# - notes/thesis_figure_4_clean_defense_tradeoff.md
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
FIGURES_DIR = ROOT / "figures"
NOTES_DIR = ROOT / "notes"

FIGURES_DIR.mkdir(exist_ok=True)
NOTES_DIR.mkdir(exist_ok=True)

INPUT_FILE = RESULTS_DIR / "defended_vs_undefended_safety_comparison.csv"

OUTPUT_FIGURE = FIGURES_DIR / "thesis_figure_4_clean_defense_tradeoff.png"
OUTPUT_MD = NOTES_DIR / "thesis_figure_4_clean_defense_tradeoff.md"


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


def get_required_row(rows_by_condition, condition_name):
    if condition_name not in rows_by_condition:
        available = ", ".join(sorted(rows_by_condition.keys()))
        raise KeyError(
            f"Missing condition '{condition_name}'. "
            f"Available conditions: {available}"
        )

    return rows_by_condition[condition_name]


def add_bar_labels(ax, bars, value_format):
    for bar in bars:
        height = bar.get_height()

        if value_format == "integer":
            label = f"{int(round(height))}"
        else:
            label = f"{height:.4f}"

        ax.annotate(
            label,
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            rotation=0,
        )


def write_markdown(summary):
    lines = []

    lines.append("# Thesis Figure 4: Clean vs Defended Clean Tradeoff")
    lines.append("")
    lines.append("This figure compares the undefended clean baseline against the defended clean model to show the clean-performance cost of the first short 5-epoch FGSM adversarial-training defense.")
    lines.append("")
    lines.append("The figure focuses only on the clean condition, without FGSM or PGD attack.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append("This is a research implementation using window-level safety-proxy metrics and software-level processed-tensor adversarial perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.")
    lines.append("")
    lines.append("## Main Result")
    lines.append("")
    lines.append(f"- Recall/sensitivity changed from `{fmt_decimal(summary['undefended_recall'])}` to `{fmt_decimal(summary['defended_recall'])}`, a change of `{fmt_decimal(summary['recall_change'])}`.")
    lines.append(f"- Missed fall rate changed from `{fmt_decimal(summary['undefended_missed_fall_rate'])}` to `{fmt_decimal(summary['defended_missed_fall_rate'])}`, a change of `{fmt_decimal(summary['missed_fall_rate_change'])}`.")
    lines.append(f"- Precision changed from `{fmt_decimal(summary['undefended_precision'])}` to `{fmt_decimal(summary['defended_precision'])}`, a change of `{fmt_decimal(summary['precision_change'])}`.")
    lines.append(f"- F1-score changed from `{fmt_decimal(summary['undefended_f1'])}` to `{fmt_decimal(summary['defended_f1'])}`, a change of `{fmt_decimal(summary['f1_change'])}`.")
    lines.append(f"- Balanced accuracy changed from `{fmt_decimal(summary['undefended_balanced_accuracy'])}` to `{fmt_decimal(summary['defended_balanced_accuracy'])}`, a change of `{fmt_decimal(summary['balanced_accuracy_change'])}`.")
    lines.append(f"- False fall alarms changed from `{summary['undefended_false_alarms']}` to `{summary['defended_false_alarms']}`, a reduction of `{summary['false_alarm_reduction']}`.")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The defended clean model reduced false fall alarms from 32 to 22, but this came with a reduction in fall recall/sensitivity, F1-score, and balanced accuracy. Missed fall rate increased from 0.3596 to 0.5955. This clean-condition tradeoff is important because a defense that reduces false alarms may still be undesirable if it increases missed falls.")
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `figures/thesis_figure_4_clean_defense_tradeoff.png`")
    lines.append("- `notes/thesis_figure_4_clean_defense_tradeoff.md`")
    lines.append("- Input: `results/defended_vs_undefended_safety_comparison.csv`")
    lines.append("")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows_by_condition = read_rows_by_condition(INPUT_FILE)

    undefended_clean = get_required_row(rows_by_condition, "undefended_clean")
    defended_clean = get_required_row(rows_by_condition, "defended_clean")

    undefended_recall = to_float(undefended_clean["recall_sensitivity"])
    defended_recall = to_float(defended_clean["recall_sensitivity"])

    undefended_missed_fall_rate = to_float(undefended_clean["missed_fall_rate"])
    defended_missed_fall_rate = to_float(defended_clean["missed_fall_rate"])

    undefended_precision = to_float(undefended_clean["precision"])
    defended_precision = to_float(defended_clean["precision"])

    undefended_f1 = to_float(undefended_clean["f1_score"])
    defended_f1 = to_float(defended_clean["f1_score"])

    undefended_balanced_accuracy = to_float(undefended_clean["balanced_accuracy"])
    defended_balanced_accuracy = to_float(defended_clean["balanced_accuracy"])

    undefended_false_alarms = to_int(undefended_clean["FP_false_fall_alarms"])
    defended_false_alarms = to_int(defended_clean["FP_false_fall_alarms"])

    summary = {
        "undefended_recall": undefended_recall,
        "defended_recall": defended_recall,
        "recall_change": defended_recall - undefended_recall,
        "undefended_missed_fall_rate": undefended_missed_fall_rate,
        "defended_missed_fall_rate": defended_missed_fall_rate,
        "missed_fall_rate_change": defended_missed_fall_rate - undefended_missed_fall_rate,
        "undefended_precision": undefended_precision,
        "defended_precision": defended_precision,
        "precision_change": defended_precision - undefended_precision,
        "undefended_f1": undefended_f1,
        "defended_f1": defended_f1,
        "f1_change": defended_f1 - undefended_f1,
        "undefended_balanced_accuracy": undefended_balanced_accuracy,
        "defended_balanced_accuracy": defended_balanced_accuracy,
        "balanced_accuracy_change": defended_balanced_accuracy - undefended_balanced_accuracy,
        "undefended_false_alarms": undefended_false_alarms,
        "defended_false_alarms": defended_false_alarms,
        "false_alarm_reduction": undefended_false_alarms - defended_false_alarms,
    }

    rate_metric_labels = [
        "Recall /\nSensitivity",
        "Missed Fall\nRate",
        "Precision",
        "F1-Score",
        "Balanced\nAccuracy",
    ]

    undefended_rate_values = [
        undefended_recall,
        undefended_missed_fall_rate,
        undefended_precision,
        undefended_f1,
        undefended_balanced_accuracy,
    ]

    defended_rate_values = [
        defended_recall,
        defended_missed_fall_rate,
        defended_precision,
        defended_f1,
        defended_balanced_accuracy,
    ]

    x = np.arange(len(rate_metric_labels))
    width = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    bars_1 = axes[0].bar(x - width / 2, undefended_rate_values, width, label="Undefended Clean")
    bars_2 = axes[0].bar(x + width / 2, defended_rate_values, width, label="Defended Clean")

    axes[0].set_title("Clean Safety-Proxy Rate Metrics")
    axes[0].set_ylabel("Metric Value")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(rate_metric_labels)
    axes[0].set_ylim(0, 1.05)
    axes[0].grid(axis="y", alpha=0.3)
    axes[0].legend()

    add_bar_labels(axes[0], bars_1, value_format="decimal")
    add_bar_labels(axes[0], bars_2, value_format="decimal")

    false_alarm_labels = ["Undefended\nClean", "Defended\nClean"]
    false_alarm_values = [undefended_false_alarms, defended_false_alarms]

    bars_3 = axes[1].bar(false_alarm_labels, false_alarm_values)

    axes[1].set_title("Clean False Fall Alarms")
    axes[1].set_ylabel("False Fall Alarm Count")
    axes[1].set_ylim(0, max(false_alarm_values) * 1.35)
    axes[1].grid(axis="y", alpha=0.3)

    add_bar_labels(axes[1], bars_3, value_format="integer")

    fig.suptitle(
        "Thesis Figure 4: Clean vs Defended Clean Tradeoff",
        fontsize=14,
        fontweight="bold",
    )

    fig.text(
        0.5,
        0.01,
        "Defense reduced clean false fall alarms, but lowered recall/sensitivity and increased missed fall rate.",
        ha="center",
        fontsize=10,
    )

    plt.tight_layout(rect=[0, 0.05, 1, 0.93])
    plt.savefig(OUTPUT_FIGURE, dpi=300)
    plt.close()

    write_markdown(summary)

    print("Created Thesis Figure 4 outputs:")
    print(f"  {OUTPUT_FIGURE}")
    print(f"  {OUTPUT_MD}")
    print("")
    print("Summary:")
    print(f"  Recall/sensitivity: {fmt_decimal(undefended_recall)} -> {fmt_decimal(defended_recall)}")
    print(f"  Missed fall rate: {fmt_decimal(undefended_missed_fall_rate)} -> {fmt_decimal(defended_missed_fall_rate)}")
    print(f"  Precision: {fmt_decimal(undefended_precision)} -> {fmt_decimal(defended_precision)}")
    print(f"  F1-score: {fmt_decimal(undefended_f1)} -> {fmt_decimal(defended_f1)}")
    print(f"  Balanced accuracy: {fmt_decimal(undefended_balanced_accuracy)} -> {fmt_decimal(defended_balanced_accuracy)}")
    print(f"  False fall alarms: {undefended_false_alarms} -> {defended_false_alarms}")


if __name__ == "__main__":
    main()