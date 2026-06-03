from pathlib import Path
import csv
import math


# ============================================================
# Thesis Table 2: Attack Impact Delta Table
#
# Purpose:
# Compare clean baseline safety-proxy metrics against FGSM and
# PGD attacked safety-proxy metrics.
#
# Important fix:
# The FGSM metrics CSV contains multiple scenarios:
# clean, fgsm_attacked, and delta_attacked_minus_clean.
# This script explicitly reads only fgsm_attacked for the
# FGSM attacked row.
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
NOTES_DIR = ROOT / "notes"

RESULTS_DIR.mkdir(exist_ok=True)
NOTES_DIR.mkdir(exist_ok=True)

CLEAN_METRICS_FILE = RESULTS_DIR / "clean_safety_proxy_metrics.csv"
FGSM_METRICS_FILE = RESULTS_DIR / "fgsm_safety_proxy_metrics_epsilon_0_03.csv"
PGD_METRICS_FILE = RESULTS_DIR / "pgd_safety_proxy_metrics_epsilon_0_03.csv"

FGSM_SWEEP_FILE = RESULTS_DIR / "fgsm_epsilon_sweep_summary.csv"
PGD_SWEEP_FILE = RESULTS_DIR / "pgd_epsilon_sweep_summary.csv"

OUTPUT_CSV = RESULTS_DIR / "thesis_table_2_attack_impact_delta.csv"
OUTPUT_MD = NOTES_DIR / "thesis_table_2_attack_impact_delta.md"


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


def read_metric_value_file(path):
    """
    Read simple metric,value CSV files.
    Used for clean_safety_proxy_metrics.csv.
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    metrics = {}

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            key = normalize_key(row.get("metric", ""))
            value = to_float(row.get("value", ""))

            if key:
                metrics[key] = value

    return metrics


def read_scenario_metric_file(path, scenario_name):
    """
    Read scenario,epsilon,metric,value CSV files.
    Used for fgsm_safety_proxy_metrics_epsilon_0_03.csv.

    This prevents accidentally reading delta rows as attacked rows.
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    metrics = {}

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            scenario = str(row.get("scenario", "")).strip()

            if scenario != scenario_name:
                continue

            key = normalize_key(row.get("metric", ""))
            value = to_float(row.get("value", ""))

            if key:
                metrics[key] = value

    if not metrics:
        raise ValueError(f"No metrics found for scenario '{scenario_name}' in {path}")

    return metrics


