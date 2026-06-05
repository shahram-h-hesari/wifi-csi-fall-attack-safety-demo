from pathlib import Path
import csv

import matplotlib.pyplot as plt


RESULTS_DIR = Path("results")
FIGURES_DIR = Path("figures")
NOTES_DIR = Path("notes")

TABLE_PATH = RESULTS_DIR / "thesis_table_16_alert_trustworthiness.csv"
FIGURE_PATH = FIGURES_DIR / "thesis_figure_16_fall_alert_composition.png"
NOTE_PATH = NOTES_DIR / "thesis_table_16_figure_16_alert_trustworthiness.md"
README_PATH = Path("README.md")


INPUT_FILES = {
    "clean": RESULTS_DIR / "clean_predictions_short.csv",
    "fgsm": RESULTS_DIR / "fgsm_predictions_short_epsilon_0_03.csv",
    "pgd": RESULTS_DIR / "pgd_predictions_short_epsilon_0_03.csv",
    "defended_clean": RESULTS_DIR / "defended_predictions_short.csv",
    "defended_fgsm": RESULTS_DIR / "defended_fgsm_predictions_short_epsilon_0_03.csv",
    "defended_pgd": RESULTS_DIR / "defended_pgd_predictions_short_epsilon_0_03.csv",
}


CONDITIONS = [
    {
        "condition_id": "clean",
        "condition_label": "Clean",
        "file_key": "clean",
        "true_col": "fall_true_binary",
        "pred_col": "fall_pred_binary",
        "condition_type": "undefended clean",
    },
    {
        "condition_id": "fgsm_attack",
        "condition_label": "FGSM Attack",
        "file_key": "fgsm",
        "true_col": "fall_true_binary",
        "pred_col": "attacked_fall_pred_binary",
        "condition_type": "undefended attacked",
    },
    {
        "condition_id": "pgd_attack",
        "condition_label": "PGD Attack",
        "file_key": "pgd",
        "true_col": "fall_true_binary",
        "pred_col": "fall_pred_binary",
        "condition_type": "undefended attacked",
    },
    {
        "condition_id": "defended_clean",
        "condition_label": "Defended Clean",
        "file_key": "defended_clean",
        "true_col": "fall_true_binary",
        "pred_col": "fall_pred_binary_clean_defended",
        "condition_type": "defended clean",
    },
    {
        "condition_id": "defended_fgsm",
        "condition_label": "Defended FGSM",
        "file_key": "defended_fgsm",
        "true_col": "fall_true_binary",
        "pred_col": "fall_pred_binary_fgsm_defended",
        "condition_type": "defended attacked",
    },
    {
        "condition_id": "defended_pgd",
        "condition_label": "Defended PGD",
        "file_key": "defended_pgd",
        "true_col": "fall_true_binary",
        "pred_col": "fall_pred_binary_pgd_defended",
        "condition_type": "defended attacked",
    },
]


def to_int(value):
    return int(float(str(value).strip()))


