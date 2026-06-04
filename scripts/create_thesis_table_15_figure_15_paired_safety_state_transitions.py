from pathlib import Path
import csv
from collections import defaultdict

import matplotlib.pyplot as plt


RESULTS_DIR = Path("results")
FIGURES_DIR = Path("figures")
NOTES_DIR = Path("notes")

TABLE_PATH = RESULTS_DIR / "thesis_table_15_paired_safety_state_transition_table.csv"
FIGURE_PATH = FIGURES_DIR / "thesis_figure_15_paired_safety_state_transition_heatmap.png"
NOTE_PATH = NOTES_DIR / "thesis_table_15_figure_15_paired_safety_state_transitions.md"
README_PATH = Path("README.md")

STATE_ORDER = ["TP", "FN", "FP", "TN"]

INPUT_FILES = {
    "clean": RESULTS_DIR / "clean_predictions_short.csv",
    "fgsm": RESULTS_DIR / "fgsm_predictions_short_epsilon_0_03.csv",
    "pgd": RESULTS_DIR / "pgd_predictions_short_epsilon_0_03.csv",
    "defended_fgsm": RESULTS_DIR / "defended_fgsm_predictions_short_epsilon_0_03.csv",
    "defended_pgd": RESULTS_DIR / "defended_pgd_predictions_short_epsilon_0_03.csv",
}


