"""
Create Failure Threshold / Robustness Collapse Plot.

This script visualizes FGSM and PGD epsilon-sweep behavior against key
window-level robustness failure thresholds.

Input:
    results/fgsm_vs_pgd_epsilon_comparison.csv

Outputs:
    figures/thesis_figure_7_failure_threshold_plot.png
    notes/thesis_figure_7_failure_threshold_plot.md

Claim boundary:
    This is a window-level robustness-collapse visualization using processed CSI
    tensors and software-level perturbations. It is not clinical validation,
    medical-device validation, physical-layer validation, or over-the-air validation.
"""

from pathlib import Path
import csv
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
NOTES_DIR = ROOT / "notes"

INPUT_CSV = RESULTS_DIR / "fgsm_vs_pgd_epsilon_comparison.csv"
OUTPUT_FIGURE = FIGURES_DIR / "thesis_figure_7_failure_threshold_plot.png"
OUTPUT_NOTE = NOTES_DIR / "thesis_figure_7_failure_threshold_plot.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level robustness-collapse visualization; "
    "software-level processed-tensor perturbations only; not clinical validation, "
    "not medical-device validation, not diagnostic evidence, not real patient "
    "deployment, not regulatory evaluation, not event-level fall validation, "
    "not long-lie validation, not time-to-alarm validation, and not physical-layer / "
    "packet-level / preamble-level / SDR / over-the-air validation."
)


def read_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required input file: {path}")

    with path.open("r", newline="", encoding="utf-8") as csvfile:
        return list(csv.DictReader(csvfile))


def as_float(value):
    return float(str(value).strip())


def get_attack_series(rows, attack_type):
    selected = [row for row in rows if row["attack_type"].upper() == attack_type.upper()]
    selected = sorted(selected, key=lambda row: as_float(row["epsilon"]))

    return {
        "epsilon": [as_float(row["epsilon"]) for row in selected],
        "missed_fall_rate": [as_float(row["missed_fall_rate"]) for row in selected],
        "recall_sensitivity": [as_float(row["recall_sensitivity"]) for row in selected],
        "f1_score": [as_float(row["f1_score"]) for row in selected],
        "false_alarm_count": [as_float(row["false_alarm_count"]) for row in selected],
        "prediction_change_rate": [as_float(row["prediction_change_rate"]) for row in selected],
        "seven_class_accuracy": [as_float(row["seven_class_accuracy"]) for row in selected],
        "balanced_accuracy": [as_float(row["balanced_accuracy"]) for row in selected],
    }


def plot_figure(fgsm, pgd):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.ravel()

    # Panel 1: missed fall rate
    ax = axes[0]
    ax.plot(fgsm["epsilon"], fgsm["missed_fall_rate"], marker="o", label="FGSM")
    ax.plot(pgd["epsilon"], pgd["missed_fall_rate"], marker="o", label="PGD")
    ax.axhline(0.75, linestyle="--", linewidth=1, label="Severe threshold = 0.75")
    ax.axhline(0.95, linestyle=":", linewidth=1, label="Near-complete threshold = 0.95")
    ax.set_title("Missed fall rate")
    ax.set_xlabel("Epsilon")
    ax.set_ylabel("Missed fall rate")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)

    # Panel 2: recall / sensitivity
    ax = axes[1]
    ax.plot(fgsm["epsilon"], fgsm["recall_sensitivity"], marker="o", label="FGSM")
    ax.plot(pgd["epsilon"], pgd["recall_sensitivity"], marker="o", label="PGD")
    ax.axhline(0.05, linestyle="--", linewidth=1, label="Recall collapse threshold = 0.05")
    ax.set_title("Fall recall / sensitivity")
    ax.set_xlabel("Epsilon")
    ax.set_ylabel("Recall / sensitivity")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)

    # Panel 3: false fall alarm count
    ax = axes[2]
    ax.plot(fgsm["epsilon"], fgsm["false_alarm_count"], marker="o", label="FGSM")
    ax.plot(pgd["epsilon"], pgd["false_alarm_count"], marker="o", label="PGD")
    ax.axhline(100, linestyle="--", linewidth=1, label="High false-alarm threshold = 100")
    ax.set_title("False fall alarm count")
    ax.set_xlabel("Epsilon")
    ax.set_ylabel("False fall alarm windows")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)

    # Panel 4: prediction change rate
    ax = axes[3]
    ax.plot(fgsm["epsilon"], fgsm["prediction_change_rate"], marker="o", label="FGSM")
    ax.plot(pgd["epsilon"], pgd["prediction_change_rate"], marker="o", label="PGD")
    ax.axhline(0.50, linestyle="--", linewidth=1, label="Instability threshold = 0.50")
    ax.set_title("Prediction change rate")
    ax.set_xlabel("Epsilon")
    ax.set_ylabel("Prediction change rate")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)

    fig.suptitle(
        "Failure Threshold / Robustness Collapse Plot\n"
        "Window-level safety-proxy degradation under FGSM and PGD",
        fontsize=14,
    )

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(OUTPUT_FIGURE, dpi=300, bbox_inches="tight")
    plt.close(fig)


