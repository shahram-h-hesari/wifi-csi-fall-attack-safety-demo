from pathlib import Path
import csv
import math
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


RESULTS_DIR = Path("results")
FIGURES_DIR = Path("figures")
NOTES_DIR = Path("notes")

TABLE_PATH = RESULTS_DIR / "thesis_table_19_missed_fall_destination_classes.csv"
FIGURE_PATH = FIGURES_DIR / "thesis_figure_19_missed_fall_destination_heatmap.png"
NOTE_PATH = NOTES_DIR / "thesis_table_19_figure_19_missed_fall_destination_classes.md"
README_PATH = Path("README.md")


DESTINATION_CLASS_ORDER = [
    (0, "lie down"),
    (2, "walk"),
    (3, "pickup"),
    (4, "run"),
    (5, "sit down"),
    (6, "stand up"),
]

DESTINATION_CLASS_ID_TO_NAME = {
    class_id: class_name for class_id, class_name in DESTINATION_CLASS_ORDER
}


INPUT_FILES = {
    "clean": RESULTS_DIR / "clean_predictions_short.csv",
    "fgsm": RESULTS_DIR / "fgsm_predictions_short_epsilon_0_03.csv",
    "pgd": RESULTS_DIR / "pgd_predictions_short_epsilon_0_03.csv",
    "defended_clean": RESULTS_DIR / "defended_predictions_short.csv",
    "defended_fgsm": RESULTS_DIR / "defended_fgsm_predictions_short_epsilon_0_03.csv",
    "defended_pgd": RESULTS_DIR / "defended_pgd_predictions_short_epsilon_0_03.csv",
}


CONDITIONS = [
    {
        "condition_id": "clean",
        "condition_label": "Clean",
        "file_key": "clean",
        "condition_type": "undefended clean",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "predicted_label_col": "predicted_label",
        "predicted_class_col": "predicted_class_name",
        "fall_true_binary_col": "fall_true_binary",
        "fall_pred_binary_col": "fall_pred_binary",
    },
    {
        "condition_id": "fgsm_attack",
        "condition_label": "FGSM Attack",
        "file_key": "fgsm",
        "condition_type": "undefended attacked",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "predicted_label_col": "attacked_predicted_label",
        "predicted_class_col": "attacked_predicted_class_name",
        "fall_true_binary_col": "fall_true_binary",
        "fall_pred_binary_col": "attacked_fall_pred_binary",
    },
    {
        "condition_id": "pgd_attack",
        "condition_label": "PGD Attack",
        "file_key": "pgd",
        "condition_type": "undefended attacked",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "predicted_label_col": "predicted_label",
        "predicted_class_col": "predicted_class_name",
        "fall_true_binary_col": "fall_true_binary",
        "fall_pred_binary_col": "fall_pred_binary",
    },
    {
        "condition_id": "defended_clean",
        "condition_label": "Defended Clean",
        "file_key": "defended_clean",
        "condition_type": "defended clean",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "predicted_label_col": "defended_clean_predicted_label",
        "predicted_class_col": "defended_clean_predicted_class_name",
        "fall_true_binary_col": "fall_true_binary",
        "fall_pred_binary_col": "fall_pred_binary_clean_defended",
    },
    {
        "condition_id": "defended_fgsm",
        "condition_label": "Defended FGSM",
        "file_key": "defended_fgsm",
        "condition_type": "defended attacked",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "predicted_label_col": "defended_fgsm_predicted_label",
        "predicted_class_col": "defended_fgsm_predicted_class_name",
        "fall_true_binary_col": "fall_true_binary",
        "fall_pred_binary_col": "fall_pred_binary_fgsm_defended",
    },
    {
        "condition_id": "defended_pgd",
        "condition_label": "Defended PGD",
        "file_key": "defended_pgd",
        "condition_type": "defended attacked",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "predicted_label_col": "defended_pgd_predicted_label",
        "predicted_class_col": "defended_pgd_predicted_class_name",
        "fall_true_binary_col": "fall_true_binary",
        "fall_pred_binary_col": "fall_pred_binary_pgd_defended",
    },
]


