from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


# =============================================================================
# Paths
# =============================================================================

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_DIR = SCRIPT_PATH.parent.parent

README_PATH = PROJECT_DIR / "README.md"
RESULTS_DIR = PROJECT_DIR / "results"
FIGURES_DIR = PROJECT_DIR / "figures"
NOTES_DIR = PROJECT_DIR / "notes"

TABLE_PATH = RESULTS_DIR / "thesis_table_24_defense_recovery_residual_gap.csv"
FIGURE_PATH = FIGURES_DIR / "thesis_figure_24_defense_recovery_residual_gap.png"
NOTE_PATH = NOTES_DIR / "thesis_table_24_figure_24_defense_recovery_residual_gap.md"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Exact project input mapping
# =============================================================================

# Binary meaning:
#   fall_true_binary = 1 means true fall window
#   selected prediction binary = 1 means predicted fall window
#   selected prediction binary = 0 means predicted non-fall window
#
# IMPORTANT:
# The FGSM file contains both clean and attacked prediction columns.
# This script intentionally uses attacked_fall_pred_binary for the FGSM attack
# condition, not clean_fall_pred_binary.

CONDITIONS = [
    {
        "condition": "Clean baseline",
        "condition_id": "clean",
        "input_file": RESULTS_DIR / "clean_predictions_short.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary",
        "prediction_source": "clean baseline prediction",
    },
    {
        "condition": "FGSM attack",
        "condition_id": "fgsm_attack",
        "input_file": RESULTS_DIR / "fgsm_predictions_short_epsilon_0_03.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "attacked_fall_pred_binary",
        "prediction_source": "FGSM attacked prediction column",
    },
    {
        "condition": "PGD attack",
        "condition_id": "pgd_attack",
        "input_file": RESULTS_DIR / "pgd_predictions_short_epsilon_0_03.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary",
        "prediction_source": "PGD attacked prediction column",
    },
    {
        "condition": "Defended FGSM",
        "condition_id": "defended_fgsm",
        "input_file": RESULTS_DIR / "defended_fgsm_predictions_short_epsilon_0_03.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary_fgsm_defended",
        "prediction_source": "defended FGSM prediction column",
    },
    {
        "condition": "Defended PGD",
        "condition_id": "defended_pgd",
        "input_file": RESULTS_DIR / "defended_pgd_predictions_short_epsilon_0_03.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary_pgd_defended",
        "prediction_source": "defended PGD prediction column",
    },
    {
        "condition": "Defended clean",
        "condition_id": "defended_clean",
        "input_file": RESULTS_DIR / "defended_predictions_short.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary_clean_defended",
        "prediction_source": "defended clean prediction column",
    },
]

RECOVERY_PAIRS = [
    {
        "attack_name": "FGSM",
        "attack_condition": "FGSM attack",
        "defended_condition": "Defended FGSM",
    },
    {
        "attack_name": "PGD",
        "attack_condition": "PGD attack",
        "defended_condition": "Defended PGD",
    },
]

PRIORITY_SCENARIOS = [
    {
        "scenario_id": "equal_1_to_1",
        "scenario_label": "1:1",
        "scenario_description": "Equal missed-fall and false-alert weighting",
        "fn_weight": 1.0,
        "fp_weight": 1.0,
    },
    {
        "scenario_id": "mild_fn_2_to_1",
        "scenario_label": "2:1",
        "scenario_description": "Missed-fall errors weighted 2x higher than false-alert errors",
        "fn_weight": 2.0,
        "fp_weight": 1.0,
    },
    {
        "scenario_id": "strong_fn_5_to_1",
        "scenario_label": "5:1",
        "scenario_description": "Missed-fall errors weighted 5x higher than false-alert errors",
        "fn_weight": 5.0,
        "fp_weight": 1.0,
    },
    {
        "scenario_id": "very_strong_fn_10_to_1",
        "scenario_label": "10:1",
        "scenario_description": "Missed-fall errors weighted 10x higher than false-alert errors",
        "fn_weight": 10.0,
        "fp_weight": 1.0,
    },
]


# =============================================================================
# Utility functions
# =============================================================================

