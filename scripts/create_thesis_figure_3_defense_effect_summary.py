from pathlib import Path
import csv
import matplotlib.pyplot as plt


# ============================================================
# Thesis Figure 3: Defense Effect Summary
#
# Purpose:
# Create a compact thesis-ready visual summary of the first
# short 5-epoch FGSM adversarial-training defense.
#
# Improved visual design:
# - Left panel: false fall alarms under FGSM/PGD before and after defense.
# - Right panel: missed fall rate under FGSM/PGD before and after defense.
#
# Reason:
# Fall recall/sensitivity is 0.0000 for all attacked conditions,
# so a recall bar chart looks visually empty. Missed fall rate
# shows the same safety failure more clearly because it remains
# 1.0000 under attack.
#
# Main message:
# The defense reduced false fall alarms under FGSM and PGD
# attack, but it did not recover missed-fall performance at
# epsilon 0.030.
#
# Input:
# - results/defended_vs_undefended_safety_comparison.csv
#
# Outputs:
# - figures/thesis_figure_3_defense_effect_summary.png
# - notes/thesis_figure_3_defense_effect_summary.md
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

OUTPUT_FIGURE = FIGURES_DIR / "thesis_figure_3_defense_effect_summary.png"
OUTPUT_MD = NOTES_DIR / "thesis_figure_3_defense_effect_summary.md"


CONDITIONS = {
    "undefended_fgsm": "undefended_fgsm_epsilon_0_03",
    "defended_fgsm": "defended_fgsm_epsilon_0_03",
    "undefended_pgd": "undefended_pgd_epsilon_0_03",
    "defended_pgd": "defended_pgd_epsilon_0_03",
}


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

        if value_format == "decimal":
            label = f"{height:.4f}"
        else:
            label = f"{int(round(height))}"

        ax.annotate(
            label,
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )


