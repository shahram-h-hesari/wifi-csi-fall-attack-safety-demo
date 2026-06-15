from pathlib import Path
import csv

import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# Paths
# ============================================================

EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = EXPERIMENT_DIR / "results"
FIGURES_DIR = EXPERIMENT_DIR / "figures"
NOTES_DIR = EXPERIMENT_DIR / "notes"

INPUT_CSV = RESULTS_DIR / "thesis_table_14_matched_attack_defense_effect_summary.csv"

OUTPUT_FIGURE = FIGURES_DIR / "thesis_figure_14_matched_attack_defense_effect_comparison.png"
OUTPUT_NOTE = NOTES_DIR / "thesis_figure_14_matched_attack_defense_effect_comparison.md"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)


CLAIM_BOUNDARY = (
    "Research implementation only; matched window-level attack-defense effect visualization; "
    "defense effects are descriptive undefended-to-defended comparisons, not clinical effectiveness claims; "
    "model confidence means predicted-class probability/confidence from the model output, not calibrated clinical confidence; "
    "software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, "
    "not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, "
    "not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, and not physical-layer / "
    "packet-level / preamble-level / SDR / over-the-air validation."
)


# ============================================================
# Helpers
# ============================================================

def safe_float(value):
    if value is None or value == "" or value == "NA":
        return None
    if isinstance(value, str) and value.endswith("%"):
        value = value.replace("%", "")
    return float(value)


def safe_int(value):
    if value is None or value == "" or value == "NA":
        return 0
    return int(float(value))


def fmt_float(value):
    if value is None:
        return "NA"
    return f"{float(value):.6f}"


def fmt_short(value):
    if value is None:
        return "NA"
    return f"{float(value):.3f}"


def fmt_count(value):
    if value is None:
        return "NA"
    return str(int(round(float(value))))


def read_rows():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_CSV}")

    with INPUT_CSV.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    attack_order = {"FGSM": 0, "PGD": 1}
    rows = sorted(rows, key=lambda row: attack_order.get(row["attack_type"], 99))

    return rows


def add_vertical_bar_labels(ax, bars, values, value_type):
    for bar, value in zip(bars, values):
        height = bar.get_height()

        if value_type == "count":
            label = fmt_count(value)
        else:
            label = fmt_short(value)

        ax.annotate(
            label,
            xy=(bar.get_x() + bar.get_width() / 2.0, height),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )


def plot_grouped_panel(
    ax,
    attack_labels,
    undefended_values,
    defended_values,
    title,
    ylabel,
    value_type,
):
    x = np.arange(len(attack_labels))
    width = 0.34

    bars_undefended = ax.bar(
        x - width / 2,
        undefended_values,
        width,
        label="Undefended attack",
        edgecolor="black",
        linewidth=0.6,
        alpha=0.88,
    )

    bars_defended = ax.bar(
        x + width / 2,
        defended_values,
        width,
        label="Defended attack",
        edgecolor="black",
        linewidth=0.6,
        alpha=0.88,
    )

    ax.set_title(title, pad=10)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.set_xticklabels(attack_labels)
    ax.grid(axis="y", alpha=0.28)

    max_value = max(max(undefended_values), max(defended_values))

    if value_type == "count":
        ax.set_ylim(0, max_value * 1.20)
    else:
        ax.set_ylim(0, min(1.08, max_value * 1.18))

    add_vertical_bar_labels(ax, bars_undefended, undefended_values, value_type)
    add_vertical_bar_labels(ax, bars_defended, defended_values, value_type)

    return bars_undefended, bars_defended


# ============================================================
# Read Table 14 data
# ============================================================

rows = read_rows()
attack_labels = [row["attack_type"] for row in rows]

undefended_high_conf = [
    safe_float(row["undefended_high_confidence_missed_fall_rate"])
    for row in rows
]
defended_high_conf = [
    safe_float(row["defended_high_confidence_missed_fall_rate"])
    for row in rows
]

undefended_median_conf = [
    safe_float(row["undefended_median_missed_fall_confidence"])
    for row in rows
]
defended_median_conf = [
    safe_float(row["defended_median_missed_fall_confidence"])
    for row in rows
]

