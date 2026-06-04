from pathlib import Path
import csv


BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = BASE_DIR / "figures"
NOTES_DIR = BASE_DIR / "notes"
SCRIPTS_DIR = BASE_DIR / "scripts"

OUTPUT_CSV = RESULTS_DIR / "thesis_table_6_output_index.csv"
OUTPUT_NOTE = NOTES_DIR / "thesis_table_6_output_index.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level safety-proxy evaluation; "
    "software-level processed-tensor perturbations only; not clinical validation, "
    "not medical-device validation, not diagnostic evidence, not real patient deployment, "
    "not regulatory evaluation, not event-level fall validation, not long-lie validation, "
    "not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / "
    "SDR / over-the-air validation."
)


ARTIFACTS = [
    {
        "output": "Table 1",
        "type": "Table",
        "title": "Clean, Attacked, and Defended Fall Safety-Proxy Metrics",
        "primary_file": "results/thesis_table_1_safety_metrics.csv",
        "companion_note": "notes/thesis_table_1_safety_metrics.md",
        "generation_script": "scripts/create_thesis_table_1_safety_metrics.py",
        "thesis_contribution": "Establishes the core clean, attacked, and defended comparison for fall-vs-non-fall safety-proxy evaluation.",
        "clinical_safety_relevance": "Reports TP, FN, FP, TN, recall/sensitivity, missed fall rate, precision, F1-score, balanced accuracy, and false fall alarm counts.",
        "use_in_thesis": "Use as the main quantitative result table for the first reproduced SenseFi UT-HAR LeNet attack-safety workflow.",
    },
    {
        "output": "Figure 1",
        "type": "Figure",
        "title": "Defended vs Undefended Safety Tradeoff",
        "primary_file": "figures/thesis_figure_1_safety_tradeoff.png",
        "companion_note": "notes/thesis_figure_1_safety_tradeoff.md",
        "generation_script": "scripts/create_thesis_figure_1_safety_tradeoff.py",
        "thesis_contribution": "Visualizes the main safety tradeoff between missed fall rate and false fall alarm count across clean, attacked, and defended conditions.",
        "clinical_safety_relevance": "Shows whether defense reduces false alarms, missed falls, or both.",
        "use_in_thesis": "Use as the first high-level visual summary of the clean-to-attack-to-defense safety-proxy result.",
    },
    {
        "output": "Table 2",
        "type": "Table",
        "title": "Attack Impact Delta Table",
        "primary_file": "results/thesis_table_2_attack_impact_delta.csv",
        "companion_note": "notes/thesis_table_2_attack_impact_delta.md",
        "generation_script": "scripts/create_thesis_table_2_attack_impact_delta.py",
        "thesis_contribution": "Quantifies how FGSM and PGD change safety-proxy metrics relative to the clean baseline.",
        "clinical_safety_relevance": "Translates adversarial degradation into changes in missed fall rate, recall/sensitivity, F1-score, false alarms, and prediction change rate.",
        "use_in_thesis": "Use to support the argument that aggregate accuracy alone is insufficient for healthcare-relevant WiFi sensing security evaluation.",
    },
    {
        "output": "Figure 2",
        "type": "Figure",
        "title": "FGSM vs PGD Epsilon Sweep Curves",
        "primary_file": "figures/thesis_figure_2_fgsm_pgd_epsilon_sweep.png",
        "companion_note": "notes/thesis_figure_2_fgsm_pgd_epsilon_sweep.md",
        "generation_script": "scripts/create_thesis_figure_2_fgsm_pgd_epsilon_sweep.py",
        "thesis_contribution": "Shows perturbation-strength dose-response behavior for FGSM and PGD.",
        "clinical_safety_relevance": "Shows how increasing epsilon changes missed fall rate, recall/sensitivity, F1-score, and false fall alarms.",
        "use_in_thesis": "Use to show that safety-proxy degradation can be analyzed across attack strength rather than only at one epsilon.",
    },
    {
        "output": "Table 3",
        "type": "Table",
        "title": "Defense Tradeoff Table",
        "primary_file": "results/thesis_table_3_defense_tradeoff.csv",
        "companion_note": "notes/thesis_table_3_defense_tradeoff.md",
        "generation_script": "scripts/create_thesis_table_3_defense_tradeoff.py",
        "thesis_contribution": "Compares undefended and defended conditions to evaluate whether the first short FGSM adversarial-training defense improves or worsens safety-proxy outcomes.",
        "clinical_safety_relevance": "Separates false alarm reduction from missed fall recovery, showing that a defense may improve one safety-proxy outcome while failing another.",
        "use_in_thesis": "Use as the main defense-evaluation table for the first defended baseline.",
    },
    {
        "output": "Table 4",
        "type": "Table",
        "title": "Epsilon Sweep Summary Table",
        "primary_file": "results/thesis_table_4_epsilon_sweep_summary.csv",
        "companion_note": "notes/thesis_table_4_epsilon_sweep_summary.md",
        "generation_script": "scripts/create_thesis_table_4_epsilon_sweep_summary.py",
        "thesis_contribution": "Condenses the FGSM and PGD epsilon sweeps into a compact table.",
        "clinical_safety_relevance": "Reports how missed fall rate, recall/sensitivity, F1-score, and false fall alarm burden change across perturbation strengths.",
        "use_in_thesis": "Use as the table counterpart to Figure 2 and as a bridge to robustness failure-threshold analysis.",
    },
    {
        "output": "Figure 3",
        "type": "Figure",
        "title": "Defense Effect Summary",
        "primary_file": "figures/thesis_figure_3_defense_effect_summary.png",
        "companion_note": "notes/thesis_figure_3_defense_effect_summary.md",
        "generation_script": "scripts/create_thesis_figure_3_defense_effect_summary.py",
        "thesis_contribution": "Provides a compact visual summary of the defended-vs-undefended attack results.",
        "clinical_safety_relevance": "Highlights that the first short defense reduced false fall alarms under attack but did not recover fall recall at epsilon 0.030.",
        "use_in_thesis": "Use as a concise visual defense-result figure in the robustness/defense chapter.",
    },
    {
        "output": "Figure 4",
        "type": "Figure",
        "title": "Clean vs Defended Clean Tradeoff",
        "primary_file": "figures/thesis_figure_4_clean_defense_tradeoff.png",
        "companion_note": "notes/thesis_figure_4_clean_defense_tradeoff.md",
        "generation_script": "scripts/create_thesis_figure_4_clean_defense_tradeoff.py",
        "thesis_contribution": "Shows the clean-condition cost of the defended model compared with the undefended clean baseline.",
        "clinical_safety_relevance": "Shows that a defense can reduce false alarms while increasing missed falls under clean conditions.",
        "use_in_thesis": "Use to discuss the clean-performance tradeoff that must be considered before interpreting a defense as beneficial.",
    },
    {
        "output": "Figure 5",
        "type": "Figure",
        "title": "Binary Fall-vs-Non-Fall Confusion Matrices",
        "primary_file": "figures/thesis_figure_5_confusion_matrices.png",
        "companion_note": "notes/thesis_figure_5_confusion_matrices.md",
        "generation_script": "scripts/create_thesis_figure_5_confusion_matrices.py",
        "thesis_contribution": "Shows binary confusion matrices for clean, FGSM, PGD, defended clean, defended FGSM, and defended PGD conditions.",
        "clinical_safety_relevance": "Makes the safety-proxy error modes visible: detected falls, missed falls, false fall alarms, and correctly rejected non-falls.",
        "use_in_thesis": "Use to explain how adversarial attacks and defense change the binary confusion-matrix structure behind the summary metrics.",
    },
    {
        "output": "Table 5",
        "type": "Table",
        "title": "Reproducibility Configuration Table",
        "primary_file": "results/thesis_table_5_reproducibility_configuration.csv",
        "companion_note": "notes/thesis_table_5_reproducibility_configuration.md",
        "generation_script": "scripts/create_thesis_table_5_reproducibility_configuration.py",
        "thesis_contribution": "Documents dataset, model, attack settings, defense settings, evaluated windows, label mapping, and claim boundaries.",
        "clinical_safety_relevance": "Clarifies that current results are window-level safety-proxy metrics and not event-level clinical outcomes.",
        "use_in_thesis": "Use as the reproducibility and scope table for repeating the workflow with another dataset.",
    },
    {
        "output": "Table 6",
        "type": "Index Table",
        "title": "Thesis Output Index / Evidence Contribution Table",
        "primary_file": "results/thesis_table_6_output_index.csv",
        "companion_note": "notes/thesis_table_6_output_index.md",
        "generation_script": "scripts/create_thesis_table_6_output_index.py",
        "thesis_contribution": "Indexes thesis-ready tables, figures, notes, scripts, and evidence contributions generated by the demo.",
        "clinical_safety_relevance": "Keeps the safety-proxy evidence set navigable and separates quantitative results, figures, metadata limitations, and conceptual diagrams.",
        "use_in_thesis": "Use as the output navigation table and appendix-style artifact index for the experiment.",
    },
    {
        "output": "Audit 1",
        "type": "Dataset Audit Note",
        "title": "UT-HAR Dataset Metadata Audit",
        "primary_file": "notes/ut_har_dataset_metadata_audit.md",
        "companion_note": "NA",
        "generation_script": "NA",
        "thesis_contribution": "Audits whether the local UT-HAR files support event-level timing, subject, trial, or recording metadata.",
        "clinical_safety_relevance": "Explains why the current demo can compute window-level safety-proxy metrics but cannot compute event-level metrics such as time-to-detection, delayed detection, long-lie proxy, or false alarms per hour/day.",
        "use_in_thesis": "Use as the dataset limitation and future collaboration justification note.",
    },
    {
        "output": "Table 7",
        "type": "Table",
        "title": "Safety Metric Availability and Data Requirement Table",
        "primary_file": "results/thesis_table_7_metric_availability.csv",
        "companion_note": "notes/thesis_table_7_metric_availability.md",
        "generation_script": "scripts/create_thesis_table_7_metric_availability.py",
        "thesis_contribution": "Separates metrics computable from current UT-HAR window-level outputs from metrics requiring richer event-level metadata.",
        "clinical_safety_relevance": "Prevents overclaiming by identifying which clinical-safety metrics are not computable with the current dataset.",
        "use_in_thesis": "Use as the metric feasibility and data-requirement table for future dataset selection and collaboration planning.",
    },
    {
        "output": "Table 8",
        "type": "Table",
        "title": "High-Risk Multiclass Error Taxonomy",
        "primary_file": "results/thesis_table_8_high_risk_multiclass_error_taxonomy.csv",
        "companion_note": "notes/thesis_table_8_high_risk_multiclass_error_taxonomy.md",
        "generation_script": "scripts/create_thesis_table_8_high_risk_multiclass_error_taxonomy.py",
        "thesis_contribution": "Identifies fall-relevant seven-class error pathways behind missed falls and false fall alarms.",
        "clinical_safety_relevance": "Shows which non-fall classes absorb true fall windows and which non-fall activities become false fall alarms.",
        "use_in_thesis": "Use as the multiclass explanation behind the binary fall-vs-non-fall safety-proxy results.",
    },
    {
        "output": "Figure 6",
        "type": "Figure",
        "title": "Seven-Class Confusion Matrix Figure",
        "primary_file": "figures/thesis_figure_6_seven_class_confusion_matrices.png",
        "companion_note": "notes/thesis_figure_6_seven_class_confusion_matrices.md",
        "generation_script": "scripts/create_thesis_figure_6_seven_class_confusion_matrices.py",
        "thesis_contribution": "Visualizes full seven-class confusion matrices for clean, attacked, and defended conditions.",
        "clinical_safety_relevance": "Complements Table 8 by making high-risk multiclass confusion pathways visible.",
        "use_in_thesis": "Use as the visual multiclass error-analysis figure.",
    },
    {
        "output": "Table 9",
        "type": "Table",
        "title": "Robustness Failure Threshold Table",
        "primary_file": "results/thesis_table_9_robustness_failure_thresholds.csv",
        "companion_note": "notes/thesis_table_9_robustness_failure_thresholds.md",
        "generation_script": "scripts/create_thesis_table_9_robustness_failure_thresholds.py",
        "thesis_contribution": "Identifies the first observed epsilon where FGSM or PGD crosses predefined window-level robustness failure thresholds.",
        "clinical_safety_relevance": "Translates epsilon sweeps into safety-proxy threshold language, such as severe missed-fall behavior, recall collapse, prediction instability, and high false-alarm burden.",
        "use_in_thesis": "Use to argue that adversarial impact should be reported as safety-proxy failure thresholds, not only aggregate accuracy loss.",
    },
    {
        "output": "Figure 7",
        "type": "Figure",
        "title": "Failure Threshold / Robustness Collapse Plot",
        "primary_file": "figures/thesis_figure_7_failure_threshold_plot.png",
        "companion_note": "notes/thesis_figure_7_failure_threshold_plot.md",
        "generation_script": "scripts/create_thesis_figure_7_failure_threshold_plot.py",
        "thesis_contribution": "Visualizes FGSM and PGD robustness-collapse behavior across epsilon values.",
        "clinical_safety_relevance": "Shows missed-fall, recall, false-alarm, and prediction-instability threshold crossings.",
        "use_in_thesis": "Use as the visual counterpart to Table 9.",
    },
    {
        "output": "Figure 8",
        "type": "Conceptual Figure",
        "title": "Safety Translation Pipeline Diagram",
        "primary_file": "figures/thesis_figure_8_safety_translation_pipeline.png",
        "companion_note": "notes/thesis_figure_8_safety_translation_pipeline.md",
        "generation_script": "scripts/create_thesis_figure_8_safety_translation_pipeline.py",
        "thesis_contribution": "Summarizes the full safety-translation pipeline from WiFi CSI predictions to window-level safety-proxy metrics and future event-level requirements.",
        "clinical_safety_relevance": "Clearly separates the current window-level contribution from future clinical-safety extensions that require richer metadata.",
        "use_in_thesis": "Use as the conceptual workflow diagram in the methods or thesis contribution section.",
    },
    {
        "output": "Table 10",
        "type": "Table",
        "title": "Extended Window-Level Diagnostic Safety Metrics",
        "primary_file": "results/thesis_table_10_extended_diagnostic_safety_metrics.csv",
        "companion_note": "notes/thesis_table_10_extended_diagnostic_safety_metrics.md",
        "generation_script": "scripts/create_thesis_table_10_extended_diagnostic_safety_metrics.py",
        "thesis_contribution": "Extends the safety-proxy analysis beyond recall, precision, F1-score, and balanced accuracy.",
        "clinical_safety_relevance": "Reports additional diagnostic-style safety-proxy metrics and uses NA for undefined ratios when TP is zero.",
        "use_in_thesis": "Use to strengthen the quantitative safety-proxy metric set while avoiding fabricated undefined values.",
    },
    {
        "output": "Figure 9",
        "type": "Figure",
        "title": "Safety Error Burden Composition Across Conditions",
        "primary_file": "figures/thesis_figure_9_safety_error_burden_composition.png",
        "companion_note": "notes/thesis_figure_9_safety_error_burden_composition.md",
        "generation_script": "scripts/create_thesis_figure_9_safety_error_burden_composition.py",
        "thesis_contribution": "Shows the composition of detected falls, missed falls, false fall alarms, and correct non-falls across conditions.",
        "clinical_safety_relevance": "Makes the clean-to-attack shift visible: attacked conditions lose detected fall windows and increase missed fall burden.",
        "use_in_thesis": "Use as a visual explanation of safety-error burden behind the confusion matrices.",
    },
    {
        "output": "Table 11",
        "type": "Table",
        "title": "Attack-Induced Safety Risk Amplification Ratios",
        "primary_file": "results/thesis_table_11_attack_induced_safety_risk_amplification.csv",
        "companion_note": "notes/thesis_table_11_attack_induced_safety_risk_amplification.md",
        "generation_script": "scripts/create_thesis_table_11_attack_induced_safety_risk_amplification.py",
        "thesis_contribution": "Quantifies how attacked and defended-attacked conditions amplify safety-relevant error ratios relative to clean baselines.",
        "clinical_safety_relevance": "Highlights attack-induced amplification of missed-fall and false-alarm burden while preserving claim boundaries.",
        "use_in_thesis": "Use as a risk-amplification style summary that connects ML degradation to safety-proxy language.",
    },
    {
        "output": "Figure 10",
        "type": "Figure",
        "title": "High-Risk Multiclass Fall Error Pathways",
        "primary_file": "figures/thesis_figure_10_high_risk_multiclass_fall_error_pathways.png",
        "companion_note": "notes/thesis_figure_10_high_risk_multiclass_fall_error_pathways.md",
        "generation_script": "scripts/create_thesis_figure_10_high_risk_multiclass_fall_error_pathways.py",
        "thesis_contribution": "Simplifies seven-class confusion matrices into fall-relevant error pathways.",
        "clinical_safety_relevance": "Shows where true fall windows go when missed and which non-fall activities become false fall alarms.",
        "use_in_thesis": "Use to connect binary fall-vs-non-fall degradation to original multiclass activity-recognition errors.",
    },
    {
        "output": "Table 12",
        "type": "Table",
        "title": "Model Confidence and Error Confidence Summary",
        "primary_file": "results/thesis_table_12_model_confidence_error_summary.csv",
        "companion_note": "notes/thesis_table_12_model_confidence_error_summary.md",
        "generation_script": "scripts/create_thesis_table_12_model_confidence_error_summary.py",
        "thesis_contribution": "Summarizes model-reported confidence for correct predictions, incorrect predictions, missed falls, and false fall alarms.",
        "clinical_safety_relevance": "Shows whether missed-fall errors are low-confidence or high-confidence errors under attack and defense.",
        "use_in_thesis": "Use as the main confidence/error-confidence table for the attacked fall-safety workflow.",
    },
    {
        "output": "Figure 11",
        "type": "Figure",
        "title": "High-Confidence Missed-Fall Error Comparison",
        "primary_file": "figures/thesis_figure_11_high_confidence_missed_fall_comparison.png",
        "companion_note": "notes/thesis_figure_11_high_confidence_missed_fall_comparison.md",
        "generation_script": "scripts/create_thesis_figure_11_high_confidence_missed_fall_comparison.py",
        "thesis_contribution": "Visualizes missed-fall confidence behavior across clean, attacked, and defended conditions.",
        "clinical_safety_relevance": "Highlights that undefended PGD produces a high-confidence missed-fall failure pattern.",
        "use_in_thesis": "Use as the visual companion to Table 12.",
    },
    {
        "output": "Figure 12",
        "type": "Figure",
        "title": "Confidence-Safety Failure Map",
        "primary_file": "figures/thesis_figure_12_confidence_safety_failure_map.png",
        "companion_note": "notes/thesis_figure_12_confidence_safety_failure_map.md",
        "generation_script": "scripts/create_thesis_figure_12_confidence_safety_failure_map.py",
        "thesis_contribution": "Combines missed fall rate and high-confidence missed-fall rate into a confidence-safety failure map.",
        "clinical_safety_relevance": "Shows that undefended PGD is the strongest confidence-safety failure case, while defended attacked conditions still miss all falls but with lower high-confidence missed-fall rates.",
        "use_in_thesis": "Use to explain the two-dimensional relationship between missed-fall safety failure and model-reported confidence.",
    },
    {
        "output": "Table 13",
        "type": "Table",
        "title": "Confidence-Safety Failure Ranking",
        "primary_file": "results/thesis_table_13_confidence_safety_failure_ranking.csv",
        "companion_note": "notes/thesis_table_13_confidence_safety_failure_ranking.md",
        "generation_script": "scripts/create_thesis_table_13_confidence_safety_failure_ranking.py",
        "thesis_contribution": "Ranks clean, attacked, and defended conditions using a descriptive confidence-safety failure score.",
        "clinical_safety_relevance": "Identifies which conditions combine missed-fall safety failure with high model-reported confidence in the wrong prediction.",
        "use_in_thesis": "Use as the ranked numeric companion to Figure 12.",
    },
    {
        "output": "Figure 13",
        "type": "Figure",
        "title": "Confidence-Safety Failure Ranking Bar Chart",
        "primary_file": "figures/thesis_figure_13_confidence_safety_failure_ranking.png",
        "companion_note": "notes/thesis_figure_13_confidence_safety_failure_ranking.md",
        "generation_script": "scripts/create_thesis_figure_13_confidence_safety_failure_ranking.py",
        "thesis_contribution": "Visualizes the Table 13 confidence-safety failure ranking as a horizontal bar chart.",
        "clinical_safety_relevance": "Makes the ranking of overconfident missed-fall safety failures visually obvious.",
        "use_in_thesis": "Use as the visual companion to Table 13.",
    },
    {
        "output": "Table 14",
        "type": "Table",
        "title": "Matched Attack Defense Effect Summary",
        "primary_file": "results/thesis_table_14_matched_attack_defense_effect_summary.csv",
        "companion_note": "notes/thesis_table_14_matched_attack_defense_effect_summary.md",
        "generation_script": "scripts/create_thesis_table_14_matched_attack_defense_effect_summary.py",
        "thesis_contribution": "Directly compares matched attacked conditions: undefended FGSM vs defended FGSM and undefended PGD vs defended PGD.",
        "clinical_safety_relevance": "Shows that the defended attacked models reduce overconfident missed-fall behavior and false alarms but do not restore fall recall.",
        "use_in_thesis": "Use as the main matched attack-defense effect summary table.",
    },
    {
        "output": "Figure 14",
        "type": "Figure",
        "title": "Matched Attack Defense Effect Comparison",
        "primary_file": "figures/thesis_figure_14_matched_attack_defense_effect_comparison.png",
        "companion_note": "notes/thesis_figure_14_matched_attack_defense_effect_comparison.md",
        "generation_script": "scripts/create_thesis_figure_14_matched_attack_defense_effect_comparison.py",
        "thesis_contribution": "Visually compares matched attack-defense effects for FGSM and PGD using three panels.",
        "clinical_safety_relevance": "Shows reductions in high-confidence missed-fall rate, median missed-fall confidence, and false fall alarm count, while noting that missed fall rate remains 1.000000.",
        "use_in_thesis": "Use as the visual companion to Table 14.",
    },
]


