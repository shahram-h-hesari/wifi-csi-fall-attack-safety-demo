# Operating-Region Characterization

Generated: 2026-07-01T13:52:33.525Z

Analysis-only run using existing per-window CSV score exports. Fall label is class 1.
Test split assumption: 45 fall windows and 455 non-fall windows.
Decision rule: predict fall when fall score >= threshold.

## Best PGD Test Operating Points
- At FAR <= 0.10, best recall is 0.356 with TP/FP 16/45. Full point: FN=29, TN=410, FAR=0.099, threshold=0.194624, AUROC=0.833, candidate=B_G1lowFA (seed42).
- At FAR <= 0.20, best recall is 0.800 with TP/FP 36/91. Full point: FN=9, TN=364, FAR=0.200, threshold=0.153246, AUROC=0.844, candidate=optionB_maxscore (seed42).
- Target recall >= 0.80 reached at FAR <= 0.10? no.
- Target recall >= 0.80 reached at FAR <= 0.20? yes.

## PGD Test Candidates
| family | candidate | AUROC | recall@FAR<=0.10 TP/FP | recall@FAR<=0.20 TP/FP |
|---|---|---:|---:|---:|
| Option B seed42 | optionB_maxscore (seed42) | 0.844 | 0.267 (12/38) | 0.800 (36/91) |
| Variant G/G1 seed44 | G_G1_v2safety (seed44) | 0.838 | 0.222 (10/43) | 0.689 (31/85) |
| Option B seed42 | optionB_maxrec (seed42) | 0.840 | 0.333 (15/43) | 0.667 (30/80) |
| Option B/Gate reference seed42 | B_G1lowFA (seed42) | 0.833 | 0.356 (16/45) | 0.644 (29/88) |
| Variant G/G1 seed42 | G_G1_v2lowFA (seed42) | 0.833 | 0.356 (16/45) | 0.644 (29/88) |
| Option B seed42 | optionB_minFA (seed42) | 0.825 | 0.244 (11/40) | 0.644 (29/89) |
| Option B/Gate reference seed42 | B_optBminFA (seed42) | 0.825 | 0.244 (11/40) | 0.644 (29/89) |
| Variant F seed42 reference | F_lamM1p0_lamF0p5_v2lowFA (seed42) | 0.810 | 0.178 (8/45) | 0.622 (28/91) |
| Option B/Gate reference seed42 | R_G1maxrec (seed42) | 0.804 | 0.156 (7/38) | 0.511 (23/90) |
| Variant G/G1 seed42 | G_G1_v2maxrec (seed42) | 0.804 | 0.156 (7/38) | 0.511 (23/90) |
| Variant G/G1 seed42 | G_G1_v2safety (seed42) | 0.804 | 0.156 (7/38) | 0.511 (23/90) |
| Variant F seed42 reference | F_lamM1p0_lamF1p0_v2lowFA (seed42) | 0.776 | 0.089 (4/38) | 0.444 (20/89) |
| Variant F seed44 reference | F_lamM1p0_lamF1p0_v2safety (seed44) | 0.748 | 0.044 (2/9) | 0.400 (18/91) |
| Variant F seed42 reference | F_lamM1p0_lamF1p0_v2safety (seed42) | 0.769 | 0.089 (4/41) | 0.378 (17/91) |
| Variant F seed44 reference | F_lamM1p0_lamF1p0_v2lowFA (seed44) | 0.772 | 0.178 (8/41) | 0.356 (16/85) |
| Variant F seed42 reference | F_lamM1p0_lamF0p5_v2safety (seed42) | 0.730 | 0.022 (1/31) | 0.222 (10/91) |

## Validation-Only Comparators
| family | candidate | AUROC | recall@FAR<=0.10 TP/FP | recall@FAR<=0.20 TP/FP |
|---|---|---:|---:|---:|
| BASAT/Stage1 validation seed42 | ST1b6_v2lowFA (seed42) | 0.869 | 0.364 (16/40) | 0.909 (40/86) |
| SAT validation seed42 | SA1_v2lowFA (seed42) | 0.873 | 0.523 (23/45) | 0.886 (39/85) |
| GAIRAT validation seed42 | GR1_v2macroF1 (seed42) | 0.871 | 0.341 (15/38) | 0.886 (39/86) |
| BASAT/Stage1 validation seed42 | ST1b6_v2macroF1 (seed42) | 0.869 | 0.318 (14/45) | 0.864 (38/90) |
| GAIRAT validation seed42 | GR1_v2lowFA (seed42) | 0.860 | 0.250 (11/43) | 0.864 (38/90) |
| BASAT/Stage1 validation seed42 | ST1_v2lowFA (seed42) | 0.864 | 0.477 (21/45) | 0.841 (37/87) |
| BASAT/Stage1 validation seed42 | ST1_v2macroF1 (seed42) | 0.876 | 0.455 (20/43) | 0.818 (36/71) |
| SAT validation seed42 | SA1_v2macroF1 (seed42) | 0.854 | 0.295 (13/44) | 0.773 (34/90) |
| BASAT/Stage1 validation seed42 | ST1b6_v2safety (seed42) | 0.847 | 0.295 (13/41) | 0.659 (29/84) |
| GAIRAT validation seed42 | GR1_v2safety (seed42) | 0.819 | 0.295 (13/26) | 0.614 (27/90) |
| SAT validation seed42 | SA1_v2safety (seed42) | 0.821 | 0.273 (12/45) | 0.591 (26/88) |
| BASAT/Stage1 validation seed42 | ST1_v2safety (seed42) | 0.823 | 0.227 (10/38) | 0.545 (24/78) |
| BiLSTM G1 validation seed42 | BLF_v2macroF1 (seed42) | 0.726 | 0.000 (0/0) | 0.250 (11/83) |
| BiLSTM G1 validation seed42 | BLF_v2safety (seed42) | 0.710 | 0.023 (1/32) | 0.227 (10/86) |
| BiLSTM G1 validation seed42 | BLF_v2maxrec (seed42) | 0.692 | 0.000 (0/0) | 0.091 (4/67) |

