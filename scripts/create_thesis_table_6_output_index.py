"""
Create Thesis Table 6: Thesis Output Index / Evidence Contribution Table.

This script indexes the thesis-ready tables, figures, notes, and audit outputs
generated for the WiFi CSI Fall Attack-Safety Demo.

It is intentionally descriptive: Table 6 is the navigation and evidence map
for the experiment outputs.

Outputs:
    results/thesis_table_6_output_index.csv
    notes/thesis_table_6_output_index.md

Claim boundary:
    Research implementation only; window-level safety-proxy evaluation;
    software-level processed-tensor perturbations only.
"""

from pathlib import Path
import csv


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
NOTES_DIR = ROOT / "notes"
SCRIPTS_DIR = ROOT / "scripts"

OUTPUT_CSV = RESULTS_DIR / "thesis_table_6_output_index.csv"
OUTPUT_NOTE = NOTES_DIR / "thesis_table_6_output_index.md"

CLAIM_BOUNDARY = (
    "Research implementation only; window-level safety-proxy evaluation; "
    "software-level processed-tensor perturbations only; not clinical validation, "
    "not medical-device validation, not diagnostic evidence, not real patient "
    "deployment, not regulatory evaluation, not event-level fall validation, "
    "not long-lie validation, not time-to-alarm validation, and not physical-layer / "
    "packet-level / preamble-level / SDR / over-the-air validation."
)


