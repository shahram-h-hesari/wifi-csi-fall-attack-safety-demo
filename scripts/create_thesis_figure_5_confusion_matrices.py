from pathlib import Path
import csv
import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# Thesis Figure 5: Binary Confusion Matrix Figure
#
# Clean thesis-ready version:
# - No color bar
# - No repeated metric boxes
# - No repeated "Predicted Class" axis title
# - Wider left margin so y-axis labels are not cut off
# - Main title moved upward with more space from subplots
# - Clean 2 x 3 confusion-matrix layout
#
# Matrix layout:
# Rows = true class
# Columns = predicted class
#
#              Predicted Fall    Predicted Non-Fall
# True Fall          TP                 FN
# True Non-Fall      FP                 TN
#
# Input:
# - results/defended_vs_undefended_safety_comparison.csv
#
# Outputs:
# - figures/thesis_figure_5_confusion_matrices.png
# - notes/thesis_figure_5_confusion_matrices.md
#
# Scope:
# Window-level fall-vs-non-fall safety-proxy evaluation only.
# Software-level processed-tensor adversarial perturbation only.
#
# Claim boundary:
# This is not clinical validation, medical-device validation,
# diagnostic evidence, regulatory evaluation, real patient
# deployment, event-level fall validation, long-lie validation,
# or physical-layer / packet-level / preamble-level / SDR /
# over-the-air validation.
# ============================================================


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
NOTES_DIR = ROOT / "notes"

FIGURES_DIR.mkdir(exist_ok=True)
NOTES_DIR.mkdir(exist_ok=True)

INPUT_FILE = RESULTS_DIR / "defended_vs_undefended_safety_comparison.csv"

OUTPUT_FIGURE = FIGURES_DIR / "thesis_figure_5_confusion_matrices.png"
OUTPUT_MD = NOTES_DIR / "thesis_figure_5_confusion_matrices.md"


CONDITION_ORDER = [
    {
        "condition": "undefended_clean",
        "title": "Undefended Clean",
    },
    {
        "condition": "undefended_fgsm_epsilon_0_03",
        "title": "Undefended FGSM\nepsilon = 0.030",
    },
    {
        "condition": "undefended_pgd_epsilon_0_03",
        "title": "Undefended PGD\nepsilon = 0.030",
    },
    {
        "condition": "defended_clean",
        "title": "Defended Clean",
    },
    {
        "condition": "defended_fgsm_epsilon_0_03",
        "title": "Defended FGSM\nepsilon = 0.030",
    },
    {
        "condition": "defended_pgd_epsilon_0_03",
        "title": "Defended PGD\nepsilon = 0.030",
    },
]


def to_float(value):
    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    try:
        return float(value)
    except ValueError:
        return None


def to_int(value):
    number = to_float(value)

    if number is None:
        return None

    return int(round(number))


def fmt_decimal(value, digits=4):
    if value is None:
        return "NA"

    return f"{value:.{digits}f}"


