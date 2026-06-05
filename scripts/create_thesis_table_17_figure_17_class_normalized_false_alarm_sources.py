from pathlib import Path
import csv
import math
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


RESULTS_DIR = Path("results")
FIGURES_DIR = Path("figures")
NOTES_DIR = Path("notes")

TABLE_PATH = RESULTS_DIR / "thesis_table_17_class_normalized_false_fall_alarm_sources.csv"
FIGURE_PATH = FIGURES_DIR / "thesis_figure_17_class_normalized_false_fall_alarm_heatmap.png"
NOTE_PATH = NOTES_DIR / "thesis_table_17_figure_17_class_normalized_false_alarm_sources.md"
README_PATH = Path("README.md")


CLASS_ORDER = [
    (0, "lie down"),
    (2, "walk"),
    (3, "pickup"),
    (4, "run"),
    (5, "sit down"),
    (6, "stand up"),
]

CLASS_ID_TO_NAME = {class_id: name for class_id, name in CLASS_ORDER}


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
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "pred_binary_col": "fall_pred_binary",
        "condition_type": "undefended clean",
    },
    {
        "condition_id": "fgsm_attack",
        "condition_label": "FGSM Attack",
        "file_key": "fgsm",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "pred_binary_col": "attacked_fall_pred_binary",
        "condition_type": "undefended attacked",
    },
    {
        "condition_id": "pgd_attack",
        "condition_label": "PGD Attack",
        "file_key": "pgd",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "pred_binary_col": "fall_pred_binary",
        "condition_type": "undefended attacked",
    },
    {
        "condition_id": "defended_clean",
        "condition_label": "Defended Clean",
        "file_key": "defended_clean",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "pred_binary_col": "fall_pred_binary_clean_defended",
        "condition_type": "defended clean",
    },
    {
        "condition_id": "defended_fgsm",
        "condition_label": "Defended FGSM",
        "file_key": "defended_fgsm",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "pred_binary_col": "fall_pred_binary_fgsm_defended",
        "condition_type": "defended attacked",
    },
    {
        "condition_id": "defended_pgd",
        "condition_label": "Defended PGD",
        "file_key": "defended_pgd",
        "true_label_col": "true_label",
        "true_class_col": "true_class_name",
        "pred_binary_col": "fall_pred_binary_pgd_defended",
        "condition_type": "defended attacked",
    },
]


def to_int(value):
    return int(float(str(value).strip()))


