"""
Create Figure 4.5: Seven-Class Confusion Matrix Figure.

This script creates a thesis-ready six-panel confusion-matrix figure for:
1. undefended clean baseline
2. undefended FGSM attack
3. undefended PGD attack
4. defended clean baseline
5. defended FGSM attack
6. defended PGD attack

Outputs:
    figures/thesis_figure_6_seven_class_confusion_matrices.png
    notes/thesis_figure_6_seven_class_confusion_matrices.md

Claim boundary:
    This is a window-level seven-class confusion-matrix visualization.
    It is not event-level fall validation, clinical validation, or
    medical-device evaluation.
"""

from pathlib import Path
import csv
import numpy as np
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
NOTES_DIR = ROOT / "notes"

OUTPUT_FIGURE = FIGURES_DIR / "thesis_figure_6_seven_class_confusion_matrices.png"
OUTPUT_NOTE = NOTES_DIR / "thesis_figure_6_seven_class_confusion_matrices.md"

CLASS_NAMES = [
    "lie down",
    "fall",
    "walk",
    "pickup",
    "run",
    "sit down",
    "stand up",
]

CLAIM_BOUNDARY = (
    "Research implementation only; window-level seven-class confusion-matrix "
    "visualization; software-level processed-tensor perturbations only; not clinical "
    "validation, not medical-device validation, not diagnostic evidence, not real "
    "patient deployment, not regulatory evaluation, not event-level fall validation, "
    "not long-lie validation, not time-to-alarm validation, and not physical-layer / "
    "packet-level / preamble-level / SDR / over-the-air validation."
)

CONDITIONS = [
    {
        "title": "Undefended Clean",
        "file": RESULTS_DIR / "clean_predictions_short.csv",
        "true_col": "true_label",
        "pred_col": "predicted_label",
    },
    {
        "title": "Undefended FGSM\nepsilon = 0.030",
        "file": RESULTS_DIR / "fgsm_predictions_short_epsilon_0_03.csv",
        "true_col": "true_label",
        "pred_col": "attacked_predicted_label",
    },
    {
        "title": "Undefended PGD\nepsilon = 0.030",
        "file": RESULTS_DIR / "pgd_predictions_short_epsilon_0_03.csv",
        "true_col": "true_label",
        "pred_col": "predicted_label",
    },
    {
        "title": "Defended Clean",
        "file": RESULTS_DIR / "defended_predictions_short.csv",
        "true_col": "true_label",
        "pred_col": "defended_clean_predicted_label",
    },
    {
        "title": "Defended FGSM\nepsilon = 0.030",
        "file": RESULTS_DIR / "defended_predictions_short.csv",
        "true_col": "true_label",
        "pred_col": "defended_fgsm_predicted_label",
    },
    {
        "title": "Defended PGD\nepsilon = 0.030",
        "file": RESULTS_DIR / "defended_predictions_short.csv",
        "true_col": "true_label",
        "pred_col": "defended_pgd_predicted_label",
    },
]


def read_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required prediction file: {path}")

    with path.open("r", newline="", encoding="utf-8") as csvfile:
        return list(csv.DictReader(csvfile))


def require_columns(rows, path, columns):
    if not rows:
        raise ValueError(f"No rows found in file: {path}")

    missing = [col for col in columns if col not in rows[0]]
    if missing:
        raise ValueError(f"Missing columns in {path}: {missing}")


def as_int(value):
    return int(float(str(value).strip()))


def confusion_matrix(rows, true_col, pred_col, n_classes=7):
    matrix = np.zeros((n_classes, n_classes), dtype=int)

    for row in rows:
        true_label = as_int(row[true_col])
        pred_label = as_int(row[pred_col])
        matrix[true_label, pred_label] += 1

    return matrix


def summarize_matrix(matrix):
    total = int(matrix.sum())
    correct = int(np.trace(matrix))
    accuracy = correct / total if total else 0.0

    fall_true_total = int(matrix[1, :].sum())
    fall_detected = int(matrix[1, 1])
    fall_missed = fall_true_total - fall_detected

    false_fall_alarms = int(matrix[:, 1].sum() - matrix[1, 1])

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "fall_true_total": fall_true_total,
        "fall_detected": fall_detected,
        "fall_missed": fall_missed,
        "false_fall_alarms": false_fall_alarms,
    }


