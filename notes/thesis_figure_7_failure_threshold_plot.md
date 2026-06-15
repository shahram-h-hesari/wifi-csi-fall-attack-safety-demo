# Failure Threshold / Robustness Collapse Plot

This figure visualizes FGSM and PGD epsilon-sweep behavior against window-level robustness failure thresholds.

## Claim Boundary

Research implementation only; window-level robustness-collapse visualization; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Output Figure

- `figures/thesis_figure_7_failure_threshold_plot.png`

## Input File

- `results/fgsm_vs_pgd_epsilon_comparison.csv`

## Panels

The figure contains four panels:

1. missed fall rate
2. fall recall / sensitivity
3. false fall alarm count
4. prediction change rate

## Key Threshold Crossings

| Threshold | FGSM First Epsilon | PGD First Epsilon |
|---|---:|---:|
| missed_fall_rate >= 0.75 | 0.0100 | 0.0050 |
| missed_fall_rate >= 0.95 | 0.0100 | 0.0100 |
| recall_sensitivity <= 0.05 | 0.0100 | 0.0100 |
| prediction_change_rate >= 0.50 | 0.0200 | 0.0100 |
| false_alarm_count >= 100 | 0.0200 | 0.0200 |

## Interpretation

Figure 7 complements Table 9 by showing the threshold-crossing behavior visually. PGD reaches the severe missed-fall threshold earlier than FGSM, while both attacks reach near-complete missed-fall behavior by epsilon 0.010.

The false-alarm panel should be interpreted as a window-count result only. It should not be converted into false alarms per hour or day because the local UT-HAR copy does not provide recording-duration metadata.

This figure should be described as a window-level robustness-collapse visualization, not as event-level clinical validation.