def read_pgd_wide_file(path):
    """
    Read one-row wide PGD metrics file.
    Used for pgd_safety_proxy_metrics_epsilon_0_03.csv.
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError(f"No rows found in {path}")

    row = rows[0]
    metrics = {}

    for key, value in row.items():
        metrics[normalize_key(key)] = to_float(value)

    return metrics


def get_metric(metrics, aliases):
    for alias in aliases:
        key = normalize_key(alias)

        if key in metrics:
            return metrics[key]

    available = ", ".join(sorted(metrics.keys()))
    raise KeyError(
        f"Could not find any aliases {aliases}. "
        f"Available metrics: {available}"
    )


def read_prediction_change_rate(path, epsilon_value=0.03):
    """
    Read prediction_change_rate from an epsilon sweep summary CSV.
    """
    if not path.exists():
        return None

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return None

    field_map = {normalize_key(name): name for name in reader.fieldnames}

    epsilon_col = None
    for possible in ["epsilon", "eps", "attack_epsilon"]:
        if possible in field_map:
            epsilon_col = field_map[possible]
            break

    prediction_change_col = None
    for possible in [
        "prediction_change_rate",
        "prediction_changed_rate",
        "changed_prediction_rate",
        "prediction_change",
    ]:
        if possible in field_map:
            prediction_change_col = field_map[possible]
            break

    if epsilon_col is None or prediction_change_col is None:
        return None

    for row in rows:
        row_epsilon = to_float(row.get(epsilon_col))

        if row_epsilon is not None and math.isclose(
            row_epsilon,
            epsilon_value,
            rel_tol=1e-6,
            abs_tol=1e-6,
        ):
            return to_float(row.get(prediction_change_col))

    return None


def fmt_decimal(value, digits=4):
    if value is None:
        return "NA"
    return f"{value:.{digits}f}"


def fmt_integer(value):
    if value is None:
        return "NA"
    return str(int(round(value)))


def build_delta_row(attack_name, clean_metrics, attack_metrics, prediction_change_rate):
    clean_missed_fall_rate = get_metric(
        clean_metrics,
        ["missed_fall_rate", "false_negative_rate", "fnr"],
    )

    attack_missed_fall_rate = get_metric(
        attack_metrics,
        ["missed_fall_rate", "false_negative_rate", "fnr"],
    )

    clean_recall = get_metric(
        clean_metrics,
        ["recall_sensitivity", "recall", "sensitivity", "true_positive_rate", "tpr"],
    )

    attack_recall = get_metric(
        attack_metrics,
        ["recall_sensitivity", "recall", "sensitivity", "true_positive_rate", "tpr"],
    )

    clean_f1 = get_metric(
        clean_metrics,
        ["f1_score", "f1"],
    )

    attack_f1 = get_metric(
        attack_metrics,
        ["f1_score", "f1"],
    )

    clean_false_alarms = get_metric(
        clean_metrics,
        ["false_alarm_count", "false_positive_false_fall_alarm", "fp_false_fall_alarms", "false_alarms", "fp"],
    )

    attack_false_alarms = get_metric(
        attack_metrics,
        ["false_alarm_count", "false_positive_false_fall_alarm", "fp_false_fall_alarms", "false_alarms", "fp"],
    )

    clean_balanced_accuracy = get_metric(
        clean_metrics,
        ["balanced_accuracy"],
    )

    attack_balanced_accuracy = get_metric(
        attack_metrics,
        ["balanced_accuracy"],
    )

    return {
        "comparison": f"Clean vs {attack_name}",
        "attack": attack_name,
        "epsilon": "0.030",
        "clean_missed_fall_rate": clean_missed_fall_rate,
        "attacked_missed_fall_rate": attack_missed_fall_rate,
        "missed_fall_rate_change": attack_missed_fall_rate - clean_missed_fall_rate,
        "clean_recall_sensitivity": clean_recall,
        "attacked_recall_sensitivity": attack_recall,
        "recall_sensitivity_change": attack_recall - clean_recall,
        "clean_f1_score": clean_f1,
        "attacked_f1_score": attack_f1,
        "f1_score_change": attack_f1 - clean_f1,
        "clean_false_alarm_count": clean_false_alarms,
        "attacked_false_alarm_count": attack_false_alarms,
        "false_alarm_count_change": attack_false_alarms - clean_false_alarms,
        "clean_balanced_accuracy": clean_balanced_accuracy,
        "attacked_balanced_accuracy": attack_balanced_accuracy,
        "balanced_accuracy_change": attack_balanced_accuracy - clean_balanced_accuracy,
        "prediction_change_rate": prediction_change_rate,
    }


def write_csv(rows):
    fieldnames = [
        "comparison",
        "attack",
        "epsilon",
        "clean_missed_fall_rate",
        "attacked_missed_fall_rate",
        "missed_fall_rate_change",
        "clean_recall_sensitivity",
        "attacked_recall_sensitivity",
        "recall_sensitivity_change",
        "clean_f1_score",
        "attacked_f1_score",
        "f1_score_change",
        "clean_false_alarm_count",
        "attacked_false_alarm_count",
        "false_alarm_count_change",
        "clean_balanced_accuracy",
        "attacked_balanced_accuracy",
        "balanced_accuracy_change",
        "prediction_change_rate",
    ]

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    "comparison": row["comparison"],
                    "attack": row["attack"],
                    "epsilon": row["epsilon"],
                    "clean_missed_fall_rate": fmt_decimal(row["clean_missed_fall_rate"]),
                    "attacked_missed_fall_rate": fmt_decimal(row["attacked_missed_fall_rate"]),
                    "missed_fall_rate_change": fmt_decimal(row["missed_fall_rate_change"]),
                    "clean_recall_sensitivity": fmt_decimal(row["clean_recall_sensitivity"]),
                    "attacked_recall_sensitivity": fmt_decimal(row["attacked_recall_sensitivity"]),
                    "recall_sensitivity_change": fmt_decimal(row["recall_sensitivity_change"]),
                    "clean_f1_score": fmt_decimal(row["clean_f1_score"]),
                    "attacked_f1_score": fmt_decimal(row["attacked_f1_score"]),
                    "f1_score_change": fmt_decimal(row["f1_score_change"]),
                    "clean_false_alarm_count": fmt_integer(row["clean_false_alarm_count"]),
                    "attacked_false_alarm_count": fmt_integer(row["attacked_false_alarm_count"]),
                    "false_alarm_count_change": fmt_integer(row["false_alarm_count_change"]),
                    "clean_balanced_accuracy": fmt_decimal(row["clean_balanced_accuracy"]),
                    "attacked_balanced_accuracy": fmt_decimal(row["attacked_balanced_accuracy"]),
                    "balanced_accuracy_change": fmt_decimal(row["balanced_accuracy_change"]),
                    "prediction_change_rate": fmt_decimal(row["prediction_change_rate"]),
                }
            )


def write_markdown(rows):
    lines = []

    lines.append("# Thesis Table 2: Attack Impact Delta Table")
    lines.append("")
    lines.append("This table compares the clean SenseFi UT-HAR LeNet baseline against the software-level FGSM and PGD attacked conditions using window-level fall-vs-non-fall safety-proxy metrics.")
    lines.append("")
    lines.append("The purpose is to show how adversarial perturbations change safety-relevant proxy metrics such as missed fall rate, recall/sensitivity, F1-score, false fall alarm count, balanced accuracy, and prediction change rate.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append("This is a research implementation using window-level safety-proxy metrics. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.")
    lines.append("")
    lines.append("## Table")
    lines.append("")
    lines.append("| Comparison | Epsilon | Missed Fall Rate Change | Recall/Sensitivity Change | F1-Score Change | False Alarm Count Change | Balanced Accuracy Change | Prediction Change Rate |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")

    for row in rows:
        lines.append(
            "| "
            f"{row['comparison']} | "
            f"{row['epsilon']} | "
            f"{fmt_decimal(row['missed_fall_rate_change'])} | "
            f"{fmt_decimal(row['recall_sensitivity_change'])} | "
            f"{fmt_decimal(row['f1_score_change'])} | "
            f"{fmt_integer(row['false_alarm_count_change'])} | "
            f"{fmt_decimal(row['balanced_accuracy_change'])} | "
            f"{fmt_decimal(row['prediction_change_rate'])} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("At epsilon 0.030, both FGSM and PGD increased the missed fall rate from the clean baseline and reduced recall/sensitivity and F1-score. Both attacks also increased the number of false fall alarms. This table translates attack impact into fall-safety proxy terms instead of relying only on aggregate seven-class accuracy.")
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `results/thesis_table_2_attack_impact_delta.csv`")
    lines.append("- `notes/thesis_table_2_attack_impact_delta.md`")
    lines.append("")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    clean_metrics = read_metric_value_file(CLEAN_METRICS_FILE)

    fgsm_metrics = read_scenario_metric_file(
        FGSM_METRICS_FILE,
        scenario_name="fgsm_attacked",
    )

    pgd_metrics = read_pgd_wide_file(PGD_METRICS_FILE)

    fgsm_prediction_change_rate = read_prediction_change_rate(
        FGSM_SWEEP_FILE,
        epsilon_value=0.03,
    )

    pgd_prediction_change_rate = read_prediction_change_rate(
        PGD_SWEEP_FILE,
        epsilon_value=0.03,
    )

    rows = [
        build_delta_row(
            "FGSM",
            clean_metrics,
            fgsm_metrics,
            fgsm_prediction_change_rate,
        ),
        build_delta_row(
            "PGD",
            clean_metrics,
            pgd_metrics,
            pgd_prediction_change_rate,
        ),
    ]

    write_csv(rows)
    write_markdown(rows)

    print("Created corrected Thesis Table 2 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_MD}")
    print("")
    print("Summary:")
    for row in rows:
        print(
            f"  {row['comparison']}: "
            f"missed_fall_rate_change={fmt_decimal(row['missed_fall_rate_change'])}, "
            f"recall_sensitivity_change={fmt_decimal(row['recall_sensitivity_change'])}, "
            f"f1_score_change={fmt_decimal(row['f1_score_change'])}, "
            f"false_alarm_count_change={fmt_integer(row['false_alarm_count_change'])}, "
            f"balanced_accuracy_change={fmt_decimal(row['balanced_accuracy_change'])}, "
            f"prediction_change_rate={fmt_decimal(row['prediction_change_rate'])}"
        )


if __name__ == "__main__":
    main()