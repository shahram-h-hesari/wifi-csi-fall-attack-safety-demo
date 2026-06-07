from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any


# =============================================================================
# Thesis Table 26
# Prediction-Column Provenance and Sanity-Check Audit
# =============================================================================
#
# Purpose:
#   Protect the credibility of Tables/Figures 23-25 by documenting exactly
#   which prediction file and prediction column were used for each model
#   condition.
#
# Why this matters:
#   Some prediction CSVs contain multiple prediction columns. For example, the
#   FGSM CSV may include both clean and attacked prediction columns. Using the
#   wrong column can make FGSM appear identical to clean baseline. This audit
#   prevents that mistake by hard-coding the intended column mapping and
#   checking that each selected column is valid.
#
# Outputs:
#   results/thesis_table_26_prediction_column_provenance_audit.csv
#   notes/thesis_table_26_prediction_column_provenance_audit.md
#   README.md section update
#
# This artifact is intentionally table-only. It is a reproducibility and
# quality-control artifact, not a performance figure.


# =============================================================================
# Paths
# =============================================================================

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_DIR = SCRIPT_PATH.parent.parent

README_PATH = PROJECT_DIR / "README.md"
RESULTS_DIR = PROJECT_DIR / "results"
NOTES_DIR = PROJECT_DIR / "notes"

TABLE_PATH = RESULTS_DIR / "thesis_table_26_prediction_column_provenance_audit.csv"
NOTE_PATH = NOTES_DIR / "thesis_table_26_prediction_column_provenance_audit.md"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Exact project input mapping
# =============================================================================

