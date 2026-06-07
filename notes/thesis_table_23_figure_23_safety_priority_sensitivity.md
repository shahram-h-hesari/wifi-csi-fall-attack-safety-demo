# Thesis Table 23 and Figure 23: Safety-Priority Sensitivity Analysis Under Missed-Fall Weighting

## Purpose

Table 23 and Figure 23 ask:

```text
Do conclusions about clean, attacked, and defended conditions change when missed-fall windows are given increasing priority over false-alert windows?
```

This artifact is a scenario-based engineering sensitivity analysis. It complements the earlier window-level safety metrics, alert-trustworthiness analysis, failure-pattern analysis, and claim-boundary map.

## Files Created

**Table 23**  
`C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\thesis_table_23_safety_priority_sensitivity.csv`

**Figure 23**  
`C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\figures\thesis_figure_23_safety_priority_sensitivity_heatmap.png`

**Companion note**  
`C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\notes\thesis_table_23_figure_23_safety_priority_sensitivity.md`

## Input Files and Prediction Columns

- Clean baseline: `C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\clean_predictions_short.csv` using `fall_pred_binary`
- FGSM attack: `C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\fgsm_predictions_short_epsilon_0_03.csv` using `attacked_fall_pred_binary`
- PGD attack: `C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\pgd_predictions_short_epsilon_0_03.csv` using `fall_pred_binary`
- Defended clean: `C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\defended_predictions_short.csv` using `fall_pred_binary_clean_defended`
- Defended FGSM: `C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\defended_fgsm_predictions_short_epsilon_0_03.csv` using `fall_pred_binary_fgsm_defended`
- Defended PGD: `C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo\results\defended_pgd_predictions_short_epsilon_0_03.csv` using `fall_pred_binary_pgd_defended`

The FGSM input file contains both clean and attacked prediction columns. This artifact intentionally uses `attacked_fall_pred_binary` for the FGSM attack condition.

## Metric Definition

For each condition and each missed-fall-priority scenario:

```text
normalized safety-priority score =
FN weight × missed-fall rate + FP weight × false-positive rate
```

where:

```text
missed_fall_rate = FN / (TP + FN)
false_positive_rate = FP / (FP + TN)
```

Lower score is better.

## Scenario Interpretation

```text
1:1  = missed-fall errors and false-alert errors are weighted equally
2:1  = missed-fall errors are weighted 2× higher than false-alert errors
5:1  = missed-fall errors are weighted 5× higher than false-alert errors
10:1 = missed-fall errors are weighted 10× higher than false-alert errors
```

These weights are scenario assumptions, not clinical cost constants.

## Rank Definition

For each weighting scenario, the six model conditions are ranked by normalized safety-priority score.

```text
rank 1 = lowest score / best within that scenario column
rank 6 = highest score / worst within that scenario column
```

Tied scores share the same rank.

## Key Findings

- Equal missed-fall and false-alert weighting (1:1): best/lower score = Clean baseline (0.395); worst/higher score = FGSM attack (1.131).
- Missed-fall errors weighted 2x higher than false-alert errors (2:1): best/lower score = Clean baseline (0.754); worst/higher score = FGSM attack (2.131).
- Missed-fall errors weighted 5x higher than false-alert errors (5:1): best/lower score = Clean baseline (1.833); worst/higher score = FGSM attack (5.131).
- Missed-fall errors weighted 10x higher than false-alert errors (10:1): best/lower score = Clean baseline (3.631); worst/higher score = FGSM attack (10.131).
- Condition rankings remain stable across the tested missed-fall-priority scenarios.
- Column verification: FGSM attack uses attacked_fall_pred_binary, not clean_fall_pred_binary.

## Interpretation

This artifact does not introduce a clinically validated cost model. Its value is that it checks whether the relative interpretation of clean, attacked, and defended conditions is stable when missed-fall windows are treated as increasingly important compared with false-alert windows.

This is useful because a defense that reduces false alerts but still misses many fall windows may look acceptable under equal error weighting but less acceptable when missed-fall windows are prioritized.

## Claim Boundary

This is a descriptive window-level safety-priority sensitivity analysis using the current UT-HAR / SenseFi prediction outputs.

It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, patient deployment, clinical utility analysis, health-economic analysis, alarm-fatigue validation, event-level fall validation, long-lie validation, time-to-alarm validation, subject-level generalization validation, room-level generalization validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.
