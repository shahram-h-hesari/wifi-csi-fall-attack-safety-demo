from pathlib import Path
import csv

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = BASE_DIR / "figures"
NOTES_DIR = BASE_DIR / "notes"

INPUT_CSV = RESULTS_DIR / "thesis_table_13_confidence_safety_failure_ranking.csv"

OUTPUT_FIGURE = FIGURES_DIR / "thesis_figure_13_confidence_safety_failure_ranking.png"
OUTPUT_NOTE = NOTES_DIR / "thesis_figure_13_confidence_safety_failure_ranking.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level confidence-safety failure ranking visualization; "
    "the confidence-safety failure score is a descriptive product of missed fall rate and "
    "high-confidence missed-fall rate, not a clinical risk score; model confidence means "
    "predicted-class probability/confidence from the model output, not calibrated clinical confidence; "
    "software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, "
    "not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, "
    "not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, and not physical-layer / "
    "packet-level / preamble-level / SDR / over-the-air validation."
)


def safe_float(value):
    if value is None or value == "" or value == "NA":
        return None
    return float(value)


def safe_int(value):
    if value is None or value == "" or value == "NA":
        return 0
    return int(float(value))


def read_rows():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_CSV}")

    with INPUT_CSV.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    rows = sorted(
        rows,
        key=lambda row: safe_int(row["rank_by_confidence_safety_failure_score"]),
    )

    return rows


def model_family(condition):
    if condition.startswith("undefended"):
        return "Undefended"
    if condition.startswith("defended"):
        return "Defended"
    return "Other"


def clean_condition_label(row):
    rank = safe_int(row["rank_by_confidence_safety_failure_score"])
    display = row["display_condition"]
    display = display.replace(" epsilon 0.03", "\nepsilon 0.03")
    return f"#{rank}  {display}"


def create_figure(rows):
    labels = [clean_condition_label(row) for row in rows]
    scores = [safe_float(row["confidence_safety_failure_score"]) for row in rows]
    families = [model_family(row["condition"]) for row in rows]

    default_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    family_colors = {
        "Undefended": default_colors[0],
        "Defended": default_colors[1],
        "Other": default_colors[2],
    }

    bar_colors = [family_colors[family] for family in families]
    y_positions = list(range(len(rows)))

    fig, ax = plt.subplots(figsize=(12.8, 7.4))

    ax.barh(
        y_positions,
        scores,
        height=0.62,
        color=bar_colors,
        edgecolor="black",
        linewidth=0.6,
        alpha=0.88,
    )

    max_score = max(scores)
    score_label_offset = max_score * 0.025

    for i, score in enumerate(scores):
        if score == 0:
            label_x = max_score * 0.025
        else:
            label_x = score + score_label_offset

        ax.text(
            label_x,
            y_positions[i],
            f"{score:.3f}",
            va="center",
            ha="left",
            fontsize=9,
        )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()

    ax.set_xlabel("Confidence-safety failure score (higher = worse)")
    ax.set_title(
        "Thesis Figure 13: Confidence-Safety Failure Ranking",
        pad=16,
    )

    ax.set_xlim(0, max_score + 0.09)
    ax.grid(axis="x", alpha=0.28)

    legend_handles = [
        Patch(
            facecolor=family_colors["Undefended"],
            edgecolor="black",
            label="Undefended model",
            alpha=0.88,
        ),
        Patch(
            facecolor=family_colors["Defended"],
            edgecolor="black",
            label="Defended model",
            alpha=0.88,
        ),
    ]

    ax.legend(
        handles=legend_handles,
        loc="lower right",
        frameon=True,
        title="Model family",
    )

    formula_text = (
        "Score = missed fall rate * high-confidence missed-fall rate"
    )

    fig.text(
        0.5,
        0.075,
        formula_text,
        ha="center",
        fontsize=9,
    )

    caption = (
        "Window-level descriptive ranking only. The score is not a clinical risk score, "
        "diagnostic score, calibrated confidence score, or medical-device safety score."
    )
    fig.text(0.5, 0.032, caption, ha="center", fontsize=9)

    fig.subplots_adjust(left=0.27, right=0.96, top=0.88, bottom=0.17)

    fig.savefig(OUTPUT_FIGURE, dpi=300, bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)


def create_note(rows):
    lines = []
    lines.append("# Thesis Figure 13: Confidence-Safety Failure Ranking")
    lines.append("")
    lines.append("This figure visualizes the Table 13 confidence-safety failure ranking as a horizontal bar chart.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Output Figure")
    lines.append("")
    lines.append("- `figures/thesis_figure_13_confidence_safety_failure_ranking.png`")
    lines.append("")
    lines.append("## Input File")
    lines.append("")
    lines.append("- `results/thesis_table_13_confidence_safety_failure_ranking.csv`")
    lines.append("")
    lines.append("## Descriptive Score Definition")
    lines.append("")
    lines.append("```text")
    lines.append("confidence-safety failure score = missed fall rate * high-confidence missed-fall rate")
    lines.append("```")
    lines.append("")
    lines.append("This score is a descriptive ranking score only. It is not a clinical risk score, diagnostic score, regulatory score, calibrated confidence score, or medical-device safety score.")
    lines.append("")
    lines.append("## Figure Data")
    lines.append("")
    lines.append("| Rank | Condition | Missed Fall Rate | High-Confidence Missed-Fall Rate | Failure Score | Recall | F1-score | Balanced Accuracy |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|---:|")

    for row in rows:
        lines.append(
            f"| {row['rank_by_confidence_safety_failure_score']} "
            f"| {row['display_condition']} "
            f"| {row['missed_fall_rate']} "
            f"| {row['high_confidence_missed_fall_rate']} "
            f"| {row['confidence_safety_failure_score']} "
            f"| {row['recall_sensitivity']} "
            f"| {row['f1_score']} "
            f"| {row['balanced_accuracy']} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("Figure 13 is the visual companion to Table 13. It makes the confidence-safety failure ranking easier to interpret.")
    lines.append("")
    lines.append("The undefended PGD condition ranks highest because it combines missed fall rate 1.000000 with high-confidence missed-fall rate 0.820225. The undefended FGSM condition ranks second because it also misses all fall windows but has a lower high-confidence missed-fall rate.")
    lines.append("")
    lines.append("The defended attacked conditions still miss all 89 fall windows, but their confidence-safety failure scores are much lower than the undefended attacked conditions because their high-confidence missed-fall rates are lower.")
    lines.append("")
    lines.append("This supports the same careful interpretation as Figure 12 and Table 13: the short defended model reduced overconfident missed-fall behavior, but it did not restore fall-detection safety performance.")
    lines.append("")
    lines.append("This figure should be interpreted as a window-level descriptive ranking only. It does not estimate clinical risk, event-level fall risk, long-lie risk, time-to-alarm risk, or medical-device safety.")

    OUTPUT_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rows = read_rows()
    create_figure(rows)
    create_note(rows)

    print("Created Thesis Figure 13 outputs:")
    print(f"  {OUTPUT_FIGURE}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Figure 13 visualizes:")
    print("  confidence-safety failure score ranking")


if __name__ == "__main__":
    main()