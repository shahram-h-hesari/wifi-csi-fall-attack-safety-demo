# Artifact Audit Investigation Report

**Branch:** cleanup/artifact-audit  
**Date:** 2026-06-11  
**Scope:** Read-only audit. No files were modified, moved, or deleted.

---

## 1. Current Artifact Count

| Category | Count | Notes |
|---|---:|---|
| Scripts (`scripts/*.py`) | 62 | 19 pipeline + 43 thesis create/export |
| Results — top-level CSVs | 26 | Pipeline + thesis tables 1–27 |
| Results — `epsilon_sweep_predictions/` CSVs | 37 | 18 eps × 2 attacks + 1 summary |
| Results total | 63 | |
| Figures (`figures/*.png`) | 45 | 17 pre-thesis + 1 fgsm_vs_pgd + 27 thesis |
| Notes (`notes/*.md`) | 61 | 20 pipeline notes + 41 thesis notes/logs |
| README.md | 1 | 3137 lines |
| THIRD_PARTY_NOTICES.md | 1 | |
| **Total tracked files** | **~233** | Excludes local-only data/model files |

---

## 2. Redundancy Map

### 2A. Pre-thesis figures superseded by thesis figures

All 17 of these figures were produced before the thesis table/figure creation phase. Their content is now covered by thesis figures.

| Pre-thesis figure | Superseded by |
|---|---|
| `fgsm_epsilon_vs_missed_fall_rate.png` | Figure 2, Figure 27A |
| `fgsm_epsilon_vs_false_alarm_count.png` | Figure 2, Figure 27A |
| `fgsm_epsilon_vs_recall.png` | Figure 2, Figure 27A |
| `fgsm_epsilon_vs_f1_score.png` | Figure 2, Figure 27A |
| `fgsm_epsilon_combined_safety_summary.png` | Figure 2 |
| `pgd_epsilon_vs_missed_fall_rate.png` | Figure 2, Figure 27A |
| `pgd_epsilon_vs_false_alarm_count.png` | Figure 2, Figure 27A |
| `pgd_epsilon_vs_recall.png` | Figure 2, Figure 27A |
| `pgd_epsilon_vs_f1_score.png` | Figure 2, Figure 27A |
| `pgd_epsilon_combined_safety_summary.png` | Figure 2 |
| `fgsm_vs_pgd_safety_comparison.png` | Figure 2, Figure 27A |
| `defended_vs_undefended_missed_fall_rate.png` | Figure 1, Figure 3 |
| `defended_vs_undefended_false_alarm_count.png` | Figure 1, Figure 3 |
| `defended_vs_undefended_recall.png` | Figure 1, Figure 3 |
| `defended_vs_undefended_f1_score.png` | Figure 1, Figure 3 |
| `defended_vs_undefended_balanced_accuracy.png` | Figure 1, Figure 3 |
| `defended_vs_undefended_prediction_change_rate.png` | Figure 1, Figure 3 |

### 2B. Plot scripts whose primary outputs are superseded

These 5 scripts generated the pre-thesis figures above. Their data-generation logic is superseded by thesis scripts.

| Script | Superseded by |
|---|---|
| `plot_fgsm_epsilon_sweep.py` | `create_thesis_figure_2_*`, `create_thesis_table_27_*` |
| `plot_fgsm_epsilon_combined_summary.py` | `create_thesis_figure_2_*` |
| `plot_pgd_epsilon_sweep.py` | `create_thesis_figure_2_*`, `create_thesis_table_27_*` |
| `plot_fgsm_vs_pgd_comparison.py` | `create_thesis_figure_2_*` |
| `plot_defended_vs_undefended_safety_comparison.py` | `create_thesis_figure_1/3/4_*` |

### 2C. Overlapping thesis figures (within the thesis set)

These pairs/groups share conceptual territory but are not exact duplicates. They are listed here for decision, not for immediate removal.

| Group | Figures | Overlap description |
|---|---|---|
| Epsilon dose-response | Figure 2 (5-pt sweep) vs Figure 27A/27B (18-pt sweep) | Both show FNR vs epsilon. Figure 27 is strictly stronger for the anti-cherry-pick argument. Figure 2 uses a different 4-panel format. Complementary but may be redundant in a trimmed thesis. |
| Defense overview | Figure 1 (all 6 conditions) vs Figure 3 (attacked before/after defense only) | Figure 3 is a subset view of Figure 1's data. Figure 3 emphasizes false-alarm reduction clearly; Figure 1 shows the full picture. In a tight thesis, Figure 3 could be demoted to supplementary. |
| Error burden | Figure 5 (binary confusion matrices) vs Figure 9 (stacked error burden composition) | Same confusion-matrix data, different visualization. Figure 5 is standard format; Figure 9 is a stacked bar alternative. Complementary but partially redundant. |
| Confidence failures | Figure 11 (high-confidence missed-fall comparison), Figure 12 (confidence-safety failure map), Figure 13 (confidence-safety failure ranking) | Three figures all addressing the same analysis angle. A tighter set would be Figure 12 (2D map) + Figure 13 (ranked bar), with Figure 11 demoted to supplementary or merged into 12. |
| Meta/documentation | Figure 21 (claim boundary matrix), Figure 22 (artifact evidence map) | Both are meta-documentation figures, not experimental results. Useful for appendix, GitHub, or thesis front-matter, but are edge cases for the main thesis chapter. |

### 2D. Thesis tables with potential consolidation opportunities

