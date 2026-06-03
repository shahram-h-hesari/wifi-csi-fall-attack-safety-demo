from pathlib import Path
import csv


# ============================================================
# Thesis Table 5: Reproducibility Configuration Table
#
# Purpose:
# Document the exact experiment configuration used for the
# WiFi CSI Fall Attack-Safety Demo.
#
# Outputs:
# - results/thesis_table_5_reproducibility_configuration.csv
# - notes/thesis_table_5_reproducibility_configuration.md
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

OUTPUT_CSV = RESULTS_DIR / "thesis_table_5_reproducibility_configuration.csv"
OUTPUT_MD = NOTES_DIR / "thesis_table_5_reproducibility_configuration.md"


CONFIG_ROWS = [
    {
        "category": "Experiment identity",
        "parameter": "Experiment name",
        "value": "WiFi CSI Fall Attack-Safety Demo",
        "notes": "Reproducible research implementation for adversarial WiFi CSI fall-safety proxy evaluation.",
    },
    {
        "category": "Experiment identity",
        "parameter": "Repository location",
        "value": "experiments/fall_detection_attack_safety_demo",
        "notes": "Primary implementation folder inside secure-wifi-csi-healthcare-sensing; also mirrored to standalone repo wifi-csi-fall-attack-safety-demo.",
    },
    {
        "category": "Baseline resource",
        "parameter": "Baseline library",
        "value": "SenseFi / WiFi-CSI-Sensing-Benchmark",
        "notes": "Used as the reproducible WiFi CSI activity-recognition baseline.",
    },
    {
        "category": "Dataset",
        "parameter": "Dataset",
        "value": "UT_HAR_data / UT-HAR",
        "notes": "Processed WiFi CSI human-activity-recognition dataset used through the SenseFi loader.",
    },
    {
        "category": "Dataset",
        "parameter": "Evaluation unit",
        "value": "Window-level processed CSI tensor",
        "notes": "The experiment evaluates windows, not event-level falls, clinical alarms, long-lie events, or real patient episodes.",
    },
    {
        "category": "Dataset",
        "parameter": "Evaluated windows",
        "value": "996 total windows",
        "notes": "89 fall windows and 907 non-fall windows.",
    },
    {
        "category": "Label mapping",
        "parameter": "Original task",
        "value": "Seven-class UT-HAR activity recognition",
        "notes": "Model predicts the original UT-HAR activity classes before binary safety-proxy conversion.",
    },
    {
        "category": "Label mapping",
        "parameter": "Binary safety-proxy mapping",
        "value": "fall = class 1; non-fall = classes 0, 2, 3, 4, 5, 6",
        "notes": "Used to compute fall-vs-non-fall TP, FN, FP, TN and derived safety-proxy metrics.",
    },
    {
        "category": "Model",
        "parameter": "Model architecture",
        "value": "LeNet / UT_HAR_LeNet",
        "notes": "SenseFi UT-HAR LeNet model used as the first reproducible baseline.",
    },
    {
        "category": "Clean baseline",
        "parameter": "Clean baseline epochs",
        "value": "5",
        "notes": "Shortened clean baseline training used for the first reproducible thesis demo.",
    },
    {
        "category": "Clean baseline",
        "parameter": "Clean baseline device",
        "value": "Local CPU environment",
        "notes": "Run inside the local sensefi_env environment; this table records the reproducible local research setting.",
    },
    {
        "category": "FGSM attack",
        "parameter": "Attack type",
        "value": "FGSM",
        "notes": "Software-level untargeted adversarial perturbation applied to processed UT-HAR CSI tensors.",
    },
    {
        "category": "FGSM attack",
        "parameter": "FGSM evaluation epsilon",
        "value": "0.030",
        "notes": "Used for the main FGSM attacked prediction export and defended-vs-undefended comparison.",
    },
    {
        "category": "FGSM attack",
        "parameter": "FGSM epsilon sweep values",
        "value": "0.000, 0.005, 0.010, 0.020, 0.030",
        "notes": "Used to characterize dose-response behavior across perturbation strength.",
    },
    {
        "category": "PGD attack",
        "parameter": "Attack type",
        "value": "PGD",
        "notes": "Software-level untargeted projected-gradient perturbation applied to processed UT-HAR CSI tensors.",
    },
    {
        "category": "PGD attack",
        "parameter": "PGD evaluation epsilon",
        "value": "0.030",
        "notes": "Used for the main PGD attacked prediction export and defended-vs-undefended comparison.",
    },
    {
        "category": "PGD attack",
        "parameter": "PGD evaluation alpha",
        "value": "0.005",
        "notes": "Step size used for the main PGD evaluation at epsilon 0.030.",
    },
    {
        "category": "PGD attack",
        "parameter": "PGD evaluation steps",
        "value": "10",
        "notes": "Number of projected-gradient steps used for the main PGD evaluation.",
    },
    {
        "category": "PGD attack",
        "parameter": "PGD epsilon sweep values",
        "value": "0.000, 0.005, 0.010, 0.020, 0.030",
        "notes": "Used to characterize PGD dose-response behavior across perturbation strength.",
    },
    {
        "category": "PGD attack",
        "parameter": "PGD epsilon sweep alpha rule",
        "value": "alpha = epsilon / 6; alpha = 0.000 when epsilon = 0.000",
        "notes": "Used in the PGD epsilon sweep script.",
    },
    {
        "category": "Defense",
        "parameter": "Defense method",
        "value": "FGSM adversarial training",
        "notes": "First short defended baseline using clean loss plus FGSM adversarial loss.",
    },
    {
        "category": "Defense",
        "parameter": "Defense epochs",
        "value": "5",
        "notes": "Shortened defended training used for the first defense comparison.",
    },
    {
        "category": "Defense",
        "parameter": "FGSM training epsilon",
        "value": "0.005",
        "notes": "Perturbation strength used during FGSM adversarial training.",
    },
    {
        "category": "Defense",
        "parameter": "Adversarial loss weight",
        "value": "0.5",
        "notes": "Weight applied to the adversarial loss term during defended training.",
    },
    {
        "category": "Evaluation",
        "parameter": "Primary comparison file",
        "value": "results/defended_vs_undefended_safety_comparison.csv",
        "notes": "Main source file for thesis-ready safety-proxy tables and figures.",
    },
    {
        "category": "Evaluation",
        "parameter": "Primary evaluated conditions",
        "value": "undefended clean; undefended FGSM; undefended PGD; defended clean; defended FGSM; defended PGD",
        "notes": "All attacked conditions use epsilon 0.030 for the main defended-vs-undefended comparison.",
    },
    {
        "category": "Evaluation",
        "parameter": "Safety-proxy metrics",
        "value": "TP, FN, FP, TN, recall/sensitivity, missed fall rate, specificity, false positive rate, precision, F1-score, balanced accuracy, false alarm count, prediction change rate",
        "notes": "Metrics translate model degradation into fall-vs-non-fall safety-proxy terms.",
    },
    {
        "category": "Claim boundary",
        "parameter": "Clinical claim boundary",
        "value": "Not clinical validation",
        "notes": "The experiment does not provide clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, or long-lie validation.",
    },
    {
        "category": "Claim boundary",
        "parameter": "Wireless attack claim boundary",
        "value": "Not physical-layer / packet-level / preamble-level / SDR / over-the-air validation",
        "notes": "FGSM and PGD are software-level perturbations applied to processed CSI tensors.",
    },
]