def read_rows_by_condition(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required input file: {path}")

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError(f"No rows found in input file: {path}")

    by_condition = {}

    for row in rows:
        condition = row.get("condition", "").strip()

        if condition:
            by_condition[condition] = row

    return by_condition


def get_required_row(rows_by_condition, condition_name):
    if condition_name not in rows_by_condition:
        available = ", ".join(sorted(rows_by_condition.keys()))
        raise KeyError(
            f"Missing condition '{condition_name}'. "
            f"Available conditions: {available}"
        )

    return rows_by_condition[condition_name]


def extract_confusion_values(row):
    tp = to_int(row["TP_detected_falls"])
    fn = to_int(row["FN_missed_falls"])
    fp = to_int(row["FP_false_fall_alarms"])
    tn = to_int(row["TN_correct_non_falls"])

    recall = to_float(row["recall_sensitivity"])
    missed_fall_rate = to_float(row["missed_fall_rate"])
    precision = to_float(row["precision"])
    f1_score = to_float(row["f1_score"])
    balanced_accuracy = to_float(row["balanced_accuracy"])

    matrix = np.array(
        [
            [tp, fn],
            [fp, tn],
        ]
    )

    return {
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "recall": recall,
        "missed_fall_rate": missed_fall_rate,
        "precision": precision,
        "f1_score": f1_score,
        "balanced_accuracy": balanced_accuracy,
        "matrix": matrix,
    }


def write_markdown(summary_rows):
    lines = []

    lines.append("# Thesis Figure 5: Binary Confusion Matrix Figure")
    lines.append("")
    lines.append("This figure shows binary fall-vs-non-fall confusion matrices for clean, FGSM-attacked, and PGD-attacked conditions before and after defense.")
    lines.append("")
    lines.append("Matrix layout:")
    lines.append("")
    lines.append("```text")
    lines.append("Rows = true class")
    lines.append("Columns = predicted class")
    lines.append("")
    lines.append("                 Predicted Fall    Predicted Non-Fall")
    lines.append("True Fall              TP                  FN")
    lines.append("True Non-Fall          FP                  TN")
    lines.append("```")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append("This is a research implementation using window-level safety-proxy metrics and software-level processed-tensor adversarial perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.")
    lines.append("")
    lines.append("## Confusion Matrix Summary")
    lines.append("")
    lines.append("| Condition | TP | FN | FP | TN | Recall/Sensitivity | Missed Fall Rate | Precision | F1-Score | Balanced Accuracy |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for row in summary_rows:
        lines.append(
            "| "
            f"{row['title'].replace(chr(10), ' ')} | "
            f"{row['tp']} | "
            f"{row['fn']} | "
            f"{row['fp']} | "
            f"{row['tn']} | "
            f"{fmt_decimal(row['recall'])} | "
            f"{fmt_decimal(row['missed_fall_rate'])} | "
            f"{fmt_decimal(row['precision'])} | "
            f"{fmt_decimal(row['f1_score'])} | "
            f"{fmt_decimal(row['balanced_accuracy'])} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The confusion matrices show which binary safety-proxy errors changed across clean, attacked, and defended conditions.")
    lines.append("")
    lines.append("Under FGSM and PGD attack, true detected falls drop to zero and missed falls rise to all 89 fall windows. The defended model reduces false fall alarms under attack but does not recover detected falls at epsilon 0.030.")
    lines.append("")
    lines.append("The clean defended model reduces false fall alarms compared with the clean undefended baseline, but it also increases missed falls from 32 to 53 fall windows.")
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `figures/thesis_figure_5_confusion_matrices.png`")
    lines.append("- `notes/thesis_figure_5_confusion_matrices.md`")
    lines.append("- Input: `results/defended_vs_undefended_safety_comparison.csv`")
    lines.append("")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows_by_condition = read_rows_by_condition(INPUT_FILE)

    summary_rows = []

    for condition_info in CONDITION_ORDER:
        raw_row = get_required_row(rows_by_condition, condition_info["condition"])
        values = extract_confusion_values(raw_row)
        values["condition"] = condition_info["condition"]
        values["title"] = condition_info["title"]
        summary_rows.append(values)

    fig, axes = plt.subplots(2, 3, figsize=(16, 10.8))
    axes = axes.flatten()

    max_value = max(row["matrix"].max() for row in summary_rows)

    for idx, (ax, row) in enumerate(zip(axes, summary_rows)):
        matrix = row["matrix"]

        ax.imshow(matrix, cmap="Blues", vmin=0, vmax=max_value)

        ax.set_title(
            row["title"],
            fontsize=20,
            fontweight="bold",
            pad=16,
        )

        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])

        ax.set_xticklabels(
            ["Pred Fall", "Pred Non-Fall"],
            fontsize=13,
        )

        ax.set_yticklabels(
            ["True Fall", "True Non-Fall"],
            fontsize=13,
        )

        # Only the left column gets the y-axis title.
        # Larger labelpad prevents the label from being cut off.
        if idx % 3 == 0:
            ax.set_ylabel("True Class", fontsize=14, labelpad=16)
        else:
            ax.set_ylabel("")

        # Do not repeat "Predicted Class" under each subplot.
        ax.set_xlabel("")

        threshold = max_value / 2.0

        for i in range(2):
            for j in range(2):
                value = matrix[i, j]
                text_color = "white" if value > threshold else "black"

                ax.text(
                    j,
                    i,
                    str(value),
                    ha="center",
                    va="center",
                    fontsize=21,
                    fontweight="bold",
                    color=text_color,
                )

    fig.suptitle(
        "Thesis Figure 5: Binary Fall-vs-Non-Fall Confusion Matrices",
        fontsize=24,
        fontweight="bold",
        y=0.992,
    )

    fig.text(
        0.5,
        0.035,
        "Matrix layout: rows = true class, columns = predicted class ([[TP, FN], [FP, TN]]).",
        ha="center",
        fontsize=13,
    )

    plt.subplots_adjust(
        left=0.11,
        right=0.985,
        top=0.87,
        bottom=0.11,
        wspace=0.34,
        hspace=0.45,
    )

    # Do not use bbox_inches='tight'; it can collapse spacing.
    plt.savefig(OUTPUT_FIGURE, dpi=300)
    plt.close()

    write_markdown(summary_rows)

    print("Created cleaned Thesis Figure 5 outputs:")
    print(f"  {OUTPUT_FIGURE}")
    print(f"  {OUTPUT_MD}")
    print("")
    print("Summary:")

    for row in summary_rows:
        print(
            f"  {row['title'].replace(chr(10), ' ')}: "
            f"TP={row['tp']}, "
            f"FN={row['fn']}, "
            f"FP={row['fp']}, "
            f"TN={row['tn']}, "
            f"recall={fmt_decimal(row['recall'])}, "
            f"missed_fall_rate={fmt_decimal(row['missed_fall_rate'])}"
        )


if __name__ == "__main__":
    main()