# Thesis Figure 14: Matched Attack Defense Effect Comparison

This figure compares matched undefended and defended attack conditions using three metrics that improved under defense, while explicitly noting that missed fall rate did not improve.

## Claim Boundary

Research implementation only; matched window-level attack-defense effect visualization; defense effects are descriptive undefended-to-defended comparisons, not clinical effectiveness claims; model confidence means predicted-class probability/confidence from the model output, not calibrated clinical confidence; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Output Figure

- `figures/thesis_figure_14_matched_attack_defense_effect_comparison.png`

## Input File

- `results/thesis_table_14_matched_attack_defense_effect_summary.csv`

## Figure Panels

```text
Panel A: high-confidence missed-fall rate
Panel B: median missed-fall confidence
Panel C: false fall alarm count
```

## Important Context

Missed fall rate remained `1.000000` for all matched attacked conditions:

- Undefended FGSM epsilon 0.03
- Defended FGSM epsilon 0.03
- Undefended PGD epsilon 0.03
- Defended PGD epsilon 0.03

Because missed fall rate did not improve, this figure focuses on the defense effects that did improve.

## Figure Data

| Attack | High-Confidence Missed-Fall Rate Undefended -> Defended | Median Missed-Fall Confidence Undefended -> Defended | False Fall Alarms Undefended -> Defended |
|---|---:|---:|---:|
| FGSM | 0.606742 -> 0.123596 | 0.833032 -> 0.357259 | 119 -> 72 |
| PGD | 0.820225 -> 0.134831 | 0.953281 -> 0.376572 | 115 -> 56 |

## Reduction Summary

### FGSM epsilon 0.03

```text
high-confidence missed-fall rate reduction = 0.483146
high-confidence missed-fall rate percent reduction = 79.63%
median missed-fall confidence reduction = 0.475773
false fall alarm count reduction = 47
missed fall rate change = 0.000000
recall change = 0.000000
```

### PGD epsilon 0.03

```text
high-confidence missed-fall rate reduction = 0.685394
high-confidence missed-fall rate percent reduction = 83.56%
median missed-fall confidence reduction = 0.576709
false fall alarm count reduction = 59
missed fall rate change = 0.000000
recall change = 0.000000
```

## Interpretation

Figure 14 shows that the defended attacked model reduced three error-burden metrics relative to the matched undefended attacked model:

1. lower high-confidence missed-fall rate
2. lower median missed-fall confidence
3. fewer false fall alarms

For FGSM, the defended model reduced high-confidence missed-fall rate from 0.606742 to 0.123596, reduced median missed-fall confidence from 0.833032 to 0.357259, and reduced false fall alarms from 119 to 72.

For PGD, the defended model reduced high-confidence missed-fall rate from 0.820225 to 0.134831, reduced median missed-fall confidence from 0.953281 to 0.376572, and reduced false fall alarms from 115 to 56.

However, the figure must be interpreted carefully: missed fall rate remained 1.000000 under all matched attacked conditions, so the defense did not restore window-level fall recall.

The figure therefore supports a careful thesis statement: the short defended model reduced overconfident error burden and false alarms, but it did not restore fall-detection safety performance.

This figure should not be interpreted as clinical defense effectiveness, medical-device validation, event-level fall-risk reduction, time-to-alarm improvement, or physical-world attack mitigation.