def safe_divide(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator


def read_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalize_class_name(name):
    return str(name).strip().lower()


def interpretation_for_row(false_alert_count, total_windows, false_alert_rate, total_false_alerts, share):
    if total_windows == 0:
        return "No windows from this true non-fall class were present in this condition."

    if false_alert_count == 0:
        return "This true non-fall class did not produce false fall alarms in this condition."

    if false_alert_rate >= 0.50:
        return "At least half of this true non-fall class was falsely predicted as fall."

    if false_alert_rate >= 0.25:
        return "This true non-fall class produced a high class-normalized false-fall-alarm rate."

    if share >= 0.50:
        return "This class contributed most of the false fall alarms in this condition, partly reflecting class count and/or class-specific error rate."

    return "This class contributed some false fall alarms, but not as the dominant normalized source."


def build_table_rows():
    table_rows = []
    heatmap_matrix = []
    heatmap_condition_labels = []

    for condition in CONDITIONS:
        path = INPUT_FILES[condition["file_key"]]
        rows = read_rows(path)

        class_totals = defaultdict(int)
        class_false_fall_alerts = defaultdict(int)

        for row in rows:
            true_label = to_int(row[condition["true_label_col"]])
            true_class_name = normalize_class_name(row[condition["true_class_col"]])
            predicted_fall_binary = to_int(row[condition["pred_binary_col"]])

            # Only true non-fall classes are part of this analysis.
            if true_label == 1 or true_class_name == "fall":
                continue

            if true_label not in CLASS_ID_TO_NAME:
                raise ValueError(
                    f"Unexpected non-fall true_label={true_label}, class={true_class_name}"
                )

            class_totals[true_label] += 1

            if predicted_fall_binary == 1:
                class_false_fall_alerts[true_label] += 1

        total_false_fall_alerts = sum(class_false_fall_alerts.values())
        row_rates_for_heatmap = []

        for class_id, class_name in CLASS_ORDER:
            total_windows = class_totals[class_id]
            false_alert_count = class_false_fall_alerts[class_id]
            false_alert_rate = safe_divide(false_alert_count, total_windows)
            share_of_condition_false_alerts = safe_divide(
                false_alert_count,
                total_false_fall_alerts,
            )

            row_rates_for_heatmap.append(false_alert_rate)

            table_rows.append(
                {
                    "condition_id": condition["condition_id"],
                    "condition_label": condition["condition_label"],
                    "condition_type": condition["condition_type"],
                    "true_nonfall_class_id": class_id,
                    "true_nonfall_class_name": class_name,
                    "total_true_windows_for_class": total_windows,
                    "false_fall_alert_count_from_class": false_alert_count,
                    "class_normalized_false_fall_alarm_rate": f"{false_alert_rate:.6f}",
                    "class_normalized_false_fall_alarm_rate_percent": f"{false_alert_rate * 100:.2f}",
                    "total_false_fall_alerts_in_condition": total_false_fall_alerts,
                    "share_of_condition_false_fall_alerts": f"{share_of_condition_false_alerts:.6f}",
                    "share_of_condition_false_fall_alerts_percent": f"{share_of_condition_false_alerts * 100:.2f}",
                    "interpretation": interpretation_for_row(
                        false_alert_count,
                        total_windows,
                        false_alert_rate,
                        total_false_fall_alerts,
                        share_of_condition_false_alerts,
                    ),
                }
            )

        heatmap_matrix.append(row_rates_for_heatmap)
        heatmap_condition_labels.append(condition["condition_label"])

    return table_rows, heatmap_matrix, heatmap_condition_labels


def write_table(rows):
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "condition_id",
        "condition_label",
        "condition_type",
        "true_nonfall_class_id",
        "true_nonfall_class_name",
        "total_true_windows_for_class",
        "false_fall_alert_count_from_class",
        "class_normalized_false_fall_alarm_rate",
        "class_normalized_false_fall_alarm_rate_percent",
        "total_false_fall_alerts_in_condition",
        "share_of_condition_false_fall_alerts",
        "share_of_condition_false_fall_alerts_percent",
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


def create_figure(heatmap_matrix, condition_labels):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    class_labels = [
        "lie\ndown",
        "walk",
        "pickup",
        "run",
        "sit\ndown",
        "stand\nup",
    ]

    max_rate = 0.0
    for row in heatmap_matrix:
        if row:
            max_rate = max(max_rate, max(row))

    if max_rate <= 0:
        color_max = 0.05
    else:
        color_max = math.ceil(max_rate * 20.0) / 20.0

    # More compact and balanced layout than the previous wide dashboard-like version.
    fig = plt.figure(figsize=(13.2, 9.2))

    grid = fig.add_gridspec(
        nrows=1,
        ncols=2,
        width_ratios=[1.0, 0.04],
        left=0.14,
        right=0.88,
        top=0.82,
        bottom=0.36,
        wspace=0.06,
    )

    ax = fig.add_subplot(grid[0, 0])
    colorbar_axis = fig.add_subplot(grid[0, 1])

    image = ax.imshow(
        heatmap_matrix,
        vmin=0,
        vmax=color_max,
        aspect="equal",
    )

    ax.set_title(
        "Thesis Figure 17: Non-Fall Classes Causing False Fall Alerts",
        fontsize=16,
        pad=16,
    )
    ax.set_xlabel("True non-fall activity class", fontsize=12, labelpad=12)
    ax.set_ylabel("Condition", fontsize=12)

    ax.set_xticks(range(len(class_labels)))
    ax.set_xticklabels(class_labels, fontsize=11)
    ax.set_yticks(range(len(condition_labels)))
    ax.set_yticklabels(condition_labels, fontsize=11)

    ax.set_xticks([x - 0.5 for x in range(1, len(class_labels))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(condition_labels))], minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.9, alpha=0.45)
    ax.tick_params(which="minor", bottom=False, left=False)

    for i, row in enumerate(heatmap_matrix):
        row_max = max(row) if row else 0.0

        for j, rate in enumerate(row):
            percent = rate * 100.0

            if percent == 0:
                label = "0"
            else:
                label = f"{percent:.1f}%"

            luminance = background_luminance(image, rate)
            text_color = "white" if luminance < 0.45 else "black"

            # The highest value in each row is the strongest normalized source
            # for that condition, so use slightly stronger text weight.
            is_row_max = rate > 0 and abs(rate - row_max) < 1e-12

            fontweight = "bold" if is_row_max or percent > 0 else "normal"
            fontsize = 10 if percent > 0 else 9

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
    colorbar.set_label("Class-normalized false-alert rate (%)", fontsize=11)
    colorbar.ax.tick_params(labelsize=10)
    colorbar.ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))

    tick_step = 0.05
    tick_count = int(round(color_max / tick_step)) + 1
    colorbar.set_ticks([tick_step * index for index in range(tick_count)])

    fig.text(
        0.5,
        0.265,
        (
            "Each cell = false fall alerts from that true class / total true windows of that class."
        ),
        ha="center",
        fontsize=11,
    )

    fig.text(
        0.5,
        0.235,
        (
            "Cells show percentages; counts and denominators are reported in Table 17."
        ),
        ha="center",
        fontsize=10.5,
    )

    fig.text(
        0.5,
        0.205,
        (
            "Higher values identify non-fall activities more likely to be misclassified as fall within each condition."
        ),
        ha="center",
        fontsize=10.5,
    )

    fig.text(
        0.5,
        0.150,
        (
            "Claim boundary: descriptive window-level class-normalized false-alert analysis only; "
            "not clinical validation, event-level validation,"
        ),
        ha="center",
        fontsize=9.6,
    )

    fig.text(
        0.5,
        0.123,
        (
            "false alarms per hour/day, long-lie analysis, or time-to-alarm validation."
        ),
        ha="center",
        fontsize=9.6,
    )

    fig.savefig(FIGURE_PATH, dpi=300, bbox_inches="tight", pad_inches=0.24)
    plt.close(fig)


