"""
Generate figures from the FGSM epsilon sweep summary.

Purpose:
    This script reads the FGSM epsilon sweep CSV and creates simple
    research figures showing how perturbation strength affects
    fall-focused safety-proxy metrics.

Important:
    These figures are based on window-level research metrics.
    They are not clinical validation, medical-device validation,
    physical-layer attack validation, or over-the-air validation.

Expected input:
    results/fgsm_epsilon_sweep_summary.csv

Expected outputs:
    figures/fgsm_epsilon_vs_missed_fall_rate.png
    figures/fgsm_epsilon_vs_false_alarm_count.png
    figures/fgsm_epsilon_vs_recall.png
    figures/fgsm_epsilon_vs_f1_score.png
"""

from pathlib import Path
import csv
import matplotlib.pyplot as plt


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = EXPERIMENT_DIR / "results"
FIGURES_DIR = EXPERIMENT_DIR / "figures"

INPUT_CSV = RESULTS_DIR / "fgsm_epsilon_sweep_summary.csv"

FIGURES_DIR.mkdir(exist_ok=True)


def read_sweep_csv(csv_path: Path):
    rows = []

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "epsilon": float(row["epsilon"]),
                "seven_class_accuracy": float(row["seven_class_accuracy"]),
                "missed_fall_rate": float(row["missed_fall_rate"]),
                "false_alarm_count": int(float(row["false_alarm_count"])),
                "recall_sensitivity": float(row["recall_sensitivity"]),
                "f1_score": float(row["f1_score"]),
                "prediction_change_rate": float(row["prediction_change_rate"]),
            })

    return rows


def make_line_plot(x_values, y_values, title, x_label, y_label, output_path):
    plt.figure(figsize=(8, 5))
    plt.plot(x_values, y_values, marker="o")
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def main():
    print("FGSM epsilon sweep figure generation")
    print("-" * 70)
    print(f"Input CSV: {INPUT_CSV}")
    print(f"Figures directory: {FIGURES_DIR}")
    print("-" * 70)

    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input CSV: {INPUT_CSV}")

    rows = read_sweep_csv(INPUT_CSV)

    epsilons = [row["epsilon"] for row in rows]
    missed_fall_rates = [row["missed_fall_rate"] for row in rows]
    false_alarm_counts = [row["false_alarm_count"] for row in rows]
    recalls = [row["recall_sensitivity"] for row in rows]
    f1_scores = [row["f1_score"] for row in rows]

    make_line_plot(
        epsilons,
        missed_fall_rates,
        "FGSM Epsilon vs Missed Fall Rate",
        "FGSM epsilon",
        "Missed fall rate",
        FIGURES_DIR / "fgsm_epsilon_vs_missed_fall_rate.png",
    )

    make_line_plot(
        epsilons,
        false_alarm_counts,
        "FGSM Epsilon vs False Fall Alarm Count",
        "FGSM epsilon",
        "False fall alarm count",
        FIGURES_DIR / "fgsm_epsilon_vs_false_alarm_count.png",
    )

    make_line_plot(
        epsilons,
        recalls,
        "FGSM Epsilon vs Fall Recall",
        "FGSM epsilon",
        "Recall / sensitivity",
        FIGURES_DIR / "fgsm_epsilon_vs_recall.png",
    )

    make_line_plot(
        epsilons,
        f1_scores,
        "FGSM Epsilon vs Fall F1-Score",
        "FGSM epsilon",
        "F1-score",
        FIGURES_DIR / "fgsm_epsilon_vs_f1_score.png",
    )

    print("Figures created:")
    print(FIGURES_DIR / "fgsm_epsilon_vs_missed_fall_rate.png")
    print(FIGURES_DIR / "fgsm_epsilon_vs_false_alarm_count.png")
    print(FIGURES_DIR / "fgsm_epsilon_vs_recall.png")
    print(FIGURES_DIR / "fgsm_epsilon_vs_f1_score.png")
    print("-" * 70)
    print("Figure generation completed successfully.")


if __name__ == "__main__":
    main()