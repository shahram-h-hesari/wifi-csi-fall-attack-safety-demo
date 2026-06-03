"""
Create thesis-ready Table 1 for the WiFi CSI Fall Attack-Safety Demo.

Input:
    results/defended_vs_undefended_safety_comparison.csv

Outputs:
    results/thesis_table_1_safety_metrics.csv
    notes/thesis_table_1_safety_metrics.md

Purpose:
    Prepare a clean thesis-ready table comparing clean, attacked, and defended
    fall-vs-non-fall safety-proxy metrics.

Claim boundary:
    This is a window-level software comparison on processed CSI tensors.
    It is not clinical validation, medical-device validation, diagnostic
    evidence, regulatory evaluation, physical-layer validation, packet-level
    validation, preamble-level validation, SDR validation, or over-the-air
    validation.
"""

from pathlib import Path
import csv


INPUT_FILE = "defended_vs_undefended_safety_comparison.csv"
OUTPUT_CSV = "thesis_table_1_safety_metrics.csv"
OUTPUT_MD = "thesis_table_1_safety_metrics.md"


CONDITION_LABELS = {
    "undefended_clean": "Undefended clean",
    "undefended_fgsm_epsilon_0_03": "Undefended FGSM, epsilon 0.03",
    "undefended_pgd_epsilon_0_03": "Undefended PGD, epsilon 0.03",
    "defended_clean": "Defended clean",
    "defended_fgsm_epsilon_0_03": "Defended FGSM, epsilon 0.03",
    "defended_pgd_epsilon_0_03": "Defended PGD, epsilon 0.03",
}


ORDER = [
    "undefended_clean",
    "undefended_fgsm_epsilon_0_03",
    "undefended_pgd_epsilon_0_03",
    "defended_clean",
    "defended_fgsm_epsilon_0_03",
    "defended_pgd_epsilon_0_03",
]


TABLE_COLUMNS = [
    "Condition",
    "Attack",
    "TP",
    "FN",
    "FP",
    "TN",
    "Missed Fall Rate",
    "Recall",
    "Precision",
    "F1-score",
    "Balanced Accuracy",
]


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


def format_float(value):
    return f"{safe_float(value):.4f}"


def build_table_rows(rows):
    by_condition = {row["condition"]: row for row in rows}

    table_rows = []

    for condition in ORDER:
        if condition not in by_condition:
            raise KeyError(f"Missing condition in input CSV: {condition}")

        row = by_condition[condition]

        table_rows.append(
            {
                "Condition": CONDITION_LABELS[condition],
                "Attack": row["attack_type"],
                "TP": row["TP_detected_falls"],
                "FN": row["FN_missed_falls"],
                "FP": row["FP_false_fall_alarms"],
                "TN": row["TN_correct_non_falls"],
                "Missed Fall Rate": format_float(row["missed_fall_rate"]),
                "Recall": format_float(row["recall_sensitivity"]),
                "Precision": format_float(row["precision"]),
                "F1-score": format_float(row["f1_score"]),
                "Balanced Accuracy": format_float(row["balanced_accuracy"]),
            }
        )

    return table_rows


def write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TABLE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows):
    lines = []

    lines.append("| " + " | ".join(TABLE_COLUMNS) + " |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for row in rows:
        lines.append("| " + " | ".join(str(row[col]) for col in TABLE_COLUMNS) + " |")

    return "\n".join(lines)


def write_markdown(path: Path, rows):
    table_text = markdown_table(rows)

    content = f"""# Thesis Table 1: Clean, Attacked, and Defended Fall Safety-Proxy Metrics

This table summarizes the first thesis-ready comparison of clean, attacked, and defended fall-vs-non-fall safety-proxy metrics for the WiFi CSI Fall Attack-Safety Demo.

The table is generated from:

```text
results/defended_vs_undefended_safety_comparison.csv
```

Generated outputs:

```text
results/thesis_table_1_safety_metrics.csv
notes/thesis_table_1_safety_metrics.md
```

---

## Table 1

{table_text}

---

## Suggested Thesis Caption

Table 1. Window-level fall-vs-non-fall safety-proxy metrics for the SenseFi UT-HAR LeNet baseline under clean, FGSM-attacked, PGD-attacked, and short FGSM-adversarial-training defended conditions. The first short defended model reduced false fall alarms under FGSM and PGD attack but did not recover fall recall at epsilon 0.03.

---

## Key Interpretation

The undefended clean model detected 57 of 89 fall windows and missed 32 fall windows.

Both undefended attacks at epsilon 0.03 caused complete fall-recall loss:

```text
undefended FGSM: TP = 0, FN = 89
undefended PGD:  TP = 0, FN = 89
```

The short FGSM-adversarial-training defended model also had complete fall-recall loss under FGSM and PGD attack at epsilon 0.03:

```text
defended FGSM: TP = 0, FN = 89
defended PGD:  TP = 0, FN = 89
```

However, the defended model reduced false fall alarms under attack:

```text
FGSM false fall alarms: 119 -> 72
PGD false fall alarms:  115 -> 56
```

This supports a careful conclusion: the first short defense baseline reduced false alarm burden under attack but did not restore fall sensitivity.

---

## Claim Boundary

This table is a window-level software comparison on processed CSI tensors.

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
    notes_dir = experiment_dir / "notes"

    input_path = results_dir / INPUT_FILE
    output_csv_path = results_dir / OUTPUT_CSV
    output_md_path = notes_dir / OUTPUT_MD

    rows = read_rows(input_path)
    table_rows = build_table_rows(rows)

    write_csv(output_csv_path, table_rows)
    write_markdown(output_md_path, table_rows)

    print("Thesis Table 1 created successfully.")
    print(f"Input: {input_path}")
    print(f"CSV output: {output_csv_path}")
    print(f"Markdown output: {output_md_path}")
    print("-" * 80)

    for row in table_rows:
        print(row)


if __name__ == "__main__":
    main()