def read_csv_by_sample_id(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required input file: {path}")

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = {}
        for row in reader:
            sample_id = int(row["sample_id"])
            rows[sample_id] = row

    return rows


def to_int(value):
    return int(float(str(value).strip()))


def safety_state(true_binary, pred_binary):
    true_binary = to_int(true_binary)
    pred_binary = to_int(pred_binary)

    if true_binary == 1 and pred_binary == 1:
        return "TP"
    if true_binary == 1 and pred_binary == 0:
        return "FN"
    if true_binary == 0 and pred_binary == 1:
        return "FP"
    if true_binary == 0 and pred_binary == 0:
        return "TN"

    raise ValueError(f"Unexpected binary values: true={true_binary}, pred={pred_binary}")


def build_condition_states():
    clean = read_csv_by_sample_id(INPUT_FILES["clean"])
    fgsm = read_csv_by_sample_id(INPUT_FILES["fgsm"])
    pgd = read_csv_by_sample_id(INPUT_FILES["pgd"])
    defended_fgsm = read_csv_by_sample_id(INPUT_FILES["defended_fgsm"])
    defended_pgd = read_csv_by_sample_id(INPUT_FILES["defended_pgd"])

    common_ids = set(clean)
    for rows in [fgsm, pgd, defended_fgsm, defended_pgd]:
        common_ids = common_ids.intersection(set(rows))

    if not common_ids:
        raise ValueError("No common sample_id values found across required prediction files.")

    common_ids = sorted(common_ids)

    states = {
        "Clean": {},
        "FGSM attack": {},
        "PGD attack": {},
        "Defended FGSM": {},
        "Defended PGD": {},
    }

    for sample_id in common_ids:
        true_clean = clean[sample_id]["fall_true_binary"]

        true_values_to_check = [
            fgsm[sample_id]["fall_true_binary"],
            pgd[sample_id]["fall_true_binary"],
            defended_fgsm[sample_id]["fall_true_binary"],
            defended_pgd[sample_id]["fall_true_binary"],
        ]

        for true_value in true_values_to_check:
            if to_int(true_value) != to_int(true_clean):
                raise ValueError(f"fall_true_binary mismatch at sample_id={sample_id}")

        states["Clean"][sample_id] = safety_state(
            true_clean,
            clean[sample_id]["fall_pred_binary"],
        )

        states["FGSM attack"][sample_id] = safety_state(
            true_clean,
            fgsm[sample_id]["attacked_fall_pred_binary"],
        )

        states["PGD attack"][sample_id] = safety_state(
            true_clean,
            pgd[sample_id]["fall_pred_binary"],
        )

        states["Defended FGSM"][sample_id] = safety_state(
            true_clean,
            defended_fgsm[sample_id]["fall_pred_binary_fgsm_defended"],
        )

        states["Defended PGD"][sample_id] = safety_state(
            true_clean,
            defended_pgd[sample_id]["fall_pred_binary_pgd_defended"],
        )

    return common_ids, states


def transition_interpretation(from_state, to_state):
    if from_state == "TP" and to_state == "FN":
        return "Detected fall window became a missed-fall window."
    if from_state == "FN" and to_state == "TP":
        return "Missed-fall window became detected fall window."
    if from_state == "TN" and to_state == "FP":
        return "Correct non-fall window became false fall alarm."
    if from_state == "FP" and to_state == "TN":
        return "False fall alarm became correct non-fall window."
    if from_state == "FP" and to_state == "FP":
        return "False fall alarm persisted."
    if from_state == "FN" and to_state == "FN":
        return "Missed-fall state persisted."
    if from_state == to_state:
        return "Safety state unchanged."

    return f"Window changed safety state from {from_state} to {to_state}."


def compute_transition_rows(sample_ids, states):
    comparisons = [
        {
            "comparison_id": "clean_to_fgsm",
            "from_condition": "Clean",
            "to_condition": "FGSM attack",
            "comparison_label": "Clean -> FGSM attack",
        },
        {
            "comparison_id": "clean_to_pgd",
            "from_condition": "Clean",
            "to_condition": "PGD attack",
            "comparison_label": "Clean -> PGD attack",
        },
        {
            "comparison_id": "fgsm_to_defended_fgsm",
            "from_condition": "FGSM attack",
            "to_condition": "Defended FGSM",
            "comparison_label": "FGSM attack -> Defended FGSM",
        },
        {
            "comparison_id": "pgd_to_defended_pgd",
            "from_condition": "PGD attack",
            "to_condition": "Defended PGD",
            "comparison_label": "PGD attack -> Defended PGD",
        },
    ]

    all_rows = []
    matrices = {}

    for comparison in comparisons:
        from_condition = comparison["from_condition"]
        to_condition = comparison["to_condition"]

        counts = defaultdict(int)
        from_totals = defaultdict(int)

        for sample_id in sample_ids:
            from_state = states[from_condition][sample_id]
            to_state = states[to_condition][sample_id]

            counts[(from_state, to_state)] += 1
            from_totals[from_state] += 1

        matrix = []
        for from_state in STATE_ORDER:
            matrix_row = []
            for to_state in STATE_ORDER:
                matrix_row.append(counts[(from_state, to_state)])
            matrix.append(matrix_row)

        matrices[comparison["comparison_label"]] = matrix

        for from_state in STATE_ORDER:
            for to_state in STATE_ORDER:
                count = counts[(from_state, to_state)]
                row_total = from_totals[from_state]
                percentage_within_from_state = count / row_total if row_total else 0.0

                all_rows.append(
                    {
                        "comparison_id": comparison["comparison_id"],
                        "comparison_label": comparison["comparison_label"],
                        "from_condition": from_condition,
                        "to_condition": to_condition,
                        "from_safety_state": from_state,
                        "to_safety_state": to_state,
                        "transition": f"{from_state} -> {to_state}",
                        "count": count,
                        "from_state_total": row_total,
                        "percentage_within_from_state": f"{percentage_within_from_state:.6f}",
                        "total_paired_windows": len(sample_ids),
                        "interpretation": transition_interpretation(from_state, to_state),
                    }
                )

    return all_rows, matrices


def write_table(rows):
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "comparison_id",
        "comparison_label",
        "from_condition",
        "to_condition",
        "from_safety_state",
        "to_safety_state",
        "transition",
        "count",
        "from_state_total",
        "percentage_within_from_state",
        "total_paired_windows",
        "interpretation",
    ]

    with TABLE_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def background_luminance(image, value):
    rgba = image.cmap(image.norm(value))
    red, green, blue = rgba[0], rgba[1], rgba[2]
    return 0.299 * red + 0.587 * green + 0.114 * blue


