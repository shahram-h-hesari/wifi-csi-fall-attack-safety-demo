# Thesis Table 8: High-Risk Multiclass Error Taxonomy

This table identifies fall-relevant seven-class error patterns from the existing prediction CSV files. It separates missed-fall multiclass errors from false-fall-alarm multiclass errors.

## Claim Boundary

Research implementation only; window-level multiclass error-taxonomy analysis; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Key Finding

The current prediction files support a window-level multiclass error-taxonomy analysis because they include true seven-class labels and predicted seven-class labels for clean, FGSM, PGD, defended clean, defended FGSM, and defended PGD conditions.

This is not an event-level clinical-safety analysis.

## Summary by Condition

| Condition | Total Windows | Missed-Fall Multiclass Errors | False-Fall-Alarm Multiclass Errors | Total High-Risk Errors |
|---|---:|---:|---:|---:|
| Undefended clean baseline | 996 | 32 | 32 | 64 |
| Undefended FGSM attack, epsilon 0.030 | 996 | 89 | 119 | 208 |
| Undefended PGD attack, epsilon 0.030 | 996 | 89 | 115 | 204 |
| Defended clean baseline | 996 | 53 | 22 | 75 |
| Defended FGSM attack, epsilon 0.030 | 996 | 89 | 72 | 161 |
| Defended PGD attack, epsilon 0.030 | 996 | 89 | 56 | 145 |

## Detailed Taxonomy

