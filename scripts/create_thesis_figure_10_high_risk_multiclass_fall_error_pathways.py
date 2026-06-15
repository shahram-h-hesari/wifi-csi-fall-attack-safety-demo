from pathlib import Path
import csv
from collections import defaultdict

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = BASE_DIR / "figures"
NOTES_DIR = BASE_DIR / "notes"

INPUT_CSV = RESULTS_DIR / "thesis_table_8_high_risk_multiclass_error_taxonomy.csv"
OUTPUT_FIGURE = FIGURES_DIR / "thesis_figure_10_high_risk_multiclass_fall_error_pathways.png"
OUTPUT_NOTE = NOTES_DIR / "thesis_figure_10_high_risk_multiclass_fall_error_pathways.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level high-risk multiclass error-pathway visualization; "
    "software-level processed-tensor perturbations only; not clinical validation, "
    "not medical-device validation, not diagnostic evidence, not real patient deployment, "
    "not regulatory evaluation, not event-level fall validation, not long-lie validation, "
    "not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / "
    "SDR / over-the-air validation."
)

CONDITION_ORDER = [
    "undefended_clean",
    "undefended_fgsm_epsilon_0_03",
    "undefended_pgd_epsilon_0_03",
    "defended_clean",
    "defended_fgsm_epsilon_0_03",
    "defended_pgd_epsilon_0_03",
]

CONDITION_LABELS = {
    "undefended_clean": "Undefended clean",
    "undefended_fgsm_epsilon_0_03": "Undefended FGSM",
    "undefended_pgd_epsilon_0_03": "Undefended PGD",
    "defended_clean": "Defended clean",
    "defended_fgsm_epsilon_0_03": "Defended FGSM",
    "defended_pgd_epsilon_0_03": "Defended PGD",
}

MISSED_FALL_DESTINATIONS = [
    "lie down",
    "walk",
    "pickup",
    "run",
    "sit down",
    "stand up",
]

FALSE_ALARM_SOURCES = [
    "lie down",
    "walk",
    "pickup",
    "run",
    "sit down",
    "stand up",
]


def safe_int(value):
    if value is None or value == "":
        return 0
    return int(float(value))


def load_table8_rows():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_CSV}")

    with INPUT_CSV.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_pathway_counts(rows):
    missed_fall_counts = defaultdict(lambda: defaultdict(int))
    false_alarm_counts = defaultdict(lambda: defaultdict(int))

    for row in rows:
        condition_id = row["condition_id"]
        error_family = row["error_family"]
        true_class_name = row["true_class_name"]
        predicted_class_name = row["predicted_class_name"]
        count = safe_int(row["count"])

        if condition_id not in CONDITION_ORDER:
            continue

        if error_family == "missed_fall_multiclass_error":
            if true_class_name == "fall" and predicted_class_name in MISSED_FALL_DESTINATIONS:
                missed_fall_counts[condition_id][predicted_class_name] += count

        if error_family == "false_fall_alarm_multiclass_error":
            if predicted_class_name == "fall" and true_class_name in FALSE_ALARM_SOURCES:
                false_alarm_counts[condition_id][true_class_name] += count

    return missed_fall_counts, false_alarm_counts


def get_panel_totals(counts_by_condition, pathway_classes):
    totals = []
    for condition_id in CONDITION_ORDER:
        total = sum(counts_by_condition[condition_id].get(cls, 0) for cls in pathway_classes)
        totals.append(total)
    return totals


def add_stacked_horizontal_bars(
    ax,
    counts_by_condition,
    pathway_classes,
    title,
    xlabel,
    shared_xmax,
):
    y_positions = list(range(len(CONDITION_ORDER)))
    left_values = [0] * len(CONDITION_ORDER)

    for pathway_class in pathway_classes:
        values = [
            counts_by_condition[condition_id].get(pathway_class, 0)
            for condition_id in CONDITION_ORDER
        ]

        ax.barh(
            y_positions,
            values,
            left=left_values,
            label=pathway_class,
            height=0.68,
        )

        for i, value in enumerate(values):
            if value >= 5:
                ax.text(
                    left_values[i] + value / 2,
                    y_positions[i],
                    str(value),
                    ha="center",
                    va="center",
                    fontsize=8,
                )

        left_values = [
            left_values[i] + values[i]
            for i in range(len(values))
        ]

    for i, total in enumerate(left_values):
        ax.text(
            total + 2,
            y_positions[i],
            f"total={total}",
            ha="left",
            va="center",
            fontsize=8,
        )

    ax.set_yticks(y_positions)
    ax.set_yticklabels([CONDITION_LABELS[c] for c in CONDITION_ORDER])
    ax.invert_yaxis()
    ax.set_title(title, pad=10)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", alpha=0.3)
    ax.set_xlim(0, shared_xmax)


