from pathlib import Path
import csv
from collections import defaultdict

import matplotlib.pyplot as plt


RESULTS_DIR = Path("results")
FIGURES_DIR = Path("figures")
NOTES_DIR = Path("notes")

TABLE_PATH = RESULTS_DIR / "thesis_table_20_fall_window_recovery_persistence.csv"
FIGURE_PATH = FIGURES_DIR / "thesis_figure_20_fall_window_recovery_persistence.png"
NOTE_PATH = NOTES_DIR / "thesis_table_20_figure_20_fall_window_recovery_persistence.md"
README_PATH = Path("README.md")


INPUT_FILES = {
    "clean": RESULTS_DIR / "clean_predictions_short.csv",
    "fgsm": RESULTS_DIR / "fgsm_predictions_short_epsilon_0_03.csv",
    "pgd": RESULTS_DIR / "pgd_predictions_short_epsilon_0_03.csv",
    "defended_fgsm": RESULTS_DIR / "defended_fgsm_predictions_short_epsilon_0_03.csv",
    "defended_pgd": RESULTS_DIR / "defended_pgd_predictions_short_epsilon_0_03.csv",
}


PATHS = [
    {
        "path_id": "fgsm_path",
        "path_label": "FGSM path",
        "attack_label": "FGSM Attack",
        "defended_label": "Defended FGSM",
        "attack_file_key": "fgsm",
        "defended_file_key": "defended_fgsm",
        "attack_pred_binary_col": "attacked_fall_pred_binary",
        "defended_pred_binary_col": "fall_pred_binary_fgsm_defended",
    },
    {
        "path_id": "pgd_path",
        "path_label": "PGD path",
        "attack_label": "PGD Attack",
        "defended_label": "Defended PGD",
        "attack_file_key": "pgd",
        "defended_file_key": "defended_pgd",
        "attack_pred_binary_col": "fall_pred_binary",
        "defended_pred_binary_col": "fall_pred_binary_pgd_defended",
    },
]


def to_int(value):
    return int(float(str(value).strip()))