def to_int(value: Any) -> int:
    return int(float(str(value).strip()))


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return math.nan
    return numerator / denominator


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input file: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require_columns(rows: list[dict[str, str]], path: Path, columns: list[str]) -> None:
    if not rows:
        raise ValueError(f"No rows found in input file: {path}")

    available = set(rows[0].keys())
    missing = [column for column in columns if column not in available]

    if missing:
        raise ValueError(
            f"Missing required columns in {path}: {missing}\n"
            f"Available columns: {sorted(available)}"
        )


def compute_confusion_for_condition(condition: dict[str, Any]) -> dict[str, Any]:
    path = condition["input_file"]
    rows = read_rows(path)

    required_columns = [
        condition["true_binary_col"],
        condition["pred_binary_col"],
    ]
    require_columns(rows, path, required_columns)

    tp = fn = fp = tn = 0

    for row in rows:
        true_binary = to_int(row[condition["true_binary_col"]])
        pred_binary = to_int(row[condition["pred_binary_col"]])

        if true_binary not in (0, 1) or pred_binary not in (0, 1):
            raise ValueError(
                "Expected binary true/pred values in "
                f"{path}: true={true_binary}, pred={pred_binary}"
            )

        if true_binary == 1 and pred_binary == 1:
            tp += 1
        elif true_binary == 1 and pred_binary == 0:
            fn += 1
        elif true_binary == 0 and pred_binary == 1:
            fp += 1
        elif true_binary == 0 and pred_binary == 0:
            tn += 1

    total_fall = tp + fn
    total_nonfall = fp + tn
    total = tp + fn + fp + tn

    if total_fall == 0:
        raise ValueError(f"No true fall windows found for {condition['condition']}")
    if total_nonfall == 0:
        raise ValueError(f"No true non-fall windows found for {condition['condition']}")

    fnr = safe_divide(fn, total_fall)
    fpr = safe_divide(fp, total_nonfall)

    return {
        "condition": condition["condition"],
        "condition_id": condition["condition_id"],
        "input_file": str(path),
        "true_binary_col": condition["true_binary_col"],
        "pred_binary_col": condition["pred_binary_col"],
        "prediction_source": condition["prediction_source"],
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "total_fall_windows": total_fall,
        "total_nonfall_windows": total_nonfall,
        "total_windows": total,
        "missed_fall_rate_fnr": fnr,
        "false_positive_rate_fpr": fpr,
    }


def compute_condition_metrics() -> dict[str, dict[str, Any]]:
    return {
        condition["condition"]: compute_confusion_for_condition(condition)
        for condition in CONDITIONS
    }


def safety_priority_score(metrics: dict[str, Any], fn_weight: float, fp_weight: float) -> float:
    return (
        fn_weight * metrics["missed_fall_rate_fnr"]
        + fp_weight * metrics["false_positive_rate_fpr"]
    )


def recovery_status(recovery_fraction: float, residual_gap: float) -> str:
    if math.isnan(recovery_fraction):
        return "undefined"
    if recovery_fraction < 0:
        return "defense worsened score"
    if recovery_fraction == 0:
        return "no recovery"
    if recovery_fraction < 0.25:
        return "limited recovery"
    if recovery_fraction < 0.75:
        return "partial recovery"
    if residual_gap > 0:
        return "large recovery but residual gap remains"
    return "full or better-than-clean recovery"


# =============================================================================
# Table 24 computation
# =============================================================================