def create_figure(missed_fall_counts, false_alarm_counts):
    missed_totals = get_panel_totals(missed_fall_counts, MISSED_FALL_DESTINATIONS)
    false_alarm_totals = get_panel_totals(false_alarm_counts, FALSE_ALARM_SOURCES)

    global_max_total = max(max(missed_totals), max(false_alarm_totals))
    shared_xmax = global_max_total + 30

    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(13.8, 9.5))

    add_stacked_horizontal_bars(
        axes[0],
        missed_fall_counts,
        MISSED_FALL_DESTINATIONS,
        "A. Missed-fall pathways: true fall predicted as non-fall activity",
        "Window count",
        shared_xmax,
    )

    add_stacked_horizontal_bars(
        axes[1],
        false_alarm_counts,
        FALSE_ALARM_SOURCES,
        "B. False-alarm pathways: true non-fall activity predicted as fall",
        "Window count",
        shared_xmax,
    )

    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="center left",
        bbox_to_anchor=(0.84, 0.50),
        title="Activity class",
        frameon=True,
    )

    fig.suptitle(
        "Figure 4.4: High-Risk Multiclass Fall Error Pathways",
        fontsize=14,
        y=0.97,
    )

    caption = (
        "Window-level pathway counts only. This figure does not report event-level fall validation, "
        "time-to-detection, long-lie risk, or clinical validation."
    )
    fig.text(0.5, 0.025, caption, ha="center", fontsize=9)

    fig.subplots_adjust(
        left=0.16,
        right=0.80,
        top=0.88,
        bottom=0.10,
        hspace=0.42,
    )

    fig.savefig(OUTPUT_FIGURE, dpi=300, bbox_inches="tight", pad_inches=0.30)
    plt.close(fig)


def create_note(missed_fall_counts, false_alarm_counts):
    lines = []
    lines.append("# Figure 4.4: High-Risk Multiclass Fall Error Pathways")
    lines.append("")
    lines.append("This figure summarizes the most clinically motivated multiclass error pathways behind the binary fall-vs-non-fall safety-proxy results.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Output Figure")
    lines.append("")
    lines.append("- `figures/thesis_figure_10_high_risk_multiclass_fall_error_pathways.png`")
    lines.append("")
    lines.append("## Input File")
    lines.append("")
    lines.append("- `results/thesis_table_8_high_risk_multiclass_error_taxonomy.csv`")
    lines.append("")
    lines.append("## Figure Panels")
    lines.append("")
    lines.append("```text")
    lines.append("Panel A: true fall -> predicted non-fall activity")
    lines.append("Panel B: true non-fall activity -> predicted fall")
    lines.append("```")
    lines.append("")
    lines.append("## Missed-Fall Pathway Summary")
    lines.append("")
    lines.append("| Condition | lie down | walk | pickup | run | sit down | stand up | Total missed-fall pathways |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")

    for condition_id in CONDITION_ORDER:
        values = [missed_fall_counts[condition_id].get(cls, 0) for cls in MISSED_FALL_DESTINATIONS]
        total = sum(values)
        label = CONDITION_LABELS[condition_id]
        lines.append(
            f"| {label} | "
            f"{values[0]} | {values[1]} | {values[2]} | {values[3]} | {values[4]} | {values[5]} | {total} |"
        )

    lines.append("")
    lines.append("## False-Fall-Alarm Pathway Summary")
    lines.append("")
    lines.append("| Condition | lie down -> fall | walk -> fall | pickup -> fall | run -> fall | sit down -> fall | stand up -> fall | Total false-alarm pathways |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")

    for condition_id in CONDITION_ORDER:
        values = [false_alarm_counts[condition_id].get(cls, 0) for cls in FALSE_ALARM_SOURCES]
        total = sum(values)
        label = CONDITION_LABELS[condition_id]
        lines.append(
            f"| {label} | "
            f"{values[0]} | {values[1]} | {values[2]} | {values[3]} | {values[4]} | {values[5]} | {total} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("Figure 10 simplifies the dense seven-class confusion matrices into fall-relevant error pathways. Panel A shows where true fall windows go when they are missed. Panel B shows which non-fall activities become false fall alarms.")
    lines.append("")
    lines.append("This figure is useful for thesis explanation because it connects binary safety-proxy degradation to the original multiclass activity-recognition task. It helps answer whether attacks mainly convert falls into specific non-fall activities, and which non-fall activities are most often converted into false fall alarms.")
    lines.append("")
    lines.append("These are window-level error-pathway counts only. They should not be interpreted as event-level fall validation, clinical diagnosis, long-lie validation, or false alarms per hour/day.")

    OUTPUT_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rows = load_table8_rows()
    missed_fall_counts, false_alarm_counts = build_pathway_counts(rows)

    create_figure(missed_fall_counts, false_alarm_counts)
    create_note(missed_fall_counts, false_alarm_counts)

    print("Created Figure 4.4 outputs:")
    print(f"  {OUTPUT_FIGURE}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Figure 10 uses:")
    print("  results/thesis_table_8_high_risk_multiclass_error_taxonomy.csv")


if __name__ == "__main__":
    main()
