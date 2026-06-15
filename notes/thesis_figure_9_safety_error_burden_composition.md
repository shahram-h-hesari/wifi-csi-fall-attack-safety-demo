# Safety Error Burden Composition Across Conditions

This figure visualizes how the window-level safety-error burden changes across clean, attacked, and defended conditions.

## Claim Boundary

Research implementation only; window-level safety-error burden visualization; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Output Figure

- `figures/thesis_figure_9_safety_error_burden_composition.png`

## Input File

- `results/defended_vs_undefended_safety_comparison.csv`

## Components Visualized

```text
detected fall windows = TP
missed fall windows = FN
false fall alarm windows = FP
correct non-fall windows = TN
```

## Window Count Summary

| Condition | Detected Falls TP | Missed Falls FN | False Fall Alarms FP | Correct Non-Falls TN |
|---|---:|---:|---:|---:|
| Undefended clean | 57 | 32 | 32 | 875 |
| Undefended FGSM | 0 | 89 | 119 | 788 |
| Undefended PGD | 0 | 89 | 115 | 792 |
| Defended clean | 36 | 53 | 22 | 885 |
| Defended FGSM | 0 | 89 | 72 | 835 |
| Defended PGD | 0 | 89 | 56 | 851 |

## Interpretation

Figure 9 complements the binary confusion matrices by showing the safety burden as a stacked composition of detected fall windows, missed fall windows, false fall alarm windows, and correct non-fall windows.

The figure makes the clean-to-attack shift visible: under FGSM and PGD at epsilon 0.030, detected fall windows collapse to zero while missed fall windows reach all 89 true fall windows. The defended attacked conditions reduce false fall alarm windows compared with the undefended attacked conditions, but still do not recover detected fall windows at epsilon 0.030.

This figure should be interpreted as a window-level safety-error burden visualization. It does not report event-level fall detection, false alarms per hour/day, detection latency, long-lie risk, or clinical validation.
