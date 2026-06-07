"""
Create Thesis Table 27 and Figure 27:
Attack-Severity Dose Response of Fall-Safety Metrics.

Updated version:
- fixes layout overlap
- improves subplot spacing
- fixes main-figure axis choices for a more defensible visual scale
- keeps Panel A/FNR and Panel B/FPR starting at 0 in the main figure
- removes crowded vertical collapse labels while keeping collapse threshold lines
- creates a second zoomed comparison figure so FGSM vs PGD differences are easier to see

Input:
    results/epsilon_sweep_predictions/attack_prediction_sweep_18eps_summary.csv

Outputs:
    results/thesis_table_27_attack_severity_dose_response.csv
    figures/thesis_figure_27a_attack_severity_dose_response.png
    figures/thesis_figure_27b_attack_severity_dose_response_zoom.png
    notes/thesis_table_27_figure_27_attack_severity_dose_response.md
    README.md section update

Claim boundary:
    This is a software-level processed-tensor adversarial stress test using
    UT-HAR / SenseFi window-level outputs. It is not physical-layer validation,
    over-the-air validation, packet-level validation, clinical validation, or
    event-level fall validation.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


# =============================================================================
# Paths
# =============================================================================

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_DIR = SCRIPT_PATH.parent.parent

README_PATH = PROJECT_DIR / "README.md"
RESULTS_DIR = PROJECT_DIR / "results"
FIGURES_DIR = PROJECT_DIR / "figures"
NOTES_DIR = PROJECT_DIR / "notes"

SWEEP_SUMMARY_PATH = (
    RESULTS_DIR
    / "epsilon_sweep_predictions"
    / "attack_prediction_sweep_18eps_summary.csv"
)

TABLE_PATH = RESULTS_DIR / "thesis_table_27_attack_severity_dose_response.csv"
FIGURE_PATH = FIGURES_DIR / "thesis_figure_27a_attack_severity_dose_response.png"
ZOOM_FIGURE_PATH = FIGURES_DIR / "thesis_figure_27b_attack_severity_dose_response_zoom.png"
NOTE_PATH = NOTES_DIR / "thesis_table_27_figure_27_attack_severity_dose_response.md"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Utility functions
# =============================================================================

def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing input summary file:\n{path}\n\n"
            "Run scripts/export_attack_prediction_sweep_18eps.py first."
        )

    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def to_float(value: Any) -> float:
    return float(str(value).strip())


def to_int(value: Any) -> int:
    return int(float(str(value).strip()))


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return math.nan
    return numerator / denominator


def format_float(value: Any, digits: int = 6) -> str:
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.{digits}f}"
    return str(value)


def require_columns(rows: list[dict[str, str]], required: list[str]) -> None:
    if not rows:
        raise ValueError(f"No rows found in {SWEEP_SUMMARY_PATH}")

    available = set(rows[0].keys())
    missing = [column for column in required if column not in available]

    if missing:
        raise ValueError(
            f"Missing required columns in {SWEEP_SUMMARY_PATH}: {missing}\n"
            f"Available columns: {sorted(available)}"
        )


# =============================================================================
# Analysis
# =============================================================================

REQUIRED_COLUMNS = [
    "attack_type",
    "epsilon",
    "attacked_accuracy",
    "missed_fall_rate_fnr",
    "false_positive_rate_fpr",
    "score_10_to_1",
    "tp",
    "fn",
    "fp",
    "tn",
    "total_windows",
    "total_fall_windows",
    "total_nonfall_windows",
]


def load_sweep_rows() -> list[dict[str, Any]]:
    raw_rows = read_csv_rows(SWEEP_SUMMARY_PATH)
    require_columns(raw_rows, REQUIRED_COLUMNS)

    rows: list[dict[str, Any]] = []

    for raw in raw_rows:
        rows.append(
            {
                "attack_type": raw["attack_type"].strip().upper(),
                "epsilon": to_float(raw["epsilon"]),
                "attacked_accuracy": to_float(raw["attacked_accuracy"]),
                "missed_fall_rate_fnr": to_float(raw["missed_fall_rate_fnr"]),
                "false_positive_rate_fpr": to_float(raw["false_positive_rate_fpr"]),
                "score_10_to_1": to_float(raw["score_10_to_1"]),
                "tp": to_int(raw["tp"]),
                "fn": to_int(raw["fn"]),
                "fp": to_int(raw["fp"]),
                "tn": to_int(raw["tn"]),
                "total_windows": to_int(raw["total_windows"]),
                "total_fall_windows": to_int(raw["total_fall_windows"]),
                "total_nonfall_windows": to_int(raw["total_nonfall_windows"]),
                "prediction_file": raw.get("prediction_file", ""),
                "alpha": raw.get("alpha", ""),
                "pgd_steps": raw.get("pgd_steps", ""),
            }
        )

    rows.sort(key=lambda row: (row["attack_type"], row["epsilon"]))
    return rows


def first_epsilon_at_or_above(
    rows: list[dict[str, Any]],
    attack_type: str,
    metric_name: str,
    threshold: float,
) -> float | None:
    attack_rows = [row for row in rows if row["attack_type"] == attack_type]
    attack_rows.sort(key=lambda row: row["epsilon"])

    for row in attack_rows:
        if row[metric_name] >= threshold:
            return row["epsilon"]
    return None


def first_epsilon_at_or_below(
    rows: list[dict[str, Any]],
    attack_type: str,
    metric_name: str,
    threshold: float,
) -> float | None:
    attack_rows = [row for row in rows if row["attack_type"] == attack_type]
    attack_rows.sort(key=lambda row: row["epsilon"])

    for row in attack_rows:
        if row[metric_name] <= threshold:
            return row["epsilon"]
    return None


def monotonic_non_decreasing(values: list[float], tolerance: float = 1e-9) -> bool:
    return all(values[i] <= values[i + 1] + tolerance for i in range(len(values) - 1))


def monotonic_non_increasing(values: list[float], tolerance: float = 1e-9) -> bool:
    return all(values[i] + tolerance >= values[i + 1] for i in range(len(values) - 1))


def build_table_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    table_rows: list[dict[str, Any]] = []

    for row in rows:
        table_rows.append(
            {
                "attack_type": row["attack_type"],
                "epsilon": row["epsilon"],
                "attacked_accuracy": row["attacked_accuracy"],
                "missed_fall_rate_fnr": row["missed_fall_rate_fnr"],
                "false_positive_rate_fpr": row["false_positive_rate_fpr"],
                "safety_priority_score_10_to_1": row["score_10_to_1"],
                "tp": row["tp"],
                "fn": row["fn"],
                "fp": row["fp"],
                "tn": row["tn"],
                "total_windows": row["total_windows"],
                "total_fall_windows": row["total_fall_windows"],
                "total_nonfall_windows": row["total_nonfall_windows"],
                "prediction_file": row["prediction_file"],
                "alpha": row["alpha"],
                "pgd_steps": row["pgd_steps"],
                "interpretation": (
                    f"{row['attack_type']} at epsilon={row['epsilon']:.6f}: "
                    f"FNR={row['missed_fall_rate_fnr']:.3f}, "
                    f"FPR={row['false_positive_rate_fpr']:.3f}, "
                    f"score10={row['score_10_to_1']:.3f}, "
                    f"accuracy={row['attacked_accuracy']:.3f}."
                ),
            }
        )

    return table_rows


def write_table(table_rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "attack_type",
        "epsilon",
        "attacked_accuracy",
        "missed_fall_rate_fnr",
        "false_positive_rate_fpr",
        "safety_priority_score_10_to_1",
        "tp",
        "fn",
        "fp",
        "tn",
        "total_windows",
        "total_fall_windows",
        "total_nonfall_windows",
        "prediction_file",
        "alpha",
        "pgd_steps",
        "interpretation",
    ]

    with TABLE_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for row in table_rows:
            output_row = {key: row[key] for key in fieldnames}
            for key in [
                "epsilon",
                "attacked_accuracy",
                "missed_fall_rate_fnr",
                "false_positive_rate_fpr",
                "safety_priority_score_10_to_1",
            ]:
                output_row[key] = format_float(output_row[key])
            writer.writerow(output_row)


def attack_arrays(rows: list[dict[str, Any]], attack_type: str, metric: str):
    attack_rows = [row for row in rows if row["attack_type"] == attack_type]
    attack_rows.sort(key=lambda row: row["epsilon"])

    eps = np.array([row["epsilon"] for row in attack_rows], dtype=float)
    vals = np.array([row[metric] for row in attack_rows], dtype=float)
    return eps, vals


def add_collapse_markers(
    ax,
    fgsm_collapse: float | None,
    pgd_collapse: float | None,
) -> None:
    """
    Add collapse-threshold reference lines without crowded vertical text labels.

    The exact epsilon values are stated in the bottom caption, which keeps the
    panel readable while preserving the main threshold information.
    """
    if pgd_collapse is not None:
        ax.axvline(pgd_collapse, linestyle=":", linewidth=1.3, alpha=0.9)

    if fgsm_collapse is not None:
        ax.axvline(fgsm_collapse, linestyle=":", linewidth=1.3, alpha=0.9)


def create_main_figure(rows: list[dict[str, Any]]) -> tuple[float | None, float | None]:
    fgsm_collapse = first_epsilon_at_or_above(rows, "FGSM", "missed_fall_rate_fnr", 1.0)
    pgd_collapse = first_epsilon_at_or_above(rows, "PGD", "missed_fall_rate_fnr", 1.0)

    fig, axes = plt.subplots(2, 2, figsize=(15.5, 10.5), dpi=150)
    fig.subplots_adjust(
        left=0.07,
        right=0.98,
        top=0.86,
        bottom=0.18,
        wspace=0.22,
        hspace=0.40,
    )

    fig.suptitle(
        "Figure 27A: Attack-Severity Dose Response of Fall-Safety Metrics",
        fontsize=18.5,
        fontweight="bold",
        y=0.955,
    )

    metrics = [
        ("missed_fall_rate_fnr", "A. Missed-fall rate / FNR", "Missed-fall rate"),
        ("false_positive_rate_fpr", "B. False-positive rate / FPR", "False-positive rate"),
        ("score_10_to_1", "C. Safety-priority score (FN:FP = 10:1)", "Safety-priority score"),
        ("attacked_accuracy", "D. Attacked accuracy", "Accuracy"),
    ]

    for idx, (ax, (metric, title, ylabel)) in enumerate(zip(axes.flatten(), metrics)):
        for attack_type in ["FGSM", "PGD"]:
            eps, vals = attack_arrays(rows, attack_type, metric)
            ax.plot(
                eps,
                vals,
                marker="o",
                linewidth=2.0,
                markersize=5.0,
                label=attack_type,
            )

        ax.set_title(title, fontsize=12.5, fontweight="bold", pad=10)
        ax.set_ylabel(ylabel, fontsize=10.5, fontweight="bold")
        ax.tick_params(axis="both", labelsize=9.5)
        ax.grid(True, linestyle="--", linewidth=0.65, alpha=0.45)
        ax.set_xlim(-0.002, 0.078)

        # Only bottom row gets x-axis label to avoid overlap.
        if idx >= 2:
            ax.set_xlabel("Epsilon", fontsize=10.5, fontweight="bold")
        else:
            ax.set_xlabel("")

        if metric == "missed_fall_rate_fnr":
            # Main figure starts rates at zero for a defensible full-scale view.
            ax.set_ylim(0.00, 1.08)
            add_collapse_markers(ax, fgsm_collapse, pgd_collapse)

        elif metric == "false_positive_rate_fpr":
            # Main figure starts at zero while still focusing on the observed FPR range.
            ax.set_ylim(0.00, 0.18)

        elif metric == "score_10_to_1":
            ax.set_ylim(3.2, 10.4)

        elif metric == "attacked_accuracy":
            ax.set_ylim(0.00, 0.72)

    axes[0, 0].legend(
        loc="lower right",
        fontsize=9.4,
        frameon=True,
    )

    collapse_text = (
        "Fall-window collapse threshold: "
        f"PGD FNR = 1.000 at ε = {pgd_collapse:.4f}; "
        f"FGSM FNR = 1.000 at ε = {fgsm_collapse:.4f}."
        if fgsm_collapse is not None and pgd_collapse is not None
        else "Fall-window collapse threshold could not be determined."
    )

    fig.text(
        0.50,
        0.115,
        collapse_text,
        ha="center",
        va="center",
        fontsize=10.2,
        fontweight="bold",
    )

    fig.text(
        0.50,
        0.080,
        (
            "Dose-response analysis uses 18 epsilon values; dotted lines in Panel A mark PGD and FGSM FNR=1.000 collapse thresholds. "
            "Inputs come from results/epsilon_sweep_predictions/."
        ),
        ha="center",
        va="center",
        fontsize=9.4,
    )

    fig.text(
        0.50,
        0.046,
        (
            "Window-level processed-tensor adversarial stress test only; not "
            "event-level, clinical, physical-layer, packet-level, SDR, or over-the-air validation."
        ),
        ha="center",
        va="center",
        fontsize=8.8,
    )

    fig.savefig(FIGURE_PATH, dpi=300, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)

    return fgsm_collapse, pgd_collapse


def create_zoom_figure(rows: list[dict[str, Any]]) -> None:
    """
    Companion Figure 27B to better separate FGSM and PGD curves where they are
    visually close in the main figure.
    """
    fig, axes = plt.subplots(2, 2, figsize=(15.0, 10.0), dpi=150)
    fig.subplots_adjust(
        left=0.08,
        right=0.98,
        top=0.88,
        bottom=0.18,
        wspace=0.22,
        hspace=0.34,
    )

    fig.suptitle(
        "Figure 27B: Early-Epsilon FGSM vs PGD Comparison",
        fontsize=17.0,
        fontweight="bold",
        y=0.955,
    )

    metrics = [
        ("missed_fall_rate_fnr", "A. Zoomed missed-fall rate / FNR", "Missed-fall rate"),
        ("false_positive_rate_fpr", "B. Zoomed false-positive rate / FPR", "False-positive rate"),
        ("score_10_to_1", "C. Zoomed safety-priority score (FN:FP = 10:1)", "Safety-priority score"),
        ("attacked_accuracy", "D. Zoomed attacked accuracy", "Accuracy"),
    ]

    for idx, (ax, (metric, title, ylabel)) in enumerate(zip(axes.flatten(), metrics)):
        for attack_type in ["FGSM", "PGD"]:
            eps, vals = attack_arrays(rows, attack_type, metric)
            ax.plot(
                eps,
                vals,
                marker="o",
                linewidth=2.0,
                markersize=5.0,
                label=attack_type,
            )

        ax.set_title(title, fontsize=12.0, fontweight="bold", pad=10)
        ax.set_ylabel(ylabel, fontsize=10.3, fontweight="bold")
        ax.tick_params(axis="both", labelsize=9.2)
        ax.grid(True, linestyle="--", linewidth=0.65, alpha=0.45)

        # Zoom to early epsilon region where the differences are most informative.
        ax.set_xlim(-0.001, 0.022)

        if idx >= 2:
            ax.set_xlabel("Epsilon", fontsize=10.3, fontweight="bold")
        else:
            ax.set_xlabel("")

        if metric == "missed_fall_rate_fnr":
            ax.set_ylim(0.30, 1.02)

        elif metric == "false_positive_rate_fpr":
            ax.set_ylim(0.02, 0.13)

        elif metric == "score_10_to_1":
            ax.set_ylim(3.4, 10.2)

        elif metric == "attacked_accuracy":
            ax.set_ylim(0.00, 0.70)

    axes[0, 0].legend(loc="lower right", fontsize=9.2, frameon=True)

    fig.text(
        0.50,
        0.090,
        "Zoom view emphasizes the early-epsilon region where FGSM and PGD differences are easier to see.",
        ha="center",
        va="center",
        fontsize=9.4,
    )

    fig.text(
        0.50,
        0.050,
        "Window-level processed-tensor adversarial stress test only; not clinical, physical-layer, SDR, or over-the-air validation.",
        ha="center",
        va="center",
        fontsize=8.6,
    )

    fig.savefig(ZOOM_FIGURE_PATH, dpi=300, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)


def summarize_findings(rows: list[dict[str, Any]]) -> dict[str, Any]:
    fgsm_collapse = first_epsilon_at_or_above(rows, "FGSM", "missed_fall_rate_fnr", 1.0)
    pgd_collapse = first_epsilon_at_or_above(rows, "PGD", "missed_fall_rate_fnr", 1.0)

    fgsm_90 = first_epsilon_at_or_above(rows, "FGSM", "missed_fall_rate_fnr", 0.90)
    pgd_90 = first_epsilon_at_or_above(rows, "PGD", "missed_fall_rate_fnr", 0.90)

    fgsm_acc_below_10 = first_epsilon_at_or_below(rows, "FGSM", "attacked_accuracy", 0.10)
    pgd_acc_below_10 = first_epsilon_at_or_below(rows, "PGD", "attacked_accuracy", 0.10)

    monotonic = {}
    for attack_type in ["FGSM", "PGD"]:
        attack_rows = [row for row in rows if row["attack_type"] == attack_type]
        attack_rows.sort(key=lambda row: row["epsilon"])

        monotonic[attack_type] = {
            "fnr_non_decreasing": monotonic_non_decreasing(
                [row["missed_fall_rate_fnr"] for row in attack_rows]
            ),
            "score10_non_decreasing": monotonic_non_decreasing(
                [row["score_10_to_1"] for row in attack_rows]
            ),
            "accuracy_non_increasing": monotonic_non_increasing(
                [row["attacked_accuracy"] for row in attack_rows]
            ),
        }

    return {
        "fgsm_fnr_90_epsilon": fgsm_90,
        "pgd_fnr_90_epsilon": pgd_90,
        "fgsm_fnr_100_epsilon": fgsm_collapse,
        "pgd_fnr_100_epsilon": pgd_collapse,
        "fgsm_accuracy_below_10_percent_epsilon": fgsm_acc_below_10,
        "pgd_accuracy_below_10_percent_epsilon": pgd_acc_below_10,
        "monotonic": monotonic,
    }


def make_markdown_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Attack | Epsilon | Accuracy | FNR | FPR | Score 10:1 | TP | FN | FP | TN |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            f"| {row['attack_type']} | {row['epsilon']:.4f} | "
            f"{row['attacked_accuracy']:.3f} | "
            f"{row['missed_fall_rate_fnr']:.3f} | "
            f"{row['false_positive_rate_fpr']:.3f} | "
            f"{row['safety_priority_score_10_to_1']:.3f} | "
            f"{row['tp']} | {row['fn']} | {row['fp']} | {row['tn']} |"
        )

    return "\n".join(lines)


def write_note(rows: list[dict[str, Any]], findings: dict[str, Any]) -> None:
    def fmt_eps(value: float | None) -> str:
        return "not reached" if value is None else f"{value:.4f}"

    fgsm_mono = findings["monotonic"]["FGSM"]
    pgd_mono = findings["monotonic"]["PGD"]

    note = f"""# Thesis Table 27 and Figure 27: Attack-Severity Dose Response of Fall-Safety Metrics