ROWS = [
    {
        "output_id": "Table 1",
        "output_type": "Table",
        "title": "Clean, Attacked, and Defended Fall Safety-Proxy Metrics",
        "primary_file": "results/thesis_table_1_safety_metrics.csv",
        "companion_note": "notes/thesis_table_1_safety_metrics.md",
        "generation_script": "scripts/create_thesis_table_1_safety_metrics.py",
        "thesis_contribution": "Establishes the core clean, attacked, and defended comparison for fall-vs-non-fall safety-proxy evaluation.",
        "clinical_safety_relevance": "Reports TP, FN, FP, TN, recall/sensitivity, missed fall rate, precision, F1-score, balanced accuracy, and false fall alarm counts.",
        "use_in_thesis": "Use as the main quantitative result table for the first reproduced SenseFi UT-HAR LeNet attack-safety workflow.",
    },
    {
        "output_id": "Figure 1",
        "output_type": "Figure",
        "title": "Defended vs Undefended Safety Tradeoff",
        "primary_file": "figures/thesis_figure_1_safety_tradeoff.png",
        "companion_note": "notes/thesis_figure_1_safety_tradeoff.md",
        "generation_script": "scripts/create_thesis_figure_1_safety_tradeoff.py",
        "thesis_contribution": "Visualizes the main safety tradeoff between missed fall rate and false fall alarm count across clean, attacked, and defended conditions.",
        "clinical_safety_relevance": "Shows whether defense reduces false alarms, missed falls, or both.",
        "use_in_thesis": "Use as the first high-level visual summary of the clean-to-attack-to-defense safety-proxy result.",
    },
    {
        "output_id": "Table 2",
        "output_type": "Table",
        "title": "Attack Impact Delta Table",
        "primary_file": "results/thesis_table_2_attack_impact_delta.csv",
        "companion_note": "notes/thesis_table_2_attack_impact_delta.md",
        "generation_script": "scripts/create_thesis_table_2_attack_impact_delta.py",
        "thesis_contribution": "Quantifies how FGSM and PGD change safety-proxy metrics relative to the clean baseline.",
        "clinical_safety_relevance": "Translates adversarial degradation into changes in missed fall rate, recall/sensitivity, F1-score, false alarms, and prediction change rate.",
        "use_in_thesis": "Use to support the argument that aggregate accuracy alone is insufficient for healthcare-relevant WiFi sensing security evaluation.",
    },
    {
        "output_id": "Figure 2",
        "output_type": "Figure",
        "title": "FGSM vs PGD Epsilon Sweep Curves",
        "primary_file": "figures/thesis_figure_2_fgsm_pgd_epsilon_sweep.png",
        "companion_note": "notes/thesis_figure_2_fgsm_pgd_epsilon_sweep.md",
        "generation_script": "scripts/create_thesis_figure_2_fgsm_pgd_epsilon_sweep.py",
        "thesis_contribution": "Shows perturbation-strength dose-response behavior for FGSM and PGD.",
        "clinical_safety_relevance": "Shows how increasing epsilon changes missed fall rate, recall/sensitivity, F1-score, and false fall alarms.",
        "use_in_thesis": "Use to show that safety-proxy degradation can be analyzed across attack strength rather than only at one epsilon.",
    },
    {
        "output_id": "Table 3",
        "output_type": "Table",
        "title": "Defense Tradeoff Table",
        "primary_file": "results/thesis_table_3_defense_tradeoff.csv",
        "companion_note": "notes/thesis_table_3_defense_tradeoff.md",
        "generation_script": "scripts/create_thesis_table_3_defense_tradeoff.py",
        "thesis_contribution": "Compares undefended and defended conditions to evaluate whether the first short FGSM adversarial-training defense improves or worsens safety-proxy outcomes.",
        "clinical_safety_relevance": "Separates false alarm reduction from missed fall recovery, showing that a defense may improve one safety-proxy outcome while worsening or failing to recover another.",
        "use_in_thesis": "Use as the main defense-evaluation table for the first defended baseline.",
    },
    {
        "output_id": "Table 4",
        "output_type": "Table",
        "title": "Epsilon Sweep Summary Table",
        "primary_file": "results/thesis_table_4_epsilon_sweep_summary.csv",
        "companion_note": "notes/thesis_table_4_epsilon_sweep_summary.md",
        "generation_script": "scripts/create_thesis_table_4_epsilon_sweep_summary.py",
        "thesis_contribution": "Condenses the FGSM and PGD epsilon sweeps into a compact table.",
        "clinical_safety_relevance": "Reports how missed fall rate, recall/sensitivity, F1-score, and false fall alarm burden change across perturbation strengths.",
        "use_in_thesis": "Use as the table counterpart to Figure 2 and as a bridge to robustness failure-threshold analysis.",
    },
    {
        "output_id": "Figure 3",
        "output_type": "Figure",
        "title": "Defense Effect Summary",
        "primary_file": "figures/thesis_figure_3_defense_effect_summary.png",
        "companion_note": "notes/thesis_figure_3_defense_effect_summary.md",
        "generation_script": "scripts/create_thesis_figure_3_defense_effect_summary.py",
        "thesis_contribution": "Provides a compact visual summary of the defended-vs-undefended attack results.",
        "clinical_safety_relevance": "Highlights that the first short defense reduced false fall alarms under attack but did not recover fall recall at epsilon 0.030.",
        "use_in_thesis": "Use as a concise visual defense-result figure in the robustness/defense chapter.",
    },
    {
        "output_id": "Figure 4",
        "output_type": "Figure",
        "title": "Clean vs Defended Clean Tradeoff",
        "primary_file": "figures/thesis_figure_4_clean_defense_tradeoff.png",
        "companion_note": "notes/thesis_figure_4_clean_defense_tradeoff.md",
        "generation_script": "scripts/create_thesis_figure_4_clean_defense_tradeoff.py",
        "thesis_contribution": "Shows the clean-condition cost of the defended model compared with the undefended clean baseline.",
        "clinical_safety_relevance": "Shows that a defense can reduce false alarms while increasing missed falls under clean conditions.",
        "use_in_thesis": "Use to discuss the clean-performance tradeoff that must be considered before interpreting a defense as beneficial.",
    },
    {
        "output_id": "Figure 5",
        "output_type": "Figure",
        "title": "Binary Fall-vs-Non-Fall Confusion Matrices",
        "primary_file": "figures/thesis_figure_5_confusion_matrices.png",
        "companion_note": "notes/thesis_figure_5_confusion_matrices.md",
        "generation_script": "scripts/create_thesis_figure_5_confusion_matrices.py",
        "thesis_contribution": "Shows binary confusion matrices for clean, FGSM, PGD, defended clean, defended FGSM, and defended PGD conditions.",
        "clinical_safety_relevance": "Makes the safety-proxy error modes visible: detected falls, missed falls, false fall alarms, and correctly rejected non-falls.",
        "use_in_thesis": "Use to explain how adversarial attacks and defense change the binary confusion-matrix structure behind the summary metrics.",
    },
    {
        "output_id": "Table 5",
        "output_type": "Table",
        "title": "Reproducibility Configuration Table",
        "primary_file": "results/thesis_table_5_reproducibility_configuration.csv",
        "companion_note": "notes/thesis_table_5_reproducibility_configuration.md",
        "generation_script": "scripts/create_thesis_table_5_reproducibility_configuration.py",
        "thesis_contribution": "Documents dataset, model, attack settings, defense settings, evaluated windows, label mapping, and claim boundaries.",
        "clinical_safety_relevance": "Clarifies that current results are window-level safety-proxy metrics and not event-level clinical outcomes.",
        "use_in_thesis": "Use as the reproducibility and scope table for repeating the workflow with another dataset.",
    },
    {
        "output_id": "Table 6",
        "output_type": "Index Table",
        "title": "Thesis Output Index / Evidence Contribution Table",
        "primary_file": "results/thesis_table_6_output_index.csv",
        "companion_note": "notes/thesis_table_6_output_index.md",
        "generation_script": "scripts/create_thesis_table_6_output_index.py",
        "thesis_contribution": "Indexes thesis-ready tables, figures, notes, scripts, and evidence contributions generated by the demo.",
        "clinical_safety_relevance": "Keeps the safety-proxy evidence set navigable and separates quantitative results, figures, metadata limitations, and conceptual diagrams.",
        "use_in_thesis": "Use as the output navigation table and appendix-style artifact index for the experiment.",
    },
    {
        "output_id": "Audit 1",
        "output_type": "Dataset Audit Note",
        "title": "UT-HAR Dataset Metadata Audit",
        "primary_file": "notes/ut_har_dataset_metadata_audit.md",
        "companion_note": "not applicable",
        "generation_script": "manual note",
        "thesis_contribution": "Audits whether the local UT-HAR files support event-level timing, subject, trial, or recording metadata.",
        "clinical_safety_relevance": "Explains why the current demo can compute window-level safety-proxy metrics but cannot compute event-level metrics such as time-to-detection, delayed detection, long-lie proxy, or false alarms per hour/day.",
        "use_in_thesis": "Use as the dataset limitation and future collaboration justification note.",
    },
    {
        "output_id": "Table 7",
        "output_type": "Table",
        "title": "Safety Metric Availability and Data Requirement Table",
        "primary_file": "results/thesis_table_7_metric_availability.csv",
        "companion_note": "notes/thesis_table_7_metric_availability.md",
        "generation_script": "scripts/create_thesis_table_7_metric_availability.py",
        "thesis_contribution": "Separates metrics computable from current UT-HAR window-level outputs from metrics requiring richer event-level, timing, subject, trial, room/session, or recording-duration metadata.",
        "clinical_safety_relevance": "Prevents overclaiming by identifying which clinical-safety metrics are not computable with the current dataset.",
        "use_in_thesis": "Use as the metric feasibility and data-requirement table for future dataset selection and collaboration planning.",
    },
    {
        "output_id": "Table 8",
        "output_type": "Table",
        "title": "High-Risk Multiclass Error Taxonomy",
        "primary_file": "results/thesis_table_8_high_risk_multiclass_error_taxonomy.csv",
        "companion_note": "notes/thesis_table_8_high_risk_multiclass_error_taxonomy.md",
        "generation_script": "scripts/create_thesis_table_8_high_risk_multiclass_error_taxonomy.py",
        "thesis_contribution": "Identifies fall-relevant seven-class error pathways behind missed falls and false fall alarms.",
        "clinical_safety_relevance": "Shows which non-fall classes absorb true fall windows and which non-fall activities become false fall alarms.",
        "use_in_thesis": "Use as the multiclass explanation behind the binary fall-vs-non-fall safety-proxy results.",
    },
    {
        "output_id": "Figure 6",
        "output_type": "Figure",
        "title": "Seven-Class Confusion Matrix Figure",
        "primary_file": "figures/thesis_figure_6_seven_class_confusion_matrices.png",
        "companion_note": "notes/thesis_figure_6_seven_class_confusion_matrices.md",
        "generation_script": "scripts/create_thesis_figure_6_seven_class_confusion_matrices.py",
        "thesis_contribution": "Visualizes full seven-class confusion matrices for clean, attacked, and defended conditions.",
        "clinical_safety_relevance": "Complements Table 8 by making high-risk multiclass confusion pathways visible.",
        "use_in_thesis": "Use as the visual multiclass error-analysis figure.",
    },
    {
        "output_id": "Table 9",
        "output_type": "Table",
        "title": "Robustness Failure Threshold Table",
        "primary_file": "results/thesis_table_9_robustness_failure_thresholds.csv",
        "companion_note": "notes/thesis_table_9_robustness_failure_thresholds.md",
        "generation_script": "scripts/create_thesis_table_9_robustness_failure_thresholds.py",
        "thesis_contribution": "Identifies the first observed epsilon where FGSM or PGD crosses predefined window-level robustness failure thresholds.",
        "clinical_safety_relevance": "Translates epsilon sweeps into safety-proxy threshold language, such as severe missed-fall behavior, recall collapse, prediction instability, and high false-alarm burden.",
        "use_in_thesis": "Use to argue that adversarial impact should be reported as safety-proxy failure thresholds, not only aggregate accuracy loss.",
    },
    {
        "output_id": "Figure 7",
        "output_type": "Figure",
        "title": "Failure Threshold / Robustness Collapse Plot",
        "primary_file": "figures/thesis_figure_7_failure_threshold_plot.png",
        "companion_note": "notes/thesis_figure_7_failure_threshold_plot.md",
        "generation_script": "scripts/create_thesis_figure_7_failure_threshold_plot.py",
        "thesis_contribution": "Visualizes FGSM and PGD robustness-collapse behavior across epsilon values.",
        "clinical_safety_relevance": "Shows missed-fall, recall, false-alarm, and prediction-instability threshold crossings.",
        "use_in_thesis": "Use as the visual counterpart to Table 9.",
    },
    {
        "output_id": "Figure 8",
        "output_type": "Conceptual Figure",
        "title": "Safety Translation Pipeline Diagram",
        "primary_file": "figures/thesis_figure_8_safety_translation_pipeline.png",
        "companion_note": "notes/thesis_figure_8_safety_translation_pipeline.md",
        "generation_script": "scripts/create_thesis_figure_8_safety_translation_pipeline.py",
        "thesis_contribution": "Summarizes the full safety-translation pipeline from WiFi CSI predictions to window-level safety-proxy metrics and future event-level requirements.",
        "clinical_safety_relevance": "Clearly separates the current window-level contribution from future clinical-safety extensions that require richer metadata.",
        "use_in_thesis": "Use as the conceptual workflow diagram in the methods or thesis contribution section.",
    },
]


