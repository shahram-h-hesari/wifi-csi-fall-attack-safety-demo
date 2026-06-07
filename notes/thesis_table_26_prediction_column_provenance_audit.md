# Thesis Table 26: Prediction-Column Provenance and Sanity-Check Audit

## Purpose

Table 26 asks:

```text
Exactly which prediction file and prediction column generated each clean, attacked, and defended condition?
```

This is a reproducibility and quality-control table. It protects Tables/Figures 23-25 from column-selection mistakes.

## Files Created

**Table 26**  
`C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\thesis_table_26_prediction_column_provenance_audit.csv`

**Companion note**  
`C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\notes\thesis_table_26_prediction_column_provenance_audit.md`

## Why this audit is needed

Several prediction CSV files contain more than one prediction-like column. In particular, the FGSM prediction file can contain both clean and attacked prediction columns. If the clean column is accidentally selected, FGSM can appear artificially similar to clean baseline.

Table 26 prevents that by explicitly documenting:

- input CSV file
- true-label column
- prediction column used
- why the selected column is correct
- TP/FN/FP/TN counts
- FNR/FPR
- sanity-check status and warnings

## Summary

- 5 condition(s) passed all sanity checks without warnings.
- 1 condition(s) passed with warnings that are documented in the table.
- All rows use explicit binary true/prediction columns.
- The FGSM attack row explicitly uses `attacked_fall_pred_binary`, avoiding the clean-column selection mistake.
- Window counts and fall/non-fall counts are checked against the clean reference.

## Audit Table

| Condition | File | True column | Prediction column | TP | FN | FP | TN | FNR | FPR | Status |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Clean baseline | `clean_predictions_short.csv` | `fall_true_binary` | `fall_pred_binary` | 57 | 32 | 32 | 875 | 0.360 | 0.035 | PASS |
| FGSM attack | `fgsm_predictions_short_epsilon_0_03.csv` | `fall_true_binary` | `attacked_fall_pred_binary` | 0 | 89 | 119 | 788 | 1.000 | 0.131 | PASS_WITH_WARNINGS |
| PGD attack | `pgd_predictions_short_epsilon_0_03.csv` | `fall_true_binary` | `fall_pred_binary` | 0 | 89 | 115 | 792 | 1.000 | 0.127 | PASS |
| Defended clean | `defended_predictions_short.csv` | `fall_true_binary` | `fall_pred_binary_clean_defended` | 36 | 53 | 22 | 885 | 0.596 | 0.024 | PASS |
| Defended FGSM | `defended_fgsm_predictions_short_epsilon_0_03.csv` | `fall_true_binary` | `fall_pred_binary_fgsm_defended` | 0 | 89 | 72 | 835 | 1.000 | 0.079 | PASS |
| Defended PGD | `defended_pgd_predictions_short_epsilon_0_03.csv` | `fall_true_binary` | `fall_pred_binary_pgd_defended` | 0 | 89 | 56 | 851 | 1.000 | 0.062 | PASS |

## Warnings

- **FGSM attack**: FGSM file also contains clean-like prediction columns; do not use them for attack metrics: clean_predicted_label, clean_predicted_class_name, clean_fall_pred_binary, clean_prediction_confidence

## Interpretation

This table is not another performance claim. It is a reproducibility guardrail. Its main value is that every downstream table and figure can be traced back to a specific file and prediction column.

The most important verification is:

```text
FGSM attack uses attacked_fall_pred_binary, not a clean prediction column.
```

## Claim Boundary

This is a prediction-column provenance and sanity-check audit for the current UT-HAR / SenseFi window-level workflow.

It is not clinical validation, event-level fall validation, deployment validation, physical-layer validation, or over-the-air validation.