## Purpose

Table 27, Figure 27A, and Figure 27B ask:

```text
Does fall-safety degradation increase systematically as adversarial attack strength increases?
```

This directly addresses the concern that a single selected epsilon value could be cherry-picked.

## Files Created

**Table 27**  
`{TABLE_PATH}`

**Figure 27A**  
`{FIGURE_PATH}`

**Figure 27B**  
`{ZOOM_FIGURE_PATH}`

**Companion note**  
`{NOTE_PATH}`

## Input

`{SWEEP_SUMMARY_PATH}`

The input summary was generated by:

```text
scripts/export_attack_prediction_sweep_18eps.py
```

## Epsilon Sweep

The sweep contains 18 epsilon values for FGSM and PGD, giving 36 attack-condition rows total.

## Key Findings

- PGD reaches missed-fall rate FNR = 1.000 at epsilon = {fmt_eps(findings['pgd_fnr_100_epsilon'])}.
- FGSM reaches missed-fall rate FNR = 1.000 at epsilon = {fmt_eps(findings['fgsm_fnr_100_epsilon'])}.
- PGD reaches FNR >= 0.90 at epsilon = {fmt_eps(findings['pgd_fnr_90_epsilon'])}.
- FGSM reaches FNR >= 0.90 at epsilon = {fmt_eps(findings['fgsm_fnr_90_epsilon'])}.
- PGD attacked accuracy drops below 10% at epsilon = {fmt_eps(findings['pgd_accuracy_below_10_percent_epsilon'])}.
- FGSM attacked accuracy drops below 10% at epsilon = {fmt_eps(findings['fgsm_accuracy_below_10_percent_epsilon'])}.