def write_markdown(summary):
    lines = []

    lines.append("# Thesis Figure 3: Defense Effect Summary")
    lines.append("")
    lines.append("This figure provides a compact visual summary of the first short 5-epoch FGSM adversarial-training defense.")
    lines.append("")
    lines.append("The figure uses two panels:")
    lines.append("")
    lines.append("- False fall alarm count under FGSM and PGD attack before and after defense")
    lines.append("- Missed fall rate under FGSM and PGD attack before and after defense")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append("This is a research implementation using window-level safety-proxy metrics and software-level processed-tensor adversarial perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.")
    lines.append("")
    lines.append("## Main Result")
    lines.append("")
    lines.append(f"- FGSM false fall alarms decreased from `{summary['fgsm_undefended_false_alarms']}` to `{summary['fgsm_defended_false_alarms']}`, a reduction of `{summary['fgsm_false_alarm_reduction']}`.")
    lines.append(f"- PGD false fall alarms decreased from `{summary['pgd_undefended_false_alarms']}` to `{summary['pgd_defended_false_alarms']}`, a reduction of `{summary['pgd_false_alarm_reduction']}`.")
    lines.append(f"- FGSM missed fall rate remained `{fmt_decimal(summary['fgsm_defended_missed_fall_rate'])}` after defense at epsilon `0.030`.")
    lines.append(f"- PGD missed fall rate remained `{fmt_decimal(summary['pgd_defended_missed_fall_rate'])}` after defense at epsilon `0.030`.")
    lines.append(f"- FGSM recall/sensitivity remained `{fmt_decimal(summary['fgsm_defended_recall'])}` after defense at epsilon `0.030`.")
    lines.append(f"- PGD recall/sensitivity remained `{fmt_decimal(summary['pgd_defended_recall'])}` after defense at epsilon `0.030`.")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The defense reduced false fall alarm burden under both FGSM and PGD attacks, but it did not recover fall recall/sensitivity or missed-fall performance at epsilon 0.030. Missed fall rate remained 1.0000 for both defended FGSM and defended PGD. This means the first short 5-epoch FGSM adversarial-training defense reduced one safety-proxy failure mode, false alarms, while leaving the most critical attacked condition, missed falls, unresolved.")
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `figures/thesis_figure_3_defense_effect_summary.png`")
    lines.append("- `notes/thesis_figure_3_defense_effect_summary.md`")
    lines.append("- Input: `results/defended_vs_undefended_safety_comparison.csv`")
    lines.append("")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows_by_condition = read_rows_by_condition(INPUT_FILE)

    undefended_fgsm = get_required_row(rows_by_condition, CONDITIONS["undefended_fgsm"])
    defended_fgsm = get_required_row(rows_by_condition, CONDITIONS["defended_fgsm"])
    undefended_pgd = get_required_row(rows_by_condition, CONDITIONS["undefended_pgd"])
    defended_pgd = get_required_row(rows_by_condition, CONDITIONS["defended_pgd"])

    fgsm_undefended_false_alarms = to_int(undefended_fgsm["FP_false_fall_alarms"])
    fgsm_defended_false_alarms = to_int(defended_fgsm["FP_false_fall_alarms"])
    pgd_undefended_false_alarms = to_int(undefended_pgd["FP_false_fall_alarms"])
    pgd_defended_false_alarms = to_int(defended_pgd["FP_false_fall_alarms"])

    fgsm_undefended_recall = to_float(undefended_fgsm["recall_sensitivity"])
    fgsm_defended_recall = to_float(defended_fgsm["recall_sensitivity"])
    pgd_undefended_recall = to_float(undefended_pgd["recall_sensitivity"])
    pgd_defended_recall = to_float(defended_pgd["recall_sensitivity"])

    fgsm_undefended_missed_fall_rate = to_float(undefended_fgsm["missed_fall_rate"])
    fgsm_defended_missed_fall_rate = to_float(defended_fgsm["missed_fall_rate"])
    pgd_undefended_missed_fall_rate = to_float(undefended_pgd["missed_fall_rate"])
    pgd_defended_missed_fall_rate = to_float(defended_pgd["missed_fall_rate"])

    summary = {
        "fgsm_undefended_false_alarms": fgsm_undefended_false_alarms,
        "fgsm_defended_false_alarms": fgsm_defended_false_alarms,
        "fgsm_false_alarm_reduction": fgsm_undefended_false_alarms - fgsm_defended_false_alarms,
        "pgd_undefended_false_alarms": pgd_undefended_false_alarms,
        "pgd_defended_false_alarms": pgd_defended_false_alarms,
        "pgd_false_alarm_reduction": pgd_undefended_false_alarms - pgd_defended_false_alarms,
        "fgsm_undefended_recall": fgsm_undefended_recall,
        "fgsm_defended_recall": fgsm_defended_recall,
        "pgd_undefended_recall": pgd_undefended_recall,
        "pgd_defended_recall": pgd_defended_recall,
        "fgsm_undefended_missed_fall_rate": fgsm_undefended_missed_fall_rate,
        "fgsm_defended_missed_fall_rate": fgsm_defended_missed_fall_rate,
        "pgd_undefended_missed_fall_rate": pgd_undefended_missed_fall_rate,
        "pgd_defended_missed_fall_rate": pgd_defended_missed_fall_rate,
    }

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    labels = [
        "FGSM\nUndefended",
        "FGSM\nDefended",
        "PGD\nUndefended",
        "PGD\nDefended",
    ]

    false_alarm_values = [
        fgsm_undefended_false_alarms,
        fgsm_defended_false_alarms,
        pgd_undefended_false_alarms,
        pgd_defended_false_alarms,
    ]

    missed_fall_values = [
        fgsm_undefended_missed_fall_rate,
        fgsm_defended_missed_fall_rate,
        pgd_undefended_missed_fall_rate,
        pgd_defended_missed_fall_rate,
    ]

    bars_1 = axes[0].bar(labels, false_alarm_values)
    axes[0].set_title("False Fall Alarms Under Attack")
    axes[0].set_ylabel("False Fall Alarm Count")
    axes[0].set_ylim(0, max(false_alarm_values) * 1.25)
    axes[0].grid(axis="y", alpha=0.3)
    add_bar_labels(axes[0], bars_1, value_format="integer")

    bars_2 = axes[1].bar(labels, missed_fall_values)
    axes[1].set_title("Missed Fall Rate Under Attack")
    axes[1].set_ylabel("Missed Fall Rate")
    axes[1].set_ylim(0, 1.15)
    axes[1].grid(axis="y", alpha=0.3)
    add_bar_labels(axes[1], bars_2, value_format="decimal")

    axes[1].text(
        0.5,
        0.08,
        "Recall/Sensitivity remains 0.0000\nfor all attacked conditions",
        transform=axes[1].transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
        bbox={"boxstyle": "round", "alpha": 0.15},
    )

    fig.suptitle(
        "Thesis Figure 3: Defense Effect Summary",
        fontsize=14,
        fontweight="bold",
    )

    fig.text(
        0.5,
        0.01,
        "Defense reduced false fall alarms, but missed fall rate remained 1.0000 and recall remained 0.0000 under FGSM and PGD attack at epsilon 0.030.",
        ha="center",
        fontsize=10,
    )

    plt.tight_layout(rect=[0, 0.05, 1, 0.93])
    plt.savefig(OUTPUT_FIGURE, dpi=300)
    plt.close()

    write_markdown(summary)

    print("Created updated Thesis Figure 3 outputs:")
    print(f"  {OUTPUT_FIGURE}")
    print(f"  {OUTPUT_MD}")
    print("")
    print("Summary:")
    print(
        f"  FGSM false alarms: "
        f"{fgsm_undefended_false_alarms} -> {fgsm_defended_false_alarms} "
        f"(reduction {summary['fgsm_false_alarm_reduction']})"
    )
    print(
        f"  PGD false alarms: "
        f"{pgd_undefended_false_alarms} -> {pgd_defended_false_alarms} "
        f"(reduction {summary['pgd_false_alarm_reduction']})"
    )
    print(
        f"  FGSM missed fall rate: "
        f"{fmt_decimal(fgsm_undefended_missed_fall_rate)} -> {fmt_decimal(fgsm_defended_missed_fall_rate)}"
    )
    print(
        f"  PGD missed fall rate: "
        f"{fmt_decimal(pgd_undefended_missed_fall_rate)} -> {fmt_decimal(pgd_defended_missed_fall_rate)}"
    )
    print(
        f"  FGSM recall: "
        f"{fmt_decimal(fgsm_undefended_recall)} -> {fmt_decimal(fgsm_defended_recall)}"
    )
    print(
        f"  PGD recall: "
        f"{fmt_decimal(pgd_undefended_recall)} -> {fmt_decimal(pgd_defended_recall)}"
    )


if __name__ == "__main__":
    main()