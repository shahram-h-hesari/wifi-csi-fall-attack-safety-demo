# Thesis Table 6: Thesis Output Index / Evidence Contribution Table

This table indexes the thesis-ready tables and figures generated for the WiFi CSI Fall Attack-Safety Demo.

The purpose is to make the repository easier to navigate, explain what each output contributes to the thesis, and separate quantitative results, visual summaries, defense analysis, epsilon-sweep analysis, confusion-matrix analysis, and reproducibility documentation.

## Claim Boundary

Research implementation only; window-level safety-proxy evaluation; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Table

| Output | Type | Title | Primary File | Thesis Contribution | Clinical-Safety Relevance | Use in Thesis |
| --- | --- | --- | --- | --- | --- | --- |
| Table 1 | Table | Clean, Attacked, and Defended Fall Safety-Proxy Metrics | results/thesis_table_1_safety_metrics.csv | Establishes the core clean, attacked, and defended comparison for fall-vs-non-fall safety-proxy evaluation. | Reports TP, FN, FP, TN, recall/sensitivity, missed fall rate, precision, F1-score, balanced accuracy, and false fall alarm counts. | Use as the main quantitative result table for the first reproduced SenseFi UT-HAR LeNet attack-safety workflow. |
| Figure 1 | Figure | Defended vs Undefended Safety Tradeoff | figures/thesis_figure_1_safety_tradeoff.png | Visualizes the main safety tradeoff between missed fall rate and false fall alarm count across clean, attacked, and defended conditions. | Shows whether defense reduces false alarms, missed falls, or both. | Use as the first high-level visual summary of the clean-to-attack-to-defense safety-proxy result. |
| Table 2 | Table | Attack Impact Delta Table | results/thesis_table_2_attack_impact_delta.csv | Quantifies how FGSM and PGD change safety-proxy metrics relative to the clean baseline. | Translates adversarial degradation into changes in missed fall rate, recall/sensitivity, F1-score, false alarms, and prediction change rate. | Use to support the argument that aggregate accuracy alone is insufficient for healthcare-relevant WiFi sensing security evaluation. |
| Figure 2 | Figure | FGSM vs PGD Epsilon Sweep Curves | figures/thesis_figure_2_fgsm_pgd_epsilon_sweep.png | Shows perturbation-strength dose-response behavior for FGSM and PGD. | Shows how increasing epsilon changes missed fall rate, recall/sensitivity, F1-score, and false fall alarms. | Use to show that safety-proxy degradation can be analyzed across attack strength rather than only at one epsilon. |
| Table 3 | Table | Defense Tradeoff Table | results/thesis_table_3_defense_tradeoff.csv | Compares undefended and defended conditions to evaluate whether the first short FGSM adversarial-training defense improves or worsens safety-proxy outcomes. | Separates false alarm reduction from missed fall recovery, showing that a defense may improve one safety-proxy outcome while worsening or failing to recover another. | Use as the main defense-evaluation table for the first defended baseline. |
| Table 4 | Table | Epsilon Sweep Summary Table | results/thesis_table_4_epsilon_sweep_summary.csv | Condenses the FGSM and PGD epsilon sweeps into a compact table. | Reports how missed fall rate, recall/sensitivity, F1-score, and false fall alarm burden change across perturbation strengths. | Use as the table counterpart to Figure 2 and as a bridge to later failure-threshold analysis. |
| Figure 3 | Figure | Defense Effect Summary | figures/thesis_figure_3_defense_effect_summary.png | Provides a compact visual summary of the defended-vs-undefended attack results. | Highlights that the first short defense reduced false fall alarms under attack but did not recover fall recall at epsilon 0.030. | Use as a concise visual defense-result figure in the robustness/defense chapter. |
| Figure 4 | Figure | Clean vs Defended Clean Tradeoff | figures/thesis_figure_4_clean_defense_tradeoff.png | Shows the clean-condition cost of the defended model compared with the undefended clean baseline. | Shows that a defense can reduce false alarms while increasing missed falls under clean conditions. | Use to discuss the clean-performance tradeoff that must be considered before interpreting a defense as beneficial. |
| Figure 5 | Figure | Binary Fall-vs-Non-Fall Confusion Matrices | figures/thesis_figure_5_confusion_matrices.png | Shows binary confusion matrices for clean, FGSM, PGD, defended clean, defended FGSM, and defended PGD conditions. | Makes the safety-proxy error modes visible: detected falls, missed falls, false fall alarms, and correctly rejected non-falls. | Use to explain how adversarial attacks and defense change the confusion-matrix structure behind the summary metrics. |
| Table 5 | Table | Reproducibility Configuration Table | results/thesis_table_5_reproducibility_configuration.csv | Documents dataset, model, attack settings, defense settings, evaluated windows, label mapping, and claim boundaries. | Clarifies that current results are window-level safety-proxy metrics and not event-level clinical outcomes. | Use as the reproducibility and scope table for repeating the workflow with another dataset. |

## File Availability Check

| Output | Primary File Exists | Companion Note Exists | Generation Script Exists |
|---|---:|---:|---:|
| Table 1 | yes | yes | yes |
| Figure 1 | yes | yes | yes |
| Table 2 | yes | yes | yes |
| Figure 2 | yes | yes | yes |
| Table 3 | yes | yes | yes |
| Table 4 | yes | yes | yes |
| Figure 3 | yes | yes | yes |
| Figure 4 | yes | yes | yes |
| Figure 5 | yes | yes | yes |
| Table 5 | yes | yes | yes |

## Interpretation

Table 6 shows that the current thesis-ready output set covers five major evidence roles:

1. core clean, attacked, and defended safety-proxy metrics;
2. attack-impact and epsilon-sweep degradation analysis;
3. defended-vs-undefended tradeoff analysis;
4. confusion-matrix visualization of binary fall-vs-non-fall error modes;
5. reproducibility configuration for repeating the workflow with another dataset.

This index also makes the next research step clearer. The current outputs are strong for window-level safety-proxy analysis. The next gap is to audit whether the dataset provides event-level timing, timestamps, subject IDs, trial IDs, recording duration, or fall start/end markers. If those metadata exist, stronger event-level metrics may be computable. If they do not exist, the limitation should be documented as a dataset constraint and future collaboration opportunity.

## Output Files

- `results/thesis_table_6_output_index.csv`
- `notes/thesis_table_6_output_index.md`
