# Defense Attempt Results Summary

Generated: 2026-07-02T18:58:51+00:00

Artifact inventory rows: 1102. Result rows: 5128.

## Availability by approach

- Exact TP/FN/FP/TN available: Undefended LeNet baseline, FGSM adversarial-training baseline, Fall-weighted training, Multi-budget training, Motion/margin loss, G1 hard-negative/source-aware margin, Static dual-tail rescue/budget objective, Rebalanced dual-tail with fall-rescue floor, Dual-specialist gate, AFAC fixed-threshold checkpoints, AFAC threshold-swept operating point, GAIRAT-style boundary reweighting, SAT-style selective filtering, BiLSTM representation pivot
- AUROC only: none
- Validation-only usable rows: GAIRAT-style boundary reweighting, SAT-style selective filtering, BiLSTM representation pivot
- Saved scores allow threshold sweeps: Multi-budget training, Motion/margin loss, G1 hard-negative/source-aware margin, Static dual-tail rescue/budget objective, Rebalanced dual-tail with fall-rescue floor, Dual-specialist gate, AFAC threshold-swept operating point, GAIRAT-style boundary reweighting, SAT-style selective filtering, BiLSTM representation pivot
- No usable standalone result artifact: TRADES-style fall-probability consistency

## Best fixed PGD test rows

| method_thesis_name | approach_group | seed | Rfall | FAR | TP | FN | FP | TN | source_file |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dual-specialist gate | Dual-specialist gate | 42 | 0.688889 | 0.228571 | 31 | 14 | 104 | 351 | results/safety_guided_defense/dual_specialist_safety_gate/A1/seed42/probabilities/R_G1maxrec_pgd_probabilities_test_epsilon_0_03.csv |
| G1 hard-negative/source-aware margin | G1 hard-negative/source-aware margin | 42 | 0.688889 | 0.228571 | 31 | 14 | 104 | 351 | results/safety_guided_defense/variantG_targeted_hardneg/seed42/test_eval/G_G1_v2maxrec_pgd_probabilities_test_epsilon_0_03.csv |
| G1 hard-negative/source-aware margin | G1 hard-negative/source-aware margin | 42 | 0.688889 | 0.228571 | 31 | 14 | 104 | 351 | results/safety_guided_defense/variantG_targeted_hardneg/seed42/test_eval/G_G1_v2safety_pgd_probabilities_test_epsilon_0_03.csv |
| G1 hard-negative/source-aware margin | G1 hard-negative/source-aware margin | 42 | 0.688889 | 0.228571 | 31 | 14 | 104 | 351 | results/safety_guided_defense/variantG_targeted_hardneg/seed42/test_eval/G_G1_v2safety_pgd_sweep_predictions_test.csv |
| G1 hard-negative/source-aware margin | G1 hard-negative/source-aware margin | 42 | 0.688889 | 0.228571 | 31 | 14 | 104 | 351 | results/safety_guided_defense/variantG_targeted_hardneg/seed42/test_eval/G_G1_v2safety_pgd_epsilon_sweep_test.csv |
| AFAC-recall | AFAC fixed-threshold checkpoints | 42 | 0.666667 | 0.186813 | 30 | 15 | 85 | 370 | results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/test_eval/optionB_maxrec_pgd_probabilities_test_epsilon_0_03.csv |
| Motion/margin loss | Motion/margin loss | 42 | 0.666667 | 0.252747 | 30 | 15 | 115 | 340 | results/safety_guided_defense/variantF_motion_margin/seed42/test_eval/F_lamM1p0_lamF1p0_v2safety_pgd_sweep_predictions_test.csv |
| Motion/margin loss | Motion/margin loss | 42 | 0.666667 | 0.252747 | 30 | 15 | 115 | 340 | results/safety_guided_defense/variantF_motion_margin/seed42/test_eval/F_lamM1p0_lamF1p0_v2safety_pgd_epsilon_sweep_test.csv |
| Motion/margin loss | Motion/margin loss | 42 | 0.666667 | 0.252747 | 30 | 15 | 115 | 340 | results/safety_guided_defense/variantF_motion_margin/seed42/test_eval/F_lamM1p0_lamF1p0_v2safety_pgd_safety_metrics_test_epsilon_0_03.csv |
| G1 hard-negative/source-aware margin | G1 hard-negative/source-aware margin | 42 | 0.644444 | 0.232967 | 29 | 16 | 106 | 349 | results/safety_guided_defense/variantG_targeted_hardneg/seed42/test_eval/G_G2_v2maxrec_pgd_probabilities_test_epsilon_0_03.csv |
| G1 hard-negative/source-aware margin | G1 hard-negative/source-aware margin | 42 | 0.644444 | 0.232967 | 29 | 16 | 106 | 349 | results/safety_guided_defense/variantG_targeted_hardneg/seed42/test_eval/G_G2_v2safety_pgd_probabilities_test_epsilon_0_03.csv |
| G1 hard-negative/source-aware margin | G1 hard-negative/source-aware margin | 42 | 0.644444 | 0.232967 | 29 | 16 | 106 | 349 | results/safety_guided_defense/variantG_targeted_hardneg/seed42/test_eval/G_G2_v2safety_pgd_sweep_predictions_test.csv |

