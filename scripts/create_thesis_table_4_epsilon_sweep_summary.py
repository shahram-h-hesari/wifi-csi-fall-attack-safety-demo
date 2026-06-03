from pathlib import Path
import csv


# ============================================================
# Thesis Table 4: Epsilon Sweep Summary Table
#
# Purpose:
# Summarize FGSM and PGD epsilon sweep results side by side.
#
# This table shows the dose-response relationship between
# perturbation strength and fall-safety degradation.
#
# Inputs:
# - results/fgsm_epsilon_sweep_summary.csv
# - results/pgd_epsilon_sweep_summary.csv
#
# Outputs:
# - results/thesis_table_4_epsilon_sweep_summary.csv
# - notes/thesis_table_4_epsilon_sweep_summary.md
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

FGSM_INPUT = RESULTS_DIR / "fgsm_epsilon_sweep_summary.csv"
PGD_INPUT = RESULTS_DIR / "pgd_epsilon_sweep_summary.csv"

OUTPUT_CSV = RESULTS_DIR / "thesis_table_4_epsilon_sweep_summary.csv"
OUTPUT_MD = NOTES_DIR / "thesis_table_4_epsilon_sweep_summary.md"


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


def fmt_decimal(value, digits=4):
    if value is None:
        return "NA"

    return f"{value:.{digits}f}"


def fmt_integer(value):
    if value is None:
        return "NA"

    return str(int(round(value)))


def read_sweep_file(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    rows = []

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for raw_row in reader:
            row = {}

            for key, value in raw_row.items():
                row[normalize_key(key)] = to_float(value)

            rows.append(row)

    if not rows:
        raise ValueError(f"No rows found in file: {path}")

    rows = sorted(rows, key=lambda item: item["epsilon"])

    return rows


def get_value(row, aliases):
    for alias in aliases:
        key = normalize_key(alias)

        if key in row:
            return row[key]

    available = ", ".join(sorted(row.keys()))
    raise KeyError(
        f"Could not find any aliases {aliases}. "
        f"Available columns: {available}"
    )


def rows_by_epsilon(rows):
    output = {}

    for row in rows:
        epsilon = get_value(row, ["epsilon"])
        epsilon_key = f"{epsilon:.6f}"
        output[epsilon_key] = row

    return output


def build_summary_rows(fgsm_rows, pgd_rows):
    fgsm_by_epsilon = rows_by_epsilon(fgsm_rows)
    pgd_by_epsilon = rows_by_epsilon(pgd_rows)

    shared_epsilons = sorted(set(fgsm_by_epsilon.keys()) & set(pgd_by_epsilon.keys()))

    if not shared_epsilons:
        raise ValueError("No matching epsilon values found between FGSM and PGD sweep files.")

    output_rows = []

    for epsilon_key in shared_epsilons:
        fgsm = fgsm_by_epsilon[epsilon_key]
        pgd = pgd_by_epsilon[epsilon_key]

        epsilon = get_value(fgsm, ["epsilon"])

        output_rows.append(
            {
                "epsilon": epsilon,
                "fgsm_missed_fall_rate": get_value(fgsm, ["missed_fall_rate"]),
                "pgd_missed_fall_rate": get_value(pgd, ["missed_fall_rate"]),
                "fgsm_recall_sensitivity": get_value(fgsm, ["recall_sensitivity", "recall"]),
                "pgd_recall_sensitivity": get_value(pgd, ["recall_sensitivity", "recall"]),
                "fgsm_f1_score": get_value(fgsm, ["f1_score", "f1"]),
                "pgd_f1_score": get_value(pgd, ["f1_score", "f1"]),
                "fgsm_false_alarm_count": get_value(
                    fgsm,
                    ["false_alarm_count", "false_alarms", "fp_false_fall_alarms"],
                ),
                "pgd_false_alarm_count": get_value(
                    pgd,
                    ["false_alarm_count", "false_alarms", "fp_false_fall_alarms"],
                ),
                "fgsm_prediction_change_rate": get_value(
                    fgsm,
                    ["prediction_change_rate", "prediction_changed_rate", "changed_prediction_rate"],
                ),
                "pgd_prediction_change_rate": get_value(
                    pgd,
                    ["prediction_change_rate", "prediction_changed_rate", "changed_prediction_rate"],
                ),
            }
        )

    return output_rows


def write_csv(rows):
    fieldnames = [
        "epsilon",
        "fgsm_missed_fall_rate",
        "pgd_missed_fall_rate",
        "fgsm_recall_sensitivity",
        "pgd_recall_sensitivity",
        "fgsm_f1_score",
        "pgd_f1_score",
        "fgsm_false_alarm_count",
        "pgd_false_alarm_count",
        "fgsm_prediction_change_rate",
        "pgd_prediction_change_rate",
    ]

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    "epsilon": fmt_decimal(row["epsilon"], digits=3),
                    "fgsm_missed_fall_rate": fmt_decimal(row["fgsm_missed_fall_rate"]),
                    "pgd_missed_fall_rate": fmt_decimal(row["pgd_missed_fall_rate"]),
                    "fgsm_recall_sensitivity": fmt_decimal(row["fgsm_recall_sensitivity"]),
                    "pgd_recall_sensitivity": fmt_decimal(row["pgd_recall_sensitivity"]),
                    "fgsm_f1_score": fmt_decimal(row["fgsm_f1_score"]),
                    "pgd_f1_score": fmt_decimal(row["pgd_f1_score"]),
                    "fgsm_false_alarm_count": fmt_integer(row["fgsm_false_alarm_count"]),
                    "pgd_false_alarm_count": fmt_integer(row["pgd_false_alarm_count"]),
                    "fgsm_prediction_change_rate": fmt_decimal(row["fgsm_prediction_change_rate"]),
                    "pgd_prediction_change_rate": fmt_decimal(row["pgd_prediction_change_rate"]),
                }
            )


