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

TABLE_PATH = RESULTS_DIR / "thesis_table_25_safety_score_component_decomposition.csv"
FIGURE_PATH = FIGURES_DIR / "thesis_figure_25_safety_score_component_decomposition.png"
NOTE_PATH = NOTES_DIR / "thesis_table_25_figure_25_safety_score_component_decomposition.md"

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
        "condition": "Defended clean",
        "condition_id": "defended_clean",
        "input_file": RESULTS_DIR / "defended_predictions_short.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary_clean_defended",
        "prediction_source": "defended clean prediction column",
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
]

# Figure 25 focuses on the strongest safety-priority scenario from Figure 23.
# This avoids repeating all four weighting scenarios again and directly explains
# why the 10:1 scores/ranks behave the way they do.
FN_WEIGHT = 10.0
FP_WEIGHT = 1.0
SCENARIO_LABEL = "10:1 missed-fall priority"


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


def compute_condition_metrics() -> list[dict[str, Any]]:
    return [compute_confusion_for_condition(condition) for condition in CONDITIONS]


def competition_ranks(values: list[float]) -> list[int]:
    """Competition ranking with ties; lower value is better."""
    unique_sorted = sorted(set(values))
    ranks = {}
    for val in unique_sorted:
        ranks[val] = 1 + sum(1 for x in values if x < val)
    return [ranks[v] for v in values]


# =============================================================================
# Table 25 computation
# =============================================================================

def build_table_rows(condition_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []

    for metrics in condition_metrics:
        missed_fall_component = FN_WEIGHT * metrics["missed_fall_rate_fnr"]
        false_alert_component = FP_WEIGHT * metrics["false_positive_rate_fpr"]
        total_score = missed_fall_component + false_alert_component

        if total_score > 0:
            missed_fall_percent = 100.0 * missed_fall_component / total_score
            false_alert_percent = 100.0 * false_alert_component / total_score
        else:
            missed_fall_percent = math.nan
            false_alert_percent = math.nan

        rows.append(
            {
                "condition": metrics["condition"],
                "condition_id": metrics["condition_id"],
                "scenario": SCENARIO_LABEL,
                "fn_weight": FN_WEIGHT,
                "fp_weight": FP_WEIGHT,
                "tp": metrics["tp"],
                "fn": metrics["fn"],
                "fp": metrics["fp"],
                "tn": metrics["tn"],
                "total_fall_windows": metrics["total_fall_windows"],
                "total_nonfall_windows": metrics["total_nonfall_windows"],
                "total_windows": metrics["total_windows"],
                "missed_fall_rate_fnr": metrics["missed_fall_rate_fnr"],
                "false_positive_rate_fpr": metrics["false_positive_rate_fpr"],
                "missed_fall_component": missed_fall_component,
                "false_alert_component": false_alert_component,
                "total_safety_priority_score": total_score,
                "missed_fall_component_percent": missed_fall_percent,
                "false_alert_component_percent": false_alert_percent,
                "score_rank_lower_is_better": None,
                "dominant_component": (
                    "missed-fall component"
                    if missed_fall_component >= false_alert_component
                    else "false-alert component"
                ),
                "input_file": metrics["input_file"],
                "true_binary_col": metrics["true_binary_col"],
                "pred_binary_col": metrics["pred_binary_col"],
                "prediction_source": metrics["prediction_source"],
                "interpretation": "",
            }
        )

    scores = [row["total_safety_priority_score"] for row in rows]
    ranks = competition_ranks(scores)

    for row, rank in zip(rows, ranks):
        row["score_rank_lower_is_better"] = rank
        row["interpretation"] = (
            f"At {SCENARIO_LABEL}, score is {row['total_safety_priority_score']:.3f}; "
            f"{row['missed_fall_component_percent']:.1f}% of the score comes from the "
            f"missed-fall component and {row['false_alert_component_percent']:.1f}% "
            "comes from the false-alert component."
        )

    return rows


def format_float(value: Any, digits: int = 6) -> str:
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.{digits}f}"
    return str(value)