def top_sources_by_condition(table_rows):
    grouped = defaultdict(list)

    for row in table_rows:
        grouped[row["condition_label"]].append(row)

    lines = []
    for condition_label, rows in grouped.items():
        sorted_rows = sorted(
            rows,
            key=lambda row: (
                float(row["class_normalized_false_fall_alarm_rate"]),
                int(row["false_fall_alert_count_from_class"]),
            ),
            reverse=True,
        )

        top = sorted_rows[0]
        lines.append(
            f"- {condition_label}: highest normalized source = "
            f"{top['true_nonfall_class_name']} "
            f"({top['class_normalized_false_fall_alarm_rate_percent']}%, "
            f"{top['false_fall_alert_count_from_class']}/"
            f"{top['total_true_windows_for_class']} windows)."
        )

    return lines


def write_note(table_rows):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    top_lines = "\n".join(top_sources_by_condition(table_rows))

    text = f"""# Thesis Table 17 and Figure 17: Class-Normalized False-Fall-Alarm Sources

This note documents the class-normalized false-fall-alarm source analysis for the WiFi CSI Fall Attack-Safety Demo.

## Purpose

Table 17 and Figure 17 ask:

```text
Which true non-fall activities are most likely to be falsely predicted as fall?
```

This is different from counting false fall alarms only. A class can produce many false fall alarms because it has many windows, or because the model has a high class-specific tendency to confuse that activity with fall.

## Files Created

```text
Table 17:
{TABLE_PATH}

Figure 17:
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

## Metric Definition

For each condition and each true non-fall class:

```text
class-normalized false-fall-alarm rate =
false fall alerts from that true class / total true windows of that class
```

The heatmap cells show this value as a percentage. Counts and denominators are reported in Table 17.

## Key Findings

{top_lines}

## Interpretation

This artifact strengthens the thesis because it identifies which non-fall activities are most vulnerable to being misclassified as fall.

Raw false-alert counts alone can be misleading because they depend on how many windows each activity class contributes. The class-normalized view makes the error source more interpretable by asking whether a class has a high false-fall-alarm rate relative to its own class size.

Higher heatmap values identify non-fall activities that are more likely to be misclassified as fall within each condition.

## Claim Boundary

This is a descriptive window-level class-normalized false-alert source analysis using UT-HAR / SenseFi prediction outputs.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, false alarms per hour/day, long-lie validation, time-to-alarm validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
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
    section_marker = "### Thesis Table 17 and Figure 17: Class-Normalized False-Fall-Alarm Sources"

    section = f"""
{section_marker}

Table 17 and Figure 17 add a class-normalized false-fall-alarm source analysis.

Files:

```text
results/thesis_table_17_class_normalized_false_fall_alarm_sources.csv
figures/thesis_figure_17_class_normalized_false_fall_alarm_heatmap.png
notes/thesis_table_17_figure_17_class_normalized_false_alarm_sources.md
```

Purpose:

```text
Which true non-fall activities are most likely to be falsely predicted as fall?
```

Metric definition:

```text
class-normalized false-fall-alarm rate =
false fall alerts from that true class / total true windows of that class
```

The heatmap cells show percentages. Counts and denominators are reported in Table 17.

This artifact avoids relying only on raw false-alert counts. It distinguishes whether a class is a false-alert source because it has many windows or because it has a high class-specific false-fall-alarm rate.

Claim boundary: this is a descriptive window-level class-normalized false-alert source analysis. It is not clinical validation, medical-device validation, event-level fall validation, false alarms per hour/day, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.
"""

    if README_PATH.exists():
        text = README_PATH.read_text(encoding="utf-8")
    else:
        text = ""

    updated_text = replace_or_append_readme_section(text, section_marker, section)
    README_PATH.write_text(updated_text, encoding="utf-8")

    if section_marker in text:
        print("README Table 17 / Figure 17 section replaced.")
    else:
        print("README updated with Table 17 / Figure 17 section.")


def main():
    print("Creating Thesis Table 17 and Figure 17...")

    table_rows, heatmap_matrix, condition_labels = build_table_rows()

    write_table(table_rows)
    create_figure(heatmap_matrix, condition_labels)
    write_note(table_rows)
    update_readme()

    print("\nCreated outputs:")
    print(f"- {TABLE_PATH}")
    print(f"- {FIGURE_PATH}")
    print(f"- {NOTE_PATH}")
    print("- README.md updated")

    print("\nTop class-normalized false-fall-alarm source by condition:")
    for line in top_sources_by_condition(table_rows):
        print(line)


if __name__ == "__main__":
    main()