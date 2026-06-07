from __future__ import annotations

import csv
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


# =============================================================================
# Paths
# =============================================================================

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_DIR = SCRIPT_PATH.parent.parent

README_PATH = PROJECT_DIR / "README.md"
RESULTS_DIR = PROJECT_DIR / "results"
FIGURES_DIR = PROJECT_DIR / "figures"
NOTES_DIR = PROJECT_DIR / "notes"

TABLE_PATH = RESULTS_DIR / "thesis_table_22_thesis_artifact_evidence_map.csv"
FIGURE_PATH = FIGURES_DIR / "thesis_figure_22_thesis_artifact_evidence_map.png"
NOTE_PATH = NOTES_DIR / "thesis_table_22_figure_22_thesis_artifact_evidence_map.md"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Content
# =============================================================================

COLUMNS = [
    {
        "column_id": 1,
        "title": "1. Research Workflow",
        "color": "#16538C",
        "sections": [
            {
                "section_title": "A. Dataset / Workflow",
                "section_role": "Research workflow foundation",
                "items": [
                    "UT-HAR / SenseFi workflow",
                    "Workflow setup + metadata audit",
                    "Output index / artifact inventory",
                    "Baseline fall-safety summary",
                ],
            },
            {
                "section_title": "B. Software Attack Stress Test",
                "section_role": "Attack degradation test",
                "items": [
                    "FGSM attack results",
                    "PGD attack results",
                    "Epsilon-sweep summaries",
                    "Clean-vs-attacked comparisons",
                ],
            },
            {
                "section_title": "C. Defense Comparison",
                "section_role": "Defended vs undefended comparison",
                "items": [
                    "Defended vs undefended behavior",
                    "Matched attack-defense effect",
                    "Paired safety-state transitions",
                    "Defense-effect heatmap",
                ],
            },
        ],
        "summary": (
            "This column explains what was run in the demo: dataset/workflow setup, "
            "software FGSM/PGD stress testing, and defended-vs-undefended comparison."
        ),
    },
    {
        "column_id": 2,
        "title": "2. Safety-Proxy Findings",
        "color": "#C66F10",
        "sections": [
            {
                "section_title": "A. Safety-Proxy Metrics",
                "section_role": "Window-level safety evidence",
                "items": [
                    "TP / FN / FP / TN safety metrics",
                    "Recall and missed-fall-rate proxy",
                    "False-alert proxy",
                    "Safety tradeoff summary",
                ],
            },
            {
                "section_title": "B. Alert Trustworthiness",
                "section_role": "Alert composition and source analysis",
                "items": [
                    "Alert trustworthiness / PPV proxy",
                    "Fall-alert composition",
                    "False-alert source classes",
                    "Class-normalized false-alert sources",
                ],
            },
            {
                "section_title": "C. Failure-Pattern Analysis",
                "section_role": "Failure-mode evidence",
                "items": [
                    "Missed-fall destination classes",
                    "Fall-window recovery / persistence",
                    "Attack-defense failure patterns",
                    "Claim-boundary evidence summary",
                ],
            },
        ],
        "summary": (
            "This column summarizes the evidence products produced by the demo: "
            "safety-proxy metrics, alert-trustworthiness analysis, and failure-pattern analysis."
        ),
    },
    {
        "column_id": 3,
        "title": "3. Collaboration Pathway",
        "color": "#16786F",
        "sections": [
            {
                "section_title": "A. What We Can Support Now",
                "section_role": "Current defensible scope",
                "items": [
                    "Window-level safety indicators",
                    "Software attack stress testing",
                    "Descriptive defense comparison",
                    "Reproducible research workflow",
                ],
            },
            {
                "section_title": "B. Richer Datasets Could Enable",
                "section_role": "Next validation targets",
                "items": [
                    "Event-level fall validation",
                    "Time-to-alarm and alarm burden",
                    "Long-lie / delayed-rescue analysis",
                    "Subject / room / site generalization",
                    "Clinical and care-setting relevance",
                ],
            },
            {
                "section_title": "C. Partner Data That Would Help",
                "section_role": "Useful richer-data examples",
                "items": [
                    "Event IDs and timestamps",
                    "Monitoring duration and alarm counts",
                    "Subject / room metadata",
                    "Realistic home/care-setting data",
                    "Cross-dataset replication opportunities",
                ],
            },
        ],
        "summary": (
            "This column makes the collaboration opportunity explicit by separating what the current demo "
            "can support from what richer real-world or partner-owned datasets could enable next."
        ),
    },
]


