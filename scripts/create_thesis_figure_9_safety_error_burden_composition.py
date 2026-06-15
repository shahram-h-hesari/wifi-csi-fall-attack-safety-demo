from pathlib import Path
import csv

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = BASE_DIR / "figures"
NOTES_DIR = BASE_DIR / "notes"

INPUT_CSV = RESULTS_DIR / "defended_vs_undefended_safety_comparison.csv"
OUTPUT_FIGURE = FIGURES_DIR / "thesis_figure_9_safety_error_burden_composition.png"
OUTPUT_NOTE = NOTES_DIR / "thesis_figure_9_safety_error_burden_composition.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level safety-error burden visualization; "
    "software-level processed-tensor perturbations only; not clinical validation, "
    "not medical-device validation, not diagnostic evidence, not real patient deployment, "
    "not regulatory evaluation, not event-level fall validation, not long-lie validation, "
    "not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / "
    "SDR / over-the-air validation."
)

ORDER = [
    "undefended_clean",
    "undefended_fgsm_epsilon_0_03",
    "undefended_pgd_epsilon_0_03",
    "defended_clean",
    "defended_fgsm_epsilon_0_03",
    "defended_pgd_epsilon_0_03",
]

DISPLAY_NAMES = {
    "undefended_clean": "Undefended\nclean",
    "undefended_fgsm_epsilon_0_03": "Undefended\nFGSM",
    "undefended_pgd_epsilon_0_03": "Undefended\nPGD",
    "defended_clean": "Defended\nclean",
    "defended_fgsm_epsilon_0_03": "Defended\nFGSM",
    "defended_pgd_epsilon_0_03": "Defended\nPGD",
}

COMPONENTS = [
    ("TP_detected_falls", "Detected fall windows (TP)"),
    ("FN_missed_falls", "Missed fall windows (FN)"),
    ("FP_false_fall_alarms", "False fall alarm windows (FP)"),
    ("TN_correct_non_falls", "Correct non-fall windows (TN)"),
]


def safe_int(value):
    if value is None or value == "":
        return 0
    return int(float(value))


def load_rows():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_CSV}")

    with INPUT_CSV.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    by_condition = {row["condition"]: row for row in rows}
    missing = [condition for condition in ORDER if condition not in by_condition]

    if missing:
        raise ValueError(f"Missing expected conditions in input CSV: {missing}")

    return [by_condition[condition] for condition in ORDER]


def create_figure(rows):
    x_positions = list(range(len(rows)))
    labels = [DISPLAY_NAMES[row["condition"]] for row in rows]

    bottoms = [0] * len(rows)
    total_windows = []

    for row in rows:
        tp = safe_int(row["TP_detected_falls"])
        fn = safe_int(row["FN_missed_falls"])
        fp = safe_int(row["FP_false_fall_alarms"])
        tn = safe_int(row["TN_correct_non_falls"])
        total_windows.append(tp + fn + fp + tn)

    max_total = max(total_windows)

    fig, ax = plt.subplots(figsize=(15.0, 8.5))

    for column_name, component_label in COMPONENTS:
        values = [safe_int(row[column_name]) for row in rows]

        ax.bar(
            x_positions,
            values,
            bottom=bottoms,
            label=component_label,
            width=0.78,
            linewidth=0.4,
        )

        for i, value in enumerate(values):
            if value > 0:
                y_position = bottoms[i] + (value / 2)
                ax.text(
                    x_positions[i],
                    y_position,
                    str(value),
                    ha="center",
                    va="center",
                    fontsize=8,
                )

        bottoms = [bottoms[i] + values[i] for i in range(len(values))]

    for i, total in enumerate(total_windows):
        ax.text(
            x_positions[i],
            total + 18,
            f"Total={total}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax.set_title(
        "Safety Error Burden Composition Across Conditions",
        pad=18,
    )
    ax.set_ylabel("Window count", labelpad=18)
    ax.set_xlabel("Condition", labelpad=12)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, max_total + 100)
    ax.grid(axis="y", alpha=0.3)

    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        borderaxespad=0.0,
        frameon=True,
    )

    caption = (
        "Window-level composition only. Counts are not event-level falls, "
        "false alarms per hour/day, time-to-detection, or clinical validation."
    )
    fig.text(0.5, 0.04, caption, ha="center", fontsize=9)

    fig.subplots_adjust(
        left=0.12,
        right=0.76,
        bottom=0.20,
        top=0.88,
    )

    fig.savefig(
        OUTPUT_FIGURE,
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.45,
    )
    plt.close(fig)


def create_note(rows):
    lines = []
    lines.append("# Safety Error Burden Composition Across Conditions")
    lines.append("")
    lines.append("This figure visualizes how the window-level safety-error burden changes across clean, attacked, and defended conditions.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Output Figure")
    lines.append("")
    lines.append("- `figures/thesis_figure_9_safety_error_burden_composition.png`")
    lines.append("")
    lines.append("## Input File")
    lines.append("")
    lines.append("- `results/defended_vs_undefended_safety_comparison.csv`")
    lines.append("")
    lines.append("## Components Visualized")
    lines.append("")
    lines.append("```text")
    lines.append("detected fall windows = TP")
    lines.append("missed fall windows = FN")
    lines.append("false fall alarm windows = FP")
    lines.append("correct non-fall windows = TN")
    lines.append("```")
    lines.append("")
    lines.append("## Window Count Summary")
    lines.append("")
    lines.append("| Condition | Detected Falls TP | Missed Falls FN | False Fall Alarms FP | Correct Non-Falls TN |")
    lines.append("|---|---:|---:|---:|---:|")

    for row in rows:
        condition = row["condition"]
        display_name = DISPLAY_NAMES.get(condition, condition).replace("\n", " ")
        tp = safe_int(row["TP_detected_falls"])
        fn = safe_int(row["FN_missed_falls"])
        fp = safe_int(row["FP_false_fall_alarms"])
        tn = safe_int(row["TN_correct_non_falls"])
        lines.append(f"| {display_name} | {tp} | {fn} | {fp} | {tn} |")

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("Figure 9 complements the binary confusion matrices by showing the safety burden as a stacked composition of detected fall windows, missed fall windows, false fall alarm windows, and correct non-fall windows.")
    lines.append("")
    lines.append("The figure makes the clean-to-attack shift visible: under FGSM and PGD at epsilon 0.030, detected fall windows collapse to zero while missed fall windows reach all 89 true fall windows. The defended attacked conditions reduce false fall alarm windows compared with the undefended attacked conditions, but still do not recover detected fall windows at epsilon 0.030.")
    lines.append("")
    lines.append("This figure should be interpreted as a window-level safety-error burden visualization. It does not report event-level fall detection, false alarms per hour/day, detection latency, long-lie risk, or clinical validation.")

    OUTPUT_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rows = load_rows()
    create_figure(rows)
    create_note(rows)

    print("Created Thesis Figure 9 outputs:")
    print(f"  {OUTPUT_FIGURE}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Figure 9 visualizes:")
    print("  TP detected fall windows")
    print("  FN missed fall windows")
    print("  FP false fall alarm windows")
    print("  TN correct non-fall windows")


if __name__ == "__main__":
    main()