def to_int(value):
    return int(float(str(value).strip()))


def safe_divide(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator


def normalize_class_name(name):
    return str(name).strip().lower()


def read_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    with path.open("r", newline="", encoding="utf-8") as file_handle:
        return list(csv.DictReader(file_handle))


def interpretation_for_destination(
    destination_count,
    total_true_fall_windows,
    total_missed_fall_windows,
):
    if total_true_fall_windows == 0:
        return "No true fall windows were present in this condition."

    if destination_count == 0:
        return "No missed fall windows were predicted as this destination class."

    destination_rate = safe_divide(destination_count, total_true_fall_windows)
    share_among_missed = safe_divide(destination_count, total_missed_fall_windows)

    if share_among_missed >= 0.50:
        return "This destination class accounts for at least half of missed fall windows in this condition."

    if destination_rate >= 0.25:
        return "A high fraction of true fall windows were missed as this destination class."

    return "This destination class accounts for some missed fall windows in this condition."


def build_table_rows():
    table_rows = []
    heatmap_rate_matrix = []
    heatmap_share_matrix = []
    heatmap_y_labels = []

    for condition in CONDITIONS:
        rows = read_rows(INPUT_FILES[condition["file_key"]])

        total_true_fall_windows = 0
        total_missed_fall_windows = 0
        destination_counts = defaultdict(int)

        for row in rows:
            true_label = to_int(row[condition["true_label_col"]])
            true_class_name = normalize_class_name(row[condition["true_class_col"]])
            fall_true_binary = to_int(row[condition["fall_true_binary_col"]])
            fall_pred_binary = to_int(row[condition["fall_pred_binary_col"]])
            predicted_label = to_int(row[condition["predicted_label_col"]])
            predicted_class_name = normalize_class_name(
                row[condition["predicted_class_col"]]
            )

            is_true_fall = (
                fall_true_binary == 1
                or true_label == 1
                or true_class_name == "fall"
            )

            if not is_true_fall:
                continue

            total_true_fall_windows += 1

            # Only false-negative fall windows are included.
            if fall_pred_binary == 1:
                continue

            total_missed_fall_windows += 1

            if predicted_class_name == "fall" or predicted_label == 1:
                raise ValueError(
                    "Missed-fall binary state conflicts with predicted fall class: "
                    f"condition={condition['condition_label']}, "
                    f"predicted_label={predicted_label}, "
                    f"predicted_class_name={predicted_class_name}"
                )

            if predicted_label not in DESTINATION_CLASS_ID_TO_NAME:
                raise ValueError(
                    f"Unexpected missed-fall destination label={predicted_label}, "
                    f"class={predicted_class_name}, "
                    f"condition={condition['condition_label']}"
                )

            destination_counts[predicted_label] += 1

        missed_fall_rate = safe_divide(
            total_missed_fall_windows,
            total_true_fall_windows,
        )

        heatmap_rate_row = []
        heatmap_share_row = []

        for destination_class_id, destination_class_name in DESTINATION_CLASS_ORDER:
            destination_count = destination_counts[destination_class_id]

            destination_rate_among_true_fall_windows = safe_divide(
                destination_count,
                total_true_fall_windows,
            )

            share_among_missed_fall_windows = safe_divide(
                destination_count,
                total_missed_fall_windows,
            )

            heatmap_rate_row.append(destination_rate_among_true_fall_windows)
            heatmap_share_row.append(share_among_missed_fall_windows)

            table_rows.append(
                {
                    "condition_id": condition["condition_id"],
                    "condition_label": condition["condition_label"],
                    "condition_type": condition["condition_type"],
                    "missed_fall_destination_class_id": destination_class_id,
                    "missed_fall_destination_class_name": destination_class_name,
                    "total_true_fall_windows": total_true_fall_windows,
                    "total_missed_fall_windows_fn": total_missed_fall_windows,
                    "overall_missed_fall_rate": f"{missed_fall_rate:.6f}",
                    "overall_missed_fall_rate_percent": f"{missed_fall_rate * 100:.2f}",
                    "missed_falls_to_destination_count": destination_count,
                    "destination_rate_among_true_fall_windows": f"{destination_rate_among_true_fall_windows:.6f}",
                    "destination_rate_among_true_fall_windows_percent": f"{destination_rate_among_true_fall_windows * 100:.2f}",
                    "share_among_missed_fall_windows": f"{share_among_missed_fall_windows:.6f}",
                    "share_among_missed_fall_windows_percent": f"{share_among_missed_fall_windows * 100:.2f}",
                    "interpretation": interpretation_for_destination(
                        destination_count,
                        total_true_fall_windows,
                        total_missed_fall_windows,
                    ),
                }
            )

        heatmap_rate_matrix.append(heatmap_rate_row)
        heatmap_share_matrix.append(heatmap_share_row)
        heatmap_y_labels.append(
            f"{condition['condition_label']} "
            f"(FN={total_missed_fall_windows}/{total_true_fall_windows} fall windows)"
        )

    return table_rows, heatmap_rate_matrix, heatmap_share_matrix, heatmap_y_labels


def write_table(rows):
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "condition_id",
        "condition_label",
        "condition_type",
        "missed_fall_destination_class_id",
        "missed_fall_destination_class_name",
        "total_true_fall_windows",
        "total_missed_fall_windows_fn",
        "overall_missed_fall_rate",
        "overall_missed_fall_rate_percent",
        "missed_falls_to_destination_count",
        "destination_rate_among_true_fall_windows",
        "destination_rate_among_true_fall_windows_percent",
        "share_among_missed_fall_windows",
        "share_among_missed_fall_windows_percent",
        "interpretation",
    ]

    with TABLE_PATH.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def background_luminance(image, value):
    rgba = image.cmap(image.norm(value))
    red, green, blue = rgba[0], rgba[1], rgba[2]
    return 0.299 * red + 0.587 * green + 0.114 * blue