undefended_false_alarms = [
    safe_int(row["undefended_false_fall_alarm_count"])
    for row in rows
]
defended_false_alarms = [
    safe_int(row["defended_false_fall_alarm_count"])
    for row in rows
]

undefended_missed_fall_rates = [
    safe_float(row["undefended_missed_fall_rate"])
    for row in rows
]
defended_missed_fall_rates = [
    safe_float(row["defended_missed_fall_rate"])
    for row in rows
]

for row, undef_rate, def_rate in zip(rows, undefended_missed_fall_rates, defended_missed_fall_rates):
    if undef_rate != 1.0 or def_rate != 1.0:
        print(
            f"Warning: expected missed fall rate 1.000000 for both attacked conditions in "
            f"{row['attack_type']}, but got undefended={undef_rate:.6f}, defended={def_rate:.6f}"
        )


# ============================================================
# Create figure
# ============================================================

fig, axes = plt.subplots(1, 3, figsize=(16.8, 7.2))

plot_grouped_panel(
    axes[0],
    attack_labels,
    undefended_high_conf,
    defended_high_conf,
    "A. High-confidence missed-fall rate",
    "Rate",
    "rate",
)

plot_grouped_panel(
    axes[1],
    attack_labels,
    undefended_median_conf,
    defended_median_conf,
    "B. Median missed-fall confidence",
    "Median confidence",
    "rate",
)

plot_grouped_panel(
    axes[2],
    attack_labels,
    undefended_false_alarms,
    defended_false_alarms,
    "C. False fall alarm count",
    "Window count",
    "count",
)

handles, labels = axes[0].get_legend_handles_labels()

fig.suptitle(
    "Matched Attack Defense Effect Comparison",
    fontsize=15,
    y=0.965,
)

subtitle = (
    "Lower values are better in all three panels. "
    "Missed fall rate remained 1.000000 under all matched attacked conditions."
)
fig.text(
    0.5,
    0.905,
    subtitle,
    ha="center",
    fontsize=9,
)

fig.text(
    0.5,
    0.205,
    "Matched attack condition",
    ha="center",
    fontsize=10,
)

fig.legend(
    handles,
    labels,
    title="Model condition",
    loc="lower center",
    ncol=2,
    frameon=True,
    bbox_to_anchor=(0.5, 0.105),
    fontsize=10,
    title_fontsize=10,
)

caption = (
    "Window-level matched attack-defense comparison only. "
    "This is not clinical defense effectiveness, clinical validation, or medical-device validation."
)
fig.text(
    0.5,
    0.035,
    caption,
    ha="center",
    fontsize=9,
)

fig.subplots_adjust(
    left=0.065,
    right=0.985,
    top=0.82,
    bottom=0.285,
    wspace=0.32,
)

fig.savefig(OUTPUT_FIGURE, dpi=300, bbox_inches="tight", pad_inches=0.35)
plt.close(fig)


# ============================================================
# Create note
# ============================================================

lines = []

lines.append("# Matched Attack Defense Effect Comparison")
lines.append("")
lines.append(
    "This figure compares matched undefended and defended attack conditions using three metrics that improved under defense, while explicitly noting that missed fall rate did not improve."
)
lines.append("")
lines.append("## Claim Boundary")
lines.append("")
lines.append(CLAIM_BOUNDARY)
lines.append("")
lines.append("## Output Figure")
lines.append("")
lines.append("- `figures/thesis_figure_14_matched_attack_defense_effect_comparison.png`")
lines.append("")
lines.append("## Input File")
lines.append("")
lines.append("- `results/thesis_table_14_matched_attack_defense_effect_summary.csv`")
lines.append("")
lines.append("## Figure Panels")
lines.append("")
lines.append("```text")
lines.append("Panel A: high-confidence missed-fall rate")
lines.append("Panel B: median missed-fall confidence")
lines.append("Panel C: false fall alarm count")
lines.append("```")
lines.append("")
lines.append("## Important Context")
lines.append("")
lines.append("Missed fall rate remained `1.000000` for all matched attacked conditions:")
lines.append("")
lines.append("- Undefended FGSM epsilon 0.03")
lines.append("- Defended FGSM epsilon 0.03")
lines.append("- Undefended PGD epsilon 0.03")
lines.append("- Defended PGD epsilon 0.03")
lines.append("")
lines.append("Because missed fall rate did not improve, this figure focuses on the defense effects that did improve.")
lines.append("")
lines.append("## Figure Data")
lines.append("")
lines.append(
    "| Attack | High-Confidence Missed-Fall Rate Undefended -> Defended | Median Missed-Fall Confidence Undefended -> Defended | False Fall Alarms Undefended -> Defended |"
)
lines.append("|---|---:|---:|---:|")

