"""
Generate one combined summary figure from the FGSM epsilon sweep.

Purpose:
    This script reads the FGSM epsilon sweep CSV and creates one
    GitHub-friendly combined figure showing how FGSM epsilon affects
    missed fall rate, recall, F1-score, and false fall alarms.

Important:
    This is a window-level research visualization.
    It is not clinical validation, medical-device validation,
    physical-layer attack validation, or over-the-air validation.

Expected input:
    results/fgsm_epsilon_sweep_summary.csv

Expected output:
    figures/fgsm_epsilon_combined_safety_summary.png
"""

from pathlib import Path
import csv
import matplotlib.pyplot as plt


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = EXPERIMENT_DIR / "results"
FIGURES_DIR = EXPERIMENT_DIR / "figures"

INPUT_CSV = RESULTS_DIR / "fgsm_epsilon_sweep_summary.csv"
OUTPUT_FIGURE = FIGURES_DIR / "fgsm_epsilon_combined_safety_summary.png"


def read_sweep_csv(csv_path: Path):
    rows = []

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "epsilon": float(row["epsilon"]),
                "missed_fall_rate": float(row["missed_fall_rate"]),
                "recall_sensitivity": float(row["recall_sensitivity"]),
                "f1_score": float(row["f1_score"]),
                "false_alarm_count": int(float(row["false_alarm_count"])),
            })

    return rows


def main():
    print("FGSM combined safety summary figure generation")
    print("-" * 70)
    print(f"Input CSV: {INPUT_CSV}")
    print(f"Output figure: {OUTPUT_FIGURE}")
    print("-" * 70)

    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input CSV: {INPUT_CSV}")

    FIGURES_DIR.mkdir(exist_ok=True)

    rows = read_sweep_csv(INPUT_CSV)

    epsilons = [row["epsilon"] for row in rows]
    missed_fall_rates = [row["missed_fall_rate"] for row in rows]
    recalls = [row["recall_sensitivity"] for row in rows]
    f1_scores = [row["f1_score"] for row in rows]
    false_alarm_counts = [row["false_alarm_count"] for row in rows]

    fig, ax1 = plt.subplots(figsize=(9, 5.5))

    ax1.plot(epsilons, missed_fall_rates, marker="o", label="Missed fall rate")
    ax1.plot(epsilons, recalls, marker="o", label="Recall / sensitivity")
    ax1.plot(epsilons, f1_scores, marker="o", label="F1-score")
    ax1.set_xlabel("FGSM epsilon")
    ax1.set_ylabel("Rate / score")
    ax1.set_ylim(-0.05, 1.05)
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(epsilons, false_alarm_counts, marker="o", linestyle="--", label="False fall alarms")
    ax2.set_ylabel("False fall alarm count")

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="center right")

    plt.title("FGSM Epsilon Sweep: Fall Safety-Proxy Degradation")
    fig.tight_layout()
    plt.savefig(OUTPUT_FIGURE, dpi=300)
    plt.close()

    print("Combined figure created successfully.")
    print(OUTPUT_FIGURE)


if __name__ == "__main__":
    main()