def create_figure(heatmap_rate_matrix, heatmap_share_matrix, y_labels):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    x_labels = [
        "lie\ndown",
        "walk",
        "pickup",
        "run",
        "sit\ndown",
        "stand\nup",
    ]

    max_rate = 0.0
    for row in heatmap_rate_matrix:
        if row:
            max_rate = max(max_rate, max(row))

    if max_rate <= 0:
        color_max = 0.05
    else:
        color_max = math.ceil(max_rate * 10.0) / 10.0

    fig = plt.figure(figsize=(16.2, 10.4))

    grid = fig.add_gridspec(
        nrows=1,
        ncols=2,
        width_ratios=[1.0, 0.04],
        left=0.22,
        right=0.90,
        top=0.82,
        bottom=0.35,
        wspace=0.06,
    )

    ax = fig.add_subplot(grid[0, 0])
    colorbar_axis = fig.add_subplot(grid[0, 1])

    image = ax.imshow(
        heatmap_rate_matrix,
        vmin=0,
        vmax=color_max,
        aspect="auto",
    )

    ax.set_title(
        "Predicted Non-Fall Classes for Missed Fall Windows",
        fontsize=16,
        pad=16,
    )

    ax.set_xlabel("Predicted non-fall destination class", fontsize=12, labelpad=10)
    ax.set_ylabel("Condition", fontsize=12)

    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, fontsize=11)
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels, fontsize=9.5)

    ax.set_xticks([x - 0.5 for x in range(1, len(x_labels))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(y_labels))], minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.9, alpha=0.45)
    ax.tick_params(which="minor", bottom=False, left=False)

    for i, row in enumerate(heatmap_rate_matrix):
        for j, rate in enumerate(row):
            destination_percent = rate * 100.0
            share_percent = heatmap_share_matrix[i][j] * 100.0

            if destination_percent == 0:
                label = "0"
            else:
                label = f"{destination_percent:.1f}%\n({share_percent:.1f}% of FN)"

            luminance = background_luminance(image, rate)
            text_color = "white" if luminance < 0.45 else "black"
            fontweight = "bold" if destination_percent > 0 else "normal"
            fontsize = 8.7 if destination_percent > 0 else 9.0

            ax.text(
                j,
                i,
                label,
                ha="center",
                va="center",
                color=text_color,
                fontsize=fontsize,
                fontweight=fontweight,
            )

    colorbar = fig.colorbar(image, cax=colorbar_axis)
    colorbar.set_label(
        "Missed-as-destination rate among true fall windows (%)",
        fontsize=10.8,
    )
    colorbar.ax.tick_params(labelsize=10)
    colorbar.ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))

    tick_step = 0.10
    tick_count = int(round(color_max / tick_step)) + 1
    colorbar.set_ticks([tick_step * index for index in range(tick_count)])

    fig.text(
        0.5,
        0.260,
        "Top cell value = fall windows missed as that predicted class / total true fall windows.",
        ha="center",
        fontsize=10.7,
    )

    fig.text(
        0.5,
        0.232,
        "Parentheses show share of all false-negative fall windows in that row; row labels show FN / total true fall windows.",
        ha="center",
        fontsize=10.3,
    )

    fig.text(
        0.5,
        0.204,
        (
            "Takeaway: attacks miss all true fall windows; defended attacks still miss all "
            "fall windows but redistribute destinations."
        ),
        ha="center",
        fontsize=10.2,
    )

    fig.text(
        0.5,
        0.145,
        (
            "Claim boundary: descriptive window-level missed-fall destination analysis only; "
            "not clinical validation, event-level validation,"
        ),
        ha="center",
        fontsize=9.3,
    )

    fig.text(
        0.5,
        0.119,
        "long-lie analysis, false alarms per hour/day, or time-to-alarm validation.",
        ha="center",
        fontsize=9.3,
    )

    fig.savefig(FIGURE_PATH, dpi=300, bbox_inches="tight", pad_inches=0.24)
    plt.close(fig)