def path_exists(relative_path):
    if relative_path in ["NA", "", None]:
        return "not applicable"
    return "yes" if (BASE_DIR / relative_path).exists() else "no"


def write_csv():
    fieldnames = [
        "output",
        "type",
        "title",
        "primary_file",
        "companion_note",
        "generation_script",
        "primary_file_exists",
        "companion_note_exists",
        "generation_script_exists",
        "thesis_contribution",
        "clinical_safety_relevance",
        "use_in_thesis",
        "claim_boundary",
    ]

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for artifact in ARTIFACTS:
            row = dict(artifact)
            row["primary_file_exists"] = path_exists(row["primary_file"])
            row["companion_note_exists"] = path_exists(row["companion_note"])
            row["generation_script_exists"] = path_exists(row["generation_script"])
            row["claim_boundary"] = CLAIM_BOUNDARY
            writer.writerow(row)


def write_note():
    lines = []

    lines.append("# Thesis Table 6: Thesis Output Index / Evidence Contribution Table")
    lines.append("")
    lines.append(
        "This table indexes the thesis-ready tables, figures, notes, scripts, and evidence contributions generated for the WiFi CSI Fall Attack-Safety Demo."
    )
    lines.append("")
    lines.append(
        "The purpose is to make the repository easier to navigate, explain what each output contributes to the thesis, and separate quantitative results, visual summaries, defense analysis, epsilon-sweep analysis, confusion-matrix analysis, metadata limitations, robustness-threshold analysis, confidence/error-confidence analysis, matched attack-defense analysis, and safety-translation documentation."
    )
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Table")
    lines.append("")
    lines.append("| Output | Type | Title | Primary File | Thesis Contribution | Clinical-Safety Relevance | Use in Thesis |")
    lines.append("|---|---|---|---|---|---|---|")

    for artifact in ARTIFACTS:
        lines.append(
            f"| {artifact['output']} "
            f"| {artifact['type']} "
            f"| {artifact['title']} "
            f"| {artifact['primary_file']} "
            f"| {artifact['thesis_contribution']} "
            f"| {artifact['clinical_safety_relevance']} "
            f"| {artifact['use_in_thesis']} |"
        )

    lines.append("")
    lines.append("## File Availability Check")
    lines.append("")
    lines.append("| Output | Primary File Exists | Companion Note Exists | Generation Script Exists |")
    lines.append("|---|---:|---:|---:|")

    for artifact in ARTIFACTS:
        lines.append(
            f"| {artifact['output']} "
            f"| {path_exists(artifact['primary_file'])} "
            f"| {path_exists(artifact['companion_note'])} "
            f"| {path_exists(artifact['generation_script'])} |"
        )

    lines.append("")
    lines.append("## Current Indexed Output Set")
    lines.append("")
    lines.append("```text")
    for artifact in ARTIFACTS:
        lines.append(f"{artifact['output']} - {artifact['title']}")
    lines.append("```")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("Table 6 shows that the current thesis-ready output set covers ten major evidence roles:")
    lines.append("")
    lines.append("1. core clean, attacked, and defended safety-proxy metrics;")
    lines.append("2. attack-impact and epsilon-sweep degradation analysis;")
    lines.append("3. defended-vs-undefended tradeoff analysis;")
    lines.append("4. binary and seven-class confusion-matrix analysis;")
    lines.append("5. reproducibility configuration for repeating the workflow with another dataset;")
    lines.append("6. dataset metadata auditing and metric-availability boundaries;")
    lines.append("7. robustness failure-threshold analysis;")
    lines.append("8. safety-translation pipeline documentation;")
    lines.append("9. confidence/error-confidence analysis for missed-fall failures;")
    lines.append("10. matched attack-defense effect analysis.")
    lines.append("")
    lines.append(
        "This index also makes the research boundary clear. The current outputs are strong for window-level safety-proxy analysis. Event-level fall detection, time-to-detection, delayed detection, long-lie proxy, false alarms per hour/day, subject-level robustness, and trial-level robustness require richer metadata than the current local UT-HAR copy provides."
    )
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `results/thesis_table_6_output_index.csv`")
    lines.append("- `notes/thesis_table_6_output_index.md`")

    OUTPUT_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    write_csv()
    write_note()

    print("Created updated Thesis Table 6 output index:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print(f"Indexed outputs: {len(ARTIFACTS)}")


if __name__ == "__main__":
    main()