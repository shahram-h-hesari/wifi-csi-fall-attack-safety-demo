# Thesis Table 6: Thesis Output Index / Evidence Contribution Table

This table indexes the thesis-ready tables, figures, notes, scripts, and evidence contributions generated for the WiFi CSI Fall Attack-Safety Demo.

The purpose is to make the repository easier to navigate, explain what each output contributes to the thesis, and separate quantitative results, visual summaries, defense analysis, epsilon-sweep analysis, confusion-matrix analysis, metadata limitations, robustness-threshold analysis, confidence/error-confidence analysis, matched attack-defense analysis, and safety-translation documentation.

## Claim Boundary

Research implementation only; window-level safety-proxy evaluation; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Table

| Output | Type | Title | Primary File | Thesis Contribution | Clinical-Safety Relevance | Use in Thesis |
|---|---|---|---|---|---|---|
| Table 1 | Table | Clean, Attacked, and Defended Fall Safety-Proxy Metrics | results/thesis_table_1_safety_metrics.csv | Establishes the core clean, attacked, and defended comparison for fall-vs-non-fall safety-proxy evaluation. | Reports TP, FN, FP, TN, recall/sensitivity, missed fall rate, precision, F1-score, balanced accuracy, and false fall alarm counts. | Use as the main quantitative result table for the first reproduced SenseFi UT-HAR LeNet attack-safety workflow. |
| Figure 1 | Figure | Defended vs Undefended Safety Tradeoff | figures/thesis_figure_1_safety_tradeoff.png | Visualizes the main safety tradeoff between missed fall rate and false fall alarm count across clean, attacked, and defended conditions. | Shows whether defense reduces false alarms, missed falls, or both. | Use as the first high-level visual summary of the clean-to-attack-to-defense safety-proxy result. |
| Table 2 | Table | Attack Impact Delta Table | results/thesis_table_2_attack_impact_delta.csv | Quantifies how FGSM and PGD change safety-proxy metrics relative to the clean baseline. | Translates adversarial degradation into changes in missed fall rate, recall/sensitivity, F1-score, false alarms, and prediction change rate. | Use to support the argument that aggregate accuracy alone is insufficient for healthcare-relevant WiFi sensing security evaluation. |
| Figure 2 | Figure | FGSM vs PGD Epsilon Sweep Curves | figures/thesis_figure_2_fgsm_pgd_epsilon_sweep.png | Shows perturbation-strength dose-response behavior for FGSM and PGD. | Shows how increasing epsilon changes missed fall rate, recall/sensitivity, F1-score, and false fall alarms. | Use to show that safety-proxy degradation can be analyzed across attack strength rather than only at one epsilon. |
| Table 3 | Table | Defense Tradeoff Table | results/thesis_table_3_defense_tradeoff.csv | Compares undefended and defended conditions to evaluate whether the first short FGSM adversarial-training defense improves or worsens safety-proxy outcomes. | Separates false alarm reduction from missed fall recovery, showing that a defense may improve one safety-proxy outcome while failing another. | Use as the main defense-evaluation table for the first defended baseline. |
| Table 4 | Table | Epsilon Sweep Summary Table | results/thesis_table_4_epsilon_sweep_summary.csv | Condenses the FGSM and PGD epsilon sweeps into a compact table. | Reports how missed fall rate, recall/sensitivity, F1-score, and false fall alarm burden change across perturbation strengths. | Use as the table counterpart to Figure 2 and as a bridge to robustness failure-threshold analysis. |
| Figure 3 | Figure | Defense Effect Summary | figures/thesis_figure_3_defense_effect_summary.png | Provides a compact visual summary of the defended-vs-undefended attack results. | Highlights that the first short defense reduced false fall alarms under attack but did not recover fall recall at epsilon 0.030. | Use as a concise visual defense-result figure in the robustness/defense chapter. |
| Figure 4 | Figure | Clean vs Defended Clean Tradeoff | figures/thesis_figure_4_clean_defense_tradeoff.png | Shows the clean-condition cost of the defended model compared with the undefended clean baseline. | Shows that a defense can reduce false alarms while increasing missed falls under clean conditions. | Use to discuss the clean-performance tradeoff that must be considered before interpreting a defense as beneficial. |
| Figure 5 | Figure | Binary Fall-vs-Non-Fall Confusion Matrices | figures/thesis_figure_5_confusion_matrices.png | Shows binary confusion matrices for clean, FGSM, PGD, defended clean, defended FGSM, and defended PGD conditions. | Makes the safety-proxy error modes visible: detected falls, missed falls, false fall alarms, and correctly rejected non-falls. | Use to explain how adversarial attacks and defense change the binary confusion-matrix structure behind the summary metrics. |
| Table 5 | Table | Reproducibility Configuration Table | results/thesis_table_5_reproducibility_configuration.csv | Documents dataset, model, attack settings, defense settings, evaluated windows, label mapping, and claim boundaries. | Clarifies that current results are window-level safety-proxy metrics and not event-level clinical outcomes. | Use as the reproducibility and scope table for repeating the workflow with another dataset. |
| Table 6 | Index Table | Thesis Output Index / Evidence Contribution Table | results/thesis_table_6_output_index.csv | Indexes thesis-ready tables, figures, notes, scripts, and evidence contributions generated by the demo. | Keeps the safety-proxy evidence set navigable and separates quantitative results, figures, metadata limitations, and conceptual diagrams. | Use as the output navigation table and appendix-style artifact index for the experiment. |
| Audit 1 | Dataset Audit Note | UT-HAR Dataset Metadata Audit | notes/ut_har_dataset_metadata_audit.md | Audits whether the local UT-HAR files support event-level timing, subject, trial, or recording metadata. | Explains why the current demo can compute window-level safety-proxy metrics but cannot compute event-level metrics such as time-to-detection, delayed detection, long-lie proxy, or false alarms per hour/day. | Use as the dataset limitation and future collaboration justification note. |
| Table 7 | Table | Safety Metric Availability and Data Requirement Table | results/thesis_table_7_metric_availability.csv | Separates metrics computable from current UT-HAR window-level outputs from metrics requiring richer event-level metadata. | Prevents overclaiming by identifying which clinical-safety metrics are not computable with the current dataset. | Use as the metric feasibility and data-requirement table for future dataset selection and collaboration planning. |
| Table 8 | Table | High-Risk Multiclass Error Taxonomy | results/thesis_table_8_high_risk_multiclass_error_taxonomy.csv | Identifies fall-relevant seven-class error pathways behind missed falls and false fall alarms. | Shows which non-fall classes absorb true fall windows and which non-fall activities become false fall alarms. | Use as the multiclass explanation behind the binary fall-vs-non-fall safety-proxy results. |
| Figure 6 | Figure | Seven-Class Confusion Matrix Figure | figures/thesis_figure_6_seven_class_confusion_matrices.png | Visualizes full seven-class confusion matrices for clean, attacked, and defended conditions. | Complements Table 8 by making high-risk multiclass confusion pathways visible. | Use as the visual multiclass error-analysis figure. |
| Table 9 | Table | Robustness Failure Threshold Table | results/thesis_table_9_robustness_failure_thresholds.csv | Identifies the first observed epsilon where FGSM or PGD crosses predefined window-level robustness failure thresholds. | Translates epsilon sweeps into safety-proxy threshold language, such as severe missed-fall behavior, recall collapse, prediction instability, and high false-alarm burden. | Use to argue that adversarial impact should be reported as safety-proxy failure thresholds, not only aggregate accuracy loss. |
| Figure 7 | Figure | Failure Threshold / Robustness Collapse Plot | figures/thesis_figure_7_failure_threshold_plot.png | Visualizes FGSM and PGD robustness-collapse behavior across epsilon values. | Shows missed-fall, recall, false-alarm, and prediction-instability threshold crossings. | Use as the visual counterpart to Table 9. |
| Figure 8 | Conceptual Figure | Safety Translation Pipeline Diagram | figures/thesis_figure_8_safety_translation_pipeline.png | Summarizes the full safety-translation pipeline from WiFi CSI predictions to window-level safety-proxy metrics and future event-level requirements. | Clearly separates the current window-level contribution from future clinical-safety extensions that require richer metadata. | Use as the conceptual workflow diagram in the methods or thesis contribution section. |
| Table 10 | Table | Extended Window-Level Diagnostic Safety Metrics | results/thesis_table_10_extended_diagnostic_safety_metrics.csv | Extends the safety-proxy analysis beyond recall, precision, F1-score, and balanced accuracy. | Reports additional diagnostic-style safety-proxy metrics and uses NA for undefined ratios when TP is zero. | Use to strengthen the quantitative safety-proxy metric set while avoiding fabricated undefined values. |
| Figure 9 | Figure | Safety Error Burden Composition Across Conditions | figures/thesis_figure_9_safety_error_burden_composition.png | Shows the composition of detected falls, missed falls, false fall alarms, and correct non-falls across conditions. | Makes the clean-to-attack shift visible: attacked conditions lose detected fall windows and increase missed fall burden. | Use as a visual explanation of safety-error burden behind the confusion matrices. |
| Table 11 | Table | Attack-Induced Safety Risk Amplification Ratios | results/thesis_table_11_attack_induced_safety_risk_amplification.csv | Quantifies how attacked and defended-attacked conditions amplify safety-relevant error ratios relative to clean baselines. | Highlights attack-induced amplification of missed-fall and false-alarm burden while preserving claim boundaries. | Use as a risk-amplification style summary that connects ML degradation to safety-proxy language. |
| Figure 10 | Figure | High-Risk Multiclass Fall Error Pathways | figures/thesis_figure_10_high_risk_multiclass_fall_error_pathways.png | Simplifies seven-class confusion matrices into fall-relevant error pathways. | Shows where true fall windows go when missed and which non-fall activities become false fall alarms. | Use to connect binary fall-vs-non-fall degradation to original multiclass activity-recognition errors. |
| Table 12 | Table | Model Confidence and Error Confidence Summary | results/thesis_table_12_model_confidence_error_summary.csv | Summarizes model-reported confidence for correct predictions, incorrect predictions, missed falls, and false fall alarms. | Shows whether missed-fall errors are low-confidence or high-confidence errors under attack and defense. | Use as the main confidence/error-confidence table for the attacked fall-safety workflow. |
| Figure 11 | Figure | High-Confidence Missed-Fall Error Comparison | figures/thesis_figure_11_high_confidence_missed_fall_comparison.png | Visualizes missed-fall confidence behavior across clean, attacked, and defended conditions. | Highlights that undefended PGD produces a high-confidence missed-fall failure pattern. | Use as the visual companion to Table 12. |
| Figure 12 | Figure | Confidence-Safety Failure Map | figures/thesis_figure_12_confidence_safety_failure_map.png | Combines missed fall rate and high-confidence missed-fall rate into a confidence-safety failure map. | Shows that undefended PGD is the strongest confidence-safety failure case, while defended attacked conditions still miss all falls but with lower high-confidence missed-fall rates. | Use to explain the two-dimensional relationship between missed-fall safety failure and model-reported confidence. |
| Table 13 | Table | Confidence-Safety Failure Ranking | results/thesis_table_13_confidence_safety_failure_ranking.csv | Ranks clean, attacked, and defended conditions using a descriptive confidence-safety failure score. | Identifies which conditions combine missed-fall safety failure with high model-reported confidence in the wrong prediction. | Use as the ranked numeric companion to Figure 12. |
| Figure 13 | Figure | Confidence-Safety Failure Ranking Bar Chart | figures/thesis_figure_13_confidence_safety_failure_ranking.png | Visualizes the Table 13 confidence-safety failure ranking as a horizontal bar chart. | Makes the ranking of overconfident missed-fall safety failures visually obvious. | Use as the visual companion to Table 13. |
| Table 14 | Table | Matched Attack Defense Effect Summary | results/thesis_table_14_matched_attack_defense_effect_summary.csv | Directly compares matched attacked conditions: undefended FGSM vs defended FGSM and undefended PGD vs defended PGD. | Shows that the defended attacked models reduce overconfident missed-fall behavior and false alarms but do not restore fall recall. | Use as the main matched attack-defense effect summary table. |
| Figure 14 | Figure | Matched Attack Defense Effect Comparison | figures/thesis_figure_14_matched_attack_defense_effect_comparison.png | Visually compares matched attack-defense effects for FGSM and PGD using three panels. | Shows reductions in high-confidence missed-fall rate, median missed-fall confidence, and false fall alarm count, while noting that missed fall rate remains 1.000000. | Use as the visual companion to Table 14. |

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
| Table 6 | yes | yes | yes |
| Audit 1 | yes | not applicable | not applicable |
| Table 7 | yes | yes | yes |
| Table 8 | yes | yes | yes |
| Figure 6 | yes | yes | yes |
| Table 9 | yes | yes | yes |
| Figure 7 | yes | yes | yes |
| Figure 8 | yes | yes | yes |
| Table 10 | yes | yes | yes |
| Figure 9 | yes | yes | yes |
| Table 11 | yes | yes | yes |
| Figure 10 | yes | yes | yes |
| Table 12 | yes | yes | yes |
| Figure 11 | yes | yes | yes |
| Figure 12 | yes | yes | yes |
| Table 13 | yes | yes | yes |
| Figure 13 | yes | yes | yes |
| Table 14 | yes | yes | yes |
| Figure 14 | yes | yes | yes |