| Group | Tables | Overlap description |
|---|---|---|
| Epsilon sweep | Table 4 (5-pt compact) + Table 27 (18-pt dose response) | Table 27 strictly extends Table 4. In a final thesis, Table 27 replaces Table 4's role. Table 4 can remain as a readable compact reference or be merged as a sub-table of Table 27. |
| Core safety metrics | Table 1 (summary) + Table 10 (extended diagnostic) + Table 11 (amplification ratios) | Tables 10 and 11 derive from the same confusion-matrix data as Table 1 but add derived ratios. They extend rather than duplicate Table 1. |
| Safety decomposition | Table 23 (priority sensitivity) + Table 24 (recovery residual gap) + Table 25 (score component decomposition) | These three were created in rapid succession and cover similar territory: how different weighting schemes change the safety-priority interpretation. They could potentially be merged into one extended sensitivity/decomposition table. |
| Meta documentation | Table 6 (output index) + Table 21 (claim boundary) + Table 22 (evidence map) | Three meta/documentation tables. All are valuable but serve administrative/navigation roles rather than experimental evidence roles. |

### 2E. Superseded notes

These pipeline logs and planning documents are fully absorbed into the README, thesis notes, or the thesis table/figure companion notes.

| Note | Status |
|---|---|
| `fgsm_epsilon_sweep_log.md` | Superseded by thesis_table_4 and thesis_table_27 notes |
| `fgsm_epsilon_sweep_figures_summary.md` | Superseded by thesis_figure_2 note |
| `pgd_epsilon_sweep_log.md` | Superseded by thesis_table_4 and thesis_table_27 notes |
| `pgd_epsilon_sweep_figures_summary.md` | Superseded by thesis_figure_2 note |
| `fgsm_vs_pgd_comparison_summary.md` | Superseded by thesis_table_4 and thesis_figure_2 notes |
| `adversarial_training_defense_plan.md` | Planning doc; content absorbed into README and thesis notes |
| `fgsm_adversarial_training_defense_log.md` | Log absorbed into README section 17 |
| `pgd_prediction_export_log.md` | Log absorbed into README section 12/13 |
| `pgd_safety_proxy_metrics_log.md` | Log absorbed into README section 12/13 |
| `fgsm_safety_proxy_metrics_log.md` | Log absorbed into README section 10 |
| `clean_safety_proxy_metrics_log.md` | Log absorbed into README section 8 |
| `defended_vs_undefended_safety_comparison_plan.md` | Planning doc absorbed into README section 18 |
| `defended_vs_undefended_safety_comparison_log.md` | Log absorbed into README section 18 and thesis_table_1 note |
| `experiment_status_summary.md` | Superseded by README sections 6/6A and thesis table notes |
| `thesis_output_status_summary_through_figure_14.md` | Stale (only covers through Table 14); superseded by README section 6A |

### 2F. Stale index / README issues

1. **Table 6 (output index) is out of date.** `results/thesis_table_6_output_index.csv` and `notes/thesis_table_6_output_index.md` only cover Tables 1–14. Tables 15–27 are not indexed there.

2. **README.md is 3137 lines.** Sections 23–27+ in the README repeat content already captured in companion notes. This creates a maintenance burden where the same numbers appear in two places and can drift.

3. **`thesis_output_status_summary_through_figure_14.md` is stale.** The title says "through Figure 14" but the current output runs through Table/Figure 27.

### 2G. Missing note

`notes/thesis_figure_14_matched_attack_defense_effect_comparison.md` does not exist. Every other figure in the 1–13 range has its own companion note. Tables 15–27 combined their table and figure notes into a single file, which is a better pattern, but Table 14 follows the earlier separate-note pattern and is missing its figure note.

### 2H. No Figure 26

`thesis_figure_26_*.png` does not exist. This is correct: Table 26 is a prediction-column provenance audit with no associated figure. It is not a gap.

### 2I. Raw data files in `epsilon_sweep_predictions/`

The folder contains 36 individual per-epsilon prediction CSVs (18 FGSM + 18 PGD) plus one summary. These are the raw data source for Table 27. They are not thesis artifacts themselves — they are intermediate pipeline outputs. They are large in aggregate and have no documentation note. They should be documented as raw data, not cited as thesis outputs.

---

## 3. Full Artifact Classification Table

### 3A. Scripts