def safe_divide(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator


def read_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_confusion_counts(rows, true_col, pred_col):
    tp = 0
    fn = 0
    fp = 0
    tn = 0

    for row in rows:
        true_value = to_int(row[true_col])
        pred_value = to_int(row[pred_col])

        if true_value == 1 and pred_value == 1:
            tp += 1
        elif true_value == 1 and pred_value == 0:
            fn += 1
        elif true_value == 0 and pred_value == 1:
            fp += 1
        elif true_value == 0 and pred_value == 0:
            tn += 1
        else:
            raise ValueError(f"Unexpected values: true={true_value}, pred={pred_value}")

    return tp, fn, fp, tn


def interpretation_for_row(tp, fn, fp, predicted_fall_alerts, alert_precision, false_alert_share):
    if predicted_fall_alerts == 0:
        return "No fall alerts were raised; alert precision is not meaningful for this condition."

    if tp == 0 and fp > 0:
        return "Fall alerts were raised, but TP was zero, so every predicted fall alert was false."

    if tp > 0 and fp == 0:
        return "All predicted fall alerts corresponded to true fall windows in this condition."

    if false_alert_share >= 0.75:
        return "Most predicted fall alerts were false fall alarms, indicating low alert trustworthiness."

    if false_alert_share >= 0.50:
        return "At least half of predicted fall alerts were false fall alarms."

    if alert_precision >= 0.75:
        return "Most predicted fall alerts corresponded to true fall windows."

    return "Predicted fall alerts were mixed between true fall detections and false fall alarms."


def build_table_rows():
    rows_out = []

    for condition in CONDITIONS:
        path = INPUT_FILES[condition["file_key"]]
        rows = read_rows(path)

        tp, fn, fp, tn = compute_confusion_counts(
            rows,
            condition["true_col"],
            condition["pred_col"],
        )

        total_windows = tp + fn + fp + tn
        total_true_fall_windows = tp + fn
        total_true_nonfall_windows = fp + tn
        predicted_fall_alerts = tp + fp
        true_fall_alerts = tp
        false_fall_alerts = fp

        alert_precision_ppv = safe_divide(tp, predicted_fall_alerts)
        false_alert_share_among_alerts = safe_divide(fp, predicted_fall_alerts)
        missed_fall_count = fn
        missed_fall_rate = safe_divide(fn, total_true_fall_windows)
        false_positive_rate = safe_divide(fp, total_true_nonfall_windows)
        recall_sensitivity = safe_divide(tp, total_true_fall_windows)

        rows_out.append(
            {
                "condition_id": condition["condition_id"],
                "condition_label": condition["condition_label"],
                "condition_type": condition["condition_type"],
                "total_windows": total_windows,
                "total_true_fall_windows": total_true_fall_windows,
                "total_true_nonfall_windows": total_true_nonfall_windows,
                "tp_true_fall_alerts": tp,
                "fn_missed_falls": fn,
                "fp_false_fall_alerts": fp,
                "tn_correct_nonfall_windows": tn,
                "predicted_fall_alerts_tp_plus_fp": predicted_fall_alerts,
                "true_fall_alerts_tp": true_fall_alerts,
                "false_fall_alerts_fp": false_fall_alerts,
                "alert_precision_ppv": f"{alert_precision_ppv:.6f}",
                "false_alert_share_among_predicted_alerts": f"{false_alert_share_among_alerts:.6f}",
                "missed_fall_count": missed_fall_count,
                "missed_fall_rate": f"{missed_fall_rate:.6f}",
                "false_positive_rate": f"{false_positive_rate:.6f}",
                "recall_sensitivity": f"{recall_sensitivity:.6f}",
                "interpretation": interpretation_for_row(
                    tp,
                    fn,
                    fp,
                    predicted_fall_alerts,
                    alert_precision_ppv,
                    false_alert_share_among_alerts,
                ),
            }
        )

    return rows_out


def write_table(rows):
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "condition_id",
        "condition_label",
        "condition_type",
        "total_windows",
        "total_true_fall_windows",
        "total_true_nonfall_windows",
        "tp_true_fall_alerts",
        "fn_missed_falls",
        "fp_false_fall_alerts",
        "tn_correct_nonfall_windows",
        "predicted_fall_alerts_tp_plus_fp",
        "true_fall_alerts_tp",
        "false_fall_alerts_fp",
        "alert_precision_ppv",
        "false_alert_share_among_predicted_alerts",
        "missed_fall_count",
        "missed_fall_rate",
        "false_positive_rate",
        "recall_sensitivity",
        "interpretation",
    ]

    with TABLE_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def create_figure(rows):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    display_labels = {
        "Clean": "Clean",
        "FGSM Attack": "FGSM\nAttack",
        "PGD Attack": "PGD\nAttack",
        "Defended Clean": "Defended\nClean",
        "Defended FGSM": "Defended\nFGSM",
        "Defended PGD": "Defended\nPGD",
    }

    labels = [display_labels[row["condition_label"]] for row in rows]
    true_alerts = [int(row["true_fall_alerts_tp"]) for row in rows]
    false_alerts = [int(row["false_fall_alerts_fp"]) for row in rows]
    missed_falls = [int(row["missed_fall_count"]) for row in rows]
    precision_values = [float(row["alert_precision_ppv"]) for row in rows]
    false_alert_share_values = [
        float(row["false_alert_share_among_predicted_alerts"]) for row in rows
    ]

    x_positions = list(range(len(labels)))

    fig, ax = plt.subplots(figsize=(15.8, 10.2))

    true_color = "#2C7FB8"
    false_color = "#F28E2B"

    ax.bar(
        x_positions,
        true_alerts,
        label="True fall alerts (TP)",
        color=true_color,
        edgecolor="black",
        linewidth=0.7,
    )

    ax.bar(
        x_positions,
        false_alerts,
        bottom=true_alerts,
        label="False fall alerts (FP)",
        color=false_color,
        edgecolor="black",
        linewidth=0.7,
    )

    ax.set_title(
        "Thesis Figure 16: Window-Level Fall Alert Composition and Trustworthiness",
        fontsize=16,
        pad=18,
    )
    ax.set_ylabel("Predicted fall alerts, count = TP + FP", fontsize=12)
    ax.set_xlabel("Condition", fontsize=12)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, fontsize=11)
    ax.legend(loc="upper left", frameon=True)

    max_alerts = max([tp + fp for tp, fp in zip(true_alerts, false_alerts)] + [1])
    ax.set_ylim(0, max_alerts * 1.55)

    ax.yaxis.grid(True, linestyle="--", linewidth=0.6, alpha=0.45)
    ax.set_axisbelow(True)

    for index, (tp, fp, fn, precision, false_share) in enumerate(
        zip(true_alerts, false_alerts, missed_falls, precision_values, false_alert_share_values)
    ):
        total_alerts = tp + fp

        if tp > 0:
            ax.text(
                index,
                tp / 2,
                f"TP={tp}",
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color="white",
            )

        if fp > 0:
            ax.text(
                index,
                tp + fp / 2,
                f"FP={fp}",
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color="black",
            )

        if total_alerts == 0:
            summary_text = f"No alerts\nFN={fn}"
        elif tp == 0 and fp > 0:
            summary_text = (
                f"PPV=0.00\n"
                f"TP=0; all alerts FP\n"
                f"FN={fn}"
            )
        else:
            summary_text = (
                f"PPV={precision:.2f}\n"
                f"FP share={false_share:.0%}\n"
                f"FN={fn}"
            )

        ax.text(
            index,
            total_alerts + max_alerts * 0.045,
            summary_text,
            ha="center",
            va="bottom",
            fontsize=9.3,
        )

    fig.text(
        0.5,
        0.112,
        (
            "Bars show predicted fall alerts only: TP + FP. "
            "Blue segments are true fall alerts; orange segments are false fall alerts."
        ),
        ha="center",
        fontsize=10.8,
    )

    fig.text(
        0.5,
        0.086,
        (
            "FN is shown above each bar as missed-fall context and is not part of the bar height. "
            "PPV = TP/(TP+FP); FP share = FP/(TP+FP)."
        ),
        ha="center",
        fontsize=10.2,
    )

    fig.text(
        0.5,
        0.061,
        (
            "PPV=0.00 with TP=0 and 'all alerts FP' means fall alerts were raised, "
            "but every predicted fall alert was false."
        ),
        ha="center",
        fontsize=10.1,
    )

    fig.text(
        0.5,
        0.037,
        (
            "Defended FGSM/PGD reduce FP count compared with matched attacks, "
            "but PPV remains 0.00 because TP remains 0."
        ),
        ha="center",
        fontsize=10.1,
    )

    fig.text(
        0.5,
        0.014,
        (
            "Claim boundary: descriptive window-level alert-trustworthiness analysis only; "
            "not clinical validation, event-level validation, false alarms per hour/day, "
            "long-lie analysis, or time-to-alarm validation."
        ),
        ha="center",
        fontsize=9.0,
    )

    fig.tight_layout(rect=[0, 0.16, 1, 1])
    fig.savefig(FIGURE_PATH, dpi=300, bbox_inches="tight", pad_inches=0.24)
    plt.close(fig)


