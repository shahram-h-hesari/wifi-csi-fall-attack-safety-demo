from pathlib import Path
import csv
import matplotlib.pyplot as plt


# ============================================================
# Thesis Figure 2: FGSM vs PGD Epsilon Sweep Curves
#
# Purpose:
# Compare FGSM and PGD dose-response behavior across epsilon
# values using window-level fall-vs-non-fall safety-proxy
# metrics.
#
# Metrics plotted:
# 1. Missed fall rate vs epsilon
# 2. Recall/sensitivity vs epsilon
# 3. F1-score vs epsilon
# 4. False fall alarm count vs epsilon
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

FGSM_SWEEP_FILE = RESULTS_DIR / "fgsm_epsilon_sweep_summary.csv"
PGD_SWEEP_FILE = RESULTS_DIR / "pgd_epsilon_sweep_summary.csv"

OUTPUT_FIGURE = FIGURES_DIR / "thesis_figure_2_fgsm_pgd_epsilon_sweep.png"
OUTPUT_MD = NOTES_DIR / "thesis_figure_2_fgsm_pgd_epsilon_sweep.md"


def normalize_key(text):
    text = str(text).strip().lower()
    text = text.replace("-", "_")
    text = text.replace(" ", "_")
    text = text.replace("/", "_")
    text = text.replace("(", "")
    text = text.replace(")", "")
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_")


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


def read_sweep_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    rows = []

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for raw_row in reader:
            row = {}

            for key, value in raw_row.items():
                row[normalize_key(key)] = to_float(value)

            rows.append(row)

    if not rows:
        raise ValueError(f"No rows found in {path}")

    rows = sorted(rows, key=lambda item: item["epsilon"])

    return rows


def get_series(rows, metric_aliases):
    values = []

    for row in rows:
        found = None

        for alias in metric_aliases:
            key = normalize_key(alias)

            if key in row:
                found = row[key]
                break

        if found is None:
            available = ", ".join(sorted(row.keys()))
            raise KeyError(
                f"Could not find any aliases {metric_aliases}. "
                f"Available columns: {available}"
            )

        values.append(found)

    return values