def write_markdown(rows):
    lines = []

    lines.append("# Thesis Table 4: Epsilon Sweep Summary Table")
    lines.append("")
    lines.append("This table summarizes the FGSM and PGD epsilon sweep results side by side using window-level fall-vs-non-fall safety-proxy metrics.")
    lines.append("")
    lines.append("The purpose is to show the dose-response relationship between perturbation strength and fall-safety degradation.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append("This is a research implementation using window-level safety-proxy metrics and software-level processed-tensor adversarial perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.")
    lines.append("")
    lines.append("## Table")
    lines.append("")
    lines.append("| Epsilon | FGSM Missed Fall Rate | PGD Missed Fall Rate | FGSM Recall/Sensitivity | PGD Recall/Sensitivity | FGSM F1-Score | PGD F1-Score | FGSM False Alarms | PGD False Alarms | FGSM Prediction Change Rate | PGD Prediction Change Rate |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for row in rows:
        lines.append(
            "| "
            f"{fmt_decimal(row['epsilon'], digits=3)} | "
            f"{fmt_decimal(row['fgsm_missed_fall_rate'])} | "
            f"{fmt_decimal(row['pgd_missed_fall_rate'])} | "
            f"{fmt_decimal(row['fgsm_recall_sensitivity'])} | "
            f"{fmt_decimal(row['pgd_recall_sensitivity'])} | "
            f"{fmt_decimal(row['fgsm_f1_score'])} | "
            f"{fmt_decimal(row['pgd_f1_score'])} | "
            f"{fmt_integer(row['fgsm_false_alarm_count'])} | "
            f"{fmt_integer(row['pgd_false_alarm_count'])} | "
            f"{fmt_decimal(row['fgsm_prediction_change_rate'])} | "
            f"{fmt_decimal(row['pgd_prediction_change_rate'])} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The epsilon sweep table shows a clear dose-response pattern. As epsilon increases, missed fall rate increases and recall/sensitivity decreases. At epsilon 0.030, both FGSM and PGD reach missed fall rate 1.0000 and recall/sensitivity 0.0000.")
    lines.append("")
    lines.append("False fall alarm counts also increase under attack. At epsilon 0.030, FGSM produces 119 false fall alarms and PGD produces 115 false fall alarms.")
    lines.append("")
    lines.append("This table supports the thesis framing that adversarial impact should be reported in fall-safety proxy terms, not only as aggregate model accuracy degradation.")
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `results/thesis_table_4_epsilon_sweep_summary.csv`")
    lines.append("- `notes/thesis_table_4_epsilon_sweep_summary.md`")
    lines.append("- Input: `results/fgsm_epsilon_sweep_summary.csv`")
    lines.append("- Input: `results/pgd_epsilon_sweep_summary.csv`")
    lines.append("")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    fgsm_rows = read_sweep_file(FGSM_INPUT)
    pgd_rows = read_sweep_file(PGD_INPUT)

    summary_rows = build_summary_rows(fgsm_rows, pgd_rows)

    write_csv(summary_rows)
    write_markdown(summary_rows)

    print("Created Thesis Table 4 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_MD}")
    print("")
    print("Summary:")
    for row in summary_rows:
        print(
            f"  epsilon={fmt_decimal(row['epsilon'], digits=3)}: "
            f"FGSM missed={fmt_decimal(row['fgsm_missed_fall_rate'])}, "
            f"PGD missed={fmt_decimal(row['pgd_missed_fall_rate'])}, "
            f"FGSM recall={fmt_decimal(row['fgsm_recall_sensitivity'])}, "
            f"PGD recall={fmt_decimal(row['pgd_recall_sensitivity'])}, "
            f"FGSM false alarms={fmt_integer(row['fgsm_false_alarm_count'])}, "
            f"PGD false alarms={fmt_integer(row['pgd_false_alarm_count'])}"
        )


if __name__ == "__main__":
    main()