def top_destinations_by_condition(table_rows):
    grouped = defaultdict(list)

    for row in table_rows:
        grouped[row["condition_label"]].append(row)

    lines = []

    for condition_label, rows in grouped.items():
        sorted_rows = sorted(
            rows,
            key=lambda row: (
                int(row["missed_falls_to_destination_count"]),
                float(row["destination_rate_among_true_fall_windows"]),
            ),
            reverse=True,
        )

        top = sorted_rows[0]
        lines.append(
            f"- {condition_label}: top missed-fall destination = "
            f"{top['missed_fall_destination_class_name']} "
            f"({top['missed_falls_to_destination_count']} windows; "
            f"{top['destination_rate_among_true_fall_windows_percent']}% of true fall windows; "
            f"{top['share_among_missed_fall_windows_percent']}% of missed fall windows)."
        )

    return lines


def write_note(table_rows):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    top_lines = "\n".join(top_destinations_by_condition(table_rows))

    text = f"""# Thesis Table 19 and Figure 19: Missed-Fall Destination Classes

This note documents the missed-fall destination analysis for the WiFi CSI Fall Attack-Safety Demo.

## Purpose

Table 19 and Figure 19 ask:

```text
When a true fall window is missed, what non-fall class does the model predict instead?
```

This is useful because the safety meaning of a missed fall window can depend on the predicted destination class. For example, a fall window predicted as lie down, sit down, walk, or stand up may suggest different failure modes and different confusion patterns.

## Files Created

```text
Table 19:
{TABLE_PATH}

Figure 19:
{FIGURE_PATH}

Companion note:
{NOTE_PATH}
```

## Input Files

```text
{INPUT_FILES["clean"]}
{INPUT_FILES["fgsm"]}
{INPUT_FILES["pgd"]}
{INPUT_FILES["defended_clean"]}
{INPUT_FILES["defended_fgsm"]}
{INPUT_FILES["defended_pgd"]}
```

## Metric Definitions

For each condition and each predicted non-fall destination class:

```text
destination rate among true fall windows =
true fall windows missed as that destination class / total true fall windows
```

The figure also reports share among missed fall windows:

```text
share among missed fall windows =
true fall windows missed as that destination class / total missed fall windows
```

Figure 19 uses two complementary percentages:

```text
top cell value = destination rate among true fall windows
parenthetical value = share among missed fall windows in that row
```

## Key Findings

{top_lines}

## Interpretation

This artifact strengthens the thesis because it moves beyond saying that fall windows were missed. It shows what the model predicted instead when it failed to recognize true fall windows.

This is especially important under attack and defended-attack conditions where missed-fall rate can be high. The destination-class view helps identify whether fall windows are being redirected toward particular non-fall activities.

In this tested configuration, FGSM and PGD attacks missed all true fall windows. The defended FGSM and defended PGD conditions also missed all true fall windows, but the destination patterns changed. FGSM and PGD mostly redirected missed fall windows toward walk and run, while defended PGD spread missed-fall destinations across more non-fall classes.

## Claim Boundary

This is a descriptive window-level missed-fall destination analysis using UT-HAR / SenseFi prediction outputs.

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
    section_marker = "### Thesis Table 19 and Figure 19: Missed-Fall Destination Classes"

    section = f"""
{section_marker}

