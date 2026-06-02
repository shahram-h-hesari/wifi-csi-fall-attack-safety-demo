"""
Create FGSM vs PGD comparison table and figure for the WiFi CSI Fall Attack-Safety Demo.

Inputs:
- results/fgsm_epsilon_sweep_summary.csv
- results/pgd_epsilon_sweep_summary.csv

Outputs:
- results/fgsm_vs_pgd_epsilon_comparison.csv
- figures/fgsm_vs_pgd_safety_comparison.png

Important claim boundary:
This comparison uses software-level adversarial perturbations applied to processed
UT-HAR CSI tensors. It is not clinical validation, medical-device validation,
physical-layer validation, SDR validation, or over-the-air validation.
"""

from pathlib import Path
import csv

import matplotlib.pyplot as plt


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = EXPERIMENT_DIR / "results"
FIGURES_DIR = EXPERIMENT_DIR / "figures"

FGSM_INPUT = RESULTS_DIR / "fgsm_epsilon_sweep_summary.csv"
PGD_INPUT = RESULTS_DIR / "pgd_epsilon_sweep_summary.csv"

OUTPUT_CSV = RESULTS_DIR / "fgsm_vs_pgd_epsilon_comparison.csv"
OUTPUT_FIGURE = FIGURES_DIR / "fgsm_vs_pgd_safety_comparison.png"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", newline="", encoding="utf-8") as csvfile:
        rows = list(csv.DictReader(csvfile))

    if not rows:
        raise ValueError(f"No rows found in input file: {path}")

    return rows


def get_value(row, possible_names, default=""):
    for name in possible_names:
        if name in row and row[name] != "":
            return row[name]
    return default


def normalize_rows(rows, attack_type):
    normalized = []

    for row in rows:
        epsilon = float(get_value(row, ["epsilon"]))

        false_alarm_count = get_value(
            row,
            ["fp_false_fall_alarms", "false_alarm_count", "false_alarms"],
            default="0",
        )

        normalized.append(
            {
                "attack_type": attack_type,
                "epsilon": epsilon,
                "seven_class_accuracy": float(
                    get_value(row, ["seven_class_accuracy", "seven_class_acc"], default="0")
                ),
                "missed_fall_rate": float(
                    get_value(row, ["missed_fall_rate"], default="0")
                ),
                "false_alarm_count": int(float(false_alarm_count)),
                "recall_sensitivity": float(
                    get_value(row, ["recall_sensitivity", "recall"], default="0")
                ),
                "f1_score": float(
                    get_value(row, ["f1_score", "f1"], default="0")
                ),
                "balanced_accuracy": float(
                    get_value(row, ["balanced_accuracy"], default="0")
                ),
                "prediction_change_rate": float(
                    get_value(row, ["prediction_change_rate"], default="0")
                ),
            }
        )

    return normalized


def write_comparison_csv(rows):
    fieldnames = [
        "attack_type",
        "epsilon",
        "seven_class_accuracy",
        "missed_fall_rate",
        "false_alarm_count",
        "recall_sensitivity",
        "f1_score",
        "balanced_accuracy",
        "prediction_change_rate",
    ]

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    "attack_type": row["attack_type"],
                    "epsilon": f"{row['epsilon']:.3f}",
                    "seven_class_accuracy": f"{row['seven_class_accuracy']:.6f}",
                    "missed_fall_rate": f"{row['missed_fall_rate']:.6f}",
                    "false_alarm_count": row["false_alarm_count"],
                    "recall_sensitivity": f"{row['recall_sensitivity']:.6f}",
                    "f1_score": f"{row['f1_score']:.6f}",
                    "balanced_accuracy": f"{row['balanced_accuracy']:.6f}",
                    "prediction_change_rate": f"{row['prediction_change_rate']:.6f}",
                }
            )


def save_comparison_figure(fgsm_rows, pgd_rows):
    fgsm_eps = [row["epsilon"] for row in fgsm_rows]
    pgd_eps = [row["epsilon"] for row in pgd_rows]

    fgsm_missed = [row["missed_fall_rate"] for row in fgsm_rows]
    pgd_missed = [row["missed_fall_rate"] for row in pgd_rows]

    fgsm_recall = [row["recall_sensitivity"] for row in fgsm_rows]
    pgd_recall = [row["recall_sensitivity"] for row in pgd_rows]

    fgsm_f1 = [row["f1_score"] for row in fgsm_rows]
    pgd_f1 = [row["f1_score"] for row in pgd_rows]

    plt.figure(figsize=(10, 6))

    plt.plot(fgsm_eps, fgsm_missed, marker="o", label="FGSM missed fall rate")
    plt.plot(pgd_eps, pgd_missed, marker="o", label="PGD missed fall rate")

    plt.plot(fgsm_eps, fgsm_recall, marker="o", label="FGSM recall")
    plt.plot(pgd_eps, pgd_recall, marker="o", label="PGD recall")

    plt.plot(fgsm_eps, fgsm_f1, marker="o", label="FGSM F1-score")
    plt.plot(pgd_eps, pgd_f1, marker="o", label="PGD F1-score")

    plt.title("FGSM vs PGD: Window-Level Fall Safety-Proxy Comparison")
    plt.xlabel("Epsilon")
    plt.ylabel("Metric value")
    plt.ylim(-0.05, 1.05)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_FIGURE, dpi=300)
    plt.close()


def print_summary(fgsm_rows, pgd_rows):
    print("FGSM vs PGD comparison completed.")
    print(f"FGSM input:     {FGSM_INPUT}")
    print(f"PGD input:      {PGD_INPUT}")
    print(f"Output CSV:     {OUTPUT_CSV}")
    print(f"Output figure:  {OUTPUT_FIGURE}")
    print()

    print("Summary")
    print("-------")
    for fgsm_row, pgd_row in zip(fgsm_rows, pgd_rows):
        epsilon = fgsm_row["epsilon"]

        print(
            f"epsilon={epsilon:.3f} | "
            f"FGSM missed={fgsm_row['missed_fall_rate']:.6f}, "
            f"PGD missed={pgd_row['missed_fall_rate']:.6f} | "
            f"FGSM recall={fgsm_row['recall_sensitivity']:.6f}, "
            f"PGD recall={pgd_row['recall_sensitivity']:.6f} | "
            f"FGSM F1={fgsm_row['f1_score']:.6f}, "
            f"PGD F1={pgd_row['f1_score']:.6f}"
        )


def main():
    fgsm_raw = read_csv(FGSM_INPUT)
    pgd_raw = read_csv(PGD_INPUT)

    fgsm_rows = normalize_rows(fgsm_raw, "FGSM")
    pgd_rows = normalize_rows(pgd_raw, "PGD")

    fgsm_rows = sorted(fgsm_rows, key=lambda row: row["epsilon"])
    pgd_rows = sorted(pgd_rows, key=lambda row: row["epsilon"])

    fgsm_eps = [row["epsilon"] for row in fgsm_rows]
    pgd_eps = [row["epsilon"] for row in pgd_rows]

    if fgsm_eps != pgd_eps:
        raise ValueError(
            "FGSM and PGD epsilon values do not match.\n"
            f"FGSM epsilons: {fgsm_eps}\n"
            f"PGD epsilons:  {pgd_eps}"
        )

    comparison_rows = []
    comparison_rows.extend(fgsm_rows)
    comparison_rows.extend(pgd_rows)

    write_comparison_csv(comparison_rows)
    save_comparison_figure(fgsm_rows, pgd_rows)
    print_summary(fgsm_rows, pgd_rows)


if __name__ == "__main__":
    main()