def write_markdown(fgsm_rows, pgd_rows):
    fgsm_eps = get_series(fgsm_rows, ["epsilon"])
    pgd_eps = get_series(pgd_rows, ["epsilon"])

    fgsm_missed = get_series(fgsm_rows, ["missed_fall_rate"])
    pgd_missed = get_series(pgd_rows, ["missed_fall_rate"])

    fgsm_recall = get_series(fgsm_rows, ["recall_sensitivity", "recall"])
    pgd_recall = get_series(pgd_rows, ["recall_sensitivity", "recall"])

    fgsm_f1 = get_series(fgsm_rows, ["f1_score", "f1"])
    pgd_f1 = get_series(pgd_rows, ["f1_score", "f1"])

    fgsm_false_alarms = get_series(fgsm_rows, ["false_alarm_count", "false_alarms", "fp_false_fall_alarms"])
    pgd_false_alarms = get_series(pgd_rows, ["false_alarm_count", "false_alarms", "fp_false_fall_alarms"])

    lines = []

    lines.append("# Thesis Figure 2: FGSM vs PGD Epsilon Sweep Curves")
    lines.append("")
    lines.append("This figure compares FGSM and PGD epsilon-sweep behavior using window-level fall-vs-non-fall safety-proxy metrics.")
    lines.append("")
    lines.append("The figure includes four dose-response curves:")
    lines.append("")
    lines.append("- Missed fall rate vs epsilon")
    lines.append("- Recall/sensitivity vs epsilon")
    lines.append("- F1-score vs epsilon")
    lines.append("- False fall alarm count vs epsilon")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append("This is a research implementation using window-level safety-proxy metrics and software-level processed-tensor adversarial perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.")
    lines.append("")
    lines.append("## Summary Table")
    lines.append("")
    lines.append("| Epsilon | FGSM Missed Fall Rate | PGD Missed Fall Rate | FGSM Recall | PGD Recall | FGSM F1 | PGD F1 | FGSM False Alarms | PGD False Alarms |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for i in range(min(len(fgsm_eps), len(pgd_eps))):
        lines.append(
            "| "
            f"{fgsm_eps[i]:.3f} | "
            f"{fgsm_missed[i]:.4f} | "
            f"{pgd_missed[i]:.4f} | "
            f"{fgsm_recall[i]:.4f} | "
            f"{pgd_recall[i]:.4f} | "
            f"{fgsm_f1[i]:.4f} | "
            f"{pgd_f1[i]:.4f} | "
            f"{int(round(fgsm_false_alarms[i]))} | "
            f"{int(round(pgd_false_alarms[i]))} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The epsilon sweep shows the dose-response relationship between perturbation strength and fall-safety degradation. As epsilon increases, missed fall rate increases and recall/sensitivity and F1-score decrease. False fall alarm counts also change with perturbation strength. This supports the thesis framing that adversarial degradation should be interpreted using safety-proxy metrics, not only aggregate model accuracy.")
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `figures/thesis_figure_2_fgsm_pgd_epsilon_sweep.png`")
    lines.append("- `notes/thesis_figure_2_fgsm_pgd_epsilon_sweep.md`")
    lines.append("- Input: `results/fgsm_epsilon_sweep_summary.csv`")
    lines.append("- Input: `results/pgd_epsilon_sweep_summary.csv`")
    lines.append("")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    fgsm_rows = read_sweep_csv(FGSM_SWEEP_FILE)
    pgd_rows = read_sweep_csv(PGD_SWEEP_FILE)

    fgsm_epsilon = get_series(fgsm_rows, ["epsilon"])
    pgd_epsilon = get_series(pgd_rows, ["epsilon"])

    fgsm_missed = get_series(fgsm_rows, ["missed_fall_rate"])
    pgd_missed = get_series(pgd_rows, ["missed_fall_rate"])

    fgsm_recall = get_series(fgsm_rows, ["recall_sensitivity", "recall"])
    pgd_recall = get_series(pgd_rows, ["recall_sensitivity", "recall"])

    fgsm_f1 = get_series(fgsm_rows, ["f1_score", "f1"])
    pgd_f1 = get_series(pgd_rows, ["f1_score", "f1"])

    fgsm_false_alarms = get_series(fgsm_rows, ["false_alarm_count", "false_alarms", "fp_false_fall_alarms"])
    pgd_false_alarms = get_series(pgd_rows, ["false_alarm_count", "false_alarms", "fp_false_fall_alarms"])

    plt.figure(figsize=(12, 9))

    plt.subplot(2, 2, 1)
    plt.plot(fgsm_epsilon, fgsm_missed, marker="o", label="FGSM")
    plt.plot(pgd_epsilon, pgd_missed, marker="s", label="PGD")
    plt.xlabel("Epsilon")
    plt.ylabel("Missed Fall Rate")
    plt.title("Missed Fall Rate vs Epsilon")
    plt.ylim(-0.05, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.subplot(2, 2, 2)
    plt.plot(fgsm_epsilon, fgsm_recall, marker="o", label="FGSM")
    plt.plot(pgd_epsilon, pgd_recall, marker="s", label="PGD")
    plt.xlabel("Epsilon")
    plt.ylabel("Recall / Sensitivity")
    plt.title("Recall/Sensitivity vs Epsilon")
    plt.ylim(-0.05, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.subplot(2, 2, 3)
    plt.plot(fgsm_epsilon, fgsm_f1, marker="o", label="FGSM")
    plt.plot(pgd_epsilon, pgd_f1, marker="s", label="PGD")
    plt.xlabel("Epsilon")
    plt.ylabel("F1-Score")
    plt.title("F1-Score vs Epsilon")
    plt.ylim(-0.05, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.subplot(2, 2, 4)
    plt.plot(fgsm_epsilon, fgsm_false_alarms, marker="o", label="FGSM")
    plt.plot(pgd_epsilon, pgd_false_alarms, marker="s", label="PGD")
    plt.xlabel("Epsilon")
    plt.ylabel("False Fall Alarm Count")
    plt.title("False Fall Alarms vs Epsilon")
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.suptitle(
        "Thesis Figure 2: FGSM vs PGD Epsilon Sweep Safety-Proxy Curves",
        fontsize=14,
        fontweight="bold",
    )

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(OUTPUT_FIGURE, dpi=300)
    plt.close()

    write_markdown(fgsm_rows, pgd_rows)

    print("Created Thesis Figure 2 outputs:")
    print(f"  {OUTPUT_FIGURE}")
    print(f"  {OUTPUT_MD}")
    print("")
    print("Summary:")
    print(f"  FGSM epsilon values: {', '.join(f'{x:.3f}' for x in fgsm_epsilon)}")
    print(f"  PGD epsilon values: {', '.join(f'{x:.3f}' for x in pgd_epsilon)}")
    print(f"  Figure saved to: {OUTPUT_FIGURE}")


if __name__ == "__main__":
    main()