def build_table_rows(condition_metrics: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    clean = condition_metrics["Clean baseline"]
    defended_clean = condition_metrics["Defended clean"]

    rows = []

    for scenario in PRIORITY_SCENARIOS:
        fn_weight = scenario["fn_weight"]
        fp_weight = scenario["fp_weight"]

        clean_score = safety_priority_score(clean, fn_weight, fp_weight)
        defended_clean_score = safety_priority_score(defended_clean, fn_weight, fp_weight)
        defended_clean_gap_to_clean = defended_clean_score - clean_score

        for pair in RECOVERY_PAIRS:
            attack = condition_metrics[pair["attack_condition"]]
            defended = condition_metrics[pair["defended_condition"]]

            attack_score = safety_priority_score(attack, fn_weight, fp_weight)
            defended_score = safety_priority_score(defended, fn_weight, fp_weight)

            attack_gap_to_clean = attack_score - clean_score
            defended_gap_to_clean = defended_score - clean_score
            score_reduction_by_defense = attack_score - defended_score

            if abs(attack_gap_to_clean) < 1e-12:
                recovery_fraction = math.nan
                residual_gap_fraction = math.nan
            else:
                recovery_fraction = score_reduction_by_defense / attack_gap_to_clean
                residual_gap_fraction = defended_gap_to_clean / attack_gap_to_clean

            row = {
                "attack_name": pair["attack_name"],
                "scenario_id": scenario["scenario_id"],
                "scenario_label": scenario["scenario_label"],
                "scenario_description": scenario["scenario_description"],
                "fn_weight": fn_weight,
                "fp_weight": fp_weight,
                "clean_score": clean_score,
                "attack_score": attack_score,
                "defended_attack_score": defended_score,
                "attack_gap_to_clean": attack_gap_to_clean,
                "defended_gap_to_clean": defended_gap_to_clean,
                "score_reduction_by_defense": score_reduction_by_defense,
                "recovery_fraction": recovery_fraction,
                "recovery_percent": recovery_fraction * 100 if not math.isnan(recovery_fraction) else math.nan,
                "residual_gap_fraction": residual_gap_fraction,
                "residual_gap_percent": residual_gap_fraction * 100 if not math.isnan(residual_gap_fraction) else math.nan,
                "clean_fnr": clean["missed_fall_rate_fnr"],
                "clean_fpr": clean["false_positive_rate_fpr"],
                "attack_fnr": attack["missed_fall_rate_fnr"],
                "attack_fpr": attack["false_positive_rate_fpr"],
                "defended_attack_fnr": defended["missed_fall_rate_fnr"],
                "defended_attack_fpr": defended["false_positive_rate_fpr"],
                "delta_fnr_defended_minus_attack": defended["missed_fall_rate_fnr"] - attack["missed_fall_rate_fnr"],
                "delta_fpr_defended_minus_attack": defended["false_positive_rate_fpr"] - attack["false_positive_rate_fpr"],
                "defended_clean_score": defended_clean_score,
                "defended_clean_gap_to_clean": defended_clean_gap_to_clean,
                "interpretation": "",
            }

            row["interpretation"] = (
                f"{pair['attack_name']} defense recovered {row['recovery_percent']:.1f}% "
                f"of the attack-induced safety-priority gap, leaving "
                f"{row['residual_gap_percent']:.1f}% residual gap to clean baseline."
            )

            row["recovery_status"] = recovery_status(
                row["recovery_fraction"],
                row["defended_gap_to_clean"],
            )

            rows.append(row)

    return rows


def format_float(value: Any, digits: int = 6) -> str:
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.{digits}f}"
    return str(value)


def write_table(rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "attack_name",
        "scenario_id",
        "scenario_label",
        "scenario_description",
        "fn_weight",
        "fp_weight",
        "clean_score",
        "attack_score",
        "defended_attack_score",
        "attack_gap_to_clean",
        "defended_gap_to_clean",
        "score_reduction_by_defense",
        "recovery_fraction",
        "recovery_percent",
        "residual_gap_fraction",
        "residual_gap_percent",
        "clean_fnr",
        "clean_fpr",
        "attack_fnr",
        "attack_fpr",
        "defended_attack_fnr",
        "defended_attack_fpr",
        "delta_fnr_defended_minus_attack",
        "delta_fpr_defended_minus_attack",
        "defended_clean_score",
        "defended_clean_gap_to_clean",
        "recovery_status",
        "interpretation",
    ]

    with TABLE_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            output_row = {
                key: format_float(row[key])
                for key in fieldnames
            }
            writer.writerow(output_row)


# =============================================================================
# Figure 24
# =============================================================================