def write_note(rows):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    key_lines = []
    for row in rows:
        key_lines.append(
            f"- {row['condition_label']}: predicted fall alerts = "
            f"{row['predicted_fall_alerts_tp_plus_fp']}, TP alerts = "
            f"{row['true_fall_alerts_tp']}, FP alerts = "
            f"{row['false_fall_alerts_fp']}, PPV = "
            f"{float(row['alert_precision_ppv']):.3f}, FP share = "
            f"{float(row['false_alert_share_among_predicted_alerts']):.3f}, "
            f"missed falls = {row['missed_fall_count']}."
        )

    key_text = "\n".join(key_lines)

    text = f"""# Thesis Table 16 and Figure 16: Alert Trustworthiness

This note documents the alert-trustworthiness analysis for the WiFi CSI Fall Attack-Safety Demo.

## Purpose

Table 16 and Figure 16 focus on predicted fall alerts.

The key question is:

```text
When the model raises a fall alert, how often is it actually a fall?
```

This is important because aggregate model accuracy does not directly tell a caregiver or reviewer whether fall alerts are trustworthy.

## Files Created

```text
Table 16:
{TABLE_PATH}

Figure 16:
{FIGURE_PATH}

Companion note:
{NOTE_PATH}
```

## Input Files

```text
{INPUT_FILES["clean"]}
{INPUT_FILES["fgsm"]}
{INPUT_FILES["pgd"]}
{INPUT_FILES["defended_clean"]}
{INPUT_FILES["defended_fgsm"]}
{INPUT_FILES["defended_pgd"]}
```

## Metric Definitions

```text
predicted fall alerts = TP + FP
true fall alerts = TP
false fall alerts = FP
alert precision / PPV = TP / (TP + FP)
false-alert share among alerts = FP / (TP + FP)
missed fall count = FN
```

## Important Figure Interpretation

Figure 16 bars show predicted fall alerts only:

```text
bar height = TP + FP
```

FN is shown above each bar as missed-fall context and is not part of the bar height.

A PPV value of 0.00 with TP = 0 and nonzero FP means the model raised fall alerts, but every predicted fall alert was false. It does not mean that the model raised no alerts.

For the tested defended FGSM and defended PGD conditions, false fall alarms were reduced compared with their matched undefended attack conditions. However, PPV remained 0.00 because TP remained 0.

## Key Findings

{key_text}

## Interpretation

This artifact strengthens the thesis because it separates three safety-relevant questions:

```text
Did the system detect real fall windows?
Were the fall alerts trustworthy when raised?
How many true fall windows were missed at the same time?
```

A model can have high or moderate aggregate accuracy while still producing clinically concerning alert behavior. For example, under the tested FGSM and PGD attack conditions, the undefended model produced fall alerts that were all false alarms while also missing all true fall windows.

The defended attacked conditions reduced false fall alarms compared with the matched undefended attacked conditions, but did not restore fall recall under the tested epsilon 0.030 attack setting.

## Claim Boundary

This is a descriptive window-level fall-alert trustworthiness analysis using binary fall-vs-non-fall predictions.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, false alarms per hour/day, long-lie validation, time-to-alarm validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
"""

    NOTE_PATH.write_text(text, encoding="utf-8")