| Script | Type | Thesis value | Redundancy concern | Recommendation |
|---|---|---|---|---|
| `run_sensefi_smoke_test.py` | Pipeline | Low (test only) | None | Keep |
| `run_sensefi_clean_baseline_short.py` | Pipeline | High (generates model) | None | Keep |
| `export_clean_predictions_short.py` | Pipeline | High (generates primary data) | None | Keep |
| `compute_clean_safety_metrics.py` | Pipeline | High | None | Keep |
| `export_fgsm_predictions_short.py` | Pipeline | High | None | Keep |
| `compute_fgsm_safety_metrics.py` | Pipeline | High | None | Keep |
| `run_fgsm_epsilon_sweep_short.py` | Pipeline | High (generates sweep data) | None | Keep |
| `plot_fgsm_epsilon_sweep.py` | Pipeline plot | Low | Output superseded by thesis Figure 2 | Archive |
| `plot_fgsm_epsilon_combined_summary.py` | Pipeline plot | Low | Output superseded by thesis Figure 2 | Archive |
| `export_pgd_predictions_short.py` | Pipeline | High | None | Keep |
| `compute_pgd_safety_metrics.py` | Pipeline | High | None | Keep |
| `run_pgd_epsilon_sweep_short.py` | Pipeline | High (generates sweep data) | None | Keep |
| `plot_pgd_epsilon_sweep.py` | Pipeline plot | Low | Output superseded by thesis Figure 2 | Archive |
| `plot_fgsm_vs_pgd_comparison.py` | Pipeline plot | Low | Output superseded by thesis Figure 2 | Archive |
| `train_fgsm_adversarial_defense_short.py` | Pipeline | High (generates defense model) | None | Keep |
| `export_defended_predictions_short.py` | Pipeline | High | None | Keep |
| `compute_defended_safety_metrics.py` | Pipeline | High | None | Keep |
| `compare_defended_vs_undefended_safety_metrics.py` | Pipeline | High (generates comparison CSV) | None | Keep |
| `plot_defended_vs_undefended_safety_comparison.py` | Pipeline plot | Low | Output superseded by thesis Figures 1/3/4 | Archive |
| `export_attack_prediction_sweep_18eps.py` | Pipeline | High (generates 18-eps sweep data) | None | Keep |
| `create_thesis_table_1_safety_metrics.py` | Thesis | High | None | Keep |
| `create_thesis_figure_1_safety_tradeoff.py` | Thesis | High | None | Keep |
| `create_thesis_table_2_attack_impact_delta.py` | Thesis | High | None | Keep |
| `create_thesis_figure_2_fgsm_pgd_epsilon_sweep.py` | Thesis | Medium | Overlaps with Figure 27 (5-pt vs 18-pt) | Keep for now; review against Figure 27 |
| `create_thesis_table_3_defense_tradeoff.py` | Thesis | High | None | Keep |
| `create_thesis_table_4_epsilon_sweep_summary.py` | Thesis | Medium | Overlaps with Table 27 (5-pt vs 18-pt) | Keep; may consolidate with Table 27 |
| `create_thesis_figure_3_defense_effect_summary.py` | Thesis | Medium | Partial overlap with Figure 1 | Keep; review against Figure 1 |
| `create_thesis_figure_4_clean_defense_tradeoff.py` | Thesis | High | Distinct from Figure 1 (clean cost only) | Keep |
| `create_thesis_figure_5_confusion_matrices.py` | Thesis | High | None | Keep |
| `create_thesis_table_5_reproducibility_configuration.py` | Thesis | High | None | Keep |
| `create_thesis_table_6_output_index.py` | Thesis (meta) | Medium | Stale: only covers Tables 1–14 | Keep; update index |
| `create_thesis_table_7_metric_availability.py` | Thesis | High (scope boundary) | None | Keep |
| `create_thesis_table_8_high_risk_multiclass_error_taxonomy.py` | Thesis | High | None | Keep |
| `create_thesis_figure_6_seven_class_confusion_matrices.py` | Thesis | High | None | Keep |
| `create_thesis_table_9_robustness_failure_thresholds.py` | Thesis | High | Unique threshold-crossing framing | Keep |
| `create_thesis_figure_7_failure_threshold_plot.py` | Thesis | High | None | Keep |
| `create_thesis_figure_8_safety_translation_pipeline.py` | Thesis | High (conceptual, unique) | None | Keep |
| `create_thesis_table_10_extended_diagnostic_safety_metrics.py` | Thesis | Medium | Derives from same data as Table 1 | Keep; consider appendix |
| `create_thesis_figure_9_safety_error_burden_composition.py` | Thesis | Medium | Partial overlap with Figure 5 | Keep; review against Figure 5 |
| `create_thesis_table_11_attack_induced_safety_risk_amplification.py` | Thesis | Medium | Derives from same data as Tables 1/2 | Keep; consider appendix |
| `create_thesis_figure_10_high_risk_multiclass_fall_error_pathways.py` | Thesis | High | Complements Figure 6 | Keep |
| `create_thesis_table_12_model_confidence_error_summary.py` | Thesis | High | None | Keep |
| `create_thesis_figure_11_high_confidence_missed_fall_comparison.py` | Thesis | Medium | Overlaps with Figure 12/13 | Keep; review for merge with Figure 12 |
| `create_thesis_figure_12_confidence_safety_failure_map.py` | Thesis | High | None | Keep |
| `create_thesis_table_13_confidence_safety_failure_ranking.py` | Thesis | High | None | Keep |
| `create_thesis_figure_13_confidence_safety_failure_ranking.py` | Thesis | High | None | Keep |
| `create_thesis_table_14_matched_attack_defense_effect_summary.py` | Thesis | High | None | Keep |
| `create_thesis_figure_14_matched_attack_defense_effect_comparison.py` | Thesis | High | None | Keep |
| `create_thesis_table_15_figure_15_paired_safety_state_transitions.py` | Thesis | High | None | Keep |
| `create_thesis_table_16_figure_16_alert_trustworthiness.py` | Thesis | High | None | Keep |
| `create_thesis_table_17_figure_17_class_normalized_false_alarm_sources.py` | Thesis | High | None | Keep |
| `create_thesis_table_18_figure_18_class_normalized_defense_effect.py` | Thesis | High | None | Keep |
| `create_thesis_table_19_figure_19_missed_fall_destination_classes.py` | Thesis | High | None | Keep |
| `create_thesis_table_20_figure_20_fall_window_recovery_persistence.py` | Thesis | High | None | Keep |
| `create_thesis_table_21_figure_21_claim_boundary_evidence_matrix.py` | Thesis (meta) | Medium | Meta documentation | Keep; use in appendix/README |
| `create_thesis_table_22_figure_22_thesis_artifact_evidence_map.py` | Thesis (meta) | Medium | Meta documentation | Keep; use in appendix/README |
| `create_thesis_table_23_figure_23_safety_priority_sensitivity.py` | Thesis | Medium | Territory overlaps with Tables 24/25 | Review for consolidation |
| `create_thesis_table_24_figure_24_defense_recovery_residual_gap.py` | Thesis | High | None | Keep |
| `create_thesis_table_25_figure_25_safety_score_component_decomposition.py` | Thesis | Medium | Territory overlaps with Tables 23/24 | Review for consolidation |
| `create_thesis_table_26_prediction_column_provenance_audit.py` | Thesis (QA) | Medium | Internal QA; no figure; no thesis body role | Keep in archive or appendix |
| `create_thesis_table_27_figure_27_attack_severity_dose_response.py` | Thesis | High | None | Keep |

