# Thesis Table 9: Robustness Failure Threshold Table

This table identifies the first observed epsilon where FGSM or PGD crosses predefined window-level robustness failure thresholds.

## Claim Boundary

Research implementation only; window-level robustness-threshold analysis; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Input File

- `results/fgsm_vs_pgd_epsilon_comparison.csv`

## Threshold Summary

| Attack | Failure Category | Metric | Threshold Rule | First Epsilon Reached | Metric Value at Threshold | Previous Epsilon | Previous Value | Status |
|---|---|---|---|---:|---:|---:|---:|---|
| FGSM | Missed-fall risk | missed_fall_rate | missed_fall_rate >= 0.75 | 0.0100 | 0.9888 | 0.0050 | 0.7416 | threshold reached |
| FGSM | Missed-fall risk | missed_fall_rate | missed_fall_rate >= 0.95 | 0.0100 | 0.9888 | 0.0050 | 0.7416 | threshold reached |
| FGSM | Missed-fall risk | missed_fall_rate | missed_fall_rate >= 1.00 | 0.0200 | 1.0000 | 0.0100 | 0.9888 | threshold reached |
| FGSM | Fall recall | recall_sensitivity | recall_sensitivity <= 0.05 | 0.0100 | 0.0112 | 0.0050 | 0.2584 | threshold reached |
| FGSM | Fall precision-recall balance | f1_score | f1_score <= 0.05 | 0.0100 | 0.0148 | 0.0050 | 0.3026 | threshold reached |
| FGSM | Multiclass recognition | seven_class_accuracy | seven_class_accuracy <= 0.25 | 0.0100 | 0.2390 | 0.0050 | 0.4116 | threshold reached |
| FGSM | Balanced binary performance | balanced_accuracy | balanced_accuracy <= 0.50 | 0.0100 | 0.4808 | 0.0050 | 0.6072 | threshold reached |
| FGSM | Prediction stability | prediction_change_rate | prediction_change_rate >= 0.50 | 0.0200 | 0.6827 | 0.0100 | 0.4839 | threshold reached |
| FGSM | False-fall alarm burden | false_alarm_count | false_alarm_count >= 100 | 0.0200 | 100.0000 | 0.0100 | 45.0000 | threshold reached |
| PGD | Missed-fall risk | missed_fall_rate | missed_fall_rate >= 0.75 | 0.0050 | 0.7865 | 0.0000 | 0.3596 | threshold reached |
| PGD | Missed-fall risk | missed_fall_rate | missed_fall_rate >= 0.95 | 0.0100 | 1.0000 | 0.0050 | 0.7865 | threshold reached |
| PGD | Missed-fall risk | missed_fall_rate | missed_fall_rate >= 1.00 | 0.0100 | 1.0000 | 0.0050 | 0.7865 | threshold reached |
| PGD | Fall recall | recall_sensitivity | recall_sensitivity <= 0.05 | 0.0100 | 0.0000 | 0.0050 | 0.2135 | threshold reached |
| PGD | Fall precision-recall balance | f1_score | f1_score <= 0.05 | 0.0100 | 0.0000 | 0.0050 | 0.2517 | threshold reached |
| PGD | Multiclass recognition | seven_class_accuracy | seven_class_accuracy <= 0.25 | 0.0100 | 0.1727 | 0.0050 | 0.3896 | threshold reached |
| PGD | Balanced binary performance | balanced_accuracy | balanced_accuracy <= 0.50 | 0.0100 | 0.4614 | 0.0050 | 0.5830 | threshold reached |
| PGD | Prediction stability | prediction_change_rate | prediction_change_rate >= 0.50 | 0.0100 | 0.5612 | 0.0050 | 0.3102 | threshold reached |
| PGD | False-fall alarm burden | false_alarm_count | false_alarm_count >= 100 | 0.0200 | 111.0000 | 0.0100 | 70.0000 | threshold reached |

## Key Interpretation

Table 9 translates the epsilon sweep into robustness-threshold language. Instead of only reporting performance at each epsilon, it asks when each attack first reaches a predefined failure condition.

This is useful for thesis writing because it supports statements such as 'FGSM reached near-complete missed-fall behavior by epsilon 0.010' or 'PGD reached severe missed-fall behavior by epsilon 0.005' while keeping the analysis explicitly window-level.

False-alarm thresholds are reported as window counts only. They should not be converted into false alarms per hour or day because the local UT-HAR copy does not provide recording duration or monitoring-time metadata.

## Output Files

- `results/thesis_table_9_robustness_failure_thresholds.csv`
- `notes/thesis_table_9_robustness_failure_thresholds.md`