def plot_matrices(matrices, summaries):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    axes = axes.ravel()

    max_value = max(int(matrix.max()) for matrix in matrices)

    for ax, condition, matrix, summary in zip(axes, CONDITIONS, matrices, summaries):
        im = ax.imshow(matrix, vmin=0, vmax=max_value)

        ax.set_title(
            f"{condition['title']}\n"
            f"Acc={summary['accuracy']:.3f}, "
            f"Missed fall={summary['fall_missed']}, "
            f"False alarms={summary['false_fall_alarms']}",
            fontsize=10,
        )

        ax.set_xlabel("Predicted class")
        ax.set_ylabel("True class")

        ax.set_xticks(range(len(CLASS_NAMES)))
        ax.set_yticks(range(len(CLASS_NAMES)))
        ax.set_xticklabels(CLASS_NAMES, rotation=45, ha="right", fontsize=8)
        ax.set_yticklabels(CLASS_NAMES, fontsize=8)

        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                value = int(matrix[i, j])
                if value > 0:
                    ax.text(j, i, str(value), ha="center", va="center", fontsize=8)

    fig.suptitle(
        "Figure 4.5: Seven-Class Confusion Matrices\n"
        "SenseFi / UT-HAR / LeNet, clean vs attacked vs defended conditions",
        fontsize=14,
    )

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.colorbar(im, ax=axes.tolist(), shrink=0.75, label="Window count")
    fig.savefig(OUTPUT_FIGURE, dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_note(matrices, summaries):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Figure 4.5: Seven-Class Confusion Matrix Figure")
    lines.append("")
    lines.append(
        "This figure visualizes seven-class confusion matrices for the clean, "
        "attacked, and defended conditions in the WiFi CSI Fall Attack-Safety Demo."
    )
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Output Figure")
    lines.append("")
    lines.append("- `figures/thesis_figure_6_seven_class_confusion_matrices.png`")
    lines.append("")
    lines.append("## Conditions Included")
    lines.append("")

    lines.append(
        "| Condition | Total Windows | Seven-Class Accuracy | Fall Windows | "
        "Detected Fall Windows | Missed Fall Windows | False Fall Alarms |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|")

    for condition, summary in zip(CONDITIONS, summaries):
        condition_title = condition["title"].replace("\n", " ")
        lines.append(
            f"| {condition_title} | "
            f"{summary['total']} | "
            f"{summary['accuracy']:.4f} | "
            f"{summary['fall_true_total']} | "
            f"{summary['fall_detected']} | "
            f"{summary['fall_missed']} | "
            f"{summary['false_fall_alarms']} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Figure 6 complements Table 8 by showing the full seven-class confusion "
        "structure behind the binary fall-vs-non-fall safety-proxy metrics."
    )
    lines.append("")
    lines.append(
        "The figure helps identify whether attack and defense conditions mainly "
        "change fall windows into specific non-fall classes, or whether they "
        "convert non-fall activities into false fall alarms."
    )
    lines.append("")
    lines.append(
        "This visualization should be described as a window-level multiclass "
        "confusion-matrix analysis. It should not be described as event-level "
        "fall validation or clinical fall validation."
    )
    lines.append("")
    lines.append("## Relationship to Table 8")
    lines.append("")
    lines.append(
        "Table 8 provides the detailed high-risk fall-related error taxonomy. "
        "Figure 6 provides the visual seven-class confusion-matrix view of the "
        "same prediction behavior."
    )
    lines.append("")

    OUTPUT_NOTE.write_text("\n".join(lines), encoding="utf-8")


def main():
    matrices = []
    summaries = []

    for condition in CONDITIONS:
        rows = read_rows(condition["file"])
        require_columns(rows, condition["file"], [condition["true_col"], condition["pred_col"]])

        matrix = confusion_matrix(rows, condition["true_col"], condition["pred_col"])
        summary = summarize_matrix(matrix)

        matrices.append(matrix)
        summaries.append(summary)

    plot_matrices(matrices, summaries)
    write_note(matrices, summaries)

    print("Created Figure 4.5 outputs:")
    print(f"  {OUTPUT_FIGURE}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Seven-class confusion matrix summary:")
    for condition, summary in zip(CONDITIONS, summaries):
        print(
            f"  {condition['title'].replace(chr(10), ' ')}: "
            f"accuracy={summary['accuracy']:.4f}, "
            f"missed_fall_windows={summary['fall_missed']}, "
            f"false_fall_alarms={summary['false_fall_alarms']}"
        )


if __name__ == "__main__":
    main()

