"""
Create Thesis Figure 8: Safety Translation Pipeline Diagram.

This version improves spacing, increases box text size, separates the
claim-boundary callout from the Layer 2 boxes, and keeps the design clean.

Layer 1: current computable workflow
Layer 2: current thesis evidence generated from window-level outputs
Layer 3: metadata gap and future event-level extension

Outputs:
    figures/thesis_figure_8_safety_translation_pipeline.png
    notes/thesis_figure_8_safety_translation_pipeline.md
"""

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = ROOT / "figures"
NOTES_DIR = ROOT / "notes"

OUTPUT_FIGURE = FIGURES_DIR / "thesis_figure_8_safety_translation_pipeline.png"
OUTPUT_NOTE = NOTES_DIR / "thesis_figure_8_safety_translation_pipeline.md"

CLAIM_BOUNDARY = (
    "Research implementation only; conceptual safety-translation pipeline; "
    "window-level safety-proxy evaluation; software-level processed-tensor "
    "perturbations only; not clinical validation, not medical-device validation, "
    "not diagnostic evidence, not real patient deployment, not regulatory "
    "evaluation, not event-level fall validation, not long-lie validation, "
    "not time-to-alarm validation, and not physical-layer / packet-level / "
    "preamble-level / SDR / over-the-air validation."
)


def add_box(
    ax,
    x,
    y,
    width,
    height,
    text,
    fontsize=9.6,
    linewidth=1.2,
):
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.04,rounding_size=0.04",
        linewidth=linewidth,
        facecolor="white",
        edgecolor="black",
    )
    ax.add_patch(box)

    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        linespacing=1.15,
    )


def add_arrow(ax, x1, y1, x2, y2, linewidth=1.2):
    arrow = FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        arrowstyle="->",
        mutation_scale=14,
        linewidth=linewidth,
        color="black",
        shrinkA=3,
        shrinkB=3,
    )
    ax.add_patch(arrow)


def add_section_label(ax, x, y, text):
    ax.text(
        x,
        y,
        text,
        ha="left",
        va="center",
        fontsize=11.8,
        fontweight="bold",
    )


def add_section_rule(ax, y):
    ax.plot(
        [0.45, 17.55],
        [y, y],
        color="black",
        linewidth=0.6,
        alpha=0.22,
    )