## Current Indexed Output Set

```text
Table 1 - Clean, Attacked, and Defended Fall Safety-Proxy Metrics
Figure 1 - Defended vs Undefended Safety Tradeoff
Table 2 - Attack Impact Delta Table
Figure 2 - FGSM vs PGD Epsilon Sweep Curves
Table 3 - Defense Tradeoff Table
Table 4 - Epsilon Sweep Summary Table
Figure 3 - Defense Effect Summary
Figure 4 - Clean vs Defended Clean Tradeoff
Figure 5 - Binary Fall-vs-Non-Fall Confusion Matrices
Table 5 - Reproducibility Configuration Table
Table 6 - Thesis Output Index / Evidence Contribution Table
Audit 1 - UT-HAR Dataset Metadata Audit
Table 7 - Safety Metric Availability and Data Requirement Table
Table 8 - High-Risk Multiclass Error Taxonomy
Figure 6 - Seven-Class Confusion Matrix Figure
Table 9 - Robustness Failure Threshold Table
Figure 7 - Failure Threshold / Robustness Collapse Plot
Figure 8 - Safety Translation Pipeline Diagram
Table 10 - Extended Window-Level Diagnostic Safety Metrics
Figure 9 - Safety Error Burden Composition Across Conditions
Table 11 - Attack-Induced Safety Risk Amplification Ratios
Figure 10 - High-Risk Multiclass Fall Error Pathways
Table 12 - Model Confidence and Error Confidence Summary
Figure 11 - High-Confidence Missed-Fall Error Comparison
Figure 12 - Confidence-Safety Failure Map
Table 13 - Confidence-Safety Failure Ranking
Figure 13 - Confidence-Safety Failure Ranking Bar Chart
Table 14 - Matched Attack Defense Effect Summary
Figure 14 - Matched Attack Defense Effect Comparison
```

## Interpretation

Table 6 shows that the current thesis-ready output set covers ten major evidence roles:

1. core clean, attacked, and defended safety-proxy metrics;
2. attack-impact and epsilon-sweep degradation analysis;
3. defended-vs-undefended tradeoff analysis;
4. binary and seven-class confusion-matrix analysis;
5. reproducibility configuration for repeating the workflow with another dataset;
6. dataset metadata auditing and metric-availability boundaries;
7. robustness failure-threshold analysis;
8. safety-translation pipeline documentation;
9. confidence/error-confidence analysis for missed-fall failures;
10. matched attack-defense effect analysis.

This index also makes the research boundary clear. The current outputs are strong for window-level safety-proxy analysis. Event-level fall detection, time-to-detection, delayed detection, long-lie proxy, false alarms per hour/day, subject-level robustness, and trial-level robustness require richer metadata than the current local UT-HAR copy provides.

## Output Files

- `results/thesis_table_6_output_index.csv`
- `notes/thesis_table_6_output_index.md`
