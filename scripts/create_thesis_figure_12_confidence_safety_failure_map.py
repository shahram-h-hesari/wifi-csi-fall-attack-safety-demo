from pathlib import Path
import csv

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse


BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = BASE_DIR / "figures"
NOTES_DIR = BASE_DIR / "notes"

SAFETY_INPUT_CSV = RESULTS_DIR / "defended_vs_undefended_safety_comparison.csv"
CONFIDENCE_INPUT_CSV = RESULTS_DIR / "thesis_table_12_model_confidence_error_summary.csv"

OUTPUT_FIGURE = FIGURES_DIR / "thesis_figure_12_confidence_safety_failure_map.png"
OUTPUT_NOTE = NOTES_DIR / "thesis_figure_12_confidence_safety_failure_map.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level confidence-safety failure map; "
    "model confidence means predicted-class probability/confidence from the model output, "
    "not calibrated clinical confidence; software-level processed-tensor perturbations only; "
    "not clinical validation, not medical-device validation, not diagnostic evidence, "
    "not real patient deployment, not regulatory evaluation, not event-level fall validation, "
    "not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, "
    "and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation."
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
    "undefended_clean": "Undefended clean",
    "undefended_fgsm_epsilon_0_03": "Undefended FGSM",
    "undefended_pgd_epsilon_0_03": "Undefended PGD",
    "defended_clean": "Defended clean",
    "defended_fgsm_epsilon_0_03": "Defended FGSM",
    "defended_pgd_epsilon_0_03": "Defended PGD",
}

MODEL_FAMILY = {
    "undefended_clean": "Undefended",
    "undefended_fgsm_epsilon_0_03": "Undefended",
    "undefended_pgd_epsilon_0_03": "Undefended",
    "defended_clean": "Defended",
    "defended_fgsm_epsilon_0_03": "Defended",
    "defended_pgd_epsilon_0_03": "Defended",
}

MARKERS = {
    "undefended_clean": "o",
    "undefended_fgsm_epsilon_0_03": "^",
    "undefended_pgd_epsilon_0_03": "s",
    "defended_clean": "o",
    "defended_fgsm_epsilon_0_03": "^",
    "defended_pgd_epsilon_0_03": "s",
}

MAIN_LABEL_OFFSETS = {
    "undefended_clean": (14, 14),
    "undefended_fgsm_epsilon_0_03": (-78, 14),
    "undefended_pgd_epsilon_0_03": (-78, -18),
    "defended_clean": (16, 14),
}