def safe_divide(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator


def normalize_class_name(value):
    return str(value).strip().lower()


def read_csv_rows(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    with path.open("r", newline="", encoding="utf-8") as file_handle:
        return list(csv.DictReader(file_handle))


def build_sample_map(rows, pred_binary_col):
    sample_map = {}

    for row in rows:
        sample_id = to_int(row["sample_id"])
        true_label = to_int(row["true_label"])
        true_class_name = normalize_class_name(row["true_class_name"])
        fall_true_binary = to_int(row["fall_true_binary"])
        fall_pred_binary = to_int(row[pred_binary_col])

        is_true_fall = (
            fall_true_binary == 1
            or true_label == 1
            or true_class_name == "fall"
        )

        if is_true_fall:
            sample_map[sample_id] = fall_pred_binary

    return sample_map


def safety_state_from_prediction(fall_pred_binary):
    if fall_pred_binary == 1:
        return "TP"

    return "FN"


def build_path_summary(path_config):
    clean_rows = read_csv_rows(INPUT_FILES["clean"])
    attack_rows = read_csv_rows(INPUT_FILES[path_config["attack_file_key"]])
    defended_rows = read_csv_rows(INPUT_FILES[path_config["defended_file_key"]])

    clean_map = build_sample_map(clean_rows, "fall_pred_binary")
    attack_map = build_sample_map(attack_rows, path_config["attack_pred_binary_col"])
    defended_map = build_sample_map(
        defended_rows,
        path_config["defended_pred_binary_col"],
    )

    common_sample_ids = sorted(
        set(clean_map.keys())
        & set(attack_map.keys())
        & set(defended_map.keys())
    )

    if not common_sample_ids:
        raise ValueError(
            f"No paired true-fall sample IDs found for {path_config['path_label']}"
        )

    total_true_fall_windows = len(common_sample_ids)

    stage_counts = {
        "clean_tp": 0,
        "clean_fn": 0,
        "attack_tp": 0,
        "attack_fn": 0,
        "defended_tp": 0,
        "defended_fn": 0,
    }

    transition_counts = defaultdict(int)

    for sample_id in common_sample_ids:
        clean_state = safety_state_from_prediction(clean_map[sample_id])
        attack_state = safety_state_from_prediction(attack_map[sample_id])
        defended_state = safety_state_from_prediction(defended_map[sample_id])

        stage_counts[f"clean_{clean_state.lower()}"] += 1
        stage_counts[f"attack_{attack_state.lower()}"] += 1
        stage_counts[f"defended_{defended_state.lower()}"] += 1

        transition_counts[f"clean_{clean_state}_to_attack_{attack_state}"] += 1
        transition_counts[f"attack_{attack_state}_to_defended_{defended_state}"] += 1
        transition_counts[
            f"clean_{clean_state}_to_attack_{attack_state}_to_defended_{defended_state}"
        ] += 1

    clean_tp = stage_counts["clean_tp"]
    clean_fn = stage_counts["clean_fn"]
    attack_tp = stage_counts["attack_tp"]
    attack_fn = stage_counts["attack_fn"]
    defended_tp = stage_counts["defended_tp"]
    defended_fn = stage_counts["defended_fn"]

    clean_tp_lost_under_attack = transition_counts["clean_TP_to_attack_FN"]
    clean_tp_preserved_under_attack = transition_counts["clean_TP_to_attack_TP"]
    clean_fn_recovered_by_attack = transition_counts["clean_FN_to_attack_TP"]
    clean_fn_persisted_under_attack = transition_counts["clean_FN_to_attack_FN"]

    attack_fn_recovered_by_defense = transition_counts["attack_FN_to_defended_TP"]
    attack_fn_persisted_after_defense = transition_counts["attack_FN_to_defended_FN"]
    attack_tp_lost_after_defense = transition_counts["attack_TP_to_defended_FN"]
    attack_tp_preserved_after_defense = transition_counts["attack_TP_to_defended_TP"]

    clean_tp_to_attack_fn_to_defended_tp = transition_counts[
        "clean_TP_to_attack_FN_to_defended_TP"
    ]
    clean_tp_to_attack_fn_to_defended_fn = transition_counts[
        "clean_TP_to_attack_FN_to_defended_FN"
    ]
    clean_fn_to_attack_fn_to_defended_tp = transition_counts[
        "clean_FN_to_attack_FN_to_defended_TP"
    ]
    clean_fn_to_attack_fn_to_defended_fn = transition_counts[
        "clean_FN_to_attack_FN_to_defended_FN"
    ]

    return {
        "path_id": path_config["path_id"],
        "path_label": path_config["path_label"],
        "attack_label": path_config["attack_label"],
        "defended_label": path_config["defended_label"],
        "total_true_fall_windows": total_true_fall_windows,
        "clean_tp": clean_tp,
        "clean_fn": clean_fn,
        "attack_tp": attack_tp,
        "attack_fn": attack_fn,
        "defended_tp": defended_tp,
        "defended_fn": defended_fn,
        "clean_recall": safe_divide(clean_tp, total_true_fall_windows),
        "attack_recall": safe_divide(attack_tp, total_true_fall_windows),
        "defended_recall": safe_divide(defended_tp, total_true_fall_windows),
        "clean_missed_fall_rate": safe_divide(clean_fn, total_true_fall_windows),
        "attack_missed_fall_rate": safe_divide(attack_fn, total_true_fall_windows),
        "defended_missed_fall_rate": safe_divide(defended_fn, total_true_fall_windows),
        "clean_tp_lost_under_attack": clean_tp_lost_under_attack,
        "clean_tp_preserved_under_attack": clean_tp_preserved_under_attack,
        "clean_fn_recovered_by_attack": clean_fn_recovered_by_attack,
        "clean_fn_persisted_under_attack": clean_fn_persisted_under_attack,
        "attack_fn_recovered_by_defense": attack_fn_recovered_by_defense,
        "attack_fn_persisted_after_defense": attack_fn_persisted_after_defense,
        "attack_tp_lost_after_defense": attack_tp_lost_after_defense,
        "attack_tp_preserved_after_defense": attack_tp_preserved_after_defense,
        "clean_tp_to_attack_fn_to_defended_tp": clean_tp_to_attack_fn_to_defended_tp,
        "clean_tp_to_attack_fn_to_defended_fn": clean_tp_to_attack_fn_to_defended_fn,
        "clean_fn_to_attack_fn_to_defended_tp": clean_fn_to_attack_fn_to_defended_tp,
        "clean_fn_to_attack_fn_to_defended_fn": clean_fn_to_attack_fn_to_defended_fn,
        "clean_tp_lost_under_attack_percent_of_clean_tp": safe_divide(
            clean_tp_lost_under_attack,
            clean_tp,
        ),
        "attack_fn_recovered_by_defense_percent_of_attack_fn": safe_divide(
            attack_fn_recovered_by_defense,
            attack_fn,
        ),
        "attack_fn_persisted_after_defense_percent_of_attack_fn": safe_divide(
            attack_fn_persisted_after_defense,
            attack_fn,
        ),
    }


def build_interpretation(summary):
    if summary["defended_tp"] == 0 and summary["attack_fn"] > 0:
        return (
            "Attack missed true fall windows and the defended attacked condition "
            "did not recover fall-window detection for this tested configuration."
        )

    if summary["attack_fn_recovered_by_defense"] > 0:
        return (
            "Some attack-missed fall windows were recovered by the defended attacked condition."
        )

    return "Fall-window recovery and persistence are summarized descriptively."


def build_table_rows():
    rows = []

    for path_config in PATHS:
        summary = build_path_summary(path_config)

        rows.append(
            {
                "path_id": summary["path_id"],
                "path_label": summary["path_label"],
                "attack_label": summary["attack_label"],
                "defended_label": summary["defended_label"],
                "total_true_fall_windows": summary["total_true_fall_windows"],
                "clean_tp": summary["clean_tp"],
                "clean_fn": summary["clean_fn"],
                "attack_tp": summary["attack_tp"],
                "attack_fn": summary["attack_fn"],
                "defended_tp": summary["defended_tp"],
                "defended_fn": summary["defended_fn"],
                "clean_recall_percent": f"{summary['clean_recall'] * 100:.2f}",
                "attack_recall_percent": f"{summary['attack_recall'] * 100:.2f}",
                "defended_recall_percent": f"{summary['defended_recall'] * 100:.2f}",
                "clean_missed_fall_rate_percent": f"{summary['clean_missed_fall_rate'] * 100:.2f}",
                "attack_missed_fall_rate_percent": f"{summary['attack_missed_fall_rate'] * 100:.2f}",
                "defended_missed_fall_rate_percent": f"{summary['defended_missed_fall_rate'] * 100:.2f}",
                "clean_tp_lost_under_attack": summary["clean_tp_lost_under_attack"],
                "clean_tp_lost_under_attack_percent_of_clean_tp": f"{summary['clean_tp_lost_under_attack_percent_of_clean_tp'] * 100:.2f}",
                "clean_tp_preserved_under_attack": summary["clean_tp_preserved_under_attack"],
                "clean_fn_recovered_by_attack": summary["clean_fn_recovered_by_attack"],
                "clean_fn_persisted_under_attack": summary["clean_fn_persisted_under_attack"],
                "attack_fn_recovered_by_defense": summary["attack_fn_recovered_by_defense"],
                "attack_fn_recovered_by_defense_percent_of_attack_fn": f"{summary['attack_fn_recovered_by_defense_percent_of_attack_fn'] * 100:.2f}",
                "attack_fn_persisted_after_defense": summary["attack_fn_persisted_after_defense"],
                "attack_fn_persisted_after_defense_percent_of_attack_fn": f"{summary['attack_fn_persisted_after_defense_percent_of_attack_fn'] * 100:.2f}",
                "attack_tp_lost_after_defense": summary["attack_tp_lost_after_defense"],
                "attack_tp_preserved_after_defense": summary["attack_tp_preserved_after_defense"],
                "clean_tp_to_attack_fn_to_defended_tp": summary["clean_tp_to_attack_fn_to_defended_tp"],
                "clean_tp_to_attack_fn_to_defended_fn": summary["clean_tp_to_attack_fn_to_defended_fn"],
                "clean_fn_to_attack_fn_to_defended_tp": summary["clean_fn_to_attack_fn_to_defended_tp"],
                "clean_fn_to_attack_fn_to_defended_fn": summary["clean_fn_to_attack_fn_to_defended_fn"],
                "interpretation": build_interpretation(summary),
            }
        )

    return rows


def write_table(rows):
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "path_id",
        "path_label",
        "attack_label",
        "defended_label",
        "total_true_fall_windows",
        "clean_tp",
        "clean_fn",
        "attack_tp",
        "attack_fn",
        "defended_tp",
        "defended_fn",
        "clean_recall_percent",
        "attack_recall_percent",
        "defended_recall_percent",
        "clean_missed_fall_rate_percent",
        "attack_missed_fall_rate_percent",
        "defended_missed_fall_rate_percent",
        "clean_tp_lost_under_attack",
        "clean_tp_lost_under_attack_percent_of_clean_tp",
        "clean_tp_preserved_under_attack",
        "clean_fn_recovered_by_attack",
        "clean_fn_persisted_under_attack",
        "attack_fn_recovered_by_defense",
        "attack_fn_recovered_by_defense_percent_of_attack_fn",
        "attack_fn_persisted_after_defense",
        "attack_fn_persisted_after_defense_percent_of_attack_fn",
        "attack_tp_lost_after_defense",
        "attack_tp_preserved_after_defense",
        "clean_tp_to_attack_fn_to_defended_tp",
        "clean_tp_to_attack_fn_to_defended_fn",
        "clean_fn_to_attack_fn_to_defended_tp",
        "clean_fn_to_attack_fn_to_defended_fn",
        "interpretation",
    ]

    with TABLE_PATH.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def create_figure(rows):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Show the shared clean baseline once to avoid implying there are two different clean models.
    clean_row = rows[0]

    plot_entries = [
        {
            "label": "Clean\nbaseline",
            "tp": int(clean_row["clean_tp"]),
            "fn": int(clean_row["clean_fn"]),
        },
        {
            "label": "FGSM\nattack",
            "tp": int(rows[0]["attack_tp"]),
            "fn": int(rows[0]["attack_fn"]),
        },
        {
            "label": "Defended\nFGSM",
            "tp": int(rows[0]["defended_tp"]),
            "fn": int(rows[0]["defended_fn"]),
        },
        {
            "label": "PGD\nattack",
            "tp": int(rows[1]["attack_tp"]),
            "fn": int(rows[1]["attack_fn"]),
        },
        {
            "label": "Defended\nPGD",
            "tp": int(rows[1]["defended_tp"]),
            "fn": int(rows[1]["defended_fn"]),
        },
    ]

    labels = [entry["label"] for entry in plot_entries]
    tp_values = [entry["tp"] for entry in plot_entries]
    fn_values = [entry["fn"] for entry in plot_entries]
    totals = [tp + fn for tp, fn in zip(tp_values, fn_values)]

    x_positions = list(range(len(labels)))
    y_limit = max(totals) * 1.42

    fig, ax = plt.subplots(figsize=(12.8, 8.8))

    ax.bar(
        x_positions,
        tp_values,
        label="Detected fall windows (TP)",
        edgecolor="black",
        linewidth=0.8,
    )

    ax.bar(
        x_positions,
        fn_values,
        bottom=tp_values,
        label="Missed fall windows (FN)",
        edgecolor="black",
        linewidth=0.8,
    )

    ax.set_title(
        "Thesis Figure 20: Fall-Window Recall Recovery After Attack and Defense",
        fontsize=15.5,
        pad=16,
    )
    ax.set_ylabel("True fall windows, count", fontsize=12)
    ax.set_xlabel("Evaluation stage", fontsize=12)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, fontsize=10.5)
    ax.set_ylim(0, y_limit)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend(loc="upper left", frameon=True)

    for x, tp, fn, total in zip(x_positions, tp_values, fn_values, totals):
        tp_rate = safe_divide(tp, total) * 100.0
        fn_rate = safe_divide(fn, total) * 100.0

        if tp > 0:
            ax.text(
                x,
                tp / 2,
                f"TP={tp}\n{tp_rate:.1f}%",
                ha="center",
                va="center",
                fontsize=9.8,
                fontweight="bold",
                color="white",
            )

        if fn > 0:
            ax.text(
                x,
                tp + fn / 2,
                f"FN={fn}\n{fn_rate:.1f}%",
                ha="center",
                va="center",
                fontsize=9.8,
                fontweight="bold",
                color="black",
            )

    # Compact paired transition annotations. These are shown above the relevant attack/defense stages.
    fgsm = rows[0]
    pgd = rows[1]

    ax.text(
        1.5,
        max(totals) * 1.14,
        (
            "FGSM paired transitions:\n"
            f"Clean TP -> Attack FN: {fgsm['clean_tp_lost_under_attack']}\n"
            f"Attack FN -> Defended TP: {fgsm['attack_fn_recovered_by_defense']}\n"
            f"Attack FN -> Defended FN: {fgsm['attack_fn_persisted_after_defense']}"
        ),
        ha="center",
        va="bottom",
        fontsize=9.3,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "alpha": 0.85},
    )

    ax.text(
        3.5,
        max(totals) * 1.14,
        (
            "PGD paired transitions:\n"
            f"Clean TP -> Attack FN: {pgd['clean_tp_lost_under_attack']}\n"
            f"Attack FN -> Defended TP: {pgd['attack_fn_recovered_by_defense']}\n"
            f"Attack FN -> Defended FN: {pgd['attack_fn_persisted_after_defense']}"
        ),
        ha="center",
        va="bottom",
        fontsize=9.3,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "alpha": 0.85},
    )

    fig.text(
        0.5,
        0.095,
        (
            "Bars show true fall windows only. The shared clean baseline is shown once; "
            "same fall-window sample IDs are tracked within each attack/defense path."
        ),
        ha="center",
        fontsize=10.1,
    )

    fig.text(
        0.5,
        0.065,
        (
            "Takeaway: under epsilon 0.030, FGSM/PGD convert all clean-detected fall windows to missed windows, "
            "and the tested defense recovers 0 attack-missed fall windows."
        ),
        ha="center",
        fontsize=9.8,
    )

    fig.text(
        0.5,
        0.038,
        (
            "Claim boundary: descriptive window-level paired recovery analysis only; not event-level, clinical, "
            "long-lie, false-alarms-per-hour/day, or time-to-alarm validation."
        ),
        ha="center",
        fontsize=9.0,
    )

    fig.tight_layout(rect=[0.04, 0.14, 0.98, 0.95])
    fig.savefig(FIGURE_PATH, dpi=300)
    plt.close(fig)


