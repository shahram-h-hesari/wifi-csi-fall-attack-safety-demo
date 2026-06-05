from pathlib import Path
import csv
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


RESULTS_DIR = Path("results")
FIGURES_DIR = Path("figures")
NOTES_DIR = Path("notes")

TABLE_PATH = RESULTS_DIR / "thesis_table_21_claim_boundary_evidence_matrix.csv"
FIGURE_PATH = FIGURES_DIR / "thesis_figure_21_claim_boundary_evidence_matrix.png"
NOTE_PATH = NOTES_DIR / "thesis_table_21_figure_21_claim_boundary_evidence_matrix.md"
README_PATH = Path("README.md")


DIRECT = "Directly supported now"
PROXY = "Window-level proxy only"
FUTURE = "Future work needed"

STATUS_COLORS = {
    DIRECT: "#1f9d55",
    PROXY: "#f2a65a",
    FUTURE: "#d9d9d9",
}

TEXT_COLORS = {
    DIRECT: "white",
    PROXY: "black",
    FUTURE: "black",
}


EVIDENCE_ROWS = [
    {
        "evidence_item": "Software-level FGSM/PGD adversarial stress test",
        "figure_label": "Software-level FGSM/PGD stress test",
        "current_support_label": DIRECT,
        "supported_by_current_outputs": "Yes",
        "current_evidence": "FGSM and PGD prediction files are used across Tables/Figures 1-20.",
        "claim_currently_supported": "Current outputs support software-level adversarial stress testing on processed CSI-derived tensors.",
        "not_supported_yet": "This is not an over-the-air, packet-level, preamble-level, or SDR attack validation.",
        "future_evidence_needed": "Physical-layer implementation, channel measurements, packet traces, SDR experiments, or controlled RF tests.",
        "recommended_claim_language": "Software-level adversarial stress test",
    },
    {
        "evidence_item": "Defended vs undefended comparison",
        "figure_label": "Defended vs undefended comparison",
        "current_support_label": DIRECT,
        "supported_by_current_outputs": "Yes",
        "current_evidence": "Defended clean, defended FGSM, and defended PGD outputs are compared against undefended conditions.",
        "claim_currently_supported": "Current outputs support descriptive comparison of defended and undefended model behavior.",
        "not_supported_yet": "This does not establish a certified, clinically safe, or deployment-ready defense.",
        "future_evidence_needed": "Multiple defenses, hyperparameter sweeps, certified bounds, cross-dataset tests, and external validation.",
        "recommended_claim_language": "Defended-vs-undefended descriptive comparison",
    },
    {
        "evidence_item": "Same-window paired clean/attack/defense transitions",
        "figure_label": "Same-window safety-state transitions",
        "current_support_label": DIRECT,
        "supported_by_current_outputs": "Yes",
        "current_evidence": "Table/Figure 15 and Table/Figure 20 track matched sample IDs across conditions.",
        "claim_currently_supported": "Current outputs support paired same-window transition analysis across clean, attack, and defended conditions.",
        "not_supported_yet": "This is not subject-level, room-level, or event-level temporal tracking.",
        "future_evidence_needed": "Subject IDs, room IDs, trial IDs, and event timestamps.",
        "recommended_claim_language": "Paired window-level transition analysis",
    },
    {
        "evidence_item": "Reproducible table/figure workflow",
        "figure_label": "Reproducible table/figure workflow",
        "current_support_label": DIRECT,
        "supported_by_current_outputs": "Yes",
        "current_evidence": "The repository includes scripts, CSV result tables, PNG figures, companion notes, and README updates for the thesis artifacts.",
        "claim_currently_supported": "Current outputs support a reproducible research-artifact workflow for this demo.",
        "not_supported_yet": "This does not prove external reproducibility across independent datasets, subjects, rooms, or laboratories.",
        "future_evidence_needed": "Independent reruns, cross-dataset replication, environment lock files, and external validation.",
        "recommended_claim_language": "Reproducible table/figure workflow",
    },
    {
        "evidence_item": "Window-level fall-vs-non-fall safety proxy",
        "figure_label": "Fall-vs-non-fall safety proxy",
        "current_support_label": PROXY,
        "supported_by_current_outputs": "Yes, as a window-level proxy",
        "current_evidence": "Tables/Figures 1-20 evaluate TP, FN, FP, TN and derived safety-proxy metrics at the window level.",
        "claim_currently_supported": "Current outputs support descriptive window-level fall-vs-non-fall safety-proxy analysis.",
        "not_supported_yet": "This does not prove clinical event-level fall detection or medical-device performance.",
        "future_evidence_needed": "Event-level fall annotations, clinical protocol, and prospective validation.",
        "recommended_claim_language": "Window-level safety-proxy analysis",
    },
    {
        "evidence_item": "Missed-fall-rate / recall degradation proxy",
        "figure_label": "Missed-fall-rate / recall degradation",
        "current_support_label": PROXY,
        "supported_by_current_outputs": "Yes, as a window-level proxy",
        "current_evidence": "Tables/Figures 1-14 and Figure 20 quantify fall-window TP/FN behavior, recall loss, and missed-fall persistence.",
        "claim_currently_supported": "Current outputs support descriptive window-level missed-fall-rate and recall-degradation proxy analysis.",
        "not_supported_yet": "This does not prove event-level missed falls, long-lie outcomes, or clinical rescue delay.",
        "future_evidence_needed": "Event-level fall IDs, timestamps, alert policy, and clinical/caregiving context.",
        "recommended_claim_language": "Window-level missed-fall / recall-degradation proxy",
    },
    {
        "evidence_item": "False-alert trustworthiness / PPV composition",
        "figure_label": "False-alert trustworthiness / PPV",
        "current_support_label": PROXY,
        "supported_by_current_outputs": "Yes, as a window-level proxy",
        "current_evidence": "Table/Figure 16 separates predicted fall alerts into true fall alerts and false fall alerts.",
        "claim_currently_supported": "Current outputs support window-level alert-composition and PPV/trustworthiness analysis.",
        "not_supported_yet": "This is not alarm burden per hour/day and not clinical alarm-fatigue validation.",
        "future_evidence_needed": "Continuous recordings, time duration per window, deployment logs, and clinician/caregiver alarm review.",
        "recommended_claim_language": "Window-level alert-trustworthiness proxy",
    },
    {
        "evidence_item": "Class-normalized false-fall-alarm sources",
        "figure_label": "Class-normalized false-alert sources",
        "current_support_label": PROXY,
        "supported_by_current_outputs": "Yes, as a window-level proxy",
        "current_evidence": "Tables/Figures 17-18 identify non-fall activity classes that generate false fall alerts and defense changes.",
        "claim_currently_supported": "Current outputs support class-normalized false-fall-alarm source analysis.",
        "not_supported_yet": "This does not establish real-home false alarm frequency or caregiver burden.",
        "future_evidence_needed": "Long-duration home recordings and real deployment time denominators.",
        "recommended_claim_language": "Window-level false-alert source analysis",
    },
    {
        "evidence_item": "Missed-fall destination classes",
        "figure_label": "Missed-fall destination classes",
        "current_support_label": PROXY,
        "supported_by_current_outputs": "Yes, as a window-level proxy",
        "current_evidence": "Table/Figure 19 shows which non-fall classes true fall windows are predicted as when missed.",
        "claim_currently_supported": "Current outputs support missed-fall destination analysis at the window level.",
        "not_supported_yet": "This does not prove clinical severity of one destination class versus another.",
        "future_evidence_needed": "Clinical interpretation, event timing, activity context, and patient-risk metadata.",
        "recommended_claim_language": "Window-level missed-fall destination analysis",
    },
    {
        "evidence_item": "Fall-window recovery and failure persistence",
        "figure_label": "Fall-window recovery / persistence",
        "current_support_label": PROXY,
        "supported_by_current_outputs": "Yes, as a window-level proxy",
        "current_evidence": "Table/Figure 20 tracks clean TP -> attack FN and attack FN -> defended TP/FN.",
        "claim_currently_supported": "Current outputs support paired fall-window recovery and persistence analysis.",
        "not_supported_yet": "This does not prove recovery of real fall events or prevention of long-lie outcomes.",
        "future_evidence_needed": "Event-level detection timing and clinical outcome mapping.",
        "recommended_claim_language": "Window-level fall-recovery proxy",
    },
    {
        "evidence_item": "Event-level fall detection",
        "figure_label": "Event-level fall detection",
        "current_support_label": FUTURE,
        "supported_by_current_outputs": "No",
        "current_evidence": "Current outputs use sample/window IDs, not full fall-event IDs.",
        "claim_currently_supported": "Current outputs do not support event-level fall detection claims.",
        "not_supported_yet": "One real fall event may contain multiple windows; current analysis should not count windows as separate events.",
        "future_evidence_needed": "Event IDs, start/end times, trial labels, and event-level aggregation rules.",
        "recommended_claim_language": "Future event-level validation needed",
    },
    {
        "evidence_item": "Detection latency / time-to-alarm",
        "figure_label": "Detection latency / time-to-alarm",
        "current_support_label": FUTURE,
        "supported_by_current_outputs": "No",
        "current_evidence": "Current prediction files do not include timestamps or event onset times.",
        "claim_currently_supported": "Current outputs do not support detection-latency or time-to-alarm claims.",
        "not_supported_yet": "Cannot estimate delayed rescue or time-to-alert without temporal information.",
        "future_evidence_needed": "Timestamps, sampling rate, window duration, window stride, event onset time, and alert policy.",
        "recommended_claim_language": "Future time-to-alarm analysis needed",
    },
    {
        "evidence_item": "False alarms per hour/day",
        "figure_label": "False alarms per hour/day",
        "current_support_label": FUTURE,
        "supported_by_current_outputs": "No",
        "current_evidence": "Current outputs count false-positive windows but do not provide monitoring duration.",
        "claim_currently_supported": "Current outputs do not support false alarms per hour/day.",
        "not_supported_yet": "Window count cannot be converted to real alarm burden without time denominators and alert aggregation.",
        "future_evidence_needed": "Continuous recording duration, window stride, alarm aggregation rule, and deployment context.",
        "recommended_claim_language": "Future alarm-burden analysis needed",
    },
    {
        "evidence_item": "Long-lie / delayed-rescue risk",
        "figure_label": "Long-lie / delayed-rescue risk",
        "current_support_label": FUTURE,
        "supported_by_current_outputs": "No",
        "current_evidence": "Current outputs quantify missed windows, not duration after a fall event.",
        "claim_currently_supported": "Current outputs do not support long-lie or delayed-rescue claims.",
        "not_supported_yet": "Long-lie risk requires event timing, alert timing, and outcome assumptions.",
        "future_evidence_needed": "Event-level timeline, alert policy, rescue threshold, and clinical/caregiving context.",
        "recommended_claim_language": "Future long-lie proxy analysis needed",
    },
    {
        "evidence_item": "Subject-level generalization",
        "figure_label": "Subject-level generalization",
        "current_support_label": FUTURE,
        "supported_by_current_outputs": "No",
        "current_evidence": "Current outputs do not report subject IDs or leave-subject-out evaluation.",
        "claim_currently_supported": "Current outputs do not support subject-generalization claims.",
        "not_supported_yet": "Cannot infer robustness across people without subject-stratified evaluation.",
        "future_evidence_needed": "Subject IDs, subject-level splits, leave-one-subject-out or cross-subject experiments.",
        "recommended_claim_language": "Future subject-level generalization needed",
    },
    {
        "evidence_item": "Room/environment-level generalization",
        "figure_label": "Room/environment generalization",
        "current_support_label": FUTURE,
        "supported_by_current_outputs": "No",
        "current_evidence": "Current outputs do not report room IDs, home IDs, or environment splits.",
        "claim_currently_supported": "Current outputs do not support room/environment generalization claims.",
        "not_supported_yet": "Cannot infer transfer across homes or rooms without environment metadata.",
        "future_evidence_needed": "Room IDs, home IDs, device placement metadata, cross-room and cross-home testing.",
        "recommended_claim_language": "Future room-level generalization needed",
    },
    {
        "evidence_item": "Physical-layer / over-the-air attack validation",
        "figure_label": "Physical-layer / over-the-air validation",
        "current_support_label": FUTURE,
        "supported_by_current_outputs": "No",
        "current_evidence": "Current attacks are software perturbations on processed model inputs.",
        "claim_currently_supported": "Current outputs do not support physical-layer or over-the-air attack claims.",
        "not_supported_yet": "No SDR, packet-level, preamble-level, or RF-channel implementation was evaluated.",
        "future_evidence_needed": "SDR or commodity-device testbed, packet traces, CSI capture, channel constraints, and over-the-air experiments.",
        "recommended_claim_language": "Future physical-layer validation needed",
    },
    {
        "evidence_item": "Clinical / regulatory / medical-device validation",
        "figure_label": "Clinical / regulatory validation",
        "current_support_label": FUTURE,
        "supported_by_current_outputs": "No",
        "current_evidence": "Current outputs are research/prototype metrics from a public dataset workflow.",
        "claim_currently_supported": "Current outputs do not support clinical, diagnostic, regulatory, or medical-device claims.",
        "not_supported_yet": "No clinical trial, patient deployment, regulatory protocol, or clinician adjudication was performed.",
        "future_evidence_needed": "IRB/clinical protocol as appropriate, patient/caregiver context, prospective validation, and clinical outcome analysis.",
        "recommended_claim_language": "Research prototype; not clinical validation",
    },
]