FIELDNAMES = [
    "output_id",
    "output_type",
    "title",
    "primary_file",
    "primary_file_exists",
    "companion_note",
    "companion_note_exists",
    "generation_script",
    "generation_script_exists",
    "thesis_contribution",
    "clinical_safety_relevance",
    "use_in_thesis",
    "claim_boundary",
]


def exists_status(path_text):
    if path_text in {"not applicable", "manual note"}:
        return "not applicable"

    path = ROOT / path_text
    return "yes" if path.exists() else "no"


def md_escape(value):
    text = str(value)
    text = text.replace("|", "\\|")
    text = text.replace("\n", " ")
    return text


def enrich_rows(rows):
    enriched = []
    for row in rows:
        output_row = dict(row)
        output_row["primary_file_exists"] = exists_status(row["primary_file"])
        output_row["companion_note_exists"] = exists_status(row["companion_note"])
        output_row["generation_script_exists"] = exists_status(row["generation_script"])
        output_row["claim_boundary"] = CLAIM_BOUNDARY
        enriched.append(output_row)
    return enriched


def write_csv(rows):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(rows):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Thesis Table 6: Thesis Output Index / Evidence Contribution Table")
    lines.append("")
    lines.append(
        "This table indexes the thesis-ready tables, figures, notes, scripts, "
        "and evidence contributions generated for the WiFi CSI Fall Attack-Safety Demo."
    )
    lines.append("")
    lines.append(
        "The purpose is to make the repository easier to navigate, explain what each "
        "output contributes to the thesis, and separate quantitative results, visual "
        "summaries, defense analysis, epsilon-sweep analysis, confusion-matrix analysis, "
        "metadata limitations, robustness-threshold analysis, and safety-translation documentation."
    )
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Table")
    lines.append("")
    lines.append(
        "| Output | Type | Title | Primary File | Thesis Contribution | "
        "Clinical-Safety Relevance | Use in Thesis |"
    )
    lines.append("|---|---|---|---|---|---|---|")

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(row["output_id"]),
                    md_escape(row["output_type"]),
                    md_escape(row["title"]),
                    md_escape(row["primary_file"]),
                    md_escape(row["thesis_contribution"]),
                    md_escape(row["clinical_safety_relevance"]),
                    md_escape(row["use_in_thesis"]),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## File Availability Check")
    lines.append("")
    lines.append("| Output | Primary File Exists | Companion Note Exists | Generation Script Exists |")
    lines.append("|---|---:|---:|---:|")

    for row in rows:
        lines.append(
            f"| {md_escape(row['output_id'])} | "
            f"{md_escape(row['primary_file_exists'])} | "
            f"{md_escape(row['companion_note_exists'])} | "
            f"{md_escape(row['generation_script_exists'])} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Table 6 shows that the current thesis-ready output set covers eight major evidence roles:"
    )
    lines.append("")
    lines.append("1. core clean, attacked, and defended safety-proxy metrics;")
    lines.append("2. attack-impact and epsilon-sweep degradation analysis;")
    lines.append("3. defended-vs-undefended tradeoff analysis;")
    lines.append("4. binary and seven-class confusion-matrix analysis;")
    lines.append("5. reproducibility configuration for repeating the workflow with another dataset;")
    lines.append("6. dataset metadata auditing and metric-availability boundaries;")
    lines.append("7. robustness failure-threshold analysis;")
    lines.append("8. safety-translation pipeline documentation.")
    lines.append("")
    lines.append(
        "This index also makes the research boundary clear. The current outputs are strong "
        "for window-level safety-proxy analysis. Event-level fall detection, time-to-detection, "
        "delayed detection, long-lie proxy, false alarms per hour/day, subject-level robustness, "
        "and trial-level robustness require richer metadata than the current local UT-HAR copy provides."
    )
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `results/thesis_table_6_output_index.csv`")
    lines.append("- `notes/thesis_table_6_output_index.md`")
    lines.append("")

    OUTPUT_NOTE.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows = enrich_rows(ROWS)
    write_csv(rows)
    write_markdown(rows)

    print("Created updated Thesis Table 6 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Indexed outputs:")
    for row in rows:
        print(
            f"  {row['output_id']}: "
            f"primary={row['primary_file_exists']}, "
            f"note={row['companion_note_exists']}, "
            f"script={row['generation_script_exists']}"
        )


if __name__ == "__main__":
    main()