def create_figure(rows: list[dict[str, Any]]) -> None:
    # Stacked 100% bar chart:
    # recovered gap + residual gap = 100% of the original attack-induced gap.
    # Layout fixes:
    # - title and legend are separate
    # - recovered labels are above tiny green segments, not squeezed inside
    # - residual labels are centered inside red segments
    # - group labels and notes have dedicated vertical space
    scenario_order = [scenario["scenario_id"] for scenario in PRIORITY_SCENARIOS]

    ordered_rows = []
    for attack_name in ["FGSM", "PGD"]:
        for scenario_id in scenario_order:
            row = next(
                item for item in rows
                if item["attack_name"] == attack_name and item["scenario_id"] == scenario_id
            )
            ordered_rows.append(row)

    x = np.array([0, 1, 2, 3, 5, 6, 7, 8], dtype=float)
    recovered = np.array([max(0.0, row["recovery_percent"]) for row in ordered_rows])
    residual = np.array([max(0.0, row["residual_gap_percent"]) for row in ordered_rows])
    labels = [row["scenario_label"] for row in ordered_rows]

    fig = plt.figure(figsize=(15.5, 9.8), dpi=150)

    # Main plot axis. Top is kept lower to make room for title + legend.
    ax = fig.add_axes([0.095, 0.325, 0.84, 0.555])

    recovered_color = "#2E7D32"
    residual_color = "#B71C1C"

    bar_width = 0.72

    ax.bar(
        x,
        recovered,
        width=bar_width,
        color=recovered_color,
        edgecolor="white",
        linewidth=1.2,
        label="Recovered gap",
        zorder=3,
    )

    ax.bar(
        x,
        residual,
        bottom=recovered,
        width=bar_width,
        color=residual_color,
        edgecolor="white",
        linewidth=1.2,
        label="Residual gap to clean baseline",
        zorder=3,
    )

    ax.set_ylim(0, 108)
    ax.set_xlim(-0.75, 8.75)

    ax.set_ylabel(
        "Attack-induced safety gap share (%)",
        fontsize=12.8,
        fontweight="bold",
        labelpad=10,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11.8, fontweight="bold")

    ax.set_yticks(np.arange(0, 101, 20))
    ax.tick_params(axis="y", labelsize=10.8)
    ax.grid(axis="y", linestyle="--", linewidth=0.7, alpha=0.45, zorder=0)
    ax.set_axisbelow(True)

    # Group separator.
    ax.axvline(4.0, color="#4b5563", linewidth=1.0, linestyle=":")

    # Title and legend in figure coordinates so they never overlap.
    fig.suptitle(
        "Figure 24: Defense Recovery Fraction and Residual Safety Gap",
        fontsize=18.6,
        fontweight="bold",
        y=0.965,
    )

    legend_handles = [
        Patch(facecolor=recovered_color, label="Recovered gap"),
        Patch(facecolor=residual_color, label="Residual gap to clean baseline"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.925),
        ncol=2,
        frameon=False,
        fontsize=10.8,
    )

    # Bar annotations. Recovered labels are outside/above tiny green segments.
    for index, row in enumerate(ordered_rows):
        rec = max(0.0, row["recovery_percent"])
        res = max(0.0, row["residual_gap_percent"])
        xpos = x[index]

        # Residual label centered in red segment.
        ax.text(
            xpos,
            rec + res / 2.0,
            f"{res:.1f}%\nresidual",
            ha="center",
            va="center",
            fontsize=9.3,
            fontweight="bold",
            color="white",
        )

        # Recovered label above green segment with a white background for readability.
        ax.text(
            xpos,
            max(rec + 1.4, 3.0),
            f"{rec:.1f}% recovered",
            ha="center",
            va="bottom",
            fontsize=8.9,
            fontweight="bold",
            color="black",
            bbox=dict(
                facecolor="white",
                edgecolor="none",
                alpha=0.86,
                boxstyle="round,pad=0.16",
            ),
        )

    # Group labels under axis, safely separated from notes.
    ax.text(
        1.5,
        -0.135,
        "FGSM attack → Defended FGSM",
        ha="center",
        va="top",
        fontsize=11.0,
        fontweight="bold",
        transform=ax.get_xaxis_transform(),
    )

    ax.text(
        6.5,
        -0.135,
        "PGD attack → Defended PGD",
        ha="center",
        va="top",
        fontsize=11.0,
        fontweight="bold",
        transform=ax.get_xaxis_transform(),
    )

    # Compact explanatory notes with enough spacing.
    fig.text(
        0.50,
        0.145,
        (
            "Recovery fraction = (attack score − defended attack score) / "
            "(attack score − clean baseline score)."
        ),
        ha="center",
        va="center",
        fontsize=10.3,
        fontweight="bold",
    )

    fig.text(
        0.50,
        0.105,
        (
            "Residual gap = defended attack score − clean baseline score. "
            "Lower residual gap means closer recovery to clean-baseline behavior."
        ),
        ha="center",
        va="center",
        fontsize=9.4,
    )

    fig.text(
        0.50,
        0.080,
        (
            "FN:FP weighting: 1:1 = equal; 2:1, 5:1, 10:1 = "
            "missed-fall errors weighted 2×, 5×, and 10× higher than false alerts."
        ),
        ha="center",
        va="center",
        fontsize=8.9,
    )

    fig.text(
        0.50,
        0.045,
        (
            "Window-level descriptive analysis only; not event-level fall validation, "
            "clinical validation, or physical-layer validation."
        ),
        ha="center",
        va="center",
        fontsize=8.8,
    )

    fig.savefig(FIGURE_PATH, dpi=300, bbox_inches="tight", pad_inches=0.14)
    plt.close(fig)