def annotation_style(image, value, global_max):
    if value == 0:
        return {
            "color": "#d8d8d8",
            "fontsize": 9,
            "fontweight": "normal",
        }

    luminance = background_luminance(image, value)

    if luminance < 0.45:
        text_color = "white"
    else:
        text_color = "black"

    if value >= global_max * 0.70:
        fontweight = "bold"
    else:
        fontweight = "semibold"

    return {
        "color": text_color,
        "fontsize": 10,
        "fontweight": fontweight,
    }


def create_heatmap_figure(matrices):
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)

    global_max = 0
    for matrix in matrices.values():
        matrix_max = max(max(row) for row in matrix) if matrix else 0
        global_max = max(global_max, matrix_max)

    if global_max == 0:
        global_max = 1

    fig = plt.figure(figsize=(18.0, 12.2))

    grid = fig.add_gridspec(
        nrows=2,
        ncols=3,
        width_ratios=[1.0, 1.0, 0.04],
        left=0.08,
        right=0.92,
        top=0.86,
        bottom=0.23,
        wspace=0.28,
        hspace=0.46,
    )

    axes = [
        fig.add_subplot(grid[0, 0]),
        fig.add_subplot(grid[0, 1]),
        fig.add_subplot(grid[1, 0]),
        fig.add_subplot(grid[1, 1]),
    ]
    colorbar_axis = fig.add_subplot(grid[:, 2])

    panel_titles = {
        "Clean -> FGSM attack": "A. Clean to FGSM Attack",
        "Clean -> PGD attack": "B. Clean to PGD Attack",
        "FGSM attack -> Defended FGSM": "C. FGSM Attack to Defended FGSM",
        "PGD attack -> Defended PGD": "D. PGD Attack to Defended PGD",
    }

    image = None

    for ax, item in zip(axes, matrices.items()):
        title, matrix = item

        image = ax.imshow(matrix, vmin=0, vmax=global_max)

        row_totals = [sum(row) for row in matrix]
        y_labels = [
            f"{state} (n={row_totals[index]})"
            for index, state in enumerate(STATE_ORDER)
        ]

        ax.set_title(panel_titles.get(title, title), fontsize=14, pad=11)
        ax.set_xlabel("Destination state after transition", fontsize=12)
        ax.set_ylabel("Source state before transition", fontsize=12)

        ax.set_xticks(range(len(STATE_ORDER)))
        ax.set_xticklabels(STATE_ORDER, fontsize=12)
        ax.set_yticks(range(len(STATE_ORDER)))
        ax.set_yticklabels(y_labels, fontsize=11)

        ax.set_xticks([x - 0.5 for x in range(1, len(STATE_ORDER))], minor=True)
        ax.set_yticks([y - 0.5 for y in range(1, len(STATE_ORDER))], minor=True)
        ax.grid(which="minor", color="white", linestyle="-", linewidth=0.9, alpha=0.45)
        ax.tick_params(which="minor", bottom=False, left=False)

        for i, row in enumerate(matrix):
            row_total = sum(row)

            for j, value in enumerate(row):
                if value == 0:
                    label = "0"
                elif row_total > 0:
                    percent = (value / row_total) * 100.0
                    label = f"{value}\n{percent:.1f}%"
                else:
                    label = str(value)

                style = annotation_style(image, value, global_max)

                ax.text(
                    j,
                    i,
                    label,
                    ha="center",
                    va="center",
                    color=style["color"],
                    fontsize=style["fontsize"],
                    fontweight=style["fontweight"],
                )

    if image is not None:
        colorbar = fig.colorbar(image, cax=colorbar_axis)
        colorbar.set_label("Window count, shared scale across panels", fontsize=12)
        colorbar.ax.tick_params(labelsize=11)

    fig.suptitle(
        "Thesis Figure 15: Paired Window-Level Safety-State Transitions",
        fontsize=18,
        y=0.95,
    )

    fig.text(
        0.5,
        0.155,
        (
            "Each panel tracks identical window IDs across two conditions. "
            "Rows are source states before transition; columns are destination states after transition."
        ),
        ha="center",
        fontsize=12,
    )

    fig.text(
        0.5,
        0.125,
        (
            "Cell labels show transition count and percentage within that source-state row, "
            "not percentage of all evaluated windows."
        ),
        ha="center",
        fontsize=11.5,
    )

    fig.text(
        0.5,
        0.095,
        (
            "Row labels show source-state totals; small light-gray zeros indicate zero-count transitions."
        ),
        ha="center",
        fontsize=11,
    )

    fig.text(
        0.5,
        0.060,
        (
            "Claim boundary: descriptive window-level fall-vs-non-fall safety-proxy analysis only; "
            "not clinical validation, event-level validation, long-lie analysis, false alarms per hour/day, or time-to-alarm validation."
        ),
        ha="center",
        fontsize=10.5,
    )

    fig.savefig(FIGURE_PATH, dpi=300, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


def summarize_key_transitions(rows):
    lookup = {}
    for row in rows:
        key = (
            row["comparison_id"],
            row["from_safety_state"],
            row["to_safety_state"],
        )
        lookup[key] = row

    important = [
        (
            "clean_to_fgsm",
            "TP",
            "FN",
            "clean detected falls converted to FGSM missed falls",
        ),
        (
            "clean_to_pgd",
            "TP",
            "FN",
            "clean detected falls converted to PGD missed falls",
        ),
        (
            "clean_to_fgsm",
            "TN",
            "FP",
            "clean correct non-falls converted to FGSM false fall alarms",
        ),
        (
            "clean_to_pgd",
            "TN",
            "FP",
            "clean correct non-falls converted to PGD false fall alarms",
        ),
        (
            "fgsm_to_defended_fgsm",
            "FN",
            "FN",
            "FGSM missed falls that persisted after defense",
        ),
        (
            "pgd_to_defended_pgd",
            "FN",
            "FN",
            "PGD missed falls that persisted after defense",
        ),
        (
            "fgsm_to_defended_fgsm",
            "FP",
            "TN",
            "FGSM false alarms recovered by defense",
        ),
        (
            "pgd_to_defended_pgd",
            "FP",
            "TN",
            "PGD false alarms recovered by defense",
        ),
    ]

    lines = []
    for comparison_id, from_state, to_state, label in important:
        row = lookup.get((comparison_id, from_state, to_state))
        if row:
            percentage = float(row["percentage_within_from_state"]) * 100.0
            lines.append(
                f"- {label}: {row['count']} windows "
                f"({percentage:.2f}% of {from_state} windows in the source condition)."
            )

    return lines


def write_note(rows, sample_count):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    key_lines = summarize_key_transitions(rows)
    key_text = "\n".join(key_lines)

    text = f"""# Thesis Table 15 and Figure 15: Paired Safety-State Transitions

This note documents the paired safety-state transition analysis for the WiFi CSI Fall Attack-Safety Demo.

## Purpose

Table 15 and Figure 15 compare the same evaluated windows across clean, attacked, and defended conditions.

Instead of only reporting aggregate condition-level metrics, this artifact asks:

```text
Which clean true-positive fall detections became missed falls under attack?
Which clean true-negative non-fall windows became false fall alarms under attack?
Which attacked missed-fall or false-alarm windows were recovered by the defended model?
Which attacked safety failures persisted after defense?
```

## Files Created

```text
Table 15:
{TABLE_PATH}

Figure 15:
{FIGURE_PATH}

Companion note:
{NOTE_PATH}
```

## Input Files

```text
{INPUT_FILES["clean"]}
{INPUT_FILES["fgsm"]}
{INPUT_FILES["pgd"]}
{INPUT_FILES["defended_fgsm"]}
{INPUT_FILES["defended_pgd"]}
```

## Safety-State Definition

The analysis maps each evaluated window into one of four binary fall-vs-non-fall safety states:

```text
TP = true fall predicted as fall
FN = true fall predicted as non-fall
FP = true non-fall predicted as fall
TN = true non-fall predicted as non-fall
```

## How to Read the Axes

For each panel:

```text
Y-axis = source safety state before transition
X-axis = destination safety state after transition
```

For example, in the Clean to FGSM Attack panel:

```text
TP row, FN column = windows that were true-positive fall detections in the clean condition and became missed falls under FGSM.
```

## Paired Window Count

```text
Total paired windows analyzed: {sample_count}
```

## Key Transition Findings

{key_text}

## How to Read the Percentages

The percentage shown inside each nonzero heatmap cell is a source-row percentage.

That means:

```text
source-row percentage = transition count / total windows in the source safety-state row
```

It is not the percentage of all evaluated windows.

For example, if a cell says:

```text
57
100.0%
```

then all 57 windows in that source row moved to that destination safety state.

## Interpretation

This analysis strengthens the thesis evidence package because it shows how safety outcomes changed at the same-window level, not only at the aggregate metric level.

The paired transition view is especially useful for explaining adversarial degradation:

```text
clean safety state
-> attacked safety state
-> defended attacked safety state
```

It also helps separate two different defense outcomes:

```text
recovered windows
persistent safety failures
```

The figure uses one shared color scale across all panels. Each nonzero cell shows the transition count and the source-row percentage. Row labels show the number of source-condition windows in each safety state. Small light-gray zero labels indicate zero-count transitions.

In the current short defended model, the most important interpretation remains consistent with Tables/Figures 1-14: the defense reduced some overconfident and false-alarm behavior, but it did not restore fall recall under the tested epsilon 0.030 FGSM/PGD conditions.

## Claim Boundary

This is a descriptive window-level safety-proxy analysis using paired sample IDs from the UT-HAR / SenseFi research workflow.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, false alarms per hour/day, subject-level robustness, trial-level robustness, room-level robustness, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
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
    section_marker = "### Thesis Table 15 and Figure 15: Paired Safety-State Transitions"

    section = f"""
{section_marker}

Table 15 and Figure 15 add a paired same-window transition analysis across clean, attacked, and defended conditions.

Files:

```text
results/thesis_table_15_paired_safety_state_transition_table.csv
figures/thesis_figure_15_paired_safety_state_transition_heatmap.png
notes/thesis_table_15_figure_15_paired_safety_state_transitions.md
```

Purpose:

```text
clean safety state
-> attacked safety state
-> defended attacked safety state
```

This artifact tracks how each evaluated window changes between TP, FN, FP, and TN. It highlights transitions such as clean TP -> attacked FN, clean TN -> attacked FP, attacked FN -> defended FN, and attacked FP -> defended TN.

How to read the figure:

```text
Y-axis = source safety state before transition
X-axis = destination safety state after transition
cell percentage = transition count / total windows in the source safety-state row
```

The cell percentage is not the percentage of all evaluated windows.

The figure uses a shared color scale across all panels. Nonzero cells show the transition count and source-row percentage, while row labels show the source-state window total.

Claim boundary: this is a descriptive window-level safety-proxy paired transition analysis. It is not clinical validation, medical-device validation, event-level fall validation, long-lie validation, time-to-alarm validation, false alarms per hour/day, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.
"""

    if README_PATH.exists():
        text = README_PATH.read_text(encoding="utf-8")
    else:
        text = ""

    updated_text = replace_or_append_readme_section(text, section_marker, section)
    README_PATH.write_text(updated_text, encoding="utf-8")

    if section_marker in text:
        print("README Table 15 / Figure 15 section replaced.")
    else:
        print("README updated with Table 15 / Figure 15 section.")


def main():
    print("Creating Thesis Table 15 and Figure 15...")

    sample_ids, states = build_condition_states()
    rows, matrices = compute_transition_rows(sample_ids, states)

    write_table(rows)
    create_heatmap_figure(matrices)
    write_note(rows, len(sample_ids))
    update_readme()

    print("\nCreated outputs:")
    print(f"- {TABLE_PATH}")
    print(f"- {FIGURE_PATH}")
    print(f"- {NOTE_PATH}")
    print("- README.md updated")

    print("\nKey transition summary:")
    for line in summarize_key_transitions(rows):
        print(line)


if __name__ == "__main__":
    main()