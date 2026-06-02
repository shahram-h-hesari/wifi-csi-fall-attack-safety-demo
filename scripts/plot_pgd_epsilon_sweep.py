"""
Plot PGD epsilon sweep figures for the WiFi CSI Fall Attack-Safety Demo.

Input:
- results/pgd_epsilon_sweep_summary.csv

Outputs:
- figures/pgd_epsilon_vs_missed_fall_rate.png
- figures/pgd_epsilon_vs_false_alarm_count.png
- figures/pgd_epsilon_vs_recall.png
- figures/pgd_epsilon_vs_f1_score.png
- figures/pgd_epsilon_combined_safety_summary.png

Important claim boundary:
These figures summarize window-level safety-proxy metrics from software-level
PGD perturbations applied to processed UT-HAR CSI tensors. They are not clinical
validation, medical-device validation, diagnostic evidence, regulatory evaluation,
physical-layer validation, SDR validation, or over-the-air validation.
"""

from pathlib import Path
import csv

import matplotlib.pyplot as plt


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = EXPERIMENT_DIR / "results"
FIGURES_DIR = EXPERIMENT_DIR / "figures"

INPUT_FILE = RESULTS_DIR / "pgd_epsilon_sweep_summary.csv"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def read_sweep_results(input_file: Path):
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with input_file.open("r", newline="", encoding="utf-8") as csvfile:
        rows = list(csv.DictReader(csvfile))

    if not rows:
        raise ValueError(f"No rows found in input file: {input_file}")

    return rows


def get_float_column(rows, column_name):
    return [float(row[column_name]) for row in rows]


def get_int_column(rows, column_name):
    return [int(row[column_name]) for row in rows]


def save_line_plot(
    x_values,
    y_values,
    title,
    x_label,
    y_label,
    output_path,
):
    plt.figure(figsize=(8, 5))
    plt.plot(x_values, y_values, marker="o")
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def save_combined_summary_plot(
    epsilons,
    missed_fall_rate,
    recall,
    f1_score,
    prediction_change_rate,
    output_path,
):
    plt.figure(figsize=(9, 6))

    plt.plot(epsilons, missed_fall_rate, marker="o", label="Missed fall rate")
    plt.plot(epsilons, recall, marker="o", label="Recall / sensitivity")
    plt.plot(epsilons, f1_score, marker="o", label="F1-score")
    plt.plot(epsilons, prediction_change_rate, marker="o", label="Prediction change rate")

    plt.title("PGD Epsilon Sweep: Window-Level Safety-Proxy Summary")
    plt.xlabel("PGD epsilon")
    plt.ylabel("Metric value")
    plt.ylim(-0.05, 1.05)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def main():
    rows = read_sweep_results(INPUT_FILE)

    epsilons = get_float_column(rows, "epsilon")
    missed_fall_rate = get_float_column(rows, "missed_fall_rate")
    false_alarm_count = get_int_column(rows, "fp_false_fall_alarms")
    recall = get_float_column(rows, "recall_sensitivity")
    f1_score = get_float_column(rows, "f1_score")
    prediction_change_rate = get_float_column(rows, "prediction_change_rate")

    output_files = {
        "missed_fall_rate": FIGURES_DIR / "pgd_epsilon_vs_missed_fall_rate.png",
        "false_alarm_count": FIGURES_DIR / "pgd_epsilon_vs_false_alarm_count.png",
        "recall": FIGURES_DIR / "pgd_epsilon_vs_recall.png",
        "f1_score": FIGURES_DIR / "pgd_epsilon_vs_f1_score.png",
        "combined": FIGURES_DIR / "pgd_epsilon_combined_safety_summary.png",
    }

    save_line_plot(
        x_values=epsilons,
        y_values=missed_fall_rate,
        title="PGD Epsilon vs Missed Fall Rate",
        x_label="PGD epsilon",
        y_label="Missed fall rate",
        output_path=output_files["missed_fall_rate"],
    )

    save_line_plot(
        x_values=epsilons,
        y_values=false_alarm_count,
        title="PGD Epsilon vs False Fall Alarm Count",
        x_label="PGD epsilon",
        y_label="False fall alarm count",
        output_path=output_files["false_alarm_count"],
    )

    save_line_plot(
        x_values=epsilons,
        y_values=recall,
        title="PGD Epsilon vs Recall / Sensitivity",
        x_label="PGD epsilon",
        y_label="Recall / sensitivity",
        output_path=output_files["recall"],
    )

    save_line_plot(
        x_values=epsilons,
        y_values=f1_score,
        title="PGD Epsilon vs F1-Score",
        x_label="PGD epsilon",
        y_label="F1-score",
        output_path=output_files["f1_score"],
    )

    save_combined_summary_plot(
        epsilons=epsilons,
        missed_fall_rate=missed_fall_rate,
        recall=recall,
        f1_score=f1_score,
        prediction_change_rate=prediction_change_rate,
        output_path=output_files["combined"],
    )

    print("PGD epsilon sweep figures created.")
    print(f"Input file: {INPUT_FILE}")
    print()
    print("Output files:")
    for path in output_files.values():
        print(f"- {path}")


if __name__ == "__main__":
    main()