## Score Availability
- epsilon 0.000: found 1 hard-prediction PGD file(s), but no fall score/probability/logit column.
- epsilon 0.005: found 1 hard-prediction PGD file(s), but no fall score/probability/logit column.
- epsilon 0.010: found 1 hard-prediction PGD file(s), but no fall score/probability/logit column.
- epsilon 0.015: found 1 hard-prediction PGD file(s), but no fall score/probability/logit column.
- epsilon 0.020: found 1 hard-prediction PGD file(s), but no fall score/probability/logit column.
- epsilon 0.025: found 1 hard-prediction PGD file(s), but no fall score/probability/logit column.
- epsilon 0.030: found 95 PGD probability/logit score file(s).
- Frozen checkpoints are present, and scripts/export_probability_predictions.py can export fall probabilities at additional epsilons without retraining.
- TRADES-named artifacts were not found in the local repo inventory.

## Hard-Prediction PGD CSVs Without Fall Scores
These files cannot support AUROC or threshold-sweep claims because no fall score/probability/logit column is present:
- results/converged_attacks/converged_seed42_pgd_predictions_legacy_epsilon_0_03.csv
- results/converged_attacks/converged_seed42_pgd_predictions_test_epsilon_0_03.csv
- results/converged_attacks/converged_seed42_pgd_sweep_predictions_legacy.csv
- results/converged_attacks/converged_seed42_pgd_sweep_predictions_test.csv
- results/converged_attacks/converged_seed43_pgd_predictions_legacy_epsilon_0_03.csv
- results/converged_attacks/converged_seed43_pgd_predictions_test_epsilon_0_03.csv
- results/converged_attacks/converged_seed43_pgd_sweep_predictions_legacy.csv
- results/converged_attacks/converged_seed43_pgd_sweep_predictions_test.csv
- results/converged_attacks/converged_seed44_pgd_predictions_legacy_epsilon_0_03.csv
- results/converged_attacks/converged_seed44_pgd_predictions_test_epsilon_0_03.csv
- results/converged_attacks/converged_seed44_pgd_sweep_predictions_legacy.csv
- results/converged_attacks/converged_seed44_pgd_sweep_predictions_test.csv
- results/converged_attacks/converged_seed45_pgd_predictions_legacy_epsilon_0_03.csv
- results/converged_attacks/converged_seed45_pgd_predictions_test_epsilon_0_03.csv
- results/converged_attacks/converged_seed45_pgd_sweep_predictions_legacy.csv
- results/converged_attacks/converged_seed45_pgd_sweep_predictions_test.csv
- results/converged_attacks/converged_seed46_pgd_predictions_legacy_epsilon_0_03.csv
- results/converged_attacks/converged_seed46_pgd_predictions_test_epsilon_0_03.csv
- results/converged_attacks/converged_seed46_pgd_sweep_predictions_legacy.csv
- results/converged_attacks/converged_seed46_pgd_sweep_predictions_test.csv
- results/converged_attacks/defended_fgsm_at_seed42_pgd_predictions_legacy_epsilon_0_03.csv
- results/converged_attacks/defended_fgsm_at_seed42_pgd_predictions_test_epsilon_0_03.csv
- results/converged_attacks/defended_fgsm_at_seed42_pgd_sweep_predictions_legacy.csv
- results/converged_attacks/defended_fgsm_at_seed42_pgd_sweep_predictions_test.csv
- results/converged_attacks/defended_fgsm_at_seed43_pgd_predictions_legacy_epsilon_0_03.csv
- results/converged_attacks/defended_fgsm_at_seed43_pgd_predictions_test_epsilon_0_03.csv
- results/converged_attacks/defended_fgsm_at_seed43_pgd_sweep_predictions_legacy.csv
- results/converged_attacks/defended_fgsm_at_seed43_pgd_sweep_predictions_test.csv
- results/converged_attacks/defended_fgsm_at_seed44_pgd_predictions_legacy_epsilon_0_03.csv
- results/converged_attacks/defended_fgsm_at_seed44_pgd_predictions_test_epsilon_0_03.csv
- results/converged_attacks/defended_fgsm_at_seed44_pgd_sweep_predictions_legacy.csv
- results/converged_attacks/defended_fgsm_at_seed44_pgd_sweep_predictions_test.csv
- results/converged_attacks/defended_fgsm_at_seed45_pgd_predictions_legacy_epsilon_0_03.csv
- results/converged_attacks/defended_fgsm_at_seed45_pgd_predictions_test_epsilon_0_03.csv
- results/converged_attacks/defended_fgsm_at_seed45_pgd_sweep_predictions_legacy.csv
- results/converged_attacks/defended_fgsm_at_seed45_pgd_sweep_predictions_test.csv
- results/converged_attacks/defended_fgsm_at_seed46_pgd_predictions_legacy_epsilon_0_03.csv
- results/converged_attacks/defended_fgsm_at_seed46_pgd_predictions_test_epsilon_0_03.csv
- results/converged_attacks/defended_fgsm_at_seed46_pgd_sweep_predictions_legacy.csv
- results/converged_attacks/defended_fgsm_at_seed46_pgd_sweep_predictions_test.csv
- ... 241 more

## Data Checks
- Score files analyzed: 31
- All analyzed test score files matched the expected 45 fall / 455 non-fall split.