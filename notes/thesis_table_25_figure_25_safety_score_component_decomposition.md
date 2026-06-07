# Thesis Table 25 and Figure 25: Safety-Score Component Decomposition

## Purpose

Table 25 and Figure 25 ask:

```text
Why are the safety-priority scores high or low?
Are they driven mainly by missed-fall contribution or false-alert contribution?
```

This artifact directly explains the mechanism behind Tables/Figures 23 and 24.

## Files Created

**Table 25**  
`<REPO_ROOT>\results\thesis_table_25_safety_score_component_decomposition.csv`

**Figure 25**  
`<REPO_ROOT>\figures\thesis_figure_25_safety_score_component_decomposition.png`

**Companion note**  
`<REPO_ROOT>\notes\thesis_table_25_figure_25_safety_score_component_decomposition.md`

## Input Files and Prediction Columns

- Clean baseline: `<REPO_ROOT>\results\clean_predictions_short.csv` using `fall_pred_binary`
- FGSM attack: `<REPO_ROOT>\results\fgsm_predictions_short_epsilon_0_03.csv` using `attacked_fall_pred_binary`
- PGD attack: `<REPO_ROOT>\results\pgd_predictions_short_epsilon_0_03.csv` using `fall_pred_binary`
- Defended clean: `<REPO_ROOT>\results\defended_predictions_short.csv` using `fall_pred_binary_clean_defended`
- Defended FGSM: `<REPO_ROOT>\results\defended_fgsm_predictions_short_epsilon_0_03.csv` using `fall_pred_binary_fgsm_defended`
- Defended PGD: `<REPO_ROOT>\results\defended_pgd_predictions_short_epsilon_0_03.csv` using `fall_pred_binary_pgd_defended`

The FGSM input file contains both clean and attacked prediction columns. This artifact intentionally uses `attacked_fall_pred_binary` for the FGSM attack condition.

## Scenario

Figure 25 focuses on the strongest missed-fall-priority scenario:

```text
FN:FP = 10:1
```

This means missed-fall errors are weighted 10× higher than false-alert errors.

## Metric Definition

```text
total safety-priority score =
missed-fall component + false-alert component

missed-fall component = 10 × FNR
false-alert component = 1 × FPR
```

where:

```text
FNR = missed-fall rate = FN / (TP + FN)
FPR = false-positive rate = FP / (FP + TN)
```

## Table Summary

| Condition | FNR | FPR | Missed-fall component | False-alert component | Total score | Rank |
|---|---:|---:|---:|---:|---:|---:|
| Clean baseline | 0.360 | 0.035 | 3.596 | 0.035 | 3.631 | 1 |
| FGSM attack | 1.000 | 0.131 | 10.000 | 0.131 | 10.131 | 6 |
| PGD attack | 1.000 | 0.127 | 10.000 | 0.127 | 10.127 | 5 |
| Defended clean | 0.596 | 0.024 | 5.955 | 0.024 | 5.979 | 2 |
| Defended FGSM | 1.000 | 0.079 | 10.000 | 0.079 | 10.079 | 4 |
| Defended PGD | 1.000 | 0.062 | 10.000 | 0.062 | 10.062 | 3 |

## Key Findings

- Clean baseline has the lowest total score (3.631), while attacked conditions are highest because their missed-fall component dominates.
- Defended clean has a higher score than clean baseline (5.979 vs 3.631) because the missed-fall component increases despite lower false-alert behavior.
- FGSM and PGD attacks have near-maximal missed-fall components (10.000 and 10.000), so false-alert improvements alone cannot restore safety-priority behavior.
- Defended FGSM/PGD reduce the false-alert component, but their missed-fall component remains 10.000/10.000; therefore the total score remains high.

## Interpretation

The decomposition shows that the high safety-priority scores under attack are driven primarily by missed-fall behavior, not false-alert behavior. This explains why the defended attack cases remain far from clean-baseline behavior: the defense reduces false positives, but it does not recover true fall-window detection in the current tested configuration.

## Claim Boundary

This is a descriptive window-level score-decomposition analysis using the current UT-HAR / SenseFi prediction outputs.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, patient deployment, clinical utility analysis, health-economic analysis, alarm-fatigue validation, event-level fall validation, long-lie validation, time-to-alarm validation, subject-level generalization validation, room-level generalization validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