def group_rows_by_status(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["current_support_label"]].append(row)
    return grouped


def write_table():
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "evidence_item",
        "figure_label",
        "current_support_label",
        "supported_by_current_outputs",
        "current_evidence",
        "claim_currently_supported",
        "not_supported_yet",
        "future_evidence_needed",
        "recommended_claim_language",
    ]

    with TABLE_PATH.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(EVIDENCE_ROWS)

    return EVIDENCE_ROWS


def add_rectangle(ax, x, y, w, h, facecolor, edgecolor="#4d4d4d", linewidth=1.0):
    rectangle = Rectangle(
        (x, y),
        w,
        h,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
    )
    ax.add_patch(rectangle)
    return rectangle


def draw_column(ax, x, y, w, h, title, rows, color, text_color, item_fontsize, item_step=None):
    add_rectangle(ax, x, y, w, h, facecolor=color, edgecolor="#333333", linewidth=1.1)

    ax.text(
        x + 0.020,
        y + h - 0.038,
        title,
        ha="left",
        va="top",
        fontsize=14.0,
        fontweight="bold",
        color=text_color,
    )

    start_y = y + h - 0.095

    if item_step is None:
        bottom_y = y + 0.050
        step = (start_y - bottom_y) / max(1, len(rows) - 1)
    else:
        step = item_step

    for index, row in enumerate(rows):
        item_y = start_y - index * step

        ax.text(
            x + 0.032,
            item_y,
            "•",
            ha="center",
            va="center",
            fontsize=15.5,
            fontweight="bold",
            color=text_color,
        )

        ax.text(
            x + 0.055,
            item_y,
            row["figure_label"],
            ha="left",
            va="center",
            fontsize=item_fontsize,
            fontweight="bold",
            color=text_color,
        )


