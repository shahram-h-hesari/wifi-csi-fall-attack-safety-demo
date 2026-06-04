from pathlib import Path
import csv

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = BASE_DIR / "figures"
NOTES_DIR = BASE_DIR / "notes"

INPUT_CSV = RESULTS_DIR / "thesis_table_12_model_confidence_error_summary.csv"
OUTPUT_FIGURE = FIGURES_DIR / "thesis_figure_11_high_confidence_missed_fall_comparison.png"
OUTPUT_NOTE = NOTES_DIR / "thesis_figure_11_high_confidence_missed_fall_comparison.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level model-reported confidence comparison for missed fall windows; "
    "confidence means predicted-class probability/confidence from the model output, not calibrated clinical confidence; "
    "software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, "
    "not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, "
    "not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, and not physical-layer / "
    "packet-level / preamble-level / SDR / over-the-air validation."
)

CONDITION_ORDER = [
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


def safe_float(value):
    if value is None or value == "" or value == "NA":
        return None
    return float(value)


def safe_int(value):
    if value is None or value == "" or value == "NA":
        return 0
    return int(float(value))


def fmt(value):
    if value is None:
        return "NA"
    return f"{value:.6f}"


def load_missed_fall_rows():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_CSV}")

    with INPUT_CSV.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    missed_rows = {
        row["condition"]: row
        for row in rows
        if row["window_group"] == "missed_fall_windows"
    }

    missing = [condition for condition in CONDITION_ORDER if condition not in missed_rows]
    if missing:
        raise ValueError(f"Missing missed-fall confidence rows for: {missing}")

    return [missed_rows[condition] for condition in CONDITION_ORDER]


def create_figure(rows):
    labels = [DISPLAY_NAMES[row["condition"]] for row in rows]
    x_positions = list(range(len(rows)))

    mean_values = [safe_float(row["mean_prediction_confidence"]) for row in rows]
    median_values = [safe_float(row["median_prediction_confidence"]) for row in rows]
    high_confidence_rates = [safe_float(row["high_confidence_rate"]) for row in rows]
    missed_counts = [safe_int(row["n_windows"]) for row in rows]

    bar_width = 0.24

    fig, ax = plt.subplots(figsize=(13.5, 7.5))

    mean_x = [x - bar_width for x in x_positions]
    median_x = x_positions
    high_x = [x + bar_width for x in x_positions]

    ax.bar(mean_x, mean_values, width=bar_width, label="Mean missed-fall confidence")
    ax.bar(median_x, median_values, width=bar_width, label="Median missed-fall confidence")
    ax.bar(high_x, high_confidence_rates, width=bar_width, label="High-confidence missed-fall rate")

    for i, value in enumerate(mean_values):
        ax.text(mean_x[i], value + 0.025, f"{value:.2f}", ha="center", va="bottom", fontsize=8)

    for i, value in enumerate(median_values):
        ax.text(median_x[i], value + 0.025, f"{value:.2f}", ha="center", va="bottom", fontsize=8)

    for i, value in enumerate(high_confidence_rates):
        ax.text(high_x[i], value + 0.025, f"{value:.2f}", ha="center", va="bottom", fontsize=8)

    for i, count in enumerate(missed_counts):
        ax.text(
            x_positions[i],
            1.065,
            f"missed={count}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax.set_title("Thesis Figure 11: High-Confidence Missed-Fall Error Comparison", pad=18)
    ax.set_ylabel("Confidence / rate")
    ax.set_xlabel("Condition")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.12)
    ax.grid(axis="y", alpha=0.3)

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
        ncol=3,
        frameon=True,
    )

    caption = (
        "Window-level model-reported confidence only. Values are not calibrated clinical confidence, "
        "diagnostic certainty, or medical-device validation."
    )
    fig.text(0.5, 0.02, caption, ha="center", fontsize=9)

    fig.subplots_adjust(left=0.09, right=0.97, top=0.86, bottom=0.26)

    fig.savefig(OUTPUT_FIGURE, dpi=300, bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)


def create_note(rows):
    lines = []
    lines.append("# Thesis Figure 11: High-Confidence Missed-Fall Error Comparison")
    lines.append("")
    lines.append("This figure visualizes missed-fall confidence behavior across clean, attacked, and defended conditions.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Output Figure")
    lines.append("")
    lines.append("- `figures/thesis_figure_11_high_confidence_missed_fall_comparison.png`")
    lines.append("")
    lines.append("## Input File")
    lines.append("")
    lines.append("- `results/thesis_table_12_model_confidence_error_summary.csv`")
    lines.append("")
    lines.append("## Metrics Visualized")
    lines.append("")
    lines.append("```text")
    lines.append("mean missed-fall confidence")
    lines.append("median missed-fall confidence")
    lines.append("high-confidence missed-fall rate")
    lines.append("```")
    lines.append("")
    lines.append("## Missed-Fall Confidence Summary")
    lines.append("")
    lines.append("| Condition | Missed Fall Windows | Mean Confidence | Median Confidence | High-Confidence Missed-Fall Rate |")
    lines.append("|---|---:|---:|---:|---:|")

    for row in rows:
        condition = row["condition"]
        label = DISPLAY_NAMES[condition].replace("\n", " ")
        missed_count = safe_int(row["n_windows"])
        mean_confidence = safe_float(row["mean_prediction_confidence"])
        median_confidence = safe_float(row["median_prediction_confidence"])
        high_confidence_rate = safe_float(row["high_confidence_rate"])

        lines.append(
            f"| {label} | {missed_count} | {fmt(mean_confidence)} | "
            f"{fmt(median_confidence)} | {fmt(high_confidence_rate)} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("Figure 11 focuses on a key safety-proxy concern: whether missed fall windows are associated with high model-reported confidence.")
    lines.append("")
    lines.append("The undefended attacked conditions show the strongest confidence concern. Under FGSM at epsilon 0.030, all 89 fall windows are missed and the high-confidence missed-fall rate is 0.606742. Under PGD at epsilon 0.030, all 89 fall windows are missed and the high-confidence missed-fall rate increases to 0.820225, with median missed-fall confidence 0.953281.")
    lines.append("")
    lines.append("The defended attacked conditions still miss all 89 fall windows at epsilon 0.030, but their missed-fall confidence is much lower than the undefended attacked conditions. This supports a careful interpretation: the short defended model did not recover fall recall, but it reduced the model-reported confidence of missed-fall errors.")
    lines.append("")
    lines.append("These values should be interpreted only as window-level model-reported predicted-class confidence summaries. They are not calibrated clinical confidence, diagnostic certainty, or medical-device reliability metrics.")

    OUTPUT_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rows = load_missed_fall_rows()
    create_figure(rows)
    create_note(rows)

    print("Created Thesis Figure 11 outputs:")
    print(f"  {OUTPUT_FIGURE}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Figure 11 uses missed-fall confidence rows from:")
    print(f"  {INPUT_CSV}")


if __name__ == "__main__":
    main()