for row in rows:
    lines.append(
        f"| {row['attack_type']} "
        f"| {row['undefended_high_confidence_missed_fall_rate']} -> {row['defended_high_confidence_missed_fall_rate']} "
        f"| {row['undefended_median_missed_fall_confidence']} -> {row['defended_median_missed_fall_confidence']} "
        f"| {row['undefended_false_fall_alarm_count']} -> {row['defended_false_fall_alarm_count']} |"
    )

lines.append("")
lines.append("## Reduction Summary")
lines.append("")

for row in rows:
    lines.append(f"### {row['attack_type']} epsilon 0.03")
    lines.append("")
    lines.append("```text")
    lines.append(
        f"high-confidence missed-fall rate reduction = {row['high_confidence_missed_fall_rate_reduction']}"
    )
    lines.append(
        f"high-confidence missed-fall rate percent reduction = {row['high_confidence_missed_fall_rate_percent_reduction']}"
    )
    lines.append(
        f"median missed-fall confidence reduction = {row['median_missed_fall_confidence_reduction']}"
    )
    lines.append(
        f"false fall alarm count reduction = {row['false_fall_alarm_count_reduction']}"
    )
    lines.append(
        f"missed fall rate change = {row['missed_fall_rate_change_defended_minus_undefended']}"
    )
    lines.append(
        f"recall change = {row['recall_change_defended_minus_undefended']}"
    )
    lines.append("```")
    lines.append("")

lines.append("## Interpretation")
lines.append("")
lines.append(
    "Figure 14 shows that the defended attacked model reduced three error-burden metrics relative to the matched undefended attacked model:"
)
lines.append("")
lines.append("1. lower high-confidence missed-fall rate")
lines.append("2. lower median missed-fall confidence")
lines.append("3. fewer false fall alarms")
lines.append("")

for row in rows:
    lines.append(
        f"For {row['attack_type']}, the defended model reduced high-confidence missed-fall rate "
        f"from {row['undefended_high_confidence_missed_fall_rate']} to {row['defended_high_confidence_missed_fall_rate']}, "
        f"reduced median missed-fall confidence from {row['undefended_median_missed_fall_confidence']} to {row['defended_median_missed_fall_confidence']}, "
        f"and reduced false fall alarms from {row['undefended_false_fall_alarm_count']} to {row['defended_false_fall_alarm_count']}."
    )
    lines.append("")

lines.append(
    "However, the figure must be interpreted carefully: missed fall rate remained 1.000000 under all matched attacked conditions, so the defense did not restore window-level fall recall."
)
lines.append("")
lines.append(
    "The figure therefore supports a careful thesis statement: the short defended model reduced overconfident error burden and false alarms, but it did not restore fall-detection safety performance."
)
lines.append("")
lines.append(
    "This figure should not be interpreted as clinical defense effectiveness, medical-device validation, event-level fall-risk reduction, time-to-alarm improvement, or physical-world attack mitigation."
)

OUTPUT_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ============================================================
# Done
# ============================================================

print("Created Thesis Figure 14 outputs:")
print(f"  {OUTPUT_FIGURE}")
print(f"  {OUTPUT_NOTE}")
print("")
print("Figure 14 compares matched attack-defense effects for:")
for attack in attack_labels:
    print(f"  {attack} epsilon 0.03")