## Best post-hoc PGD test rows at FAR <= 0.20

| method_thesis_name | approach_group | seed | Rfall_at_FAR_020 | TP_at_FAR_020 | FP_at_FAR_020 | AUROC | threshold | F20_reached | source_file |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AFAC-score | AFAC threshold-swept operating point | 42 | 0.8 | 36 | 91 | 0.843907 | 0.153246 | true | results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/test_eval/optionB_maxscore_pgd_probabilities_test_epsilon_0_03.csv |
| G1 hard-negative/source-aware margin | G1 hard-negative/source-aware margin | 44 | 0.688889 | 31 | 85 | 0.8379 | 0.234601 | false | results/safety_guided_defense/variantG_targeted_hardneg/seed44/test_eval/G_G1_v2safety_pgd_probabilities_test_epsilon_0_03.csv |
| Rebalanced dual-tail with fall-rescue floor | Rebalanced dual-tail with fall-rescue floor | 42 | 0.688889 | 31 | 89 | 0.824225 | 0.177115 | false | results/safety_guided_defense/variantH_dual_tail_budget/optionA_rebalanced/A1/seed42/test_eval/A1_v2safety_pgd_probabilities_test_epsilon_0_03.csv |
| AFAC-recall | AFAC threshold-swept operating point | 42 | 0.666667 | 30 | 80 | 0.839756 | 0.229193 | false | results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/test_eval/optionB_maxrec_pgd_probabilities_test_epsilon_0_03.csv |
| Dual-specialist gate | Dual-specialist gate | 42 | 0.644444 | 29 | 88 | 0.832772 | 0.087811 | false | results/safety_guided_defense/dual_specialist_safety_gate/A1/seed42/probabilities/B_G1lowFA_pgd_probabilities_test_epsilon_0_03.csv |
| G1 hard-negative/source-aware margin | G1 hard-negative/source-aware margin | 42 | 0.644444 | 29 | 88 | 0.832772 | 0.087811 | false | results/safety_guided_defense/variantG_targeted_hardneg/seed42/test_eval/G_G1_v2lowFA_pgd_probabilities_test_epsilon_0_03.csv |
| AFAC-lowFA | AFAC threshold-swept operating point | 42 | 0.644444 | 29 | 89 | 0.825397 | 0.093825 | false | results/safety_guided_defense/variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/test_eval/optionB_minFA_pgd_probabilities_test_epsilon_0_03.csv |
| Dual-specialist gate | Dual-specialist gate | 42 | 0.644444 | 29 | 89 | 0.825397 | 0.093825 | false | results/safety_guided_defense/dual_specialist_safety_gate/A1/seed42/probabilities/B_optBminFA_pgd_probabilities_test_epsilon_0_03.csv |
| G1 hard-negative/source-aware margin | G1 hard-negative/source-aware margin | 44 | 0.644444 | 29 | 91 | 0.82149 | 0.228303 | false | results/safety_guided_defense/variantG_targeted_hardneg/seed44/test_eval/G_G1_v2safety_pgd20_pgd_probabilities_test_epsilon_0_03.csv |
| G1 hard-negative/source-aware margin | G1 hard-negative/source-aware margin | 42 | 0.622222 | 28 | 85 | 0.822271 | 0.090157 | false | results/safety_guided_defense/variantG_targeted_hardneg/seed42/test_eval/G_G1_v2lowFA_pgd20_pgd_probabilities_test_epsilon_0_03.csv |
| G1 hard-negative/source-aware margin | G1 hard-negative/source-aware margin | 42 | 0.622222 | 28 | 89 | 0.832674 | 0.091949 | false | results/safety_guided_defense/variantG_targeted_hardneg/seed42/test_eval/G_G2_v2lowFA_pgd_probabilities_test_epsilon_0_03.csv |
| Motion/margin loss | Motion/margin loss | 42 | 0.622222 | 28 | 91 | 0.809768 | 0.098716 | false | results/safety_guided_defense/variantF_motion_margin/seed42/test_eval/F_lamM1p0_lamF0p5_v2lowFA_pgd_probabilities_test_epsilon_0_03.csv |

## Interpretation

- Fixed-threshold/argmax test evidence still favors the validated G1 and Variant F operating points for lower false-alarm burden at nonzero PGD recall.
- Post-hoc score thresholding changes the operating point: AFAC-score reaches the F20 criterion on test at FAR <= 0.20 from saved PGD scores.
- SAT/BASAT and GAIRAT have strong validation-score operating points, but the classified artifacts here do not provide matching test-score rows for those pilots.
- TRADES-style consistency has no classified local result artifact in this inventory.
- Existing CSVs are enough for many thesis rows, but not enough to fill a complete all-approach table without marking TRADES as not found and SAT/GAIRAT/BiLSTM pilots as validation-only.
