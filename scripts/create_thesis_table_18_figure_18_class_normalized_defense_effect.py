from pathlib import Path
import csv
import math
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


RESULTS_DIR = Path("results")
FIGURES_DIR = Path("figures")
NOTES_DIR = Path("notes")

TABLE_PATH = RESULTS_DIR / "thesis_table_18_class_normalized_defense_effect.csv"
FIGURE_PATH = FIGURES_DIR / "thesis_figure_18_class_normalized_defense_effect_heatmap.png"
NOTE_PATH = NOTES_DIR / "thesis_table_18_figure_18_class_normalized_defense_effect.md"
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
    "fgsm": RESULTS_DIR / "fgsm_predictions_short_epsilon_0_03.csv",
    "pgd": RESULTS_DIR / "pgd_predictions_short_epsilon_0_03.csv",
    "defended_fgsm": RESULTS_DIR / "defended_fgsm_predictions_short_epsilon_0_03.csv",
    "defended_pgd": RESULTS_DIR / "defended_pgd_predictions_short_epsilon_0_03.csv",
}


MATCHED_COMPARISONS = [
    {
        "comparison_id": "fgsm_to_defended_fgsm",
        "comparison_label": "FGSM -> Defended FGSM",
        "comparison_label_long": "FGSM Attack -> Defended FGSM",
        "attack_label": "FGSM Attack",
        "defended_label": "Defended FGSM",
        "attack_file_key": "fgsm",
        "defended_file_key": "defended_fgsm",
        "attack_true_label_col": "true_label",
        "attack_true_class_col": "true_class_name",
        "attack_pred_binary_col": "attacked_fall_pred_binary",
        "defended_true_label_col": "true_label",
        "defended_true_class_col": "true_class_name",
        "defended_pred_binary_col": "fall_pred_binary_fgsm_defended",
    },
    {
        "comparison_id": "pgd_to_defended_pgd",
        "comparison_label": "PGD -> Defended PGD",
        "comparison_label_long": "PGD Attack -> Defended PGD",
        "attack_label": "PGD Attack",
        "defended_label": "Defended PGD",
        "attack_file_key": "pgd",
        "defended_file_key": "defended_pgd",
        "attack_true_label_col": "true_label",
        "attack_true_class_col": "true_class_name",
        "attack_pred_binary_col": "fall_pred_binary",
        "defended_true_label_col": "true_label",
        "defended_true_class_col": "true_class_name",
        "defended_pred_binary_col": "fall_pred_binary_pgd_defended",
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


def class_false_alarm_counts(rows, true_label_col, true_class_col, pred_binary_col):
    class_totals = defaultdict(int)
    class_false_fall_alerts = defaultdict(int)

    for row in rows:
        true_label = to_int(row[true_label_col])
        true_class_name = normalize_class_name(row[true_class_col])
        predicted_fall_binary = to_int(row[pred_binary_col])

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

    return class_totals, class_false_fall_alerts


def interpretation_for_change(attack_rate, defended_rate, change_rate, attack_count, defended_count):
    if attack_rate == 0 and defended_rate == 0:
        return "No false fall alarms for this class in either attacked or defended condition."

    if change_rate < -0.10:
        return "Defense substantially reduced the class-normalized false-fall-alarm rate for this class."

    if change_rate < 0:
        return "Defense reduced the class-normalized false-fall-alarm rate for this class."

    if change_rate > 0.10:
        return "Defense substantially increased the class-normalized false-fall-alarm rate for this class."

    if change_rate > 0:
        return "Defense increased the class-normalized false-fall-alarm rate for this class."

    if attack_count != defended_count:
        return "Defense changed raw false-alarm count but not the class-normalized rate after rounding."

    return "No class-normalized change was observed for this class."


def build_table_rows():
    table_rows = []
    heatmap_matrix = []
    heatmap_labels = []

    for comparison in MATCHED_COMPARISONS:
        attack_rows = read_rows(INPUT_FILES[comparison["attack_file_key"]])
        defended_rows = read_rows(INPUT_FILES[comparison["defended_file_key"]])

        attack_totals, attack_false_alerts = class_false_alarm_counts(
            attack_rows,
            comparison["attack_true_label_col"],
            comparison["attack_true_class_col"],
            comparison["attack_pred_binary_col"],
        )

        defended_totals, defended_false_alerts = class_false_alarm_counts(
            defended_rows,
            comparison["defended_true_label_col"],
            comparison["defended_true_class_col"],
            comparison["defended_pred_binary_col"],
        )

        row_changes = []

        for class_id, class_name in CLASS_ORDER:
            attack_total = attack_totals[class_id]
            defended_total = defended_totals[class_id]

            if attack_total != defended_total:
                raise ValueError(
                    f"Class denominator mismatch for {class_name}: "
                    f"attack_total={attack_total}, defended_total={defended_total}"
                )

            attack_false_count = attack_false_alerts[class_id]
            defended_false_count = defended_false_alerts[class_id]

            attack_rate = safe_divide(attack_false_count, attack_total)
            defended_rate = safe_divide(defended_false_count, defended_total)

            absolute_rate_change = defended_rate - attack_rate
            absolute_rate_reduction = attack_rate - defended_rate
            absolute_count_change = defended_false_count - attack_false_count
            absolute_count_reduction = attack_false_count - defended_false_count

            if attack_rate > 0:
                relative_rate_reduction = (attack_rate - defended_rate) / attack_rate
            else:
                relative_rate_reduction = 0.0

            row_changes.append(absolute_rate_change)

            table_rows.append(
                {
                    "comparison_id": comparison["comparison_id"],
                    "comparison_label": comparison["comparison_label_long"],
                    "attack_condition": comparison["attack_label"],
                    "defended_condition": comparison["defended_label"],
                    "true_nonfall_class_id": class_id,
                    "true_nonfall_class_name": class_name,
                    "total_true_windows_for_class": attack_total,
                    "attack_false_fall_alert_count": attack_false_count,
                    "defended_false_fall_alert_count": defended_false_count,
                    "attack_class_normalized_false_alarm_rate": f"{attack_rate:.6f}",
                    "defended_class_normalized_false_alarm_rate": f"{defended_rate:.6f}",
                    "absolute_rate_change_defended_minus_attack": f"{absolute_rate_change:.6f}",
                    "absolute_rate_change_percentage_points": f"{absolute_rate_change * 100:.2f}",
                    "absolute_rate_reduction_attack_minus_defended": f"{absolute_rate_reduction:.6f}",
                    "absolute_rate_reduction_percentage_points": f"{absolute_rate_reduction * 100:.2f}",
                    "absolute_count_change_defended_minus_attack": absolute_count_change,
                    "absolute_count_reduction_attack_minus_defended": absolute_count_reduction,
                    "relative_rate_reduction": f"{relative_rate_reduction:.6f}",
                    "relative_rate_reduction_percent": f"{relative_rate_reduction * 100:.2f}",
                    "interpretation": interpretation_for_change(
                        attack_rate,
                        defended_rate,
                        absolute_rate_change,
                        attack_false_count,
                        defended_false_count,
                    ),
                }
            )

        heatmap_matrix.append(row_changes)
        heatmap_labels.append(comparison["comparison_label"])

    return table_rows, heatmap_matrix, heatmap_labels


def write_table(rows):
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "comparison_id",
        "comparison_label",
        "attack_condition",
        "defended_condition",
        "true_nonfall_class_id",
        "true_nonfall_class_name",
        "total_true_windows_for_class",
        "attack_false_fall_alert_count",
        "defended_false_fall_alert_count",
        "attack_class_normalized_false_alarm_rate",
        "defended_class_normalized_false_alarm_rate",
        "absolute_rate_change_defended_minus_attack",
        "absolute_rate_change_percentage_points",
        "absolute_rate_reduction_attack_minus_defended",
        "absolute_rate_reduction_percentage_points",
        "absolute_count_change_defended_minus_attack",
        "absolute_count_reduction_attack_minus_defended",
        "relative_rate_reduction",
        "relative_rate_reduction_percent",
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


def pp_formatter(value, _position):
    if abs(value) < 1e-12:
        return "0 pp"
    return f"{value * 100:+.0f} pp"


def create_figure(heatmap_matrix, comparison_labels):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    class_labels = [
        "lie\ndown",
        "walk",
        "pickup",
        "run",
        "sit\ndown",
        "stand\nup",
    ]

    max_abs_change = 0.0
    for row in heatmap_matrix:
        if row:
            max_abs_change = max(max_abs_change, max(abs(value) for value in row))

    if max_abs_change <= 0:
        color_limit = 0.05
    else:
        color_limit = math.ceil(max_abs_change * 20.0) / 20.0

    fig = plt.figure(figsize=(13.6, 8.9))

    grid = fig.add_gridspec(
        nrows=1,
        ncols=2,
        width_ratios=[1.0, 0.045],
        left=0.16,
        right=0.90,
        top=0.78,
        bottom=0.34,
        wspace=0.07,
    )

    ax = fig.add_subplot(grid[0, 0])
    colorbar_axis = fig.add_subplot(grid[0, 1])

    image = ax.imshow(
        heatmap_matrix,
        vmin=-color_limit,
        vmax=color_limit,
        cmap="coolwarm",
        aspect="auto",
    )

    ax.set_title(
        "Thesis Figure 18: Matched Defense Effect on False-Fall-Alarm Rates",
        fontsize=15.5,
        pad=15,
    )
    ax.set_xlabel("True non-fall activity class", fontsize=12, labelpad=10)
    ax.set_ylabel("Matched comparison", fontsize=12)

    ax.set_xticks(range(len(class_labels)))
    ax.set_xticklabels(class_labels, fontsize=11)
    ax.set_yticks(range(len(comparison_labels)))
    ax.set_yticklabels(comparison_labels, fontsize=11)

    ax.set_xticks([x - 0.5 for x in range(1, len(class_labels))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(comparison_labels))], minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.9, alpha=0.45)
    ax.tick_params(which="minor", bottom=False, left=False)

    for i, row in enumerate(heatmap_matrix):
        for j, change in enumerate(row):
            change_percent = change * 100.0

            if abs(change_percent) < 0.05:
                label = "0"
            else:
                label = f"{change_percent:+.1f} pp"

            luminance = background_luminance(image, change)
            text_color = "white" if luminance < 0.45 else "black"
            fontweight = "bold" if abs(change_percent) > 0.05 else "normal"

            ax.text(
                j,
                i,
                label,
                ha="center",
                va="center",
                color=text_color,
                fontsize=10.5,
                fontweight=fontweight,
            )

    colorbar = fig.colorbar(image, cax=colorbar_axis)
    colorbar.set_label("Defense effect (percentage points)", fontsize=10.8)
    colorbar.ax.tick_params(labelsize=10)
    colorbar.ax.yaxis.set_major_formatter(FuncFormatter(pp_formatter))

    tick_step = 0.05
    tick_count = int(round((2 * color_limit) / tick_step)) + 1
    ticks = [-color_limit + tick_step * index for index in range(tick_count)]
    colorbar.set_ticks(ticks)

    fig.text(
        0.5,
        0.245,
        (
            "Each cell = defended class-normalized false-alert rate minus matched attack rate."
        ),
        ha="center",
        fontsize=10.8,
    )

    fig.text(
        0.5,
        0.215,
        (
            "Blue/negative = defense reduced false-alert rate; red/positive = defense increased it. "
            "pp = percentage points."
        ),
        ha="center",
        fontsize=10.5,
    )

    fig.text(
        0.5,
        0.185,
        (
            "Takeaway: defense reduces most class-specific false-alert rates, "
            "but FGSM stand-up increases and PGD pickup slightly increases."
        ),
        ha="center",
        fontsize=10.3,
    )

    fig.text(
        0.5,
        0.130,
        (
            "Claim boundary: descriptive window-level matched defense-effect analysis only; "
            "not clinical validation, event-level validation,"
        ),
        ha="center",
        fontsize=9.4,
    )

    fig.text(
        0.5,
        0.105,
        (
            "false alarms per hour/day, long-lie analysis, or time-to-alarm validation."
        ),
        ha="center",
        fontsize=9.4,
    )

    fig.savefig(FIGURE_PATH, dpi=300, bbox_inches="tight", pad_inches=0.24)
    plt.close(fig)


def top_effects_by_comparison(table_rows):
    grouped = defaultdict(list)

    for row in table_rows:
        grouped[row["comparison_label"]].append(row)

    lines = []

    for comparison_label, rows in grouped.items():
        largest_reduction = sorted(
            rows,
            key=lambda row: float(row["absolute_rate_reduction_attack_minus_defended"]),
            reverse=True,
        )[0]

        largest_increase = sorted(
            rows,
            key=lambda row: float(row["absolute_rate_change_defended_minus_attack"]),
            reverse=True,
        )[0]

        lines.append(
            f"- {comparison_label}: largest reduction = "
            f"{largest_reduction['true_nonfall_class_name']} "
            f"({largest_reduction['absolute_rate_reduction_percentage_points']} percentage points; "
            f"{largest_reduction['attack_false_fall_alert_count']} -> "
            f"{largest_reduction['defended_false_fall_alert_count']} false alerts)."
        )

        if float(largest_increase["absolute_rate_change_defended_minus_attack"]) > 0:
            lines.append(
                f"  Largest increase = {largest_increase['true_nonfall_class_name']} "
                f"({largest_increase['absolute_rate_change_percentage_points']} percentage points; "
                f"{largest_increase['attack_false_fall_alert_count']} -> "
                f"{largest_increase['defended_false_fall_alert_count']} false alerts)."
            )

    return lines


def write_note(table_rows):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    effect_lines = "\n".join(top_effects_by_comparison(table_rows))

    text = f"""# Thesis Table 18 and Figure 18: Class-Normalized Defense Effect on False-Fall-Alarm Sources

This note documents the matched defense-effect analysis for class-normalized false-fall-alarm rates.

## Purpose

Table 18 and Figure 18 ask:

```text
For each true non-fall activity, did the defended model reduce or increase false fall alarms compared with the matched attack?
```

The matched comparisons are:

```text
FGSM Attack -> Defended FGSM
PGD Attack -> Defended PGD
```

## Files Created

```text
Table 18:
{TABLE_PATH}

Figure 18:
{FIGURE_PATH}

Companion note:
{NOTE_PATH}
```

## Input Files

```text
{INPUT_FILES["fgsm"]}
{INPUT_FILES["defended_fgsm"]}
{INPUT_FILES["pgd"]}
{INPUT_FILES["defended_pgd"]}
```

## Metric Definition

For each matched attack/defense pair and each true non-fall class:

```text
class-normalized defense effect =
defended class-normalized false-alert rate - attacked class-normalized false-alert rate
```

Therefore:

```text
negative value = defense reduced false-fall-alarm rate
positive value = defense increased false-fall-alarm rate
zero = no class-normalized rate change
```

Figure 18 reports this as percentage-point change, abbreviated as pp.

## Key Findings

{effect_lines}

## Interpretation

This artifact strengthens the thesis because it shows where the short defended model reduced false-fall-alarm tendency and where it did not.

Table 16 showed that defended FGSM/PGD reduced total false fall alerts compared with matched attacks, while PPV remained zero because TP remained zero. Table 18 adds class-level detail by showing which true non-fall activities drove those reductions or increases.

For the tested configuration, most class-specific false-alert rates decreased under defense. However, the FGSM stand-up class increased and the PGD pickup class slightly increased, showing that the short defense did not uniformly improve every false-alert source.

## Claim Boundary

This is a descriptive window-level matched defense-effect analysis using UT-HAR / SenseFi prediction outputs.

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
    section_marker = "### Thesis Table 18 and Figure 18: Class-Normalized Defense Effect"

    section = f"""
{section_marker}

Table 18 and Figure 18 add a matched class-normalized defense-effect analysis for false-fall-alarm sources.

Files:

```text
results/thesis_table_18_class_normalized_defense_effect.csv
figures/thesis_figure_18_class_normalized_defense_effect_heatmap.png
notes/thesis_table_18_figure_18_class_normalized_defense_effect.md
```

Purpose:

```text
For each true non-fall activity, did the defended model reduce or increase false fall alarms compared with the matched attack?
```

Matched comparisons:

```text
FGSM Attack -> Defended FGSM
PGD Attack -> Defended PGD
```

Metric definition:

```text
class-normalized defense effect =
defended class-normalized false-alert rate - attacked class-normalized false-alert rate
```

Interpretation:

```text
negative value = defense reduced false-fall-alarm rate
positive value = defense increased false-fall-alarm rate
pp = percentage points
```

This artifact complements Table 16 and Figure 16 by showing that total false fall alerts decreased under defense, while Table 18 identifies which true non-fall classes drove those changes.

Claim boundary: this is a descriptive window-level matched defense-effect analysis. It is not clinical validation, medical-device validation, event-level fall validation, false alarms per hour/day, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.
"""

    if README_PATH.exists():
        text = README_PATH.read_text(encoding="utf-8")
    else:
        text = ""

    updated_text = replace_or_append_readme_section(text, section_marker, section)
    README_PATH.write_text(updated_text, encoding="utf-8")

    if section_marker in text:
        print("README Table 18 / Figure 18 section replaced.")
    else:
        print("README updated with Table 18 / Figure 18 section.")


def main():
    print("Creating Thesis Table 18 and Figure 18...")

    table_rows, heatmap_matrix, comparison_labels = build_table_rows()

    write_table(table_rows)
    create_figure(heatmap_matrix, comparison_labels)
    write_note(table_rows)
    update_readme()

    print("\nCreated outputs:")
    print(f"- {TABLE_PATH}")
    print(f"- {FIGURE_PATH}")
    print(f"- {NOTE_PATH}")
    print("- README.md updated")

    print("\nTop class-normalized defense effects:")
    for line in top_effects_by_comparison(table_rows):
        print(line)


if __name__ == "__main__":
    main()