### 3B. Results (top-level CSVs)

| File | Type | Thesis role | Recommendation |
|---|---|---|---|
| `clean_baseline_short_metrics.csv` | Pipeline data | Training logs | Keep (input to scripts) |
| `clean_predictions_short.csv` | Primary data | Input to most thesis table scripts | Keep |
| `clean_safety_proxy_metrics.csv` | Pipeline data | Absorbed into thesis tables | Keep (reference data) |
| `fgsm_predictions_short_epsilon_0_03.csv` | Primary data | Input to thesis table scripts | Keep |
| `fgsm_safety_proxy_metrics_epsilon_0_03.csv` | Pipeline data | Absorbed into thesis tables | Keep (reference data) |
| `fgsm_epsilon_sweep_summary.csv` | Pipeline data | Input to Table 4, Table 9, Figure 7 | Keep |
| `pgd_predictions_short_epsilon_0_03.csv` | Primary data | Input to thesis table scripts | Keep |
| `pgd_safety_proxy_metrics_epsilon_0_03.csv` | Pipeline data | Absorbed into thesis tables | Keep (reference data) |
| `pgd_epsilon_sweep_summary.csv` | Pipeline data | Input to Table 4, Figure 7 | Keep |
| `fgsm_vs_pgd_epsilon_comparison.csv` | Pipeline data | Input to Tables 4, 9; Figures 2, 7 | Keep |
| `fgsm_adversarial_training_short_metrics.csv` | Pipeline data | Training logs | Keep |
| `defended_predictions_short.csv` | Primary data | Input to thesis table scripts | Keep |
| `defended_fgsm_predictions_short_epsilon_0_03.csv` | Primary data | Input to thesis table scripts | Keep |
| `defended_pgd_predictions_short_epsilon_0_03.csv` | Primary data | Input to thesis table scripts | Keep |
| `defended_safety_proxy_metrics.csv` | Pipeline data | Absorbed into thesis tables | Keep (reference data) |
| `defended_vs_undefended_safety_comparison.csv` | Pipeline data | Input to Tables 1, 3, 10, 11 | Keep |
| `thesis_table_1_safety_metrics.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_2_attack_impact_delta.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_3_defense_tradeoff.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_4_epsilon_sweep_summary.csv` | Thesis table | Compact sweep; overlaps with Table 27 | Keep; review |
| `thesis_table_5_reproducibility_configuration.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_6_output_index.csv` | Meta index | Stale (covers Tables 1–14 only) | Keep; update |
| `thesis_table_7_metric_availability.csv` | Thesis table | PRIMARY scope boundary | Keep |
| `thesis_table_8_high_risk_multiclass_error_taxonomy.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_9_robustness_failure_thresholds.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_10_extended_diagnostic_safety_metrics.csv` | Thesis table | Appendix-level detail | Keep; appendix |
| `thesis_table_11_attack_induced_safety_risk_amplification.csv` | Thesis table | Appendix-level detail | Keep; appendix |
| `thesis_table_12_model_confidence_error_summary.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_13_confidence_safety_failure_ranking.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_14_matched_attack_defense_effect_summary.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_15_paired_safety_state_transition_table.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_16_alert_trustworthiness.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_17_class_normalized_false_fall_alarm_sources.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_18_class_normalized_defense_effect.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_19_missed_fall_destination_classes.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_20_fall_window_recovery_persistence.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_21_claim_boundary_evidence_matrix.csv` | Meta table | Scope boundary doc | Keep; appendix |
| `thesis_table_22_thesis_artifact_evidence_map.csv` | Meta table | Navigation doc | Keep; appendix |
| `thesis_table_23_safety_priority_sensitivity.csv` | Thesis table | Sensitivity analysis | Keep; review consolidation |
| `thesis_table_24_defense_recovery_residual_gap.csv` | Thesis table | PRIMARY thesis output | Keep |
| `thesis_table_25_safety_score_component_decomposition.csv` | Thesis table | Decomposition detail | Keep; review consolidation |
| `thesis_table_26_prediction_column_provenance_audit.csv` | QA audit | Internal QA | Keep; appendix/archive |
| `thesis_table_27_attack_severity_dose_response.csv` | Thesis table | PRIMARY thesis output | Keep |

### 3C. Results — epsilon_sweep_predictions/