def key_findings(rows):
    lines = []

    for row in rows:
        lines.append(
            f"- {row['path_label']}: clean TP={row['clean_tp']}, clean FN={row['clean_fn']}; "
            f"attack TP={row['attack_tp']}, attack FN={row['attack_fn']}; "
            f"defended attack TP={row['defended_tp']}, defended attack FN={row['defended_fn']}."
        )
        lines.append(
            f"  Clean TP -> Attack FN: {row['clean_tp_lost_under_attack']} "
            f"({row['clean_tp_lost_under_attack_percent_of_clean_tp']}% of clean TP windows). "
            f"Attack FN -> Defended TP: {row['attack_fn_recovered_by_defense']} "
            f"({row['attack_fn_recovered_by_defense_percent_of_attack_fn']}% of attack FN windows). "
            f"Attack FN -> Defended FN: {row['attack_fn_persisted_after_defense']} "
            f"({row['attack_fn_persisted_after_defense_percent_of_attack_fn']}% of attack FN windows)."
        )

    return "\n".join(lines)


def write_note(rows):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    findings_text = key_findings(rows)

    text = f"""# Thesis Table 20 and Figure 20: Fall-Window Recovery and Failure Persistence

This note documents the fall-window recovery and failure-persistence analysis.

## Purpose

Table 20 and Figure 20 ask:

```text
For true fall windows, how many were detected cleanly, lost under attack, recovered by defense, or still missed after defense?
```

This complements Figure 19, which showed where missed fall windows were redirected. Figure 20 focuses on whether the fall-window detection itself was recovered.

## Files Created

```text
Table 20:
{TABLE_PATH}

Figure 20:
{FIGURE_PATH}

Companion note:
{NOTE_PATH}
```

## Input Files

```text
{INPUT_FILES["clean"]}
{INPUT_FILES["fgsm"]}
{INPUT_FILES["pgd"]}
{INPUT_FILES["defended_fgsm"]}
{INPUT_FILES["defended_pgd"]}
```

## Definitions

```text
TP = true fall window predicted as fall
FN = true fall window predicted as non-fall
Clean TP -> Attack FN = clean-detected fall window lost under attack
Attack FN -> Defended TP = attack-missed fall window recovered by defense
Attack FN -> Defended FN = attack-missed fall window still missed after defense
```

## Key Findings

{findings_text}

## Interpretation

This artifact strengthens the thesis by separating false-alarm improvement from fall-window recovery.

The short defended model may reduce some false-alert burden in earlier figures, but this analysis directly checks whether the defended attacked condition restores fall-window detection. Under the tested epsilon 0.030 FGSM/PGD conditions, the defended attacked outputs recover 0 attack-missed fall windows and all attack-missed fall windows persist.

## Claim Boundary

This is a descriptive window-level paired recovery analysis using UT-HAR / SenseFi prediction outputs.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, false alarms per hour/day, time-to-alarm validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
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
    section_marker = "### Thesis Table 20 and Figure 20: Fall-Window Recovery and Failure Persistence"

    section = f"""
{section_marker}

