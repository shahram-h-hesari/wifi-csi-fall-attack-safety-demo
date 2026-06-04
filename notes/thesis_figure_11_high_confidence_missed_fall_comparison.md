# Thesis Figure 11: High-Confidence Missed-Fall Error Comparison

This figure visualizes missed-fall confidence behavior across clean, attacked, and defended conditions.

## Claim Boundary

Research implementation only; window-level model-reported confidence comparison for missed fall windows; confidence means predicted-class probability/confidence from the model output, not calibrated clinical confidence; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Output Figure

- `figures/thesis_figure_11_high_confidence_missed_fall_comparison.png`

## Input File

- `results/thesis_table_12_model_confidence_error_summary.csv`

## Metrics Visualized

```text
mean missed-fall confidence
median missed-fall confidence
high-confidence missed-fall rate
```

## Missed-Fall Confidence Summary

| Condition | Missed Fall Windows | Mean Confidence | Median Confidence | High-Confidence Missed-Fall Rate |
|---|---:|---:|---:|---:|
| Undefended clean | 32 | 0.663120 | 0.688591 | 0.281250 |
| Undefended FGSM | 89 | 0.775721 | 0.833032 | 0.606742 |
| Undefended PGD | 89 | 0.872827 | 0.953281 | 0.820225 |
| Defended clean | 53 | 0.462122 | 0.415679 | 0.000000 |
| Defended FGSM | 89 | 0.439962 | 0.357259 | 0.123596 |
| Defended PGD | 89 | 0.455713 | 0.376572 | 0.134831 |

## Interpretation

Figure 11 focuses on a key safety-proxy concern: whether missed fall windows are associated with high model-reported confidence.

The undefended attacked conditions show the strongest confidence concern. Under FGSM at epsilon 0.030, all 89 fall windows are missed and the high-confidence missed-fall rate is 0.606742. Under PGD at epsilon 0.030, all 89 fall windows are missed and the high-confidence missed-fall rate increases to 0.820225, with median missed-fall confidence 0.953281.

The defended attacked conditions still miss all 89 fall windows at epsilon 0.030, but their missed-fall confidence is much lower than the undefended attacked conditions. This supports a careful interpretation: the short defended model did not recover fall recall, but it reduced the model-reported confidence of missed-fall errors.

These values should be interpreted only as window-level model-reported predicted-class confidence summaries. They are not calibrated clinical confidence, diagnostic certainty, or medical-device reliability metrics.