# =============================================================================
# Notes and README
# =============================================================================

def summarize_key_findings(rows: list[dict[str, Any]]) -> str:
    lines = []

    for attack_name in ["FGSM", "PGD"]:
        attack_rows = [row for row in rows if row["attack_name"] == attack_name]

        first = next(row for row in attack_rows if row["scenario_id"] == "equal_1_to_1")
        last = next(row for row in attack_rows if row["scenario_id"] == "very_strong_fn_10_to_1")

        lines.append(
            f"- {attack_name}: recovery decreases from {first['recovery_percent']:.1f}% "
            f"under 1:1 weighting to {last['recovery_percent']:.1f}% under 10:1 weighting, "
            f"leaving {last['residual_gap_percent']:.1f}% residual gap under 10:1."
        )

    lines.append(
        "- The defense mostly reduces false-alert contribution, but it does not recover missed-fall behavior because defended attack FNR remains high."
    )

    return "\n".join(lines)


def write_note(rows: list[dict[str, Any]], condition_metrics: dict[str, dict[str, Any]]) -> None:
    key_findings = summarize_key_findings(rows)

    input_file_lines = []
    for condition in CONDITIONS:
        input_file_lines.append(
            f"- {condition['condition']}: `{condition['input_file']}` "
            f"using `{condition['pred_binary_col']}`"
        )
    input_files_text = "\n".join(input_file_lines)

    text = f"""# Thesis Table 24 and Figure 24: Defense Recovery Fraction and Residual Safety Gap

## Purpose

Table 24 and Figure 24 ask:

```text
How much of the attack-induced safety-priority degradation is recovered by the defended model, and how much gap remains relative to clean baseline?
```

This directly follows Table/Figure 23. Figure 23 shows the safety-priority score under missed-fall weighting. Figure 24 explains how much of the attack-induced gap is recovered by defense.

## Files Created

**Table 24**  
`{TABLE_PATH}`

**Figure 24**  
`{FIGURE_PATH}`

**Companion note**  
`{NOTE_PATH}`

## Input Files and Prediction Columns

{input_files_text}

The FGSM input file contains both clean and attacked prediction columns. This artifact intentionally uses `attacked_fall_pred_binary` for the FGSM attack condition.

## Metric Definitions

For each attack type and missed-fall-priority scenario:

```text
attack gap to clean =
attack score − clean baseline score

defended gap to clean =
defended attack score − clean baseline score

score reduction by defense =
attack score − defended attack score

recovery fraction =
(attack score − defended attack score) /
(attack score − clean baseline score)

residual gap fraction =
(defended attack score − clean baseline score) /
(attack score − clean baseline score)
```

A recovery fraction of 1.0 means full recovery to clean-baseline score. A recovery fraction near 0 means little recovery. A negative recovery fraction would mean the defense made the score worse than the attack.

## Key Findings

{key_findings}

## Interpretation

This artifact shows that the defended model recovers only a small fraction of the attack-induced safety-priority gap. The recovery fraction becomes smaller as missed-fall errors are given more weight because the defended attack conditions still miss all true fall windows in this tested configuration.

This result is important because it shows that reducing false-alert burden is not enough if missed-fall behavior remains unresolved.

## Claim Boundary

This is a descriptive window-level defense-recovery and residual-gap analysis using the current UT-HAR / SenseFi prediction outputs.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, patient deployment, clinical utility analysis, health-economic analysis, alarm-fatigue validation, event-level fall validation, long-lie validation, time-to-alarm validation, subject-level generalization validation, room-level generalization validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
"""

    NOTE_PATH.write_text(text, encoding="utf-8")


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