ZOOM_LABEL_OFFSETS = {
    "defended_fgsm_epsilon_0_03": (18, -22),
    "defended_pgd_epsilon_0_03": (18, 14),
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


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")

    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_rows():
    safety_rows = read_csv(SAFETY_INPUT_CSV)
    confidence_rows = read_csv(CONFIDENCE_INPUT_CSV)

    safety_by_condition = {row["condition"]: row for row in safety_rows}

    missed_confidence_by_condition = {
        row["condition"]: row
        for row in confidence_rows
        if row["window_group"] == "missed_fall_windows"
    }

    missing_safety = [
        condition for condition in CONDITION_ORDER
        if condition not in safety_by_condition
    ]

    missing_confidence = [
        condition for condition in CONDITION_ORDER
        if condition not in missed_confidence_by_condition
    ]

    if missing_safety:
        raise ValueError(f"Missing safety rows for: {missing_safety}")

    if missing_confidence:
        raise ValueError(f"Missing missed-fall confidence rows for: {missing_confidence}")

    output_rows = []

    for condition in CONDITION_ORDER:
        safety_row = safety_by_condition[condition]
        confidence_row = missed_confidence_by_condition[condition]

        output_rows.append(
            {
                "condition": condition,
                "display_condition": DISPLAY_NAMES[condition],
                "model_family": MODEL_FAMILY[condition],
                "missed_fall_rate": safe_float(safety_row["missed_fall_rate"]),
                "missed_fall_windows": safe_int(confidence_row["n_windows"]),
                "mean_missed_fall_confidence": safe_float(confidence_row["mean_prediction_confidence"]),
                "median_missed_fall_confidence": safe_float(confidence_row["median_prediction_confidence"]),
                "high_confidence_missed_fall_rate": safe_float(confidence_row["high_confidence_rate"]),
            }
        )

    return output_rows


def get_family_colors():
    default_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    return {
        "Undefended": default_colors[0],
        "Defended": default_colors[1],
    }


def plot_single_point(ax, row, family_colors, point_size=170):
    condition = row["condition"]
    family = row["model_family"]

    ax.scatter(
        row["missed_fall_rate"],
        row["high_confidence_missed_fall_rate"],
        s=point_size,
        alpha=0.85,
        edgecolors="black",
        linewidths=0.9,
        marker=MARKERS[condition],
        color=family_colors[family],
        zorder=3,
    )


def add_label(ax, row, offset):
    condition = row["condition"]

    if condition in [
        "defended_fgsm_epsilon_0_03",
        "defended_pgd_epsilon_0_03",
    ]:
        label_text = (
            f"{row['display_condition']}\n"
            f"high-conf.={row['high_confidence_missed_fall_rate']:.2f}"
        )
    else:
        label_text = (
            f"{row['display_condition']}\n"
            f"high-conf. rate={row['high_confidence_missed_fall_rate']:.2f}"
        )

    ax.annotate(
        label_text,
        xy=(row["missed_fall_rate"], row["high_confidence_missed_fall_rate"]),
        xytext=offset,
        textcoords="offset points",
        fontsize=8,
        ha="left" if offset[0] >= 0 else "right",
        va="center",
        arrowprops={
            "arrowstyle": "-",
            "linewidth": 0.8,
            "color": "dimgray",
            "shrinkA": 0,
            "shrinkB": 5,
        },
        bbox={
            "boxstyle": "round,pad=0.20",
            "facecolor": "white",
            "alpha": 0.90,
            "linewidth": 0.4,
        },
        zorder=4,
    )


def create_figure(rows):
    family_colors = get_family_colors()

    fig = plt.figure(figsize=(13.2, 7.8))
    grid = fig.add_gridspec(
        nrows=1,
        ncols=2,
        width_ratios=[3.1, 1.25],
        wspace=0.25,
    )

    ax_main = fig.add_subplot(grid[0, 0])
    ax_zoom = fig.add_subplot(grid[0, 1])

    for row in rows:
        plot_single_point(ax_main, row, family_colors, point_size=175)

    for row in rows:
        condition = row["condition"]
        if condition in MAIN_LABEL_OFFSETS:
            add_label(ax_main, row, MAIN_LABEL_OFFSETS[condition])

    defended_cluster = Ellipse(
        xy=(1.0, 0.129),
        width=0.080,
        height=0.090,
        angle=0,
        fill=False,
        linestyle="--",
        linewidth=1.1,
        edgecolor="dimgray",
        zorder=2,
    )
    ax_main.add_patch(defended_cluster)

    ax_main.annotate(
        "Defended attacked cluster\nexpanded in Panel B",
        xy=(1.0, 0.129),
        xytext=(-155, 34),
        textcoords="offset points",
        fontsize=8,
        ha="right",
        va="center",
        arrowprops={
            "arrowstyle": "-",
            "linewidth": 0.8,
            "color": "dimgray",
            "shrinkA": 0,
            "shrinkB": 8,
        },
        bbox={
            "boxstyle": "round,pad=0.22",
            "facecolor": "white",
            "alpha": 0.90,
            "linewidth": 0.4,
        },
        zorder=4,
    )

    ax_main.set_title(
        "A. Overall confidence-safety map (right/up = higher concern)",
        pad=12,
    )
    ax_main.set_xlabel("Missed fall rate")
    ax_main.set_ylabel("High-confidence missed-fall rate")
    ax_main.set_xlim(-0.04, 1.12)
    ax_main.set_ylim(-0.07, 1.08)
    ax_main.grid(alpha=0.28, zorder=0)

    defended_attack_rows = [
        row
        for row in rows
        if row["condition"] in [
            "defended_fgsm_epsilon_0_03",
            "defended_pgd_epsilon_0_03",
        ]
    ]

    for row in defended_attack_rows:
        plot_single_point(ax_zoom, row, family_colors, point_size=180)
        add_label(
            ax_zoom,
            row,
            ZOOM_LABEL_OFFSETS[row["condition"]],
        )

    ax_zoom.set_title("B. Zoom on defended attacks", pad=12)
    ax_zoom.set_xlabel("Missed fall rate")
    ax_zoom.set_ylabel("High-confidence missed-fall rate")
    ax_zoom.set_xlim(0.985, 1.015)
    ax_zoom.set_ylim(0.10, 0.15)
    ax_zoom.grid(alpha=0.28, zorder=0)
    ax_zoom.tick_params(axis="both", labelsize=8)

    family_legend = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Undefended model",
            markerfacecolor=family_colors["Undefended"],
            markeredgecolor="black",
            markersize=8,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Defended model",
            markerfacecolor=family_colors["Defended"],
            markeredgecolor="black",
            markersize=8,
        ),
    ]

    attack_legend = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="black",
            label="Clean",
            markerfacecolor="white",
            linestyle="None",
            markersize=7,
        ),
        Line2D(
            [0],
            [0],
            marker="^",
            color="black",
            label="FGSM",
            markerfacecolor="white",
            linestyle="None",
            markersize=7,
        ),
        Line2D(
            [0],
            [0],
            marker="s",
            color="black",
            label="PGD",
            markerfacecolor="white",
            linestyle="None",
            markersize=7,
        ),
    ]

    fig.legend(
        handles=family_legend,
        loc="lower center",
        bbox_to_anchor=(0.36, 0.075),
        ncol=2,
        frameon=True,
        title="Model family",
    )

    fig.legend(
        handles=attack_legend,
        loc="lower center",
        bbox_to_anchor=(0.73, 0.075),
        ncol=3,
        frameon=True,
        title="Condition type",
    )

    fig.suptitle(
        "Thesis Figure 12: Confidence-Safety Failure Map",
        y=0.96,
        fontsize=14,
    )

    caption = (
        "Window-level safety-confidence map only. No clinical thresholds are shown. "
        "Point labels report high-confidence missed-fall rate. "
        "Model confidence is not calibrated clinical confidence."
    )
    fig.text(0.5, 0.025, caption, ha="center", fontsize=9)

    fig.subplots_adjust(left=0.08, right=0.97, top=0.86, bottom=0.24)

    fig.savefig(OUTPUT_FIGURE, dpi=300, bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)