| File | Type | Recommendation |
|---|---|---|
| `fgsm_predictions_short_epsilon_0.csv` through `*_0_075.csv` (18 files) | Raw sweep data | Keep but document as raw data; not primary thesis artifacts |
| `pgd_predictions_short_epsilon_0.csv` through `*_0_075.csv` (18 files) | Raw sweep data | Keep but document as raw data |
| `attack_prediction_sweep_18eps_summary.csv` | Sweep summary | Keep; primary input to Table 27 |

### 3D. Figures

| Figure | Type | Thesis value | Redundancy concern | Recommendation |
|---|---|---|---|---|
| `fgsm_epsilon_vs_missed_fall_rate.png` | Pre-thesis | None | Superseded by thesis Figure 2/27A | Archive |
| `fgsm_epsilon_vs_false_alarm_count.png` | Pre-thesis | None | Superseded | Archive |
| `fgsm_epsilon_vs_recall.png` | Pre-thesis | None | Superseded | Archive |
| `fgsm_epsilon_vs_f1_score.png` | Pre-thesis | None | Superseded | Archive |
| `fgsm_epsilon_combined_safety_summary.png` | Pre-thesis | None | Superseded | Archive |
| `pgd_epsilon_vs_missed_fall_rate.png` | Pre-thesis | None | Superseded | Archive |
| `pgd_epsilon_vs_false_alarm_count.png` | Pre-thesis | None | Superseded | Archive |
| `pgd_epsilon_vs_recall.png` | Pre-thesis | None | Superseded | Archive |
| `pgd_epsilon_vs_f1_score.png` | Pre-thesis | None | Superseded | Archive |
| `pgd_epsilon_combined_safety_summary.png` | Pre-thesis | None | Superseded | Archive |
| `fgsm_vs_pgd_safety_comparison.png` | Pre-thesis | None | Superseded by thesis Figure 2 | Archive |
| `defended_vs_undefended_missed_fall_rate.png` | Pre-thesis | None | Superseded by thesis Figure 1/3 | Archive |
| `defended_vs_undefended_false_alarm_count.png` | Pre-thesis | None | Superseded | Archive |
| `defended_vs_undefended_recall.png` | Pre-thesis | None | Superseded | Archive |
| `defended_vs_undefended_f1_score.png` | Pre-thesis | None | Superseded | Archive |
| `defended_vs_undefended_balanced_accuracy.png` | Pre-thesis | None | Superseded | Archive |
| `defended_vs_undefended_prediction_change_rate.png` | Pre-thesis | None | Superseded | Archive |
| `thesis_figure_1_safety_tradeoff.png` | Thesis | High | None | Keep |
| `thesis_figure_2_fgsm_pgd_epsilon_sweep.png` | Thesis | Medium | 5-pt vs 18-pt overlap with Figure 27A | Keep; review |
| `thesis_figure_3_defense_effect_summary.png` | Thesis | Medium | Partial subset of Figure 1 | Keep; review |
| `thesis_figure_4_clean_defense_tradeoff.png` | Thesis | High | None | Keep |
| `thesis_figure_5_confusion_matrices.png` | Thesis | High | None | Keep |
| `thesis_figure_6_seven_class_confusion_matrices.png` | Thesis | High | None | Keep |
| `thesis_figure_7_failure_threshold_plot.png` | Thesis | High | None | Keep |
| `thesis_figure_8_safety_translation_pipeline.png` | Thesis | High | None | Keep |
| `thesis_figure_9_safety_error_burden_composition.png` | Thesis | Medium | Partial overlap with Figure 5 | Keep; review |
| `thesis_figure_10_high_risk_multiclass_fall_error_pathways.png` | Thesis | High | None | Keep |
| `thesis_figure_11_high_confidence_missed_fall_comparison.png` | Thesis | Medium | Overlaps with Figures 12/13 | Keep; review for merge |
| `thesis_figure_12_confidence_safety_failure_map.png` | Thesis | High | None | Keep |
| `thesis_figure_13_confidence_safety_failure_ranking.png` | Thesis | High | None | Keep |
| `thesis_figure_14_matched_attack_defense_effect_comparison.png` | Thesis | High | None | Keep |
| `thesis_figure_15_paired_safety_state_transition_heatmap.png` | Thesis | High | None | Keep |
| `thesis_figure_16_fall_alert_composition.png` | Thesis | High | None | Keep |
| `thesis_figure_17_class_normalized_false_fall_alarm_heatmap.png` | Thesis | High | None | Keep |
| `thesis_figure_18_class_normalized_defense_effect_heatmap.png` | Thesis | High | None | Keep |
| `thesis_figure_19_missed_fall_destination_heatmap.png` | Thesis | High | None | Keep |
| `thesis_figure_20_fall_window_recovery_persistence.png` | Thesis | High | None | Keep |
| `thesis_figure_21_claim_boundary_evidence_matrix.png` | Thesis (meta) | Medium | Documentation figure | Keep; appendix |
| `thesis_figure_22_thesis_artifact_evidence_map.png` | Thesis (meta) | Medium | Documentation figure | Keep; appendix |
| `thesis_figure_23_safety_priority_sensitivity_heatmap.png` | Thesis | Medium | Review consolidation with 24/25 | Keep; review |
| `thesis_figure_24_defense_recovery_residual_gap.png` | Thesis | High | None | Keep |
| `thesis_figure_25_safety_score_component_decomposition.png` | Thesis | Medium | Review consolidation with 23/24 | Keep; review |
| `thesis_figure_27a_attack_severity_dose_response.png` | Thesis | High | None | Keep |
| `thesis_figure_27b_attack_severity_dose_response_zoom.png` | Thesis | High | None | Keep |

