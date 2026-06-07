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

TABLE_PATH = RESULTS_DIR / "thesis_table_23_safety_priority_sensitivity.csv"
FIGURE_PATH = FIGURES_DIR / "thesis_figure_23_safety_priority_sensitivity_heatmap.png"
NOTE_PATH = NOTES_DIR / "thesis_table_23_figure_23_safety_priority_sensitivity.md"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Exact project input mapping
# =============================================================================

# This script intentionally uses exact binary fall/non-fall columns from the
# current UT-HAR / SenseFi prediction outputs. This avoids the previous error
# where FGSM was accidentally computed from the clean prediction column inside
# the FGSM CSV.
#
# Binary meaning:
#   fall_true_binary = 1 means true fall window
#   selected prediction binary = 1 means predicted fall window
#   selected prediction binary = 0 means predicted non-fall window

CONDITIONS = [
    {
        "condition": "Clean baseline",
        "condition_id": "clean",
        "input_file": RESULTS_DIR / "clean_predictions_short.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary",
        "label_pred_col": "predicted_label",
        "prediction_source": "clean baseline prediction",
    },
    {
        "condition": "FGSM attack",
        "condition_id": "fgsm_attack",
        "input_file": RESULTS_DIR / "fgsm_predictions_short_epsilon_0_03.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "attacked_fall_pred_binary",
        "label_pred_col": "attacked_predicted_label",
        "prediction_source": "FGSM attacked prediction column",
    },
    {
        "condition": "PGD attack",
        "condition_id": "pgd_attack",
        "input_file": RESULTS_DIR / "pgd_predictions_short_epsilon_0_03.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary",
        "label_pred_col": "predicted_label",
        "prediction_source": "PGD attacked prediction column",
    },
    {
        "condition": "Defended clean",
        "condition_id": "defended_clean",
        "input_file": RESULTS_DIR / "defended_predictions_short.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary_clean_defended",
        "label_pred_col": "defended_clean_predicted_label",
        "prediction_source": "defended clean prediction column",
    },
    {
        "condition": "Defended FGSM",
        "condition_id": "defended_fgsm",
        "input_file": RESULTS_DIR / "defended_fgsm_predictions_short_epsilon_0_03.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary_fgsm_defended",
        "label_pred_col": "defended_fgsm_predicted_label",
        "prediction_source": "defended FGSM prediction column",
    },
    {
        "condition": "Defended PGD",
        "condition_id": "defended_pgd",
        "input_file": RESULTS_DIR / "defended_pgd_predictions_short_epsilon_0_03.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary_pgd_defended",
        "label_pred_col": "defended_pgd_predicted_label",
        "prediction_source": "defended PGD prediction column",
    },
]

