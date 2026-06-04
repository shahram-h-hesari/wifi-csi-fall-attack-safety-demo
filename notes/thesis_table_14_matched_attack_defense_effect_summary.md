# Thesis Table 14: Matched Attack Defense Effect Summary

This table compares matched undefended and defended attack conditions to summarize the observed defense effect.

## Claim Boundary

Research implementation only; matched window-level attack-defense effect summary; defense effects are descriptive clean-to-attacked and undefended-to-defended comparisons, not clinical effectiveness claims; model confidence means predicted-class probability/confidence from the model output, not calibrated clinical confidence; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Output File

- `results/thesis_table_14_matched_attack_defense_effect_summary.csv`

## Input Files

- `results/defended_vs_undefended_safety_comparison.csv`
- `results/thesis_table_12_model_confidence_error_summary.csv`
- `results/thesis_table_13_confidence_safety_failure_ranking.csv`

## Matched Comparisons

```text
Undefended FGSM epsilon 0.03 vs Defended FGSM epsilon 0.03
Undefended PGD epsilon 0.03 vs Defended PGD epsilon 0.03
```

## Summary Table

| Attack | Missed Fall Rate Undefended -> Defended | High-Confidence Missed-Fall Rate Undefended -> Defended | Failure Score Undefended -> Defended | False Fall Alarms Undefended -> Defended | Interpretation |
|---|---:|---:|---:|---:|---|
| FGSM | 1.000000 -> 1.000000 | 0.606742 -> 0.123596 | 0.606742 -> 0.123596 | 119 -> 72 | Defense reduced overconfident missed-fall behavior but did not restore fall recall. |
| PGD | 1.000000 -> 1.000000 | 0.820225 -> 0.134831 | 0.820225 -> 0.134831 | 115 -> 56 | Defense reduced overconfident missed-fall behavior but did not restore fall recall. |

## Main Defense-Effect Details

### FGSM epsilon 0.03

```text
missed fall rate change = 0.000000
high-confidence missed-fall rate reduction = 0.483146
high-confidence missed-fall rate percent reduction = 79.63%
confidence-safety failure score reduction = 0.483146
confidence-safety failure score percent reduction = 79.63%
mean missed-fall confidence reduction = 0.335759
median missed-fall confidence reduction = 0.475773
false fall alarm count reduction = 47
recall change = 0.000000
F1-score change = 0.000000
balanced accuracy change = 0.025910
```

### PGD epsilon 0.03

```text
missed fall rate change = 0.000000
high-confidence missed-fall rate reduction = 0.685394
high-confidence missed-fall rate percent reduction = 83.56%
confidence-safety failure score reduction = 0.685394
confidence-safety failure score percent reduction = 83.56%
mean missed-fall confidence reduction = 0.417114
median missed-fall confidence reduction = 0.576709
false fall alarm count reduction = 59
recall change = 0.000000
F1-score change = 0.000000
balanced accuracy change = 0.032525
```

## Interpretation

Table 14 directly compares matched attack conditions. In both FGSM and PGD cases, the defended model does not restore fall recall because missed fall rate remains 1.000000. However, the defended attacked conditions have much lower high-confidence missed-fall rates and lower confidence-safety failure scores than the corresponding undefended attacked conditions.

This supports a careful thesis statement: the short defended model reduced overconfident missed-fall behavior, but it did not restore window-level fall-detection safety performance.

This table should not be interpreted as clinical defense effectiveness, medical-device validation, event-level fall-risk reduction, time-to-alarm improvement, or physical-world attack mitigation.