def write_csv(rows):
    fieldnames = ["category", "parameter", "value", "notes"]

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def write_markdown(rows):
    lines = []

    lines.append("# Thesis Table 5: Reproducibility Configuration Table")
    lines.append("")
    lines.append("This table documents the key configuration choices used in the WiFi CSI Fall Attack-Safety Demo.")
    lines.append("")
    lines.append("The purpose is to make the first clean-to-attack-to-defense workflow easier to reproduce, audit, and extend to another dataset.")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append("This is a research implementation using window-level safety-proxy metrics and software-level processed-tensor adversarial perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.")
    lines.append("")
    lines.append("## Table")
    lines.append("")
    lines.append("| Category | Parameter | Value | Notes |")
    lines.append("|---|---|---|---|")

    for row in rows:
        lines.append(
            "| "
            f"{row['category']} | "
            f"{row['parameter']} | "
            f"{row['value']} | "
            f"{row['notes']} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("This configuration table records the experimental scope and parameter values behind the thesis-ready tables and figures. It is especially useful for repeating the workflow with another WiFi CSI dataset because it separates dataset choice, model choice, attack settings, defense settings, evaluation metrics, and claim boundaries.")
    lines.append("")
    lines.append("The most important reproducibility settings are: SenseFi UT-HAR data, LeNet model, 5 clean training epochs, 5 defended training epochs, FGSM evaluation epsilon 0.030, PGD evaluation epsilon 0.030, PGD alpha 0.005, 10 PGD steps, FGSM adversarial-training epsilon 0.005, and adversarial loss weight 0.5.")
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `results/thesis_table_5_reproducibility_configuration.csv`")
    lines.append("- `notes/thesis_table_5_reproducibility_configuration.md`")
    lines.append("")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    write_csv(CONFIG_ROWS)
    write_markdown(CONFIG_ROWS)

    print("Created Thesis Table 5 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_MD}")
    print("")
    print("Summary:")
    print("  Dataset: SenseFi UT-HAR / UT_HAR_data")
    print("  Model: LeNet / UT_HAR_LeNet")
    print("  Clean epochs: 5")
    print("  Defense: FGSM adversarial training")
    print("  Defense epochs: 5")
    print("  FGSM evaluation epsilon: 0.030")
    print("  PGD evaluation epsilon: 0.030")
    print("  PGD alpha: 0.005")
    print("  PGD steps: 10")
    print("  FGSM training epsilon: 0.005")
    print("  Adversarial loss weight: 0.5")


if __name__ == "__main__":
    main()