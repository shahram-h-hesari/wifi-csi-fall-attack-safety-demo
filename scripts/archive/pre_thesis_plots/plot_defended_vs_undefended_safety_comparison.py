"""
Plot defended vs undefended fall-vs-non-fall safety-proxy metrics.

Input:
    results/defended_vs_undefended_safety_comparison.csv

Outputs:
    figures/defended_vs_undefended_missed_fall_rate.png
    figures/defended_vs_undefended_false_alarm_count.png
    figures/defended_vs_undefended_recall.png
    figures/defended_vs_undefended_f1_score.png
    figures/defended_vs_undefended_balanced_accuracy.png
    figures/defended_vs_undefended_prediction_change_rate.png

Claim boundary:
    These are window-level software comparison plots on processed CSI tensors.
    They are not clinical validation, medical-device validation, diagnostic
    evidence, regulatory evaluation, physical-layer validation, packet-level
    validation, preamble-level validation, SDR validation, or over-the-air
    validation.
"""

from pathlib import Path
import csv

import matplotlib.pyplot as plt


INPUT_FILE = "defended_vs_undefended_safety_comparison.csv"


PLOTS = [
    {
        "column": "missed_fall_rate",
        "title": "Defended vs Undefended Missed Fall Rate",
        "ylabel": "Missed fall rate",
        "filename": "defended_vs_undefended_missed_fall_rate.png",
    },
    {
        "column": "FP_false_fall_alarms",
        "title": "Defended vs Undefended False Fall Alarm Count",
        "ylabel": "False fall alarms",
        "filename": "defended_vs_undefended_false_alarm_count.png",
    },
    {
        "column": "recall_sensitivity",
        "title": "Defended vs Undefended Recall / Sensitivity",
        "ylabel": "Recall / sensitivity",
        "filename": "defended_vs_undefended_recall.png",
    },
    {
        "column": "f1_score",
        "title": "Defended vs Undefended F1-Score",
        "ylabel": "F1-score",
        "filename": "defended_vs_undefended_f1_score.png",
    },
    {
        "column": "balanced_accuracy",
        "title": "Defended vs Undefended Balanced Accuracy",
        "ylabel": "Balanced accuracy",
        "filename": "defended_vs_undefended_balanced_accuracy.png",
    },
    {
        "column": "prediction_change_rate",
        "title": "Defended vs Undefended Prediction Change Rate",
        "ylabel": "Prediction change rate",
        "filename": "defended_vs_undefended_prediction_change_rate.png",
    },
]


LABELS = {
    "undefended_clean": "Undefended\nclean",
    "undefended_fgsm_epsilon_0_03": "Undefended\nFGSM",
    "undefended_pgd_epsilon_0_03": "Undefended\nPGD",
    "defended_clean": "Defended\nclean",
    "defended_fgsm_epsilon_0_03": "Defended\nFGSM",
    "defended_pgd_epsilon_0_03": "Defended\nPGD",
}


def read_rows(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")

    with path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError(f"No rows found in: {path}")

    return rows


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def plot_metric(rows, column, title, ylabel, output_path):
    labels = [LABELS.get(row["condition"], row["condition"]) for row in rows]
    values = [safe_float(row[column]) for row in rows]

    plt.figure(figsize=(10, 6))
    plt.bar(labels, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def main():
    experiment_dir = Path(__file__).resolve().parents[1]
    results_dir = experiment_dir / "results"
    figures_dir = experiment_dir / "figures"

    figures_dir.mkdir(parents=True, exist_ok=True)

    input_path = results_dir / INPUT_FILE
    rows = read_rows(input_path)

    print("Creating defended vs undefended safety-proxy plots")
    print("-" * 80)
    print(f"Input file: {input_path}")
    print(f"Rows loaded: {len(rows)}")
    print(f"Figures directory: {figures_dir}")
    print("-" * 80)

    for plot_config in PLOTS:
        output_path = figures_dir / plot_config["filename"]

        plot_metric(
            rows=rows,
            column=plot_config["column"],
            title=plot_config["title"],
            ylabel=plot_config["ylabel"],
            output_path=output_path,
        )

        print(f"Saved: {output_path}")

    print("-" * 80)
    print("Defended vs undefended plots completed successfully.")


if __name__ == "__main__":
    main()