def create_note(rows):
    lines = []
    lines.append("# Thesis Figure 12: Confidence-Safety Failure Map")
    lines.append("")
    lines.append("This figure maps each condition using missed fall rate and high-confidence missed-fall rate.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Output Figure")
    lines.append("")
    lines.append("- `figures/thesis_figure_12_confidence_safety_failure_map.png`")
    lines.append("")
    lines.append("## Input Files")
    lines.append("")
    lines.append("- `results/defended_vs_undefended_safety_comparison.csv`")
    lines.append("- `results/thesis_table_12_model_confidence_error_summary.csv`")
    lines.append("")
    lines.append("## Figure Panels")
    lines.append("")
    lines.append("```text")
    lines.append("Panel A = overall confidence-safety map")
    lines.append("Panel B = zoomed view of defended attacked conditions")
    lines.append("Dashed oval in Panel A marks the defended attacked cluster shown in Panel B")
    lines.append("```")
    lines.append("")
    lines.append("## Axes")
    lines.append("")
    lines.append("```text")
    lines.append("x-axis = missed fall rate")
    lines.append("y-axis = high-confidence missed-fall rate")
    lines.append("circle = clean")
    lines.append("triangle = FGSM")
    lines.append("square = PGD")
    lines.append("Point labels report high-confidence missed-fall rate.")
    lines.append("No clinical threshold lines are shown.")
    lines.append("```")
    lines.append("")
    lines.append("## Figure Data")
    lines.append("")
    lines.append("| Condition | Missed Fall Rate | Missed Fall Windows | Mean Missed-Fall Confidence | Median Missed-Fall Confidence | High-Confidence Missed-Fall Rate |")
    lines.append("|---|---:|---:|---:|---:|---:|")

    for row in rows:
        lines.append(
            f"| {row['display_condition']} "
            f"| {fmt(row['missed_fall_rate'])} "
            f"| {row['missed_fall_windows']} "
            f"| {fmt(row['mean_missed_fall_confidence'])} "
            f"| {fmt(row['median_missed_fall_confidence'])} "
            f"| {fmt(row['high_confidence_missed_fall_rate'])} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("Figure 12 combines safety failure and confidence failure into one map. Moving right means the condition misses more fall windows. Moving upward means missed fall windows are more often high-confidence errors.")
    lines.append("")
    lines.append("The upper-right area of Panel A represents the highest-concern region because both missed fall rate and high-confidence missed-fall rate are high. In this experiment, the undefended PGD condition is the strongest confidence-safety failure case: it misses all 89 fall windows and has a high-confidence missed-fall rate of 0.820225.")
    lines.append("")
    lines.append("The defended attacked conditions remain far to the right because they still miss all 89 fall windows at epsilon 0.030. However, they are much lower on the y-axis because their high-confidence missed-fall rates are much lower than the undefended attacked conditions. Panel B separates defended FGSM and defended PGD so their small difference is visible.")
    lines.append("")
    lines.append("No clinical threshold lines are shown in the figure. The map is intended as a descriptive visualization of relative window-level safety-confidence behavior, not as a clinical decision chart.")
    lines.append("")
    lines.append("These values are window-level model-reported confidence and safety-proxy metrics only. They are not clinical risk estimates, calibrated clinical confidence, diagnostic certainty, or medical-device validation metrics.")

    OUTPUT_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rows = build_rows()
    create_figure(rows)
    create_note(rows)

    print("Created Thesis Figure 12 outputs:")
    print(f"  {OUTPUT_FIGURE}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Figure 12 combines:")
    print("  missed fall rate")
    print("  high-confidence missed-fall rate")


if __name__ == "__main__":
    main()