## Monotonicity Checks

- FGSM FNR non-decreasing across epsilon: `{fgsm_mono['fnr_non_decreasing']}`
- PGD FNR non-decreasing across epsilon: `{pgd_mono['fnr_non_decreasing']}`
- FGSM safety score 10:1 non-decreasing across epsilon: `{fgsm_mono['score10_non_decreasing']}`
- PGD safety score 10:1 non-decreasing across epsilon: `{pgd_mono['score10_non_decreasing']}`
- FGSM attacked accuracy non-increasing across epsilon: `{fgsm_mono['accuracy_non_increasing']}`
- PGD attacked accuracy non-increasing across epsilon: `{pgd_mono['accuracy_non_increasing']}`

## Table Summary

{make_markdown_table(rows)}

## Interpretation

The expanded sweep shows a clear attack-severity dose response. As epsilon increases, missed-fall rate rises sharply, safety-priority score increases, and attacked accuracy decreases. The Figure 27A shows the overall dose-response pattern, while the Figure 27B focuses on the early-epsilon region where FGSM and PGD are visually close and easier to compare.

This makes the adversarial robustness result stronger than the earlier single-point epsilon = 0.03 analysis because it shows that the degradation is systematic across attack strength.

## Claim Boundary

This is a window-level software adversarial stress test on processed UT-HAR / SenseFi CSI tensors.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, event-level fall validation, long-lie validation, time-to-alarm validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
"""

    NOTE_PATH.write_text(note, encoding="utf-8")


def replace_or_append_readme_section(text: str, section_marker: str, section: str) -> str:
    if section_marker not in text:
        return text.rstrip() + "\n\n" + section.lstrip()

    start = text.find(section_marker)
    before = text[:start].rstrip()

    next_heading = text.find("\n### ", start + len(section_marker))
    if next_heading == -1:
        after = ""
    else:
        after = text[next_heading:].lstrip()

    if after:
        return before + "\n\n" + section.lstrip().rstrip() + "\n\n" + after

    return before + "\n\n" + section.lstrip().rstrip() + "\n"


def update_readme(findings: dict[str, Any]) -> None:
    def fmt_eps(value: float | None) -> str:
        return "not reached" if value is None else f"{value:.4f}"

    section_marker = "### Thesis Table 27 and Figure 27: Attack-Severity Dose Response"

    section = f"""
{section_marker}

