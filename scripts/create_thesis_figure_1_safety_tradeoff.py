"""
Create thesis-ready Figure 1 for the WiFi CSI Fall Attack-Safety Demo.

Input:
    results/defended_vs_undefended_safety_comparison.csv

Outputs:
    figures/thesis_figure_1_safety_tradeoff.png
    notes/thesis_figure_1_safety_tradeoff.md

Purpose:
    Create a thesis-ready figure showing the safety tradeoff between
    missed fall rate and false fall alarm count for undefended and defended
    clean/attacked conditions.

Claim boundary:
    This is a window-level software comparison on processed CSI tensors.
    It is not clinical validation, medical-device validation, diagnostic
    evidence, regulatory evaluation, physical-layer validation, packet-level
    validation, preamble-level validation, SDR validation, or over-the-air
    validation.
"""

from pathlib import Path
import csv

import matplotlib.pyplot as plt


INPUT_FILE = "defended_vs_undefended_safety_comparison.csv"
OUTPUT_FIGURE = "thesis_figure_1_safety_tradeoff.png"
OUTPUT_NOTE = "thesis_figure_1_safety_tradeoff.md"


ORDER = [
    "undefended_clean",
    "undefended_fgsm_epsilon_0_03",
    "undefended_pgd_epsilon_0_03",
    "defended_clean",
    "defended_fgsm_epsilon_0_03",
    "defended_pgd_epsilon_0_03",
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


def safe_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def ordered_rows(rows):
    by_condition = {row["condition"]: row for row in rows}

    missing = [condition for condition in ORDER if condition not in by_condition]
    if missing:
        raise KeyError(f"Missing required conditions: {missing}")

    return [by_condition[condition] for condition in ORDER]


def create_figure(rows, output_path: Path):
    labels = [LABELS[row["condition"]] for row in rows]
    missed_fall_rate = [safe_float(row["missed_fall_rate"]) for row in rows]
    false_alarm_count = [safe_int(row["FP_false_fall_alarms"]) for row in rows]

    x = list(range(len(rows)))

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].bar(x, missed_fall_rate)
    axes[0].set_title("Missed Fall Rate")
    axes[0].set_ylabel("Missed fall rate")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=0)
    axes[0].set_ylim(0, 1.1)

    for index, value in enumerate(missed_fall_rate):
        axes[0].text(
            index,
            value + 0.03,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    axes[1].bar(x, false_alarm_count)
    axes[1].set_title("False Fall Alarm Count")
    axes[1].set_ylabel("False fall alarms")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=0)

    max_false_alarms = max(false_alarm_count) if false_alarm_count else 1
    axes[1].set_ylim(0, max_false_alarms * 1.2)

    for index, value in enumerate(false_alarm_count):
        axes[1].text(
            index,
            value + max_false_alarms * 0.03,
            str(value),
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.suptitle(
        "Figure 1. Defended vs Undefended Fall Safety-Proxy Tradeoff",
        fontsize=14,
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def write_note(path: Path):
    content = """# Thesis Figure 1: Defended vs Undefended Safety Tradeoff

This note documents the first thesis-ready figure for the WiFi CSI Fall Attack-Safety Demo.

Generated figure:

```text
figures/thesis_figure_1_safety_tradeoff.png
```

Input data:

```text
results/defended_vs_undefended_safety_comparison.csv
```

---

## Figure Purpose

The figure compares two fall-focused safety-proxy outcomes across clean, attacked, and defended conditions:

```text
missed fall rate
false fall alarm count
```

The compared conditions are:

```text
undefended clean
undefended FGSM epsilon 0.03
undefended PGD epsilon 0.03
defended clean
defended FGSM epsilon 0.03
defended PGD epsilon 0.03
```

---

## Suggested Thesis Caption

Figure 1. Window-level fall safety-proxy tradeoff for the SenseFi UT-HAR LeNet baseline under clean, FGSM-attacked, PGD-attacked, and short FGSM-adversarial-training defended conditions. The defended model reduced false fall alarms under attack but did not recover fall recall at epsilon 0.03, so missed fall rate remained 1.0 under defended FGSM and defended PGD attack.

---

## Key Interpretation

The figure highlights two different safety-proxy effects.

First, the attacked models missed all fall windows at epsilon 0.03:

```text
undefended FGSM missed fall rate = 1.0000
undefended PGD missed fall rate = 1.0000
defended FGSM missed fall rate = 1.0000
defended PGD missed fall rate = 1.0000
```

Second, the defended model reduced false fall alarms under attack:

```text
FGSM false fall alarms: 119 -> 72
PGD false fall alarms:  115 -> 56
```

This supports a careful interpretation: the first short FGSM adversarial-training defense reduced false alarm burden under attack but did not restore fall sensitivity.

---

## Claim Boundary

This figure is a window-level software comparison on processed CSI tensors.

It is not:

```text
clinical validation
medical-device validation
diagnostic evidence
regulatory evaluation
real patient deployment evidence
event-level fall validation
long-lie validation
time-to-detection validation
physical-layer attack validation
physical-layer defense validation
packet-level validation
preamble-level validation
SDR validation
over-the-air validation
```
"""

    path.write_text(content, encoding="utf-8")


def main():
    experiment_dir = Path(__file__).resolve().parents[1]
    results_dir = experiment_dir / "results"
    figures_dir = experiment_dir / "figures"
    notes_dir = experiment_dir / "notes"

    figures_dir.mkdir(parents=True, exist_ok=True)
    notes_dir.mkdir(parents=True, exist_ok=True)

    input_path = results_dir / INPUT_FILE
    output_figure_path = figures_dir / OUTPUT_FIGURE
    output_note_path = notes_dir / OUTPUT_NOTE

    rows = ordered_rows(read_rows(input_path))

    create_figure(rows, output_figure_path)
    write_note(output_note_path)

    print("Thesis Figure 1 created successfully.")
    print(f"Input: {input_path}")
    print(f"Figure output: {output_figure_path}")
    print(f"Note output: {output_note_path}")


if __name__ == "__main__":
    main()