def write_table(rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "condition",
        "condition_id",
        "scenario",
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
        "missed_fall_component",
        "false_alert_component",
        "total_safety_priority_score",
        "missed_fall_component_percent",
        "false_alert_component_percent",
        "score_rank_lower_is_better",
        "dominant_component",
        "input_file",
        "true_binary_col",
        "pred_binary_col",
        "prediction_source",
        "interpretation",
    ]

    with TABLE_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            output_row = {key: row[key] for key in fieldnames}
            for key in [
                "missed_fall_rate_fnr",
                "false_positive_rate_fpr",
                "missed_fall_component",
                "false_alert_component",
                "total_safety_priority_score",
                "missed_fall_component_percent",
                "false_alert_component_percent",
            ]:
                output_row[key] = format_float(output_row[key])
            writer.writerow(output_row)


# =============================================================================
# Figure 25
# =============================================================================

def create_figure(rows: list[dict[str, Any]]) -> None:
    # Keep the same condition order as prior figures.
    ordered_rows = rows

    conditions = [row["condition"] for row in ordered_rows]
    missed_components = np.array([row["missed_fall_component"] for row in ordered_rows], dtype=float)
    false_components = np.array([row["false_alert_component"] for row in ordered_rows], dtype=float)
    total_scores = np.array([row["total_safety_priority_score"] for row in ordered_rows], dtype=float)
    ranks = [row["score_rank_lower_is_better"] for row in ordered_rows]

    x = np.arange(len(conditions), dtype=float)

    # Layout fixes:
    # - title and legend are separated
    # - totals are shown with 3 decimals so FGSM and PGD are not both rounded to 10.13
    # - in-bar labels clarify that percentages are percent of the score, not FNR
    # - false-alert component is labeled numerically because it is visually tiny
    fig = plt.figure(figsize=(16.0, 9.8), dpi=150)
    ax = fig.add_axes([0.09, 0.31, 0.88, 0.56])

    bar_width = 0.70

    ax.bar(
        x,
        missed_components,
        width=bar_width,
        edgecolor="white",
        linewidth=1.2,
        label="Missed-fall component",
        zorder=3,
    )

    ax.bar(
        x,
        false_components,
        bottom=missed_components,
        width=bar_width,
        edgecolor="white",
        linewidth=1.2,
        label="False-alert component",
        zorder=3,
    )

    fig.suptitle(
        "Figure 25: Safety-Score Component Decomposition",
        fontsize=18.6,
        fontweight="bold",
        y=0.965,
    )

    fig.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 0.925),
        ncol=2,
        frameon=False,
        fontsize=10.6,
    )

    ax.set_ylabel(
        "Safety-priority score contribution",
        fontsize=12.8,
        fontweight="bold",
        labelpad=10,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [
            "Clean\nbaseline",
            "FGSM\nattack",
            "PGD\nattack",
            "Defended\nclean",
            "Defended\nFGSM",
            "Defended\nPGD",
        ],
        fontsize=10.6,
        fontweight="bold",
    )

    y_max = max(float(total_scores.max()) * 1.18, 1.0)
    ax.set_ylim(0, y_max)
    ax.tick_params(axis="y", labelsize=10.5)
    ax.grid(axis="y", linestyle="--", linewidth=0.7, alpha=0.45, zorder=0)
    ax.set_axisbelow(True)

    # Annotate total score and rank above each bar.
    for i, row in enumerate(ordered_rows):
        total = row["total_safety_priority_score"]
        missed_pct = row["missed_fall_component_percent"]
        false_pct = row["false_alert_component_percent"]
        rank = row["score_rank_lower_is_better"]

        ax.text(
            x[i],
            total + y_max * 0.018,
            f"total {total:.3f}\nrank {rank}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )

        # Clarify that this is the share of score from missed-fall contribution,
        # not the missed-fall rate itself.
        if row["missed_fall_component"] > y_max * 0.09:
            ax.text(
                x[i],
                row["missed_fall_component"] / 2.0,
                f"{missed_pct:.1f}% of score\nfrom missed falls",
                ha="center",
                va="center",
                fontsize=7.8,
                fontweight="bold",
                color="white",
            )

        # The false-alert component is tiny; show its value near the cap instead
        # of trying to fit a percent inside a very thin segment.
        ax.text(
            x[i],
            total + y_max * 0.075,
            f"FA={row['false_alert_component']:.3f}",
            ha="center",
            va="bottom",
            fontsize=7.4,
        )

    fig.text(
        0.50,
        0.200,
        (
            "Scenario shown: FN:FP = 10:1, meaning missed-fall errors are weighted "
            "10× higher than false alerts."
        ),
        ha="center",
        va="center",
        fontsize=10.5,
        fontweight="bold",
    )

    fig.text(
        0.50,
        0.160,
        (
            "Total score = missed-fall component + false-alert component "
            "= 10 × FNR + 1 × FPR."
        ),
        ha="center",
        va="center",
        fontsize=10.0,
    )

    fig.text(
        0.50,
        0.120,
        (
            "FNR = missed-fall rate; FPR = false-positive rate. "
            "Ranks compare the six conditions under this 10:1 scenario; lower is better."
        ),
        ha="center",
        va="center",
        fontsize=9.4,
    )

    fig.text(
        0.50,
        0.072,
        (
            "Window-level descriptive analysis only; not event-level fall validation, "
            "clinical validation, or physical-layer validation."
        ),
        ha="center",
        va="center",
        fontsize=8.9,
    )

    fig.savefig(FIGURE_PATH, dpi=300, bbox_inches="tight", pad_inches=0.14)
    plt.close(fig)

# =============================================================================
# Notes and README
# =============================================================================

def summarize_key_findings(rows: list[dict[str, Any]]) -> str:
    clean = next(row for row in rows if row["condition"] == "Clean baseline")
    defended_clean = next(row for row in rows if row["condition"] == "Defended clean")
    fgsm = next(row for row in rows if row["condition"] == "FGSM attack")
    pgd = next(row for row in rows if row["condition"] == "PGD attack")
    defended_fgsm = next(row for row in rows if row["condition"] == "Defended FGSM")
    defended_pgd = next(row for row in rows if row["condition"] == "Defended PGD")

    lines = [
        (
            f"- Clean baseline has the lowest total score "
            f"({clean['total_safety_priority_score']:.3f}), while attacked conditions "
            f"are highest because their missed-fall component dominates."
        ),
        (
            f"- Defended clean has a higher score than clean baseline "
            f"({defended_clean['total_safety_priority_score']:.3f} vs "
            f"{clean['total_safety_priority_score']:.3f}) because the missed-fall "
            "component increases despite lower false-alert behavior."
        ),
        (
            f"- FGSM and PGD attacks have near-maximal missed-fall components "
            f"({fgsm['missed_fall_component']:.3f} and {pgd['missed_fall_component']:.3f}), "
            "so false-alert improvements alone cannot restore safety-priority behavior."
        ),
        (
            f"- Defended FGSM/PGD reduce the false-alert component, but their missed-fall "
            f"component remains {defended_fgsm['missed_fall_component']:.3f}/"
            f"{defended_pgd['missed_fall_component']:.3f}; therefore the total score remains high."
        ),
    ]

    return "\n".join(lines)


def write_note(rows: list[dict[str, Any]], condition_metrics: list[dict[str, Any]]) -> None:
    key_findings = summarize_key_findings(rows)

    input_file_lines = []
    for metrics in condition_metrics:
        input_file_lines.append(
            f"- {metrics['condition']}: `{metrics['input_file']}` "
            f"using `{metrics['pred_binary_col']}`"
        )
    input_files_text = "\n".join(input_file_lines)

    table_lines = []
    table_lines.append("| Condition | FNR | FPR | Missed-fall component | False-alert component | Total score | Rank |")
    table_lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        table_lines.append(
            f"| {row['condition']} | {row['missed_fall_rate_fnr']:.3f} | "
            f"{row['false_positive_rate_fpr']:.3f} | "
            f"{row['missed_fall_component']:.3f} | "
            f"{row['false_alert_component']:.3f} | "
            f"{row['total_safety_priority_score']:.3f} | "
            f"{row['score_rank_lower_is_better']} |"
        )
    table_text = "\n".join(table_lines)

    text = f"""# Thesis Table 25 and Figure 25: Safety-Score Component Decomposition

## Purpose

Table 25 and Figure 25 ask:

```text
Why are the safety-priority scores high or low?
Are they driven mainly by missed-fall contribution or false-alert contribution?
```

This artifact directly explains the mechanism behind Tables/Figures 23 and 24.

## Files Created

**Table 25**  
`{TABLE_PATH}`

**Figure 25**  
`{FIGURE_PATH}`

**Companion note**  
`{NOTE_PATH}`

## Input Files and Prediction Columns

{input_files_text}

The FGSM input file contains both clean and attacked prediction columns. This artifact intentionally uses `attacked_fall_pred_binary` for the FGSM attack condition.

## Scenario

Figure 25 focuses on the strongest missed-fall-priority scenario:

```text
FN:FP = 10:1
```

This means missed-fall errors are weighted 10× higher than false-alert errors.

## Metric Definition

```text
total safety-priority score =
missed-fall component + false-alert component

missed-fall component = 10 × FNR
false-alert component = 1 × FPR
```

where:

```text
FNR = missed-fall rate = FN / (TP + FN)
FPR = false-positive rate = FP / (FP + TN)
```

## Table Summary

{table_text}

## Key Findings

{key_findings}

## Interpretation

The decomposition shows that the high safety-priority scores under attack are driven primarily by missed-fall behavior, not false-alert behavior. This explains why the defended attack cases remain far from clean-baseline behavior: the defense reduces false positives, but it does not recover true fall-window detection in the current tested configuration.

## Claim Boundary

This is a descriptive window-level score-decomposition analysis using the current UT-HAR / SenseFi prediction outputs.

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
    section_marker = "### Thesis Table 25 and Figure 25: Safety-Score Component Decomposition"

    section = f"""
{section_marker}

Table 25 and Figure 25 add a safety-score component decomposition.

**Files**

- `results/thesis_table_25_safety_score_component_decomposition.csv`
- `figures/thesis_figure_25_safety_score_component_decomposition.png`
- `notes/thesis_table_25_figure_25_safety_score_component_decomposition.md`

**Purpose**

This artifact explains why the safety-priority scores in Tables/Figures 23 and 24 are high or low by decomposing each total score into missed-fall and false-alert components.

**Scenario**

```text
FN:FP = 10:1
```

This means missed-fall errors are weighted 10× higher than false-alert errors.

**Metric**

```text
total safety-priority score =
missed-fall component + false-alert component

missed-fall component = 10 × FNR
false-alert component = 1 × FPR
```

**Main interpretation**

The high scores under attack and defended attack are dominated by the missed-fall component. The tested defense reduces false-alert contribution but does not recover missed-fall behavior in the current outputs.

**Claim boundary**

This is a descriptive window-level score-decomposition analysis using current prediction outputs. It is not clinical validation, event-level fall validation, alarm-fatigue validation, time-to-alarm validation, health-economic analysis, or physical-layer / over-the-air validation.
"""

    old_text = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
    new_text = replace_or_append_readme_section(old_text, section_marker, section)
    README_PATH.write_text(new_text, encoding="utf-8")

    if section_marker in old_text:
        print("README Table 25 / Figure 25 section replaced.")
    else:
        print("README updated with Table 25 / Figure 25 section.")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    print("Creating Thesis Table 25 and Figure 25...")
    print("Using exact binary prediction columns for score-component decomposition.")

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