def create_figure(rows):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    grouped = group_rows_by_status(rows)

    fig = plt.figure(figsize=(16.5, 9.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    fig.text(
        0.5,
        0.958,
        "Thesis Figure 21: What the Current Evidence Supports — and What It Does Not",
        ha="center",
        va="top",
        fontsize=19.0,
        fontweight="bold",
    )

    fig.text(
        0.5,
        0.914,
        "Evidence-status summary, not a performance metric.",
        ha="center",
        va="top",
        fontsize=11.8,
    )

    add_rectangle(
        ax,
        0.06,
        0.820,
        0.88,
        0.065,
        facecolor="#eef5ff",
        edgecolor="#6f8fc9",
        linewidth=1.0,
    )

    ax.text(
        0.5,
        0.852,
        (
            "Takeaway: current results support window-level safety-proxy and software-level adversarial stress-test claims;\n"
            "they do not support clinical, event-level, deployment, or physical-layer validation claims."
        ),
        ha="center",
        va="center",
        fontsize=10.5,
        fontweight="bold",
    )

    col_y = 0.250
    col_h = 0.520
    col_w = 0.285
    gap = 0.025

    col1_x = 0.055
    col2_x = col1_x + col_w + gap
    col3_x = col2_x + col_w + gap

    # Column A uses a fixed step so its 4 items are not spread across the full column height.
    draw_column(
        ax,
        x=col1_x,
        y=col_y,
        w=col_w,
        h=col_h,
        title="A. Directly supported now",
        rows=grouped[DIRECT],
        color=STATUS_COLORS[DIRECT],
        text_color=TEXT_COLORS[DIRECT],
        item_fontsize=10.2,
        item_step=0.075,
    )

    draw_column(
        ax,
        x=col2_x,
        y=col_y,
        w=col_w,
        h=col_h,
        title="B. Window-level safety proxies",
        rows=grouped[PROXY],
        color=STATUS_COLORS[PROXY],
        text_color=TEXT_COLORS[PROXY],
        item_fontsize=9.7,
        item_step=None,
    )

    draw_column(
        ax,
        x=col3_x,
        y=col_y,
        w=col_w,
        h=col_h,
        title="C. Future validation required",
        rows=grouped[FUTURE],
        color=STATUS_COLORS[FUTURE],
        text_color=TEXT_COLORS[FUTURE],
        item_fontsize=9.3,
        item_step=None,
    )

    ax.text(
        0.5,
        0.190,
        (
            "Green = directly supported now    |    Orange = window-level proxy only    |    "
            "Gray = future work needed"
        ),
        ha="center",
        va="center",
        fontsize=9.7,
    )

    ax.text(
        0.5,
        0.150,
        "Evidence source: UT-HAR / SenseFi window-level workflow; supports proxy analysis and software-level stress testing, not clinical validation.",
        ha="center",
        va="center",
        fontsize=9.7,
        fontweight="bold",
    )

    ax.text(
        0.5,
        0.108,
        (
            "Purpose: separate defensible current claims from future clinical, event-level, "
            "subject/room-generalization, and physical-layer validation needs."
        ),
        ha="center",
        va="center",
        fontsize=9.8,
    )

    ax.text(
        0.5,
        0.070,
        (
            "Claim boundary: current results support descriptive window-level safety-proxy and software-level "
            "adversarial stress-test analysis only."
        ),
        ha="center",
        va="center",
        fontsize=9.0,
    )

    fig.savefig(FIGURE_PATH, dpi=300, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)


def count_by_support(rows):
    counts = defaultdict(int)
    for row in rows:
        counts[row["current_support_label"]] += 1
    return counts


def write_note(rows):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    counts = count_by_support(rows)
    grouped = group_rows_by_status(rows)

    direct_lines = "\n".join(
        f"- {row['evidence_item']}: {row['recommended_claim_language']}"
        for row in grouped[DIRECT]
    )
    proxy_lines = "\n".join(
        f"- {row['evidence_item']}: {row['recommended_claim_language']}"
        for row in grouped[PROXY]
    )
    future_lines = "\n".join(
        f"- {row['evidence_item']}: {row['recommended_claim_language']}"
        for row in grouped[FUTURE]
    )

    text = f"""# Thesis Table 21 and Figure 21: Claim Boundary and Evidence Strength Matrix

This note documents the claim-boundary and evidence-strength summary for the WiFi CSI Fall Attack-Safety Demo.

## Purpose

Table 21 and Figure 21 ask:

```text
What claims are supported by the current experiment, and what claims require future data, validation, or collaboration?
```

This artifact strengthens the thesis and GitHub repository because it prevents overclaiming while showing a clear path for future collaboration.

## Files Created

```text
Table 21:
{TABLE_PATH}

Figure 21:
{FIGURE_PATH}

Companion note:
{NOTE_PATH}
```

## Evidence Source

```text
UT-HAR / SenseFi window-level research workflow.
```

This supports descriptive window-level proxy analysis and software-level adversarial stress testing. It does not support clinical validation, medical-device validation, event-level fall validation, deployment validation, or physical-layer / over-the-air validation.

## Evidence Strength Categories

```text
Directly supported now = current experiment directly supports this research claim
Window-level proxy only = current result is useful, but only as a window-level clinical-safety proxy
Future work needed = current results should not be used to make this claim yet
```

## Count by Category

```text
Directly supported now: {counts[DIRECT]}
Window-level proxy only: {counts[PROXY]}
Future work needed: {counts[FUTURE]}
```

## Directly Supported Research Claims

{direct_lines}

## Window-Level Proxy Claims

{proxy_lines}

## Claims Requiring Future Evidence

{future_lines}

## Interpretation

The current evidence package strongly supports a research-prototype claim: software-level adversarial perturbations can degrade window-level fall-detection safety proxies, and defended/undefended outputs can be compared using clinical-safety-oriented window-level metrics.

The current evidence package also supports paired same-window transition analysis and a reproducible table/figure workflow, but only supports several clinically motivated interpretations as window-level proxies rather than as clinical or event-level validation.

The current evidence package does not support clinical validation, medical-device validation, patient deployment, event-level fall validation, long-lie validation, false alarms per hour/day, time-to-alarm validation, subject-level generalization, room-level generalization, or over-the-air physical-layer attack validation.

This matrix can be used in the thesis, README, Wiki, and collaboration discussions to clearly separate what is shown now from what future datasets or external partnerships can add.

## Claim Boundary

This is a descriptive claim-boundary and evidence-strength summary based on the current UT-HAR / SenseFi window-level research workflow.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, false alarms per hour/day, time-to-alarm validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
"""

    NOTE_PATH.write_text(text, encoding="utf-8")


def replace_or_append_readme_section(text, section_marker, section):
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


def update_readme():
    section_marker = "### Thesis Table 21 and Figure 21: Claim Boundary and Evidence Strength Matrix"

    section = f"""
{section_marker}

Table 21 and Figure 21 add a claim-boundary and evidence-strength summary.

Files:

```text
results/thesis_table_21_claim_boundary_evidence_matrix.csv
figures/thesis_figure_21_claim_boundary_evidence_matrix.png
notes/thesis_table_21_figure_21_claim_boundary_evidence_matrix.md
```

Purpose:

```text
What claims are supported by the current experiment, and what claims require future data, validation, or collaboration?
```

Evidence source:

```text
UT-HAR / SenseFi window-level research workflow.
```

This supports descriptive window-level proxy analysis and software-level adversarial stress testing. It does not support clinical validation, medical-device validation, event-level fall validation, deployment validation, or physical-layer / over-the-air validation.

Figure 21 separates the evidence into three vertical columns:

```text
A. Directly supported now
B. Window-level safety proxies
C. Future validation required
```

Directly supported now:

```text
software-level FGSM/PGD adversarial stress testing
defended-vs-undefended descriptive comparison
paired same-window transition analysis
reproducible table/figure workflow
```

Supported only as window-level proxies:

```text
window-level fall-vs-non-fall safety proxy
missed-fall-rate / recall degradation proxy
false-alert trustworthiness proxy
class-normalized false-alert source analysis
missed-fall destination analysis
fall-window recovery and persistence analysis
```

Not supported yet:

```text
clinical / regulatory / medical-device validation
event-level fall validation
long-lie validation
false alarms per hour/day
time-to-alarm validation
subject-level generalization
room-level generalization
physical-layer / packet-level / preamble-level / SDR / over-the-air validation
```

Claim boundary: this is a descriptive claim-boundary and evidence-strength summary based on the current window-level research workflow. It is not clinical validation, medical-device validation, event-level validation, long-lie validation, false alarms per hour/day, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.
"""

    if README_PATH.exists():
        text = README_PATH.read_text(encoding="utf-8")
    else:
        text = ""

    updated_text = replace_or_append_readme_section(text, section_marker, section)
    README_PATH.write_text(updated_text, encoding="utf-8")

    if section_marker in text:
        print("README Table 21 / Figure 21 section replaced.")
    else:
        print("README updated with Table 21 / Figure 21 section.")


def main():
    print("Creating Thesis Table 21 and Figure 21...")

    rows = write_table()
    create_figure(rows)
    write_note(rows)
    update_readme()

    print("\nCreated outputs:")
    print(f"- {TABLE_PATH}")
    print(f"- {FIGURE_PATH}")
    print(f"- {NOTE_PATH}")
    print("- README.md updated")

    print("\nEvidence-strength count:")
    counts = count_by_support(rows)
    for label in [DIRECT, PROXY, FUTURE]:
        print(f"- {label}: {counts[label]}")


if __name__ == "__main__":
    main()