### 3E. Notes

| Note | Type | Thesis value | Recommendation |
|---|---|---|---|
| `dataset_selection.md` | Research log | Low | Archive |
| `sensefi_review.md` | Research log | Low | Archive |
| `smoke_test_log.md` | Pipeline log | Low | Archive |
| `clean_baseline_short_log.md` | Pipeline log | Medium (reproducibility) | Keep |
| `clean_safety_proxy_metrics_log.md` | Pipeline log | Low | Archive |
| `fgsm_safety_proxy_metrics_log.md` | Pipeline log | Low | Archive |
| `fgsm_epsilon_sweep_log.md` | Pipeline log | Low | Archive |
| `fgsm_epsilon_sweep_figures_summary.md` | Pipeline log | Low | Archive |
| `pgd_prediction_export_log.md` | Pipeline log | Low | Archive |
| `pgd_safety_proxy_metrics_log.md` | Pipeline log | Low | Archive |
| `pgd_epsilon_sweep_log.md` | Pipeline log | Low | Archive |
| `pgd_epsilon_sweep_figures_summary.md` | Pipeline log | Low | Archive |
| `fgsm_vs_pgd_comparison_summary.md` | Pipeline log | Low | Archive |
| `experiment_status_summary.md` | Status doc | Low (superseded by README) | Archive |
| `final_fgsm_pgd_attack_safety_lab_report.md` | Lab report | HIGH (readable narrative) | Keep |
| `window_level_vs_event_level_limitations.md` | Scope doc | HIGH | Keep |
| `adversarial_training_defense_plan.md` | Planning doc | Low | Archive |
| `fgsm_adversarial_training_defense_log.md` | Pipeline log | Low | Archive |
| `defended_vs_undefended_safety_comparison_plan.md` | Planning doc | Low | Archive |
| `defended_vs_undefended_safety_comparison_log.md` | Pipeline log | Low | Archive |
| `thesis_table_1_safety_metrics.md` | Thesis note | HIGH | Keep |
| `thesis_figure_1_safety_tradeoff.md` | Thesis note | HIGH | Keep |
| `thesis_table_2_attack_impact_delta.md` | Thesis note | HIGH | Keep |
| `thesis_figure_2_fgsm_pgd_epsilon_sweep.md` | Thesis note | HIGH | Keep |
| `thesis_table_3_defense_tradeoff.md` | Thesis note | HIGH | Keep |
| `thesis_table_4_epsilon_sweep_summary.md` | Thesis note | HIGH | Keep |
| `thesis_figure_3_defense_effect_summary.md` | Thesis note | HIGH | Keep |
| `thesis_figure_4_clean_defense_tradeoff.md` | Thesis note | HIGH | Keep |
| `thesis_figure_5_confusion_matrices.md` | Thesis note | HIGH | Keep |
| `thesis_table_5_reproducibility_configuration.md` | Thesis note | HIGH | Keep |
| `ut_har_dataset_metadata_audit.md` | Dataset audit | HIGH | Keep |
| `thesis_table_6_output_index.md` | Meta index | HIGH (but stale) | Keep; update |
| `thesis_table_7_metric_availability.md` | Thesis note | HIGH | Keep |
| `thesis_table_8_high_risk_multiclass_error_taxonomy.md` | Thesis note | HIGH | Keep |
| `thesis_figure_6_seven_class_confusion_matrices.md` | Thesis note | HIGH | Keep |
| `thesis_table_9_robustness_failure_thresholds.md` | Thesis note | HIGH | Keep |
| `thesis_figure_7_failure_threshold_plot.md` | Thesis note | HIGH | Keep |
| `thesis_figure_8_safety_translation_pipeline.md` | Thesis note | HIGH | Keep |
| `thesis_table_10_extended_diagnostic_safety_metrics.md` | Thesis note | HIGH | Keep |
| `thesis_figure_9_safety_error_burden_composition.md` | Thesis note | HIGH | Keep |
| `thesis_table_11_attack_induced_safety_risk_amplification.md` | Thesis note | HIGH | Keep |
| `thesis_figure_10_high_risk_multiclass_fall_error_pathways.md` | Thesis note | HIGH | Keep |
| `thesis_table_12_model_confidence_error_summary.md` | Thesis note | HIGH | Keep |
| `thesis_figure_11_high_confidence_missed_fall_comparison.md` | Thesis note | HIGH | Keep |
| `thesis_figure_12_confidence_safety_failure_map.md` | Thesis note | HIGH | Keep |
| `thesis_table_13_confidence_safety_failure_ranking.md` | Thesis note | HIGH | Keep |
| `thesis_figure_13_confidence_safety_failure_ranking.md` | Thesis note | HIGH | Keep |
| `thesis_table_14_matched_attack_defense_effect_summary.md` | Thesis note | HIGH | Keep |
| `thesis_table_6_output_index.md` | Meta index | HIGH (but stale) | Keep; update |
| `thesis_output_status_summary_through_figure_14.md` | Status doc | Low (stale) | Archive |
| `thesis_table_15_figure_15_paired_safety_state_transitions.md` | Thesis note | HIGH | Keep |
| `thesis_table_16_figure_16_alert_trustworthiness.md` | Thesis note | HIGH | Keep |
| `thesis_table_17_figure_17_class_normalized_false_alarm_sources.md` | Thesis note | HIGH | Keep |
| `thesis_table_18_figure_18_class_normalized_defense_effect.md` | Thesis note | HIGH | Keep |
| `thesis_table_19_figure_19_missed_fall_destination_classes.md` | Thesis note | HIGH | Keep |
| `thesis_table_20_figure_20_fall_window_recovery_persistence.md` | Thesis note | HIGH | Keep |
| `thesis_table_21_figure_21_claim_boundary_evidence_matrix.md` | Thesis note | HIGH | Keep |
| `thesis_table_22_figure_22_thesis_artifact_evidence_map.md` | Thesis note | HIGH | Keep |
| `thesis_table_23_figure_23_safety_priority_sensitivity.md` | Thesis note | HIGH | Keep |
| `thesis_table_24_figure_24_defense_recovery_residual_gap.md` | Thesis note | HIGH | Keep |
| `thesis_table_25_figure_25_safety_score_component_decomposition.md` | Thesis note | HIGH | Keep |
| `thesis_table_26_prediction_column_provenance_audit.md` | QA note | Medium | Keep; appendix |
| `thesis_table_27_figure_27_attack_severity_dose_response.md` | Thesis note | HIGH | Keep |