def replace_or_append_readme_section(text, section_marker, section):
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


def update_readme():
    section_marker = "### Thesis Table 16 and Figure 16: Alert Trustworthiness"

    section = f"""
{section_marker}

Table 16 and Figure 16 add an alert-trustworthiness view focused on predicted fall alerts.

Files:

```text
results/thesis_table_16_alert_trustworthiness.csv
figures/thesis_figure_16_fall_alert_composition.png
notes/thesis_table_16_figure_16_alert_trustworthiness.md
```

Purpose:

```text
When the model raises a fall alert, how often is it actually a fall?
```

Core definitions:

```text
predicted fall alerts = TP + FP
true fall alerts = TP
false fall alerts = FP
alert precision / PPV = TP / (TP + FP)
false-alert share among alerts = FP / (TP + FP)
missed fall count = FN
```

Figure 16 bars show predicted fall alerts only:

```text
bar height = TP + FP
```

FN is shown above each bar as missed-fall context and is not part of the bar height.

Important interpretation: PPV = 0.00 with TP = 0 and nonzero false fall alerts means fall alerts were raised, but every predicted fall alert was false. It does not mean no alerts were raised.

The defended FGSM and defended PGD conditions reduced false fall alarms compared with their matched undefended attack conditions, but PPV remained 0.00 because TP remained 0.

This artifact helps separate fall-alert trustworthiness from aggregate accuracy. It shows whether fall alerts were true fall detections or false fall alarms, and it reports missed fall count alongside alert precision.

Claim boundary: this is a descriptive window-level alert-trustworthiness analysis. It is not clinical validation, medical-device validation, event-level fall validation, false alarms per hour/day, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.
"""

    if README_PATH.exists():
        text = README_PATH.read_text(encoding="utf-8")
    else:
        text = ""

    updated_text = replace_or_append_readme_section(text, section_marker, section)
    README_PATH.write_text(updated_text, encoding="utf-8")

    if section_marker in text:
        print("README Table 16 / Figure 16 section replaced.")
    else:
        print("README updated with Table 16 / Figure 16 section.")


def main():
    print("Creating Thesis Table 16 and Figure 16...")

    rows = build_table_rows()
    write_table(rows)
    create_figure(rows)
    write_note(rows)
    update_readme()

    print("\nCreated outputs:")
    print(f"- {TABLE_PATH}")
    print(f"- {FIGURE_PATH}")
    print(f"- {NOTE_PATH}")
    print("- README.md updated")

    print("\nAlert trustworthiness summary:")
    for row in rows:
        print(
            f"- {row['condition_label']}: alerts={row['predicted_fall_alerts_tp_plus_fp']}, "
            f"TP={row['true_fall_alerts_tp']}, FP={row['false_fall_alerts_fp']}, "
            f"PPV={float(row['alert_precision_ppv']):.3f}, "
            f"FP share={float(row['false_alert_share_among_predicted_alerts']):.3f}, "
            f"FN={row['missed_fall_count']}"
        )


if __name__ == "__main__":
    main()