def create_figure():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(19, 11.5))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 11.0)
    ax.axis("off")

    fig.suptitle(
        "Thesis Figure 8: Safety Translation Pipeline Diagram\n"
        "Current window-level safety-proxy workflow and future event-level metadata requirements",
        fontsize=15.8,
        y=0.975,
    )

    # ================================================================
    # Layer 1
    # ================================================================
    add_section_label(ax, 0.6, 9.25, "Layer 1: Current computable workflow")

    top_y = 7.95
    box_w = 2.45
    box_h = 0.98
    top_x = [0.45, 3.25, 6.05, 8.85, 11.65, 14.45]

    top_boxes = [
        "Processed WiFi CSI\nwindows\nSenseFi / UT-HAR",
        "Clean model\nprediction\nseven-class label",
        "FGSM / PGD\nperturbation\nprocessed CSI",
        "Attacked model\nprediction\nseven-class label",
        "Binary mapping\nfall vs non-fall",
        "Window-level\nsafety metrics\nmissed falls, false alarms",
    ]

    for x, text in zip(top_x, top_boxes):
        add_box(ax, x, top_y, box_w, box_h, text, fontsize=9.4)

    for i in range(len(top_x) - 1):
        add_arrow(
            ax,
            top_x[i] + box_w,
            top_y + box_h / 2,
            top_x[i + 1],
            top_y + box_h / 2,
        )

    add_section_rule(ax, 7.15)

    # ================================================================
    # Layer 2
    # ================================================================
    add_section_label(
        ax,
        0.6,
        6.6,
        "Layer 2: Current thesis evidence generated from window-level outputs",
    )

    # Claim boundary is a separate callout above the row, not connected by arrows.
    add_box(
        ax,
        13.35,
        5.95,
        3.85,
        0.8,
        "Claim boundary\nwindow-level only\nnot clinical validation",
        fontsize=9.0,
        linewidth=1.4,
    )

    evidence_y = 4.75
    evidence_w = 3.55
    evidence_h = 0.98
    evidence_x = [0.8, 4.95, 9.1, 13.25]

    evidence_boxes = [
        "Robustness threshold\ntranslation\nfirst epsilon crossing",
        "Multiclass error\ntaxonomy\nmissed-fall pathways",
        "Safety-proxy\nsummary metrics\nrecall, F1, false alarms",
        "Reproducible\nGitHub artifacts\nscripts, notes, figures",
    ]

    for x, text in zip(evidence_x, evidence_boxes):
        add_box(ax, x, evidence_y, evidence_w, evidence_h, text, fontsize=9.2)

    ax.text(
        9,
        4.15,
        "Layer 2 summarizes outputs from Layer 1 into thesis-ready tables, figures, scripts, and notes.",
        ha="center",
        va="center",
        fontsize=9.3,
    )

    add_section_rule(ax, 3.75)

    # ================================================================
    # Layer 3
    # ================================================================
    add_section_label(
        ax,
        0.6,
        3.35,
        "Layer 3: Metadata gap and future event-level extension",
    )

    ax.text(
        9,
        2.95,
        "The metadata audit limits the current demo to window-level metrics and identifies what future datasets must provide.",
        ha="center",
        va="center",
        fontsize=9.3,
    )

    bottom_y = 1.75
    bottom_w = 3.8
    bottom_h = 1.0
    bottom_x = [0.8, 5.1, 9.4, 13.7]

    bottom_boxes = [
        "Current UT-HAR\nmetadata gap\nno timestamp, event ID,\nsubject/trial ID, duration",
        "Future dataset /\ncollaboration need\nevent IDs, timestamps,\nfall onset, alert time",
        "Future event-level\nmetrics\ntime-to-detection,\nlong-lie proxy",
        "Future extension\nnot claimed in\ncurrent demo",
    ]

    for x, text in zip(bottom_x, bottom_boxes):
        add_box(ax, x, bottom_y, bottom_w, bottom_h, text, fontsize=9.2)

    for i in range(len(bottom_x) - 1):
        add_arrow(
            ax,
            bottom_x[i] + bottom_w,
            bottom_y + bottom_h / 2,
            bottom_x[i + 1],
            bottom_y + bottom_h / 2,
        )

    ax.text(
        9,
        0.8,
        "Current contribution: translate adversarial degradation into window-level fall safety-proxy metrics. "
        "Future requirement: richer metadata for event-level clinical-safety metrics.",
        ha="center",
        va="center",
        fontsize=9.7,
    )

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(OUTPUT_FIGURE, dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_note():
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Thesis Figure 8: Safety Translation Pipeline Diagram")
    lines.append("")
    lines.append(
        "This figure summarizes the safety-translation pipeline used in the "
        "WiFi CSI Fall Attack-Safety Demo."
    )
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Output Figure")
    lines.append("")
    lines.append("- `figures/thesis_figure_8_safety_translation_pipeline.png`")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append(
        "The figure explains how the current workflow translates WiFi CSI model "
        "outputs into window-level safety-proxy evidence while separating current "
        "computable outputs from future event-level requirements."
    )
    lines.append("")
    lines.append("The current pipeline is:")
    lines.append("")
    lines.append("```text")
    lines.append("processed WiFi CSI windows")
    lines.append("-> clean model prediction")
    lines.append("-> software-level FGSM / PGD perturbation")
    lines.append("-> attacked prediction")
    lines.append("-> binary fall-vs-non-fall mapping")
    lines.append("-> window-level safety-proxy metrics")
    lines.append("```")
    lines.append("")
    lines.append("## Current Computable Outputs")
    lines.append("")
    lines.append(
        "The current dataset and prediction files support window-level metrics "
        "such as missed fall rate, false fall alarm count, recall, precision, "
        "F1-score, balanced accuracy, robustness thresholds, and multiclass "
        "error-taxonomy analysis."
    )
    lines.append("")
    lines.append("## Current Thesis Evidence")
    lines.append("")
    lines.append(
        "The current workflow produces thesis-ready tables, figures, scripts, "
        "and notes that compare clean, attacked, and defended model behavior. "
        "These outputs support window-level safety-proxy analysis, robustness "
        "threshold analysis, and multiclass error interpretation."
    )
    lines.append("")
    lines.append("## Metadata Gap")
    lines.append("")
    lines.append(
        "The local UT-HAR copy does not provide event IDs, timestamps, subject IDs, "
        "trial IDs, recording duration, fall onset time, alert time, or monitoring "
        "duration. Therefore, event-level metrics are not computed in this demo."
    )
    lines.append("")
    lines.append("## Future Extension")
    lines.append("")
    lines.append(
        "A future dataset or collaboration with richer metadata could support "
        "event-level fall detection rate, time-to-detection, delayed detection, "
        "long-lie proxy, false alarms per hour/day, subject-level robustness, "
        "and trial-level robustness."
    )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Figure 8 is useful for the thesis because it clearly separates the current "
        "research contribution from future clinical-safety extensions. The current "
        "contribution is not clinical validation. It is a reproducible workflow for "
        "translating adversarial degradation into window-level fall safety-proxy "
        "metrics."
    )
    lines.append("")

    OUTPUT_NOTE.write_text("\n".join(lines), encoding="utf-8")


def main():
    create_figure()
    write_note()

    print("Created improved Thesis Figure 8 outputs:")
    print(f"  {OUTPUT_FIGURE}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Figure 8 summarizes:")
    print("  Layer 1: current computable workflow")
    print("  Layer 2: current thesis evidence")
    print("  Layer 3: metadata gap and future event-level extension")


if __name__ == "__main__":
    main()