# =============================================================================
# Helpers
# =============================================================================

def wrap_lines(text: str, width: int) -> list[str]:
    return textwrap.wrap(
        text,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [""]


def wrap_text(text: str, width: int) -> str:
    return "\n".join(wrap_lines(text, width))


def replace_or_append_readme_section(text: str, section_marker: str, section: str) -> str:
    if section_marker not in text:
        return text.rstrip() + "\n\n" + section.lstrip()

    start = text.find(section_marker)
    before = text[:start].rstrip()

    next_heading = text.find("\n### ", start + len(section_marker))
    if next_heading == -1:
        after = ""
    else:
        after = text[next_heading:].lstrip()

    if after:
        return before + "\n\n" + section.lstrip().rstrip() + "\n\n" + after

    return before + "\n\n" + section.lstrip().rstrip() + "\n"


def add_round_rect(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    facecolor: str,
    edgecolor: str = "#1F2937",
    linewidth: float = 1.4,
    rounding: float = 0.018,
    zorder: float = 1,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.008,rounding_size={rounding}",
        linewidth=linewidth,
        edgecolor=edgecolor,
        facecolor=facecolor,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def draw_multiline_text(
    ax,
    x: float,
    y: float,
    text: str,
    width: int,
    fontsize: float,
    color: str,
    fontweight: str = "normal",
    line_height: float = 0.016,
    ha: str = "left",
    zorder: int = 3,
) -> float:
    """Draw wrapped text and return y-coordinate below the drawn text."""
    lines = wrap_lines(text, width)

    for index, line in enumerate(lines):
        ax.text(
            x,
            y - index * line_height,
            line,
            ha=ha,
            va="top",
            fontsize=fontsize,
            color=color,
            fontweight=fontweight,
            zorder=zorder,
        )

    return y - len(lines) * line_height


# =============================================================================
# Table generation
# =============================================================================

def build_table_rows() -> list[dict]:
    rows = []

    for column in COLUMNS:
        for section in column["sections"]:
            for item in section["items"]:
                rows.append(
                    {
                        "column_id": column["column_id"],
                        "column_title": column["title"],
                        "column_summary": column["summary"],
                        "section_title": section["section_title"],
                        "section_role": section["section_role"],
                        "artifact_or_theme": item,
                    }
                )

    return rows


def write_table(rows: list[dict]) -> None:
    fieldnames = [
        "column_id",
        "column_title",
        "column_summary",
        "section_title",
        "section_role",
        "artifact_or_theme",
    ]

    with TABLE_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# =============================================================================
# Figure drawing
# =============================================================================

def draw_column_panel(ax, column: dict, x: float, y: float, w: float, h: float) -> None:
    add_round_rect(
        ax=ax,
        x=x,
        y=y,
        w=w,
        h=h,
        facecolor=column["color"],
        edgecolor="#1F2937",
        linewidth=1.4,
        rounding=0.020,
        zorder=2,
    )

    inner_left = x + 0.025
    inner_right = x + w - 0.025

    # Column title. This stays close to the previous size because it already looked good.
    ax.text(
        x + w / 2,
        y + h - 0.036,
        column["title"],
        ha="center",
        va="top",
        fontsize=19.2,
        fontweight="bold",
        color="white",
        zorder=3,
    )

    current_y = y + h - 0.096

    # Increased font sizes for sections and items, using the available empty space.
    section_title_font = 14.7
    section_role_font = 10.2
    item_font = 10.6

    section_title_line = 0.020
    section_role_line = 0.016
    item_line = 0.018

    role_gap = 0.006
    before_items_gap = 0.011
    item_gap = 0.011
    after_section_gap = 0.024

    section_title_wrap = 40
    section_role_wrap = 44
    item_wrap = 41

    for section_index, section in enumerate(column["sections"]):
        current_y = draw_multiline_text(
            ax=ax,
            x=inner_left,
            y=current_y,
            text=section["section_title"],
            width=section_title_wrap,
            fontsize=section_title_font,
            color="white",
            fontweight="bold",
            line_height=section_title_line,
        )

        current_y -= role_gap

        current_y = draw_multiline_text(
            ax=ax,
            x=inner_left,
            y=current_y,
            text=section["section_role"],
            width=section_role_wrap,
            fontsize=section_role_font,
            color="#D9E8F7",
            fontweight="normal",
            line_height=section_role_line,
        )

        current_y -= before_items_gap

        for item in section["items"]:
            item_y = current_y

            ax.text(
                inner_left + 0.002,
                item_y,
                "•",
                ha="left",
                va="top",
                fontsize=11.8,
                fontweight="bold",
                color="white",
                zorder=3,
            )

            current_y = draw_multiline_text(
                ax=ax,
                x=inner_left + 0.019,
                y=item_y,
                text=item,
                width=item_wrap,
                fontsize=item_font,
                color="white",
                fontweight="bold",
                line_height=item_line,
            )

            current_y -= item_gap

        current_y -= after_section_gap

        if section_index < len(column["sections"]) - 1:
            separator_y = current_y + 0.011
            ax.plot(
                [inner_left, inner_right],
                [separator_y, separator_y],
                color=(1, 1, 1, 0.24),
                linewidth=1.2,
                zorder=3,
            )


def create_figure() -> None:
    fig = plt.figure(figsize=(20.5, 12.0), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Main title only.
    ax.text(
        0.5,
        0.960,
        "Fall Attack-Safety Demo: Evidence Map and Collaboration Pathway",
        ha="center",
        va="top",
        fontsize=23.5,
        fontweight="bold",
        color="#1E293B",
    )

    # Column layout: taller columns and larger text.
    col_y = 0.145
    col_h = 0.725
    col_w = 0.300
    gap = 0.020

    x_positions = [
        0.035,
        0.035 + col_w + gap,
        0.035 + 2 * (col_w + gap),
    ]

    for x, column in zip(x_positions, COLUMNS):
        draw_column_panel(ax, column, x, col_y, col_w, col_h)

    # Footer
    ax.text(
        0.5,
        0.102,
        "Evidence base: UT-HAR dataset + SenseFi window-level workflow.",
        ha="center",
        va="center",
        fontsize=12.2,
        fontweight="bold",
        color="#111827",
    )

    ax.text(
        0.5,
        0.074,
        (
            "Current scope: proxy analysis and software-level FGSM/PGD stress testing; "
            "not clinical, event-level, deployment, or physical-layer validation."
        ),
        ha="center",
        va="center",
        fontsize=10.2,
        color="#475569",
    )

    ax.text(
        0.5,
        0.048,
        (
            "Collaboration opportunity: event IDs, timestamps, monitoring duration, "
            "subject/room metadata, and care-setting context could enable stronger validation."
        ),
        ha="center",
        va="center",
        fontsize=10.2,
        color="#475569",
    )

    fig.savefig(FIGURE_PATH, dpi=300, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)


# =============================================================================
# Notes
# =============================================================================

def write_note(rows: list[dict]) -> None:
    grouped_text = []

    for column in COLUMNS:
        grouped_text.append(f"## {column['title']}")
        grouped_text.append(column["summary"])
        grouped_text.append("")

        for section in column["sections"]:
            grouped_text.append(f"### {section['section_title']}")
            grouped_text.append(f"Role: {section['section_role']}")
            for item in section["items"]:
                grouped_text.append(f"- {item}")
            grouped_text.append("")

    grouped_body = "\n".join(grouped_text)

    text = f"""# Thesis Table 22 and Figure 22: End-to-End Evidence Map

## Purpose

Table 22 and Figure 22 summarize the full artifact package for the fall attack-safety demo in a form that is useful for research discussion and collaboration meetings.

This version is designed to answer three practical questions:

1. **What was done?**
2. **What evidence was produced?**
3. **Where could collaboration with richer datasets add value?**

## Files Created

**Table 22**  
`{TABLE_PATH}`

**Figure 22**  
`{FIGURE_PATH}`

**Companion note**  
`{NOTE_PATH}`

## Structure of the figure

The figure is organized into three large columns:

- **Research Workflow** — what was run in the demo
- **Evidence Generated** — what the demo measured and revealed
- **What Collaboration Could Enable** — how richer real-world datasets could strengthen validation

{grouped_body}

## Interpretation

The figure is not intended as a performance plot. Instead, it is an **evidence map**.

It shows that the current demo already supports:

- a reproducible window-level workflow,
- software FGSM/PGD attack stress testing,
- descriptive defended-vs-undefended analysis,
- and window-level safety-indicator interpretation.

It also makes the next collaboration opportunity visible:

- event-level validation,
- time-to-alarm and alarm-burden analysis,
- long-lie / delayed-rescue analysis,
- subject / room / site generalization,
- and stronger clinical / care-setting relevance,

all of which would benefit from richer partner-owned datasets.

## Claim Boundary

This is a descriptive artifact-map and collaboration-oriented summary for the UT-HAR / SenseFi fall attack-safety demo.

The current evidence supports:

- window-level proxy analysis,
- software-level FGSM/PGD stress testing,
- descriptive defense comparison,
- and reproducible artifact organization.

The current evidence does **not** establish:

- clinical validation,
- medical-device validation,
- real-patient deployment,
- event-level fall validation,
- false alarms per hour/day,
- time-to-alarm validation,
- long-lie validation,
- subject-level generalization,
- room-level generalization,
- or physical-layer / over-the-air validation.
"""

    NOTE_PATH.write_text(text, encoding="utf-8")


# =============================================================================
# README update
# =============================================================================

def update_readme() -> None:
    section_marker = "### Thesis Table 22 and Figure 22: End-to-End Evidence Map"

    section = f"""
{section_marker}

Table 22 and Figure 22 add a meeting-friendly end-to-end evidence map for the fall attack-safety demo.

**Files**

- `results/thesis_table_22_thesis_artifact_evidence_map.csv`
- `figures/thesis_figure_22_thesis_artifact_evidence_map.png`
- `notes/thesis_table_22_figure_22_thesis_artifact_evidence_map.md`

**Purpose**

This artifact is designed to explain:

1. what was done in the demo,
2. what evidence products were produced,
3. and where collaboration with richer real-world datasets could add value.

**Figure structure**

The figure is organized into three large vertical columns:

- **Research Workflow**
- **Evidence Generated**
- **What Collaboration Could Enable**

**Main message**

Current evidence supports window-level fall-safety analysis and software-level FGSM/PGD stress testing. Richer datasets could enable event-level validation, alarm-burden analysis, long-lie analysis, subject/room generalization, and stronger clinical / care-setting relevance.

**Claim boundary**

The current package supports descriptive window-level proxy analysis and software-level stress testing. It does not by itself establish clinical, event-level, deployment, or physical-layer validation.
"""

    old_text = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
    new_text = replace_or_append_readme_section(old_text, section_marker, section)
    README_PATH.write_text(new_text, encoding="utf-8")

    if section_marker in old_text:
        print("README Table 22 / Figure 22 section replaced.")
    else:
        print("README updated with Table 22 / Figure 22 section.")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    print("Creating Thesis Table 22 and Figure 22...")

    rows = build_table_rows()
    write_table(rows)
    create_figure()
    write_note(rows)
    update_readme()

    print("\nCreated outputs:")
    print(f"- {TABLE_PATH}")
    print(f"- {FIGURE_PATH}")
    print(f"- {NOTE_PATH}")
    print("- README.md updated")

    print("\nEvidence-map structure:")
    for row in rows:
        print(
            f"- {row['column_title']} | {row['section_title']} | {row['artifact_or_theme']}"
        )


if __name__ == "__main__":
    main()