Table 19 and Figure 19 add a missed-fall destination-class analysis.

Files:

```text
results/thesis_table_19_missed_fall_destination_classes.csv
figures/thesis_figure_19_missed_fall_destination_heatmap.png
notes/thesis_table_19_figure_19_missed_fall_destination_classes.md
```

Purpose:

```text
When a true fall window is missed, what non-fall class does the model predict instead?
```

Metric definitions:

```text
destination rate among true fall windows =
true fall windows missed as that destination class / total true fall windows

share among missed fall windows =
true fall windows missed as that destination class / total missed fall windows
```

Figure 19 uses two complementary percentages: the top cell value is the destination rate among true fall windows, while the parenthetical value is the share among missed fall windows in that row.

This artifact complements missed-fall-rate analysis by showing the predicted non-fall destination class for false-negative fall windows.

Claim boundary: this is a descriptive window-level missed-fall destination analysis. It is not clinical validation, medical-device validation, event-level fall validation, long-lie validation, false alarms per hour/day, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.
"""

    if README_PATH.exists():
        text = README_PATH.read_text(encoding="utf-8")
    else:
        text = ""

    updated_text = replace_or_append_readme_section(text, section_marker, section)
    README_PATH.write_text(updated_text, encoding="utf-8")

    if section_marker in text:
        print("README Table 19 / Figure 19 section replaced.")
    else:
        print("README updated with Table 19 / Figure 19 section.")


def main():
    print("Creating Thesis Table 19 and Figure 19...")

    (
        table_rows,
        heatmap_rate_matrix,
        heatmap_share_matrix,
        y_labels,
    ) = build_table_rows()

    write_table(table_rows)
    create_figure(heatmap_rate_matrix, heatmap_share_matrix, y_labels)
    write_note(table_rows)
    update_readme()

    print("\nCreated outputs:")
    print(f"- {TABLE_PATH}")
    print(f"- {FIGURE_PATH}")
    print(f"- {NOTE_PATH}")
    print("- README.md updated")

    print("\nTop missed-fall destination by condition:")
    for line in top_destinations_by_condition(table_rows):
        print(line)


if __name__ == "__main__":
    main()