---

## 4. Proposed Final Thesis-Ready Artifact Set

### 4A. Core thesis figures (main chapter body)

This is the minimum thesis-essential figure set. These have clear distinct purposes and do not duplicate each other.

```
Figure 1  — Full clean/attacked/defended safety tradeoff
Figure 4  — Clean vs defended-clean performance cost
Figure 5  — Binary confusion matrices for all 6 conditions
Figure 6  — Seven-class confusion matrices for all 6 conditions
Figure 7  — Robustness failure threshold plot
Figure 8  — Safety translation pipeline diagram (conceptual)
Figure 10 — Multiclass fall error pathways
Figure 12 — Confidence-safety failure map
Figure 13 — Confidence-safety failure ranking
Figure 14 — Matched attack-defense effect comparison
Figure 15 — Paired safety-state transition heatmap
Figure 16 — Fall alert composition
Figure 17 — Class-normalized false fall alarm heatmap
Figure 19 — Missed-fall destination heatmap
Figure 20 — Fall window recovery persistence
Figure 24 — Defense recovery residual gap
Figure 27A — Attack-severity dose response (18-epsilon)
Figure 27B — Attack-severity dose response zoom
```

### 4B. Core thesis figures (supplementary or secondary)

These figures are valid but partially overlap with figures above.

```
Figure 2  — FGSM vs PGD epsilon sweep curves (5-pt; review vs Figure 27A)
Figure 3  — Defense effect summary (partial overlap with Figure 1)
Figure 9  — Safety error burden composition (partial overlap with Figure 5)
Figure 11 — High-confidence missed-fall comparison (partial overlap with Figure 12)
Figure 18 — Class-normalized defense effect heatmap
Figure 23 — Safety priority sensitivity heatmap (review vs Figure 24/25)
Figure 25 — Safety score component decomposition (review vs Figure 23/24)
```

### 4C. Appendix or meta figures

```
Figure 21 — Claim boundary evidence matrix
Figure 22 — Thesis artifact evidence map
```

### 4D. Core thesis tables (main chapter body)

```
Table 1  — Clean, attacked, and defended safety-proxy metrics
Table 2  — Attack impact delta
Table 3  — Defense tradeoff
Table 5  — Reproducibility configuration
Table 7  — Metric availability and data requirements
Table 8  — High-risk multiclass error taxonomy
Table 9  — Robustness failure thresholds
Table 12 — Model confidence and error confidence summary
Table 13 — Confidence-safety failure ranking
Table 14 — Matched attack-defense effect summary
Table 15 — Paired safety-state transitions
Table 16 — Alert trustworthiness
Table 17 — Class-normalized false fall alarm sources
Table 19 — Missed-fall destination classes
Table 20 — Fall window recovery persistence
Table 24 — Defense recovery residual gap
Table 27 — Attack-severity dose response (18-epsilon)
```

### 4E. Supplementary or appendix tables

```
Table 4  — Epsilon sweep summary (compact; review vs Table 27)
Table 6  — Thesis output index (update to cover Tables 1–27)
Table 10 — Extended diagnostic safety metrics
Table 11 — Attack-induced safety risk amplification ratios
Table 18 — Class-normalized defense effect
Table 21 — Claim boundary evidence matrix
Table 22 — Thesis artifact evidence map
Table 23 — Safety priority sensitivity (review vs Table 24/25)
Table 25 — Safety score component decomposition
Table 26 — Prediction column provenance audit
```

---

## 5. Proposed Cleanup Plan

This plan is ordered from safest/most-reversible to most impactful. No files are moved until each step is approved.

### Step 1 — Archive pre-thesis figures (17 files, safe)

Create `figures/archive/` and move these 17 pre-thesis figures there. These are 100% superseded by thesis figures. No script references them as inputs.

Files:
```
fgsm_epsilon_vs_missed_fall_rate.png
fgsm_epsilon_vs_false_alarm_count.png
fgsm_epsilon_vs_recall.png
fgsm_epsilon_vs_f1_score.png
fgsm_epsilon_combined_safety_summary.png
pgd_epsilon_vs_missed_fall_rate.png
pgd_epsilon_vs_false_alarm_count.png
pgd_epsilon_vs_recall.png
pgd_epsilon_vs_f1_score.png
pgd_epsilon_combined_safety_summary.png
fgsm_vs_pgd_safety_comparison.png
defended_vs_undefended_missed_fall_rate.png
defended_vs_undefended_false_alarm_count.png
defended_vs_undefended_recall.png
defended_vs_undefended_f1_score.png
defended_vs_undefended_balanced_accuracy.png
defended_vs_undefended_prediction_change_rate.png
```