Table 27, Figure 27A, and Figure 27B add an expanded attack-severity dose-response analysis using the 18-epsilon FGSM/PGD prediction sweep.

**Files**

- `results/thesis_table_27_attack_severity_dose_response.csv`
- `figures/thesis_figure_27a_attack_severity_dose_response.png`
- `figures/thesis_figure_27b_attack_severity_dose_response_zoom.png`
- `notes/thesis_table_27_figure_27_attack_severity_dose_response.md`

**Input**

- `results/epsilon_sweep_predictions/attack_prediction_sweep_18eps_summary.csv`

**Question**

```text
Does fall-safety degradation increase systematically as adversarial attack strength increases?
```

**Main findings**

- PGD reaches FNR = 1.000 at epsilon = {fmt_eps(findings['pgd_fnr_100_epsilon'])}.
- FGSM reaches FNR = 1.000 at epsilon = {fmt_eps(findings['fgsm_fnr_100_epsilon'])}.
- The expanded sweep shows a systematic dose response: missed-fall rate and safety-priority score increase as epsilon increases, while attacked accuracy decreases.

**Interpretation**

This strengthens the thesis result beyond a single epsilon point. The fall-safety degradation is not only observed at epsilon = 0.03; it appears systematically across attack strength in the current processed-tensor stress test. The companion Figure 27B helps reveal the early-epsilon FGSM-vs-PGD differences more clearly.