| Condition | Error Family | True Class | Predicted Class | Count | Percent of Windows | Interpretation |
|---|---|---|---|---:|---:|---|
| Undefended clean baseline | missed_fall_multiclass_error | fall | walk | 12 | 1.2048 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Undefended clean baseline | missed_fall_multiclass_error | fall | run | 20 | 2.0080 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Undefended clean baseline | false_fall_alarm_multiclass_error | pickup | fall | 17 | 1.7068 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended clean baseline | false_fall_alarm_multiclass_error | run | fall | 2 | 0.2008 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended clean baseline | false_fall_alarm_multiclass_error | sit down | fall | 2 | 0.2008 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended clean baseline | false_fall_alarm_multiclass_error | stand up | fall | 11 | 1.1044 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended FGSM attack, epsilon 0.030 | missed_fall_multiclass_error | fall | lie down | 6 | 0.6024 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Undefended FGSM attack, epsilon 0.030 | missed_fall_multiclass_error | fall | walk | 60 | 6.0241 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Undefended FGSM attack, epsilon 0.030 | missed_fall_multiclass_error | fall | run | 17 | 1.7068 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Undefended FGSM attack, epsilon 0.030 | missed_fall_multiclass_error | fall | stand up | 6 | 0.6024 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Undefended FGSM attack, epsilon 0.030 | false_fall_alarm_multiclass_error | lie down | fall | 11 | 1.1044 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended FGSM attack, epsilon 0.030 | false_fall_alarm_multiclass_error | walk | fall | 36 | 3.6145 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended FGSM attack, epsilon 0.030 | false_fall_alarm_multiclass_error | pickup | fall | 3 | 0.3012 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended FGSM attack, epsilon 0.030 | false_fall_alarm_multiclass_error | run | fall | 50 | 5.0201 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended FGSM attack, epsilon 0.030 | false_fall_alarm_multiclass_error | sit down | fall | 9 | 0.9036 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended FGSM attack, epsilon 0.030 | false_fall_alarm_multiclass_error | stand up | fall | 10 | 1.0040 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended PGD attack, epsilon 0.030 | missed_fall_multiclass_error | fall | lie down | 9 | 0.9036 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Undefended PGD attack, epsilon 0.030 | missed_fall_multiclass_error | fall | walk | 54 | 5.4217 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Undefended PGD attack, epsilon 0.030 | missed_fall_multiclass_error | fall | run | 15 | 1.5060 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Undefended PGD attack, epsilon 0.030 | missed_fall_multiclass_error | fall | sit down | 11 | 1.1044 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Undefended PGD attack, epsilon 0.030 | false_fall_alarm_multiclass_error | lie down | fall | 20 | 2.0080 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended PGD attack, epsilon 0.030 | false_fall_alarm_multiclass_error | walk | fall | 35 | 3.5141 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended PGD attack, epsilon 0.030 | false_fall_alarm_multiclass_error | run | fall | 34 | 3.4137 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended PGD attack, epsilon 0.030 | false_fall_alarm_multiclass_error | sit down | fall | 10 | 1.0040 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Undefended PGD attack, epsilon 0.030 | false_fall_alarm_multiclass_error | stand up | fall | 16 | 1.6064 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended clean baseline | missed_fall_multiclass_error | fall | walk | 39 | 3.9157 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended clean baseline | missed_fall_multiclass_error | fall | run | 14 | 1.4056 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended clean baseline | false_fall_alarm_multiclass_error | walk | fall | 1 | 0.1004 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended clean baseline | false_fall_alarm_multiclass_error | pickup | fall | 8 | 0.8032 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended clean baseline | false_fall_alarm_multiclass_error | run | fall | 3 | 0.3012 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended clean baseline | false_fall_alarm_multiclass_error | stand up | fall | 10 | 1.0040 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended FGSM attack, epsilon 0.030 | missed_fall_multiclass_error | fall | lie down | 14 | 1.4056 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended FGSM attack, epsilon 0.030 | missed_fall_multiclass_error | fall | walk | 42 | 4.2169 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended FGSM attack, epsilon 0.030 | missed_fall_multiclass_error | fall | pickup | 3 | 0.3012 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended FGSM attack, epsilon 0.030 | missed_fall_multiclass_error | fall | run | 19 | 1.9076 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended FGSM attack, epsilon 0.030 | missed_fall_multiclass_error | fall | sit down | 1 | 0.1004 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended FGSM attack, epsilon 0.030 | missed_fall_multiclass_error | fall | stand up | 10 | 1.0040 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended FGSM attack, epsilon 0.030 | false_fall_alarm_multiclass_error | lie down | fall | 9 | 0.9036 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended FGSM attack, epsilon 0.030 | false_fall_alarm_multiclass_error | walk | fall | 5 | 0.5020 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended FGSM attack, epsilon 0.030 | false_fall_alarm_multiclass_error | pickup | fall | 1 | 0.1004 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended FGSM attack, epsilon 0.030 | false_fall_alarm_multiclass_error | run | fall | 37 | 3.7149 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended FGSM attack, epsilon 0.030 | false_fall_alarm_multiclass_error | sit down | fall | 4 | 0.4016 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended FGSM attack, epsilon 0.030 | false_fall_alarm_multiclass_error | stand up | fall | 16 | 1.6064 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended PGD attack, epsilon 0.030 | missed_fall_multiclass_error | fall | lie down | 25 | 2.5100 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended PGD attack, epsilon 0.030 | missed_fall_multiclass_error | fall | walk | 27 | 2.7108 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended PGD attack, epsilon 0.030 | missed_fall_multiclass_error | fall | pickup | 4 | 0.4016 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended PGD attack, epsilon 0.030 | missed_fall_multiclass_error | fall | run | 16 | 1.6064 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended PGD attack, epsilon 0.030 | missed_fall_multiclass_error | fall | sit down | 4 | 0.4016 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended PGD attack, epsilon 0.030 | missed_fall_multiclass_error | fall | stand up | 13 | 1.3052 | Fall window predicted as a non-fall activity; contributes to window-level missed fall rate. |
| Defended PGD attack, epsilon 0.030 | false_fall_alarm_multiclass_error | lie down | fall | 7 | 0.7028 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended PGD attack, epsilon 0.030 | false_fall_alarm_multiclass_error | walk | fall | 1 | 0.1004 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended PGD attack, epsilon 0.030 | false_fall_alarm_multiclass_error | pickup | fall | 1 | 0.1004 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended PGD attack, epsilon 0.030 | false_fall_alarm_multiclass_error | run | fall | 31 | 3.1124 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended PGD attack, epsilon 0.030 | false_fall_alarm_multiclass_error | sit down | fall | 5 | 0.5020 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |
| Defended PGD attack, epsilon 0.030 | false_fall_alarm_multiclass_error | stand up | fall | 11 | 1.1044 | Non-fall window predicted as fall; contributes to window-level false fall alarm count. |

## Interpretation

Table 8 provides the multiclass explanation behind the binary fall-vs-non-fall safety-proxy metrics. A missed-fall multiclass error occurs when a true fall window is predicted as a non-fall activity. A false-fall-alarm multiclass error occurs when a true non-fall activity is predicted as fall.

This table is useful because two conditions may have similar binary safety-proxy metrics while failing through different seven-class confusion pathways. For example, attacks may convert fall windows into specific non-fall classes, or convert specific non-fall activities into false fall alarms.

The result should be reported as a window-level multiclass error-taxonomy analysis. It should not be described as event-level fall validation or clinical fall validation.

## Output Files

- `results/thesis_table_8_high_risk_multiclass_error_taxonomy.csv`
- `notes/thesis_table_8_high_risk_multiclass_error_taxonomy.md`