### Step 2 — Archive superseded pipeline plot scripts (5 files, safe)

Create `scripts/archive/` and move these 5 scripts there. Their outputs are superseded. The pipeline data-generation scripts (run_*, export_*, compute_*) are NOT affected.

Files:
```
plot_fgsm_epsilon_sweep.py
plot_fgsm_epsilon_combined_summary.py
plot_pgd_epsilon_sweep.py
plot_fgsm_vs_pgd_comparison.py
plot_defended_vs_undefended_safety_comparison.py
```

### Step 3 — Archive superseded pipeline notes (15 files, safe)

Create `notes/archive/` and move these 15 notes there. Their content is absorbed into the README and thesis table/figure notes.

Files:
```
fgsm_epsilon_sweep_log.md
fgsm_epsilon_sweep_figures_summary.md
pgd_epsilon_sweep_log.md
pgd_epsilon_sweep_figures_summary.md
fgsm_vs_pgd_comparison_summary.md
adversarial_training_defense_plan.md
fgsm_adversarial_training_defense_log.md
pgd_prediction_export_log.md
pgd_safety_proxy_metrics_log.md
fgsm_safety_proxy_metrics_log.md
clean_safety_proxy_metrics_log.md
defended_vs_undefended_safety_comparison_plan.md
defended_vs_undefended_safety_comparison_log.md
experiment_status_summary.md
thesis_output_status_summary_through_figure_14.md
```

Optional archive (lower priority, have some standalone value):
```
dataset_selection.md
sensefi_review.md
smoke_test_log.md
```

### Step 4 — Add missing note (1 file)

Create `notes/thesis_figure_14_matched_attack_defense_effect_comparison.md` to fill the gap in the per-figure companion note set for Figures 1–14.

### Step 5 — Update Table 6 output index (2 files)

Re-run `scripts/create_thesis_table_6_output_index.py` (or edit it) to include Tables 15–27 and Figures 15–25/27. Update `results/thesis_table_6_output_index.csv` and `notes/thesis_table_6_output_index.md`.

### Step 6 — Trim README.md (structural improvement)

The README is 3137 lines because it inlines the full result numbers for every table and figure. The proposed structure:

- Section 1: Research goal (keep, brief)
- Section 2: Repository roles (keep, brief)
- Section 3: Experiment scope (keep, brief)
- Section 4: Dataset and model (keep)
- Section 5: Label mapping (keep)
- Section 6: Milestone table (keep — but update to include Tables 15–27)
- Section 7–18: Currently inline result numbers — REPLACE with a one-line summary + pointer to the companion note
- Section 19: File guide (keep, update to include 18-eps sweep, Tables 15–27)
- Section 20: Reproducibility commands (keep)
- Section 21: Claim boundary (keep)
- Section 22: Next planned work (update to reflect audit/cleanup branch)
- Section 23+: REMOVE inline table/figure descriptions — these live in the companion notes

This reduces the README to ~400–500 lines and eliminates content duplication.

### Step 7 — Review overlapping thesis artifact groups (decisions needed)

These require your judgment before any action:

a. **Table 4 vs Table 27**: Keep both for now. In the thesis write-up, use Table 27 as the primary dose-response table and cite Table 4 as the compact 5-epsilon reference. Or: drop Table 4 from the thesis body and keep only Table 27.

b. **Figure 2 vs Figure 27A**: Keep both for now. In the thesis write-up, Figure 2 can serve as a visual introduction before the full dose-response analysis in Figure 27. Or: drop Figure 2 and start directly with Figure 27.

c. **Tables 23/24/25** (safety priority sensitivity, recovery gap, score decomposition): These were produced in rapid succession and share the safety-score theme. Review whether all three need to be in the thesis body, or whether two of them can be moved to supplementary material or merged.

d. **Figure 3 vs Figure 1**: If you keep both, clarify in the thesis that Figure 1 shows the full picture and Figure 3 emphasizes the defense-effect contrast. Or: drop Figure 3 and add a defense-effect panel directly to Figure 1.

### Step 8 — Document epsilon_sweep_predictions/ (1 note)

Add a `results/epsilon_sweep_predictions/README_data_source.md` (or equivalent) noting that this folder contains 36 raw per-epsilon prediction CSVs generated by `export_attack_prediction_sweep_18eps.py`, used as input to Table 27, and are raw data files rather than primary thesis artifacts.

---

## 6. Summary

**Definite archive (zero ambiguity):** 17 pre-thesis figures + 5 superseded plot scripts + 15 superseded notes = **37 files to archive**.

**Definite keep:** All thesis table/figure scripts, all primary prediction CSVs, all thesis table result CSVs, all thesis companion notes, `final_fgsm_pgd_attack_safety_lab_report.md`, `window_level_vs_event_level_limitations.md`, `ut_har_dataset_metadata_audit.md`.

**Decisions needed before action:** Figure 2 vs 27A, Table 4 vs 27, Tables 23/24/25 consolidation, Figure 3 vs 1, Figure 9 vs 5, Figure 11 vs 12.

**Structural improvements (no deletions):** Update Table 6, add Figure 14 companion note, trim README, add epsilon_sweep_predictions README.