**Claim boundary**

This is a window-level software adversarial stress test on processed UT-HAR / SenseFi CSI tensors. It is not clinical validation, event-level fall validation, physical-layer validation, packet-level validation, SDR validation, or over-the-air validation.
"""

    old_text = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
    new_text = replace_or_append_readme_section(old_text, section_marker, section)
    README_PATH.write_text(new_text, encoding="utf-8")

    if section_marker in old_text:
        print("README Table 27 / Figure 27 section replaced.")
    else:
        print("README updated with Table 27 / Figure 27 section.")


def main() -> None:
    print("Creating Thesis Table 27 and Figure 27...")
    print(f"Reading sweep summary: {SWEEP_SUMMARY_PATH}")

    rows = load_sweep_rows()
    table_rows = build_table_rows(rows)
    write_table(table_rows)

    findings = summarize_findings(rows)

    fgsm_collapse, pgd_collapse = create_main_figure(rows)
    create_zoom_figure(rows)
    write_note(table_rows, findings)
    update_readme(findings)

    print("\nCreated outputs:")
    print(f"- {TABLE_PATH}")
    print(f"- {FIGURE_PATH}")
    print(f"- {ZOOM_FIGURE_PATH}")
    print(f"- {NOTE_PATH}")
    print("- README.md updated")

    print("\nKey findings:")
    if pgd_collapse is not None:
        print(f"- PGD reaches FNR=1.000 at epsilon={pgd_collapse:.4f}")
    if fgsm_collapse is not None:
        print(f"- FGSM reaches FNR=1.000 at epsilon={fgsm_collapse:.4f}")
    print(f"- PGD reaches FNR>=0.90 at epsilon={findings['pgd_fnr_90_epsilon']:.4f}")
    print(f"- FGSM reaches FNR>=0.90 at epsilon={findings['fgsm_fnr_90_epsilon']:.4f}")
    print(f"- PGD accuracy drops below 10% at epsilon={findings['pgd_accuracy_below_10_percent_epsilon']:.4f}")
    print(f"- FGSM accuracy drops below 10% at epsilon={findings['fgsm_accuracy_below_10_percent_epsilon']:.4f}")

    print("\nMonotonicity checks:")
    for attack_type in ["FGSM", "PGD"]:
        m = findings["monotonic"][attack_type]
        print(
            f"- {attack_type}: "
            f"FNR non-decreasing={m['fnr_non_decreasing']}, "
            f"score10 non-decreasing={m['score10_non_decreasing']}, "
            f"accuracy non-increasing={m['accuracy_non_increasing']}"
        )


if __name__ == "__main__":
    main()
