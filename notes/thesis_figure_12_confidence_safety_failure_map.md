# Thesis Figure 12: Confidence-Safety Failure Map

This figure maps each condition using missed fall rate and high-confidence missed-fall rate.

## Claim Boundary

Research implementation only; window-level confidence-safety failure map; model confidence means predicted-class probability/confidence from the model output, not calibrated clinical confidence; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Output Figure

- `figures/thesis_figure_12_confidence_safety_failure_map.png`

## Input Files

- `results/defended_vs_undefended_safety_comparison.csv`
- `results/thesis_table_12_model_confidence_error_summary.csv`

## Figure Panels

```text
Panel A = overall confidence-safety map
Panel B = zoomed view of defended attacked conditions
Dashed oval in Panel A marks the defended attacked cluster shown in Panel B
```

## Axes

```text
x-axis = missed fall rate
y-axis = high-confidence missed-fall rate
circle = clean
triangle = FGSM
square = PGD
Point labels report high-confidence missed-fall rate.
No clinical threshold lines are shown.
```

## Figure Data

| Condition | Missed Fall Rate | Missed Fall Windows | Mean Missed-Fall Confidence | Median Missed-Fall Confidence | High-Confidence Missed-Fall Rate |
|---|---:|---:|---:|---:|---:|
| Undefended clean | 0.359551 | 32 | 0.663120 | 0.688591 | 0.281250 |
| Undefended FGSM | 1.000000 | 89 | 0.775721 | 0.833032 | 0.606742 |
| Undefended PGD | 1.000000 | 89 | 0.872827 | 0.953281 | 0.820225 |
| Defended clean | 0.595506 | 53 | 0.462122 | 0.415679 | 0.000000 |
| Defended FGSM | 1.000000 | 89 | 0.439962 | 0.357259 | 0.123596 |
| Defended PGD | 1.000000 | 89 | 0.455713 | 0.376572 | 0.134831 |

## Interpretation

Figure 12 combines safety failure and confidence failure into one map. Moving right means the condition misses more fall windows. Moving upward means missed fall windows are more often high-confidence errors.

The upper-right area of Panel A represents the highest-concern region because both missed fall rate and high-confidence missed-fall rate are high. In this experiment, the undefended PGD condition is the strongest confidence-safety failure case: it misses all 89 fall windows and has a high-confidence missed-fall rate of 0.820225.

The defended attacked conditions remain far to the right because they still miss all 89 fall windows at epsilon 0.030. However, they are much lower on the y-axis because their high-confidence missed-fall rates are much lower than the undefended attacked conditions. Panel B separates defended FGSM and defended PGD so their small difference is visible.

No clinical threshold lines are shown in the figure. The map is intended as a descriptive visualization of relative window-level safety-confidence behavior, not as a clinical decision chart.

These values are window-level model-reported confidence and safety-proxy metrics only. They are not clinical risk estimates, calibrated clinical confidence, diagnostic certainty, or medical-device validation metrics.