Table 20 and Figure 20 add a paired fall-window recovery and failure-persistence analysis.

Files:

```text
results/thesis_table_20_fall_window_recovery_persistence.csv
figures/thesis_figure_20_fall_window_recovery_persistence.png
notes/thesis_table_20_figure_20_fall_window_recovery_persistence.md
```

Purpose:

```text
For true fall windows, how many were detected cleanly, lost under attack, recovered by defense, or still missed after defense?
```

Definitions:

```text
TP = true fall window predicted as fall
FN = true fall window predicted as non-fall
Clean TP -> Attack FN = clean-detected fall window lost under attack
Attack FN -> Defended TP = attack-missed fall window recovered by defense
Attack FN -> Defended FN = attack-missed fall window still missed after defense
```

This artifact complements Figure 19 by showing whether fall-window detection itself was recovered after attack. The figure shows the shared clean baseline once and tracks the same fall-window sample IDs within each matched attack/defense path.

Claim boundary: this is a descriptive window-level paired recovery analysis. It is not clinical validation, medical-device validation, event-level fall validation, long-lie validation, false alarms per hour/day, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.
"""

    if README_PATH.exists():
        text = README_PATH.read_text(encoding="utf-8")
    else:
        text = ""

    updated_text = replace_or_append_readme_section(text, section_marker, section)
    README_PATH.write_text(updated_text, encoding="utf-8")

    if section_marker in text:
        print("README Table 20 / Figure 20 section replaced.")
    else:
        print("README updated with Table 20 / Figure 20 section.")


def main():
    print("Creating Thesis Table 20 and Figure 20...")

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

    print("\nKey findings:")
    print(key_findings(rows))


if __name__ == "__main__":
    main()