def first_crossing(series, metric, direction, threshold):
    previous = None

    for epsilon, value in zip(series["epsilon"], series[metric]):
        if direction == ">=" and value >= threshold:
            return epsilon, value, previous
        if direction == "<=" and value <= threshold:
            return epsilon, value, previous
        previous = (epsilon, value)

    return None, None, previous


def write_note(fgsm, pgd):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    fgsm_missed = first_crossing(fgsm, "missed_fall_rate", ">=", 0.75)
    pgd_missed = first_crossing(pgd, "missed_fall_rate", ">=", 0.75)

    fgsm_near_complete = first_crossing(fgsm, "missed_fall_rate", ">=", 0.95)
    pgd_near_complete = first_crossing(pgd, "missed_fall_rate", ">=", 0.95)

    fgsm_recall = first_crossing(fgsm, "recall_sensitivity", "<=", 0.05)
    pgd_recall = first_crossing(pgd, "recall_sensitivity", "<=", 0.05)

    fgsm_instability = first_crossing(fgsm, "prediction_change_rate", ">=", 0.50)
    pgd_instability = first_crossing(pgd, "prediction_change_rate", ">=", 0.50)

    fgsm_false_alarm = first_crossing(fgsm, "false_alarm_count", ">=", 100)
    pgd_false_alarm = first_crossing(pgd, "false_alarm_count", ">=", 100)

    lines = []
    lines.append("# Failure Threshold / Robustness Collapse Plot")
    lines.append("")
    lines.append(
        "This figure visualizes FGSM and PGD epsilon-sweep behavior against "
        "window-level robustness failure thresholds."
    )
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Output Figure")
    lines.append("")
    lines.append("- `figures/thesis_figure_7_failure_threshold_plot.png`")
    lines.append("")
    lines.append("## Input File")
    lines.append("")
    lines.append("- `results/fgsm_vs_pgd_epsilon_comparison.csv`")
    lines.append("")
    lines.append("## Panels")
    lines.append("")
    lines.append("The figure contains four panels:")
    lines.append("")
    lines.append("1. missed fall rate")
    lines.append("2. fall recall / sensitivity")
    lines.append("3. false fall alarm count")
    lines.append("4. prediction change rate")
    lines.append("")
    lines.append("## Key Threshold Crossings")
    lines.append("")
    lines.append("| Threshold | FGSM First Epsilon | PGD First Epsilon |")
    lines.append("|---|---:|---:|")
    lines.append(
        f"| missed_fall_rate >= 0.75 | {fgsm_missed[0]:.4f} | {pgd_missed[0]:.4f} |"
    )
    lines.append(
        f"| missed_fall_rate >= 0.95 | {fgsm_near_complete[0]:.4f} | {pgd_near_complete[0]:.4f} |"
    )
    lines.append(
        f"| recall_sensitivity <= 0.05 | {fgsm_recall[0]:.4f} | {pgd_recall[0]:.4f} |"
    )
    lines.append(
        f"| prediction_change_rate >= 0.50 | {fgsm_instability[0]:.4f} | {pgd_instability[0]:.4f} |"
    )
    lines.append(
        f"| false_alarm_count >= 100 | {fgsm_false_alarm[0]:.4f} | {pgd_false_alarm[0]:.4f} |"
    )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Figure 7 complements Table 9 by showing the threshold-crossing behavior "
        "visually. PGD reaches the severe missed-fall threshold earlier than FGSM, "
        "while both attacks reach near-complete missed-fall behavior by epsilon 0.010."
    )
    lines.append("")
    lines.append(
        "The false-alarm panel should be interpreted as a window-count result only. "
        "It should not be converted into false alarms per hour or day because the "
        "local UT-HAR copy does not provide recording-duration metadata."
    )
    lines.append("")
    lines.append(
        "This figure should be described as a window-level robustness-collapse "
        "visualization, not as event-level clinical validation."
    )
    lines.append("")

    OUTPUT_NOTE.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows = read_rows(INPUT_CSV)
    fgsm = get_attack_series(rows, "FGSM")
    pgd = get_attack_series(rows, "PGD")

    plot_figure(fgsm, pgd)
    write_note(fgsm, pgd)

    print("Created Thesis Figure 7 outputs:")
    print(f"  {OUTPUT_FIGURE}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Key threshold crossings:")
    for attack_name, series in [("FGSM", fgsm), ("PGD", pgd)]:
        severe = first_crossing(series, "missed_fall_rate", ">=", 0.75)
        near_complete = first_crossing(series, "missed_fall_rate", ">=", 0.95)
        recall = first_crossing(series, "recall_sensitivity", "<=", 0.05)
        instability = first_crossing(series, "prediction_change_rate", ">=", 0.50)
        false_alarm = first_crossing(series, "false_alarm_count", ">=", 100)

        print(f"  {attack_name}:")
        print(f"    missed_fall_rate >= 0.75 at epsilon {severe[0]:.4f}")
        print(f"    missed_fall_rate >= 0.95 at epsilon {near_complete[0]:.4f}")
        print(f"    recall_sensitivity <= 0.05 at epsilon {recall[0]:.4f}")
        print(f"    prediction_change_rate >= 0.50 at epsilon {instability[0]:.4f}")
        print(f"    false_alarm_count >= 100 at epsilon {false_alarm[0]:.4f}")


if __name__ == "__main__":
    main()