def update_readme() -> None:
    section_marker = "### Thesis Table 24 and Figure 24: Defense Recovery Fraction and Residual Safety Gap"

    section = f"""
{section_marker}

Table 24 and Figure 24 add a defense-recovery and residual-gap analysis.

**Files**

- `results/thesis_table_24_defense_recovery_residual_gap.csv`
- `figures/thesis_figure_24_defense_recovery_residual_gap.png`
- `notes/thesis_table_24_figure_24_defense_recovery_residual_gap.md`

**Purpose**

This artifact asks how much of the attack-induced safety-priority degradation is recovered by the defended model, and how much gap remains relative to clean baseline.

**Metric definitions**

```text
attack gap to clean =
attack score − clean baseline score

defended gap to clean =
defended attack score − clean baseline score

recovery fraction =
(attack score − defended attack score) /
(attack score − clean baseline score)

residual gap fraction =
(defended attack score − clean baseline score) /
(attack score − clean baseline score)
```

**Main interpretation**

The defended model recovers only a small fraction of the attack-induced safety-priority gap, especially as missed-fall errors receive stronger weighting. This indicates that reducing false-alert burden is not enough if missed-fall behavior remains unresolved.

**Claim boundary**

This is a descriptive window-level recovery and residual-gap analysis using current prediction outputs. It is not clinical validation, event-level fall validation, alarm-fatigue validation, time-to-alarm validation, health-economic analysis, or physical-layer / over-the-air validation.
"""

    old_text = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
    new_text = replace_or_append_readme_section(old_text, section_marker, section)
    README_PATH.write_text(new_text, encoding="utf-8")

    if section_marker in old_text:
        print("README Table 24 / Figure 24 section replaced.")
    else:
        print("README updated with Table 24 / Figure 24 section.")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    print("Creating Thesis Table 24 and Figure 24...")
    print("Using exact binary prediction columns for defense-recovery analysis.")

    condition_metrics = compute_condition_metrics()

    print("\nVerified input files and selected columns:")
    for condition_name, metrics in condition_metrics.items():
        print(f"- {condition_name}")
        print(f"  file: {metrics['input_file']}")
        print(f"  true_binary_col: {metrics['true_binary_col']}")
        print(f"  pred_binary_col: {metrics['pred_binary_col']}")
        print(f"  source: {metrics['prediction_source']}")
        print(
            f"  TP={metrics['tp']}, FN={metrics['fn']}, FP={metrics['fp']}, TN={metrics['tn']}, "
            f"FNR={metrics['missed_fall_rate_fnr']:.3f}, FPR={metrics['false_positive_rate_fpr']:.3f}"
        )

    rows = build_table_rows(condition_metrics)
    write_table(rows)
    create_figure(rows)
    write_note(rows, condition_metrics)
    update_readme()

    print("\nCreated outputs:")
    print(f"- {TABLE_PATH}")
    print(f"- {FIGURE_PATH}")
    print(f"- {NOTE_PATH}")
    print("- README.md updated")

    print("\nScenario summary:")
    print(summarize_key_findings(rows))


if __name__ == "__main__":
    main()