CONDITIONS = [
    {
        "condition": "Clean baseline",
        "condition_id": "clean",
        "input_file": RESULTS_DIR / "clean_predictions_short.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary",
        "prediction_source": "clean baseline prediction",
        "why_correct": "Clean baseline condition should use the baseline fall prediction column.",
        "known_column_risk": "Low; clean file normally contains the baseline prediction column.",
    },
    {
        "condition": "FGSM attack",
        "condition_id": "fgsm_attack",
        "input_file": RESULTS_DIR / "fgsm_predictions_short_epsilon_0_03.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "attacked_fall_pred_binary",
        "prediction_source": "FGSM attacked prediction column",
        "why_correct": "FGSM attack must use the attacked prediction column, not the clean prediction column stored in the same CSV.",
        "known_column_risk": "High; using clean_fall_pred_binary here would incorrectly make FGSM resemble clean baseline.",
    },
    {
        "condition": "PGD attack",
        "condition_id": "pgd_attack",
        "input_file": RESULTS_DIR / "pgd_predictions_short_epsilon_0_03.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary",
        "prediction_source": "PGD attacked prediction column",
        "why_correct": "PGD file stores the selected attacked binary prediction in fall_pred_binary.",
        "known_column_risk": "Medium; column name is generic, so this row documents the intended PGD attacked output.",
    },
    {
        "condition": "Defended clean",
        "condition_id": "defended_clean",
        "input_file": RESULTS_DIR / "defended_predictions_short.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary_clean_defended",
        "prediction_source": "defended clean prediction column",
        "why_correct": "Defended clean condition should use the clean-defended prediction column.",
        "known_column_risk": "Medium; defended file can contain multiple defended prediction variants.",
    },
    {
        "condition": "Defended FGSM",
        "condition_id": "defended_fgsm",
        "input_file": RESULTS_DIR / "defended_fgsm_predictions_short_epsilon_0_03.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary_fgsm_defended",
        "prediction_source": "defended FGSM prediction column",
        "why_correct": "Defended FGSM condition should use the defended prediction column for FGSM attacked inputs.",
        "known_column_risk": "Medium; explicitly documents the defended FGSM prediction source.",
    },
    {
        "condition": "Defended PGD",
        "condition_id": "defended_pgd",
        "input_file": RESULTS_DIR / "defended_pgd_predictions_short_epsilon_0_03.csv",
        "true_binary_col": "fall_true_binary",
        "pred_binary_col": "fall_pred_binary_pgd_defended",
        "prediction_source": "defended PGD prediction column",
        "why_correct": "Defended PGD condition should use the defended prediction column for PGD attacked inputs.",
        "known_column_risk": "Medium; explicitly documents the defended PGD prediction source.",
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


def available_columns(path: Path) -> list[str]:
    rows = read_rows(path)
    if not rows:
        return []
    return list(rows[0].keys())


def binary_value_set(rows: list[dict[str, str]], column: str) -> set[int]:
    values = set()
    for row in rows:
        values.add(to_int(row[column]))
    return values


def compute_confusion(rows: list[dict[str, str]], true_col: str, pred_col: str) -> dict[str, Any]:
    tp = fn = fp = tn = 0

    for row in rows:
        true_binary = to_int(row[true_col])
        pred_binary = to_int(row[pred_col])

        if true_binary == 1 and pred_binary == 1:
            tp += 1
        elif true_binary == 1 and pred_binary == 0:
            fn += 1
        elif true_binary == 0 and pred_binary == 1:
            fp += 1
        elif true_binary == 0 and pred_binary == 0:
            tn += 1
        else:
            raise ValueError(
                f"Non-binary value encountered: true={true_binary}, pred={pred_binary}"
            )

    total_fall = tp + fn
    total_nonfall = fp + tn
    total_windows = tp + fn + fp + tn

    return {
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "total_fall_windows": total_fall,
        "total_nonfall_windows": total_nonfall,
        "total_windows": total_windows,
        "missed_fall_rate_fnr": safe_divide(fn, total_fall),
        "false_positive_rate_fpr": safe_divide(fp, total_nonfall),
    }


def evaluate_condition(condition: dict[str, Any], reference_counts: dict[str, int] | None = None) -> dict[str, Any]:
    path = condition["input_file"]

    checks: list[str] = []
    warnings: list[str] = []

    file_exists = path.exists()
    if file_exists:
        checks.append("file exists")
    else:
        raise FileNotFoundError(f"Missing required file for {condition['condition']}: {path}")

    rows = read_rows(path)
    columns = list(rows[0].keys()) if rows else []

    true_col = condition["true_binary_col"]
    pred_col = condition["pred_binary_col"]

    true_col_exists = true_col in columns
    pred_col_exists = pred_col in columns

    if true_col_exists:
        checks.append("true-label column found")
    else:
        raise ValueError(
            f"Missing true-label column {true_col} in {path}. Available columns: {columns}"
        )

    if pred_col_exists:
        checks.append("selected prediction column found")
    else:
        raise ValueError(
            f"Missing prediction column {pred_col} in {path}. Available columns: {columns}"
        )

    true_values = binary_value_set(rows, true_col)
    pred_values = binary_value_set(rows, pred_col)

    true_binary_ok = true_values.issubset({0, 1})
    pred_binary_ok = pred_values.issubset({0, 1})

    if true_binary_ok:
        checks.append("true-label values are binary")
    else:
        raise ValueError(f"Non-binary true values in {path}: {true_values}")

    if pred_binary_ok:
        checks.append("prediction values are binary")
    else:
        raise ValueError(f"Non-binary prediction values in {path}: {pred_values}")

    metrics = compute_confusion(rows, true_col, pred_col)

    if reference_counts is not None:
        if metrics["total_windows"] == reference_counts["total_windows"]:
            checks.append("total window count matches clean reference")
        else:
            warnings.append(
                f"total window count differs from clean reference "
                f"({metrics['total_windows']} vs {reference_counts['total_windows']})"
            )

        if metrics["total_fall_windows"] == reference_counts["total_fall_windows"]:
            checks.append("fall-window count matches clean reference")
        else:
            warnings.append(
                f"fall-window count differs from clean reference "
                f"({metrics['total_fall_windows']} vs {reference_counts['total_fall_windows']})"
            )

        if metrics["total_nonfall_windows"] == reference_counts["total_nonfall_windows"]:
            checks.append("non-fall-window count matches clean reference")
        else:
            warnings.append(
                f"non-fall-window count differs from clean reference "
                f"({metrics['total_nonfall_windows']} vs {reference_counts['total_nonfall_windows']})"
            )

    # Specific protection against the real mistake we discovered.
    if condition["condition"] == "FGSM attack":
        if pred_col == "attacked_fall_pred_binary":
            checks.append("FGSM uses attacked_fall_pred_binary")
        else:
            warnings.append("FGSM does not use attacked_fall_pred_binary")

        risky_clean_like_cols = [
            col for col in columns
            if "clean" in col.lower() and "pred" in col.lower()
        ]
        if risky_clean_like_cols:
            warnings.append(
                "FGSM file also contains clean-like prediction columns; do not use them for attack metrics: "
                + ", ".join(risky_clean_like_cols)
            )

    if condition["condition"] == "PGD attack" and pred_col == "fall_pred_binary":
        checks.append("PGD selected column documented despite generic name")

    if math.isfinite(metrics["missed_fall_rate_fnr"]):
        checks.append("FNR finite")
    else:
        warnings.append("FNR is not finite")

    if math.isfinite(metrics["false_positive_rate_fpr"]):
        checks.append("FPR finite")
    else:
        warnings.append("FPR is not finite")

    status = "PASS" if not warnings else "PASS_WITH_WARNINGS"

    return {
        "condition": condition["condition"],
        "condition_id": condition["condition_id"],
        "input_file": str(path),
        "true_binary_col": true_col,
        "pred_binary_col": pred_col,
        "prediction_source": condition["prediction_source"],
        "why_correct": condition["why_correct"],
        "known_column_risk": condition["known_column_risk"],
        "file_exists": file_exists,
        "true_col_exists": true_col_exists,
        "pred_col_exists": pred_col_exists,
        "true_binary_values": sorted(true_values),
        "pred_binary_values": sorted(pred_values),
        "available_prediction_like_columns": ", ".join(
            col for col in columns
            if (
                "pred" in col.lower()
                or "prediction" in col.lower()
                or "fall_pred" in col.lower()
            )
        ),
        "tp": metrics["tp"],
        "fn": metrics["fn"],
        "fp": metrics["fp"],
        "tn": metrics["tn"],
        "total_fall_windows": metrics["total_fall_windows"],
        "total_nonfall_windows": metrics["total_nonfall_windows"],
        "total_windows": metrics["total_windows"],
        "missed_fall_rate_fnr": metrics["missed_fall_rate_fnr"],
        "false_positive_rate_fpr": metrics["false_positive_rate_fpr"],
        "sanity_status": status,
        "sanity_checks_passed": "; ".join(checks),
        "warnings": "; ".join(warnings) if warnings else "",
    }


def build_audit_rows() -> list[dict[str, Any]]:
    clean_condition = CONDITIONS[0]
    clean_rows = read_rows(clean_condition["input_file"])
    clean_reference = compute_confusion(
        clean_rows,
        clean_condition["true_binary_col"],
        clean_condition["pred_binary_col"],
    )

    reference_counts = {
        "total_windows": clean_reference["total_windows"],
        "total_fall_windows": clean_reference["total_fall_windows"],
        "total_nonfall_windows": clean_reference["total_nonfall_windows"],
    }

    return [
        evaluate_condition(condition, reference_counts)
        for condition in CONDITIONS
    ]


def format_value(value: Any) -> str:
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.6f}"
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


def write_table(rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "condition",
        "condition_id",
        "input_file",
        "true_binary_col",
        "pred_binary_col",
        "prediction_source",
        "why_correct",
        "known_column_risk",
        "file_exists",
        "true_col_exists",
        "pred_col_exists",
        "true_binary_values",
        "pred_binary_values",
        "available_prediction_like_columns",
        "tp",
        "fn",
        "fp",
        "tn",
        "total_fall_windows",
        "total_nonfall_windows",
        "total_windows",
        "missed_fall_rate_fnr",
        "false_positive_rate_fpr",
        "sanity_status",
        "sanity_checks_passed",
        "warnings",
    ]

    with TABLE_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({key: format_value(row[key]) for key in fieldnames})


# =============================================================================
# Notes and README
# =============================================================================

def summarize_rows(rows: list[dict[str, Any]]) -> str:
    pass_count = sum(1 for row in rows if row["sanity_status"] == "PASS")
    warning_count = sum(1 for row in rows if row["sanity_status"] == "PASS_WITH_WARNINGS")

    lines = [
        f"- {pass_count} condition(s) passed all sanity checks without warnings.",
        f"- {warning_count} condition(s) passed with warnings that are documented in the table.",
        "- All rows use explicit binary true/prediction columns.",
        "- The FGSM attack row explicitly uses `attacked_fall_pred_binary`, avoiding the clean-column selection mistake.",
        "- Window counts and fall/non-fall counts are checked against the clean reference.",
    ]

    return "\n".join(lines)


def markdown_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Condition | File | True column | Prediction column | TP | FN | FP | TN | FNR | FPR | Status |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    for row in rows:
        file_name = Path(row["input_file"]).name
        lines.append(
            f"| {row['condition']} | `{file_name}` | `{row['true_binary_col']}` | "
            f"`{row['pred_binary_col']}` | {row['tp']} | {row['fn']} | {row['fp']} | "
            f"{row['tn']} | {row['missed_fall_rate_fnr']:.3f} | "
            f"{row['false_positive_rate_fpr']:.3f} | {row['sanity_status']} |"
        )

    return "\n".join(lines)


def write_note(rows: list[dict[str, Any]]) -> None:
    warning_lines = []
    for row in rows:
        if row["warnings"]:
            warning_lines.append(f"- **{row['condition']}**: {row['warnings']}")

    warnings_text = "\n".join(warning_lines) if warning_lines else "- No warnings."

    text = f"""# Thesis Table 26: Prediction-Column Provenance and Sanity-Check Audit

## Purpose

Table 26 asks:

```text
Exactly which prediction file and prediction column generated each clean, attacked, and defended condition?
```

This is a reproducibility and quality-control table. It protects Tables/Figures 23-25 from column-selection mistakes.

## Files Created

**Table 26**  
`{TABLE_PATH}`

**Companion note**  
`{NOTE_PATH}`

## Why this audit is needed

Several prediction CSV files contain more than one prediction-like column. In particular, the FGSM prediction file can contain both clean and attacked prediction columns. If the clean column is accidentally selected, FGSM can appear artificially similar to clean baseline.

Table 26 prevents that by explicitly documenting:

- input CSV file
- true-label column
- prediction column used
- why the selected column is correct
- TP/FN/FP/TN counts
- FNR/FPR
- sanity-check status and warnings

## Summary

{summarize_rows(rows)}

## Audit Table

{markdown_table(rows)}

## Warnings

{warnings_text}

## Interpretation

This table is not another performance claim. It is a reproducibility guardrail. Its main value is that every downstream table and figure can be traced back to a specific file and prediction column.

The most important verification is:

```text
FGSM attack uses attacked_fall_pred_binary, not a clean prediction column.
```

## Claim Boundary

This is a prediction-column provenance and sanity-check audit for the current UT-HAR / SenseFi window-level workflow.

It is not clinical validation, event-level fall validation, deployment validation, physical-layer validation, or over-the-air validation.
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
    section_marker = "### Thesis Table 26: Prediction-Column Provenance and Sanity-Check Audit"

    section = f"""
{section_marker}

Table 26 adds a reproducibility and quality-control audit for the prediction columns used in Tables/Figures 23-25.

**Files**

- `results/thesis_table_26_prediction_column_provenance_audit.csv`
- `notes/thesis_table_26_prediction_column_provenance_audit.md`

**Purpose**

This artifact documents exactly which prediction file and prediction column generated each clean, attacked, and defended condition.

**Why this matters**

The FGSM CSV can contain both clean and attacked prediction columns. Table 26 explicitly verifies that the FGSM attack condition uses `attacked_fall_pred_binary`, not a clean prediction column.

**Main interpretation**

This is not a new performance figure. It is a reproducibility guardrail that makes the later safety-priority, defense-recovery, and score-decomposition artifacts more defensible.

**Claim boundary**

This is a prediction-column provenance and sanity-check audit for the current window-level workflow. It is not clinical validation, event-level fall validation, deployment validation, physical-layer validation, or over-the-air validation.
"""

    old_text = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
    new_text = replace_or_append_readme_section(old_text, section_marker, section)
    README_PATH.write_text(new_text, encoding="utf-8")

    if section_marker in old_text:
        print("README Table 26 section replaced.")
    else:
        print("README updated with Table 26 section.")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    print("Creating Thesis Table 26...")
    print("Running prediction-column provenance and sanity-check audit.")

    rows = build_audit_rows()
    write_table(rows)
    write_note(rows)
    update_readme()

    print("\nCreated outputs:")
    print(f"- {TABLE_PATH}")
    print(f"- {NOTE_PATH}")
    print("- README.md updated")

    print("\nAudit summary:")
    print(summarize_rows(rows))

    print("\nCondition-level status:")
    for row in rows:
        print(
            f"- {row['condition']}: {row['sanity_status']} | "
            f"{Path(row['input_file']).name} | {row['pred_binary_col']} | "
            f"TP={row['tp']}, FN={row['fn']}, FP={row['fp']}, TN={row['tn']}, "
            f"FNR={row['missed_fall_rate_fnr']:.3f}, FPR={row['false_positive_rate_fpr']:.3f}"
        )
        if row["warnings"]:
            print(f"  warnings: {row['warnings']}")


if __name__ == "__main__":
    main()