PRIORITY_SCENARIOS = [
    {
        "scenario_id": "equal_1_to_1",
        "scenario_label": "Equal\n1:1",
        "scenario_description": "Equal missed-fall and false-alert weighting",
        "fn_weight": 1.0,
        "fp_weight": 1.0,
    },
    {
        "scenario_id": "mild_fn_2_to_1",
        "scenario_label": "Mild\n2:1",
        "scenario_description": "Missed-fall errors weighted 2x higher than false-alert errors",
        "fn_weight": 2.0,
        "fp_weight": 1.0,
    },
    {
        "scenario_id": "strong_fn_5_to_1",
        "scenario_label": "Strong\n5:1",
        "scenario_description": "Missed-fall errors weighted 5x higher than false-alert errors",
        "fn_weight": 5.0,
        "fp_weight": 1.0,
    },
    {
        "scenario_id": "very_strong_fn_10_to_1",
        "scenario_label": "Very strong\n10:1",
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
        condition["label_pred_col"],
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
        "label_pred_col": condition["label_pred_col"],
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


def compute_condition_metrics() -> list[dict[str, Any]]:
    return [compute_confusion_for_condition(condition) for condition in CONDITIONS]


# =============================================================================
# Sensitivity analysis
# =============================================================================

def rank_rows_with_ties(rows: list[dict[str, Any]]) -> None:
    """Competition ranking with ties.

    Example:
    scores: 0.1, 0.1, 0.3, 0.5
    ranks:  1,   1,   3,   4
    """
    condition_order = [condition["condition"] for condition in CONDITIONS]

    sorted_rows = sorted(
        rows,
        key=lambda row: (
            row["normalized_safety_priority_score"],
            condition_order.index(row["condition"]),
        ),
    )

    tolerance = 1e-12
    previous_score = None
    previous_rank = None

    for position, row in enumerate(sorted_rows, start=1):
        score = row["normalized_safety_priority_score"]

        if previous_score is not None and abs(score - previous_score) <= tolerance:
            row["rank_lower_is_better"] = previous_rank
        else:
            row["rank_lower_is_better"] = position
            previous_rank = position
            previous_score = score

    for row in rows:
        score = row["normalized_safety_priority_score"]
        row["tie_count_at_score"] = sum(
            1
            for other in rows
            if abs(other["normalized_safety_priority_score"] - score) <= tolerance
        )


def build_table_rows(condition_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    all_rows = []

    for scenario in PRIORITY_SCENARIOS:
        scenario_rows = []

        for metrics in condition_metrics:
            fn_weight = scenario["fn_weight"]
            fp_weight = scenario["fp_weight"]

            raw_score = fn_weight * metrics["fn"] + fp_weight * metrics["fp"]
            normalized_score = (
                fn_weight * metrics["missed_fall_rate_fnr"]
                + fp_weight * metrics["false_positive_rate_fpr"]
            )

            row = {
                "condition": metrics["condition"],
                "condition_id": metrics["condition_id"],
                "scenario_id": scenario["scenario_id"],
                "scenario_description": scenario["scenario_description"],
                "fn_weight": fn_weight,
                "fp_weight": fp_weight,
                "tp": metrics["tp"],
                "fn": metrics["fn"],
                "fp": metrics["fp"],
                "tn": metrics["tn"],
                "total_fall_windows": metrics["total_fall_windows"],
                "total_nonfall_windows": metrics["total_nonfall_windows"],
                "total_windows": metrics["total_windows"],
                "missed_fall_rate_fnr": metrics["missed_fall_rate_fnr"],
                "false_positive_rate_fpr": metrics["false_positive_rate_fpr"],
                "raw_weighted_score": raw_score,
                "normalized_safety_priority_score": normalized_score,
                "rank_lower_is_better": None,
                "tie_count_at_score": None,
                "rank_change_vs_equal_priority": None,
                "input_file": metrics["input_file"],
                "true_binary_col": metrics["true_binary_col"],
                "pred_binary_col": metrics["pred_binary_col"],
                "label_pred_col": metrics["label_pred_col"],
                "prediction_source": metrics["prediction_source"],
                "interpretation": "",
            }
            scenario_rows.append(row)

        rank_rows_with_ties(scenario_rows)
        all_rows.extend(scenario_rows)

    equal_ranks = {
        row["condition"]: row["rank_lower_is_better"]
        for row in all_rows
        if row["scenario_id"] == "equal_1_to_1"
    }

    for row in all_rows:
        row["rank_change_vs_equal_priority"] = (
            row["rank_lower_is_better"] - equal_ranks[row["condition"]]
        )

        tie_text = " tied score" if row["tie_count_at_score"] > 1 else ""
        row["interpretation"] = (
            f"Window-level score = {row['normalized_safety_priority_score']:.3f}; "
            f"rank {row['rank_lower_is_better']} of {len(CONDITIONS)}{tie_text} "
            "(lower is better)."
        )

    scenario_order = [scenario["scenario_id"] for scenario in PRIORITY_SCENARIOS]
    condition_order = [condition["condition"] for condition in CONDITIONS]

    return sorted(
        all_rows,
        key=lambda row: (
            scenario_order.index(row["scenario_id"]),
            condition_order.index(row["condition"]),
        ),
    )


def write_table(rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "condition",
        "condition_id",
        "scenario_id",
        "scenario_description",
        "fn_weight",
        "fp_weight",
        "tp",
        "fn",
        "fp",
        "tn",
        "total_fall_windows",
        "total_nonfall_windows",
        "total_windows",
        "missed_fall_rate_fnr",
        "false_positive_rate_fpr",
        "raw_weighted_score",
        "normalized_safety_priority_score",
        "rank_lower_is_better",
        "tie_count_at_score",
        "rank_change_vs_equal_priority",
        "interpretation",
        "input_file",
        "true_binary_col",
        "pred_binary_col",
        "label_pred_col",
        "prediction_source",
    ]

    with TABLE_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            output_row = row.copy()
            for key in [
                "missed_fall_rate_fnr",
                "false_positive_rate_fpr",
                "raw_weighted_score",
                "normalized_safety_priority_score",
            ]:
                output_row[key] = f"{float(output_row[key]):.6f}"
            writer.writerow(output_row)


# =============================================================================
# Figure
# =============================================================================

def build_matrices(
    rows: list[dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], list[str]]:
    condition_labels = [condition["condition"] for condition in CONDITIONS]
    scenario_ids = [scenario["scenario_id"] for scenario in PRIORITY_SCENARIOS]
    scenario_labels = [scenario["scenario_label"] for scenario in PRIORITY_SCENARIOS]

    score_matrix = np.full((len(condition_labels), len(scenario_ids)), np.nan)
    rank_matrix = np.full((len(condition_labels), len(scenario_ids)), np.nan)
    tie_matrix = np.full((len(condition_labels), len(scenario_ids)), 1.0)

    lookup = {
        (row["condition"], row["scenario_id"]): row
        for row in rows
    }

    for i, condition_label in enumerate(condition_labels):
        for j, scenario_id in enumerate(scenario_ids):
            row = lookup[(condition_label, scenario_id)]
            score_matrix[i, j] = float(row["normalized_safety_priority_score"])
            rank_matrix[i, j] = float(row["rank_lower_is_better"])
            tie_matrix[i, j] = float(row["tie_count_at_score"])

    return score_matrix, rank_matrix, tie_matrix, condition_labels, scenario_labels


def create_figure(rows: list[dict[str, Any]]) -> None:
    score_matrix, rank_matrix, tie_matrix, condition_labels, _scenario_labels = build_matrices(rows)

    # Manual layout is used to avoid the x-label and explanatory notes overlapping.
    # The heatmap is wide enough for 4 columns and not vertically stretched.
    fig = plt.figure(figsize=(15.8, 9.2), dpi=150)

    # Main heatmap axis: [left, bottom, width, height]
    ax = fig.add_axes([0.18, 0.33, 0.64, 0.50])

    max_value = np.nanmax(score_matrix)
    if not np.isfinite(max_value) or max_value <= 0:
        max_value = 1.0

    image = ax.imshow(
        score_matrix,
        aspect="auto",
        cmap="YlOrRd",
        vmin=0,
        vmax=max_value,
    )

    scenario_labels_for_plot = [
        "Equal\n1:1",
        "Mild\n2:1",
        "Strong\n5:1",
        "Very strong\n10:1",
    ]

    ax.set_xticks(np.arange(len(scenario_labels_for_plot)))
    ax.set_yticks(np.arange(len(condition_labels)))

    ax.set_xticklabels(scenario_labels_for_plot, fontsize=12.0, fontweight="bold")
    ax.set_yticklabels(condition_labels, fontsize=12.4, fontweight="bold")

    ax.set_title(
        "Figure 23: Missed-Fall-Priority Sensitivity Analysis",
        fontsize=17.2,
        fontweight="bold",
        pad=14,
    )

    ax.set_ylabel(
        "Model condition",
        fontsize=12.0,
        labelpad=12,
    )

    # Cell annotations.
    for i in range(score_matrix.shape[0]):
        for j in range(score_matrix.shape[1]):
            value = score_matrix[i, j]
            rank = int(rank_matrix[i, j])
            tie_count = int(tie_matrix[i, j])
            text_color = "white" if value > max_value * 0.58 else "black"
            rank_text = f"tie rank {rank}" if tie_count > 1 else f"rank {rank}"

            ax.text(
                j,
                i,
                f"{value:.3f}\n{rank_text}",
                ha="center",
                va="center",
                fontsize=10.0,
                fontweight="bold",
                color=text_color,
            )

    # Grid lines.
    ax.set_xticks(np.arange(-0.5, len(scenario_labels_for_plot), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(condition_labels), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.8)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Colorbar with its own axis for clean spacing.
    cax = fig.add_axes([0.845, 0.33, 0.022, 0.50])
    colorbar = fig.colorbar(image, cax=cax)
    colorbar.set_label(
        "Safety-priority score\nlower is better",
        fontsize=10.5,
        fontweight="bold",
    )
    colorbar.ax.tick_params(labelsize=10.4)

    # Explanatory notes, separated and compact.
    fig.text(
        0.50,
        0.250,
        "Scenario assumption: FN:FP weighting, where FN = missed fall and FP = false alert.",
        ha="center",
        va="center",
        fontsize=11.0,
        fontweight="bold",
    )

    fig.text(
        0.50,
        0.215,
        (
            "1:1 = missed-fall and false-alert errors weighted equally; "
            "2:1 = missed-fall errors weighted 2× higher."
        ),
        ha="center",
        va="center",
        fontsize=9.5,
    )

    fig.text(
        0.50,
        0.185,
        (
            "5:1 = missed-fall errors weighted 5× higher; "
            "10:1 = missed-fall errors weighted 10× higher."
        ),
        ha="center",
        va="center",
        fontsize=9.5,
    )

    fig.text(
        0.50,
        0.140,
        "Score = FN weight × FNR + FP weight × FPR.",
        ha="center",
        va="center",
        fontsize=10.8,
        fontweight="bold",
    )

    fig.text(
        0.50,
        0.112,
        "FNR = missed-fall rate; FPR = false-positive rate.",
        ha="center",
        va="center",
        fontsize=10.2,
        fontweight="bold",
    )

    fig.text(
        0.50,
        0.080,
        "Ranks are descriptive within-column orderings across the six conditions; lower score is better.",
        ha="center",
        va="center",
        fontsize=9.8,
        fontweight="bold",
    )

    fig.text(
        0.50,
        0.040,
        (
            "Weights are scenario assumptions, not clinical cost constants. "
            "Window-level descriptive analysis only; not event-level or clinical validation."
        ),
        ha="center",
        va="center",
        fontsize=8.8,
    )

    fig.savefig(FIGURE_PATH, dpi=300, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


# =============================================================================
# Notes and README
# =============================================================================

def summarize_key_findings(rows: list[dict[str, Any]]) -> str:
    lines = []

    for scenario in PRIORITY_SCENARIOS:
        scenario_rows = [
            row for row in rows
            if row["scenario_id"] == scenario["scenario_id"]
        ]
        scenario_rows = sorted(
            scenario_rows,
            key=lambda row: (
                row["normalized_safety_priority_score"],
                row["rank_lower_is_better"],
            ),
        )

        best = scenario_rows[0]
        worst = scenario_rows[-1]

        lines.append(
            f"- {scenario['scenario_description']} "
            f"({scenario['fn_weight']:.0f}:{scenario['fp_weight']:.0f}): "
            f"best/lower score = {best['condition']} "
            f"({best['normalized_safety_priority_score']:.3f}); "
            f"worst/higher score = {worst['condition']} "
            f"({worst['normalized_safety_priority_score']:.3f})."
        )

    ranks_changed = [
        row for row in rows
        if row["rank_change_vs_equal_priority"] not in (0, None)
    ]

    if ranks_changed:
        lines.append(
            "- Some condition rankings change as missed-fall priority increases."
        )
    else:
        lines.append(
            "- Condition rankings remain stable across the tested missed-fall-priority scenarios."
        )

    lines.append(
        "- Column verification: FGSM attack uses attacked_fall_pred_binary, not clean_fall_pred_binary."
    )

    return "\n".join(lines)


def write_note(rows: list[dict[str, Any]]) -> None:
    key_findings = summarize_key_findings(rows)

    input_file_lines = []
    for condition in CONDITIONS:
        input_file_lines.append(
            f"- {condition['condition']}: `{condition['input_file']}` "
            f"using `{condition['pred_binary_col']}`"
        )
    input_files_text = "\n".join(input_file_lines)

    text = f"""# Thesis Table 23 and Figure 23: Safety-Priority Sensitivity Analysis Under Missed-Fall Weighting

## Purpose

Table 23 and Figure 23 ask:

```text
Do conclusions about clean, attacked, and defended conditions change when missed-fall windows are given increasing priority over false-alert windows?
```

This artifact is a scenario-based engineering sensitivity analysis. It complements the earlier window-level safety metrics, alert-trustworthiness analysis, failure-pattern analysis, and claim-boundary map.

## Files Created

**Table 23**  
`{TABLE_PATH}`

**Figure 23**  
`{FIGURE_PATH}`

**Companion note**  
`{NOTE_PATH}`

## Input Files and Prediction Columns

{input_files_text}

The FGSM input file contains both clean and attacked prediction columns. This artifact intentionally uses `attacked_fall_pred_binary` for the FGSM attack condition.

## Metric Definition

For each condition and each missed-fall-priority scenario:

```text
normalized safety-priority score =
FN weight × missed-fall rate + FP weight × false-positive rate
```

where:

```text
missed_fall_rate = FN / (TP + FN)
false_positive_rate = FP / (FP + TN)
```

Lower score is better.

## Scenario Interpretation

```text
1:1  = missed-fall errors and false-alert errors are weighted equally
2:1  = missed-fall errors are weighted 2× higher than false-alert errors
5:1  = missed-fall errors are weighted 5× higher than false-alert errors
10:1 = missed-fall errors are weighted 10× higher than false-alert errors
```

These weights are scenario assumptions, not clinical cost constants.

## Rank Definition

For each weighting scenario, the six model conditions are ranked by normalized safety-priority score.

```text
rank 1 = lowest score / best within that scenario column
rank 6 = highest score / worst within that scenario column
```

Tied scores share the same rank.

## Key Findings

{key_findings}

## Interpretation

This artifact does not introduce a clinically validated cost model. Its value is that it checks whether the relative interpretation of clean, attacked, and defended conditions is stable when missed-fall windows are treated as increasingly important compared with false-alert windows.

This is useful because a defense that reduces false alerts but still misses many fall windows may look acceptable under equal error weighting but less acceptable when missed-fall windows are prioritized.

## Claim Boundary

This is a descriptive window-level safety-priority sensitivity analysis using the current UT-HAR / SenseFi prediction outputs.

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
    section_marker = "### Thesis Table 23 and Figure 23: Safety-Priority Sensitivity Analysis"

    section = f"""
{section_marker}

Table 23 and Figure 23 add a missed-fall-priority sensitivity analysis.

**Files**

- `results/thesis_table_23_safety_priority_sensitivity.csv`
- `figures/thesis_figure_23_safety_priority_sensitivity_heatmap.png`
- `notes/thesis_table_23_figure_23_safety_priority_sensitivity.md`

**Purpose**

This artifact asks whether conclusions about clean, attacked, and defended conditions change when missed-fall windows are given increasing priority over false-alert windows.

**Important column mapping**

The FGSM CSV contains both clean and attacked prediction columns. This artifact uses `attacked_fall_pred_binary` for FGSM attack, not `clean_fall_pred_binary`.

**Metric**

```text
normalized safety-priority score =
FN weight × missed-fall rate + FP weight × false-positive rate
```

where:

```text
missed_fall_rate = FN / (TP + FN)
false_positive_rate = FP / (FP + TN)
```

**Scenario interpretation**

```text
1:1  = missed-fall errors and false-alert errors are weighted equally
2:1  = missed-fall errors are weighted 2× higher than false-alert errors
5:1  = missed-fall errors are weighted 5× higher than false-alert errors
10:1 = missed-fall errors are weighted 10× higher than false-alert errors
```

Lower score is better. Ranks compare the six model conditions within each scenario column.

**Claim boundary**

The weights are scenario assumptions, not clinical cost constants. This is a descriptive window-level sensitivity analysis using the current prediction outputs. It is not clinical validation, event-level fall validation, alarm-fatigue validation, time-to-alarm validation, health-economic analysis, or physical-layer / over-the-air validation.
"""

    old_text = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
    new_text = replace_or_append_readme_section(old_text, section_marker, section)
    README_PATH.write_text(new_text, encoding="utf-8")

    if section_marker in old_text:
        print("README Table 23 / Figure 23 section replaced.")
    else:
        print("README updated with Table 23 / Figure 23 section.")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    print("Creating Thesis Table 23 and Figure 23...")
    print("Using exact binary prediction columns for each condition.")

    condition_metrics = compute_condition_metrics()

    print("\nVerified input files and selected columns:")
    for metrics in condition_metrics:
        print(f"- {metrics['condition']}")
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
    write_note(rows)
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
