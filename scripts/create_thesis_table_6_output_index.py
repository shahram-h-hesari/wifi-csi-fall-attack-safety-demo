"""
Create Thesis Table 6: Thesis Output Index / Evidence Contribution Table.

This script creates a thesis-ready index of every table and figure already
generated for the WiFi CSI Fall Attack-Safety Demo.

Outputs:
    results/thesis_table_6_output_index.csv
    notes/thesis_table_6_output_index.md

Claim boundary:
    This is a research implementation using window-level safety-proxy metrics
    and software-level processed-tensor adversarial perturbations.
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
    "not long-lie validation, and not physical-layer / packet-level / "
    "preamble-level / SDR / over-the-air validation."
)


ENTRIES = [
    {
        "rank": 1,
        "output_id": "Table 1",
        "output_type": "Table",
        "title": "Clean, Attacked, and Defended Fall Safety-Proxy Metrics",
        "primary_file": "results/thesis_table_1_safety_metrics.csv",
        "companion_note": "notes/thesis_table_1_safety_metrics.md",
        "generation_script": "scripts/create_thesis_table_1_safety_metrics.py",
        "primary_source_data": "results/defended_vs_undefended_safety_comparison.csv",
        "thesis_contribution": (
            "Establishes the core clean, attacked, and defended comparison for "
            "fall-vs-non-fall safety-proxy evaluation."
        ),
        "clinical_safety_relevance": (
            "Reports TP, FN, FP, TN, recall/sensitivity, missed fall rate, "
            "precision, F1-score, balanced accuracy, and false fall alarm counts."
        ),
        "use_in_thesis": (
            "Use as the main quantitative result table for the first reproduced "
            "SenseFi UT-HAR LeNet attack-safety workflow."
        ),
    },
    {
        "rank": 2,
        "output_id": "Figure 1",
        "output_type": "Figure",
        "title": "Defended vs Undefended Safety Tradeoff",
        "primary_file": "figures/thesis_figure_1_safety_tradeoff.png",
        "companion_note": "notes/thesis_figure_1_safety_tradeoff.md",
        "generation_script": "scripts/create_thesis_figure_1_safety_tradeoff.py",
        "primary_source_data": "results/defended_vs_undefended_safety_comparison.csv",
        "thesis_contribution": (
            "Visualizes the main safety tradeoff between missed fall rate and "
            "false fall alarm count across clean, attacked, and defended conditions."
        ),
        "clinical_safety_relevance": (
            "Shows whether defense reduces false alarms, missed falls, or both."
        ),
        "use_in_thesis": (
            "Use as the first high-level visual summary of the clean-to-attack-to-defense "
            "safety-proxy result."
        ),
    },
    {
        "rank": 3,
        "output_id": "Table 2",
        "output_type": "Table",
        "title": "Attack Impact Delta Table",
        "primary_file": "results/thesis_table_2_attack_impact_delta.csv",
        "companion_note": "notes/thesis_table_2_attack_impact_delta.md",
        "generation_script": "scripts/create_thesis_table_2_attack_impact_delta.py",
        "primary_source_data": (
            "results/clean_safety_proxy_metrics.csv; "
            "results/fgsm_safety_proxy_metrics.csv; "
            "results/pgd_safety_proxy_metrics.csv"
        ),
        "thesis_contribution": (
            "Quantifies how FGSM and PGD change safety-proxy metrics relative to "
            "the clean baseline."
        ),
        "clinical_safety_relevance": (
            "Translates adversarial degradation into changes in missed fall rate, "
            "recall/sensitivity, F1-score, false alarms, and prediction change rate."
        ),
        "use_in_thesis": (
            "Use to support the argument that aggregate accuracy alone is insufficient "
            "for healthcare-relevant WiFi sensing security evaluation."
        ),
    },
    {
        "rank": 4,
        "output_id": "Figure 2",
        "output_type": "Figure",
        "title": "FGSM vs PGD Epsilon Sweep Curves",
        "primary_file": "figures/thesis_figure_2_fgsm_pgd_epsilon_sweep.png",
        "companion_note": "notes/thesis_figure_2_fgsm_pgd_epsilon_sweep.md",
        "generation_script": "scripts/create_thesis_figure_2_fgsm_pgd_epsilon_sweep.py",
        "primary_source_data": (
            "results/fgsm_epsilon_sweep_short.csv; "
            "results/pgd_epsilon_sweep_short.csv"
        ),
        "thesis_contribution": (
            "Shows perturbation-strength dose-response behavior for FGSM and PGD."
        ),
        "clinical_safety_relevance": (
            "Shows how increasing epsilon changes missed fall rate, recall/sensitivity, "
            "F1-score, and false fall alarms."
        ),
        "use_in_thesis": (
            "Use to show that safety-proxy degradation can be analyzed across attack "
            "strength rather than only at one epsilon."
        ),
    },
    {
        "rank": 5,
        "output_id": "Table 3",
        "output_type": "Table",
        "title": "Defense Tradeoff Table",
        "primary_file": "results/thesis_table_3_defense_tradeoff.csv",
        "companion_note": "notes/thesis_table_3_defense_tradeoff.md",
        "generation_script": "scripts/create_thesis_table_3_defense_tradeoff.py",
        "primary_source_data": "results/defended_vs_undefended_safety_comparison.csv",
        "thesis_contribution": (
            "Compares undefended and defended conditions to evaluate whether the first "
            "short FGSM adversarial-training defense improves or worsens safety-proxy outcomes."
        ),
        "clinical_safety_relevance": (
            "Separates false alarm reduction from missed fall recovery, showing that "
            "a defense may improve one safety-proxy outcome while worsening or failing "
            "to recover another."
        ),
        "use_in_thesis": (
            "Use as the main defense-evaluation table for the first defended baseline."
        ),
    },
    {
        "rank": 6,
        "output_id": "Table 4",
        "output_type": "Table",
        "title": "Epsilon Sweep Summary Table",
        "primary_file": "results/thesis_table_4_epsilon_sweep_summary.csv",
        "companion_note": "notes/thesis_table_4_epsilon_sweep_summary.md",
        "generation_script": "scripts/create_thesis_table_4_epsilon_sweep_summary.py",
        "primary_source_data": (
            "results/fgsm_epsilon_sweep_short.csv; "
            "results/pgd_epsilon_sweep_short.csv"
        ),
        "thesis_contribution": (
            "Condenses the FGSM and PGD epsilon sweeps into a compact table."
        ),
        "clinical_safety_relevance": (
            "Reports how missed fall rate, recall/sensitivity, F1-score, and false "
            "fall alarm burden change across perturbation strengths."
        ),
        "use_in_thesis": (
            "Use as the table counterpart to Figure 2 and as a bridge to later "
            "failure-threshold analysis."
        ),
    },
    {
        "rank": 7,
        "output_id": "Figure 3",
        "output_type": "Figure",
        "title": "Defense Effect Summary",
        "primary_file": "figures/thesis_figure_3_defense_effect_summary.png",
        "companion_note": "notes/thesis_figure_3_defense_effect_summary.md",
        "generation_script": "scripts/create_thesis_figure_3_defense_effect_summary.py",
        "primary_source_data": "results/defended_vs_undefended_safety_comparison.csv",
        "thesis_contribution": (
            "Provides a compact visual summary of the defended-vs-undefended attack results."
        ),
        "clinical_safety_relevance": (
            "Highlights that the first short defense reduced false fall alarms under "
            "attack but did not recover fall recall at epsilon 0.030."
        ),
        "use_in_thesis": (
            "Use as a concise visual defense-result figure in the robustness/defense chapter."
        ),
    },
    {
        "rank": 8,
        "output_id": "Figure 4",
        "output_type": "Figure",
        "title": "Clean vs Defended Clean Tradeoff",
        "primary_file": "figures/thesis_figure_4_clean_defense_tradeoff.png",
        "companion_note": "notes/thesis_figure_4_clean_defense_tradeoff.md",
        "generation_script": "scripts/create_thesis_figure_4_clean_defense_tradeoff.py",
        "primary_source_data": "results/defended_vs_undefended_safety_comparison.csv",
        "thesis_contribution": (
            "Shows the clean-condition cost of the defended model compared with the "
            "undefended clean baseline."
        ),
        "clinical_safety_relevance": (
            "Shows that a defense can reduce false alarms while increasing missed falls "
            "under clean conditions."
        ),
        "use_in_thesis": (
            "Use to discuss the clean-performance tradeoff that must be considered "
            "before interpreting a defense as beneficial."
        ),
    },
    {
        "rank": 9,
        "output_id": "Figure 5",
        "output_type": "Figure",
        "title": "Binary Fall-vs-Non-Fall Confusion Matrices",
        "primary_file": "figures/thesis_figure_5_confusion_matrices.png",
        "companion_note": "notes/thesis_figure_5_confusion_matrices.md",
        "generation_script": "scripts/create_thesis_figure_5_confusion_matrices.py",
        "primary_source_data": "results/defended_vs_undefended_safety_comparison.csv",
        "thesis_contribution": (
            "Shows binary confusion matrices for clean, FGSM, PGD, defended clean, "
            "defended FGSM, and defended PGD conditions."
        ),
        "clinical_safety_relevance": (
            "Makes the safety-proxy error modes visible: detected falls, missed falls, "
            "false fall alarms, and correctly rejected non-falls."
        ),
        "use_in_thesis": (
            "Use to explain how adversarial attacks and defense change the confusion-matrix "
            "structure behind the summary metrics."
        ),
    },
    {
        "rank": 10,
        "output_id": "Table 5",
        "output_type": "Table",
        "title": "Reproducibility Configuration Table",
        "primary_file": "results/thesis_table_5_reproducibility_configuration.csv",
        "companion_note": "notes/thesis_table_5_reproducibility_configuration.md",
        "generation_script": "scripts/create_thesis_table_5_reproducibility_configuration.py",
        "primary_source_data": (
            "Experiment scripts, generated result files, and documented configuration values"
        ),
        "thesis_contribution": (
            "Documents dataset, model, attack settings, defense settings, evaluated windows, "
            "label mapping, and claim boundaries."
        ),
        "clinical_safety_relevance": (
            "Clarifies that current results are window-level safety-proxy metrics and not "
            "event-level clinical outcomes."
        ),
        "use_in_thesis": (
            "Use as the reproducibility and scope table for repeating the workflow with "
            "another dataset."
        ),
    },
]


FIELDNAMES = [
    "rank",
    "output_id",
    "output_type",
    "title",
    "primary_file",
    "primary_file_exists",
    "companion_note",
    "companion_note_exists",
    "generation_script",
    "generation_script_exists",
    "primary_source_data",
    "thesis_contribution",
    "clinical_safety_relevance",
    "use_in_thesis",
    "claim_boundary",
]


def exists_from_relative(relative_path: str) -> str:
    """Return yes/no for a semicolon-separated set of relative paths."""
    parts = [part.strip() for part in relative_path.split(";")]
    if not parts:
        return "no"

    statuses = []
    for part in parts:
        if not part:
            continue
        candidate = ROOT / part
        statuses.append(candidate.exists())

    if statuses and all(statuses):
        return "yes"
    if statuses and any(statuses):
        return "partial"
    return "no"


def md_escape(value) -> str:
    """Escape Markdown table-sensitive characters."""
    text = str(value)
    text = text.replace("|", "\\|")
    text = text.replace("\n", " ")
    return text


def enrich_entries():
    rows = []
    for entry in ENTRIES:
        row = dict(entry)
        row["primary_file_exists"] = exists_from_relative(row["primary_file"])
        row["companion_note_exists"] = exists_from_relative(row["companion_note"])
        row["generation_script_exists"] = exists_from_relative(row["generation_script"])
        row["claim_boundary"] = CLAIM_BOUNDARY
        rows.append(row)
    return rows


def write_csv(rows):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDNAMES})


def write_markdown(rows):
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Thesis Table 6: Thesis Output Index / Evidence Contribution Table")
    lines.append("")
    lines.append(
        "This table indexes the thesis-ready tables and figures generated for the "
        "WiFi CSI Fall Attack-Safety Demo."
    )
    lines.append("")
    lines.append(
        "The purpose is to make the repository easier to navigate, explain what each "
        "output contributes to the thesis, and separate quantitative results, visual "
        "summaries, defense analysis, epsilon-sweep analysis, confusion-matrix analysis, "
        "and reproducibility documentation."
    )
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(CLAIM_BOUNDARY)
    lines.append("")
    lines.append("## Table")
    lines.append("")

    display_fields = [
        "output_id",
        "output_type",
        "title",
        "primary_file",
        "thesis_contribution",
        "clinical_safety_relevance",
        "use_in_thesis",
    ]

    headers = [
        "Output",
        "Type",
        "Title",
        "Primary File",
        "Thesis Contribution",
        "Clinical-Safety Relevance",
        "Use in Thesis",
    ]

    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in rows:
        lines.append(
            "| "
            + " | ".join(md_escape(row[field]) for field in display_fields)
            + " |"
        )

    lines.append("")
    lines.append("## File Availability Check")
    lines.append("")
    lines.append(
        "| Output | Primary File Exists | Companion Note Exists | Generation Script Exists |"
    )
    lines.append("|---|---:|---:|---:|")

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(row["output_id"]),
                    md_escape(row["primary_file_exists"]),
                    md_escape(row["companion_note_exists"]),
                    md_escape(row["generation_script_exists"]),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Table 6 shows that the current thesis-ready output set covers five major "
        "evidence roles:"
    )
    lines.append("")
    lines.append(
        "1. core clean, attacked, and defended safety-proxy metrics;"
    )
    lines.append(
        "2. attack-impact and epsilon-sweep degradation analysis;"
    )
    lines.append(
        "3. defended-vs-undefended tradeoff analysis;"
    )
    lines.append(
        "4. confusion-matrix visualization of binary fall-vs-non-fall error modes;"
    )
    lines.append(
        "5. reproducibility configuration for repeating the workflow with another dataset."
    )
    lines.append("")
    lines.append(
        "This index also makes the next research step clearer. The current outputs "
        "are strong for window-level safety-proxy analysis. The next gap is to audit "
        "whether the dataset provides event-level timing, timestamps, subject IDs, "
        "trial IDs, recording duration, or fall start/end markers. If those metadata "
        "exist, stronger event-level metrics may be computable. If they do not exist, "
        "the limitation should be documented as a dataset constraint and future "
        "collaboration opportunity."
    )
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `results/thesis_table_6_output_index.csv`")
    lines.append("- `notes/thesis_table_6_output_index.md`")
    lines.append("")

    OUTPUT_NOTE.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows = enrich_entries()
    write_csv(rows)
    write_markdown(rows)

    print("Created Thesis Table 6 outputs:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_NOTE}")
    print("")
    print("Indexed outputs:")
    for row in rows:
        print(
            f"  {row['output_id']}: {row['title']} "
            f"(file exists: {row['primary_file_exists']})"
        )


if __name__ == "__main__":
    main()