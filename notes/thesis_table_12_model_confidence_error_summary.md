# Thesis Table 12: Model Confidence and Error Confidence Summary

This table summarizes model-reported prediction confidence for correct predictions, incorrect predictions, missed fall windows, false fall alarm windows, and other clinically motivated window groups.

## Claim Boundary

Research implementation only; window-level model-reported prediction-confidence summary; confidence means predicted-class probability/confidence from the model output, not calibrated clinical confidence; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Output File

- `results/thesis_table_12_model_confidence_error_summary.csv`

## Input Files

- `results/clean_predictions_short.csv`
- `results/fgsm_predictions_short_epsilon_0_03.csv`
- `results/pgd_predictions_short_epsilon_0_03.csv`
- `results/defended_predictions_short.csv`

## Confidence Meaning

The confidence values are model-reported predicted-class confidence values exported from the prediction files. They should be interpreted as model output confidence, not calibrated clinical certainty.

## Thresholds

```text
high-confidence threshold = 0.80
low-confidence threshold = 0.50
```

## Main Confidence Summary

| Condition | Group | N | Mean Confidence | Median Confidence | High-Confidence Rate | Low-Confidence Rate |
|---|---|---:|---:|---:|---:|---:|
| Undefended clean | all_windows | 996 | 0.660882 | 0.671661 | 0.298193 | 0.239960 |
| Undefended clean | correct_predictions | 657 | 0.721284 | 0.740962 | 0.401826 | 0.133942 |
| Undefended clean | incorrect_predictions | 339 | 0.543818 | 0.519745 | 0.097345 | 0.445428 |
| Undefended clean | missed_fall_windows | 32 | 0.663120 | 0.688591 | 0.281250 | 0.250000 |
| Undefended clean | false_fall_alarm_windows | 32 | 0.403927 | 0.380573 | 0.000000 | 0.843750 |
| Undefended FGSM epsilon 0.03 | all_windows | 996 | 0.715659 | 0.731898 | 0.422691 | 0.190763 |
| Undefended FGSM epsilon 0.03 | correct_predictions | 10 | 0.402359 | 0.407772 | 0.000000 | 0.800000 |
| Undefended FGSM epsilon 0.03 | incorrect_predictions | 986 | 0.718836 | 0.735743 | 0.426978 | 0.184584 |
| Undefended FGSM epsilon 0.03 | missed_fall_windows | 89 | 0.775721 | 0.833032 | 0.606742 | 0.168539 |
| Undefended FGSM epsilon 0.03 | false_fall_alarm_windows | 119 | 0.566919 | 0.576503 | 0.016807 | 0.319328 |
| Undefended PGD epsilon 0.03 | all_windows | 996 | 0.816495 | 0.878386 | 0.630522 | 0.076305 |
| Undefended PGD epsilon 0.03 | correct_predictions | 0 | NA | NA | NA | NA |
| Undefended PGD epsilon 0.03 | incorrect_predictions | 996 | 0.816495 | 0.878386 | 0.630522 | 0.076305 |
| Undefended PGD epsilon 0.03 | missed_fall_windows | 89 | 0.872827 | 0.953281 | 0.820225 | 0.123596 |
| Undefended PGD epsilon 0.03 | false_fall_alarm_windows | 115 | 0.669228 | 0.662828 | 0.208696 | 0.104348 |
| Defended clean | all_windows | 996 | 0.504646 | 0.476372 | 0.091365 | 0.541165 |
| Defended clean | correct_predictions | 605 | 0.564123 | 0.558903 | 0.137190 | 0.403306 |
| Defended clean | incorrect_predictions | 391 | 0.412617 | 0.378998 | 0.020460 | 0.754476 |
| Defended clean | missed_fall_windows | 53 | 0.462122 | 0.415679 | 0.000000 | 0.641509 |
| Defended clean | false_fall_alarm_windows | 22 | 0.287155 | 0.300335 | 0.000000 | 1.000000 |
| Defended FGSM epsilon 0.03 | all_windows | 996 | 0.478099 | 0.424836 | 0.087349 | 0.620482 |
| Defended FGSM epsilon 0.03 | correct_predictions | 152 | 0.416649 | 0.381139 | 0.026316 | 0.730263 |
| Defended FGSM epsilon 0.03 | incorrect_predictions | 844 | 0.489166 | 0.430113 | 0.098341 | 0.600711 |
| Defended FGSM epsilon 0.03 | missed_fall_windows | 89 | 0.439962 | 0.357259 | 0.123596 | 0.696629 |
| Defended FGSM epsilon 0.03 | false_fall_alarm_windows | 72 | 0.389254 | 0.392958 | 0.000000 | 1.000000 |
| Defended PGD epsilon 0.03 | all_windows | 996 | 0.522286 | 0.471884 | 0.134538 | 0.540161 |
| Defended PGD epsilon 0.03 | correct_predictions | 77 | 0.385887 | 0.327233 | 0.000000 | 0.792208 |
| Defended PGD epsilon 0.03 | incorrect_predictions | 919 | 0.533714 | 0.484921 | 0.145811 | 0.519042 |
| Defended PGD epsilon 0.03 | missed_fall_windows | 89 | 0.455713 | 0.376572 | 0.134831 | 0.707865 |
| Defended PGD epsilon 0.03 | false_fall_alarm_windows | 56 | 0.417461 | 0.424872 | 0.000000 | 1.000000 |

## Missed-Fall Confidence Focus

| Condition | Missed Fall Windows | Mean Confidence | Median Confidence | High-Confidence Missed-Fall Rate |
|---|---:|---:|---:|---:|
| Undefended clean | 32 | 0.663120 | 0.688591 | 0.281250 |
| Undefended FGSM epsilon 0.03 | 89 | 0.775721 | 0.833032 | 0.606742 |
| Undefended PGD epsilon 0.03 | 89 | 0.872827 | 0.953281 | 0.820225 |
| Defended clean | 53 | 0.462122 | 0.415679 | 0.000000 |
| Defended FGSM epsilon 0.03 | 89 | 0.439962 | 0.357259 | 0.123596 |
| Defended PGD epsilon 0.03 | 89 | 0.455713 | 0.376572 | 0.134831 |

## Interpretation

Table 12 adds a confidence dimension to the safety-proxy analysis. It helps identify whether the model is merely wrong, or wrong with high model-reported confidence.

This is important for thesis discussion because high-confidence missed fall windows may be more concerning than low-confidence missed fall windows in a safety-monitoring context. Similarly, high-confidence false fall alarms may reduce trust in alerts.

The table should not be interpreted as clinical confidence, calibrated uncertainty, diagnostic certainty, or medical-device reliability. It is a window-level summary of model-reported predicted-class confidence.
