# Thesis Figure 10: High-Risk Multiclass Fall Error Pathways

This figure summarizes the most clinically motivated multiclass error pathways behind the binary fall-vs-non-fall safety-proxy results.

## Claim Boundary

Research implementation only; window-level high-risk multiclass error-pathway visualization; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Output Figure

- `figures/thesis_figure_10_high_risk_multiclass_fall_error_pathways.png`

## Input File

- `results/thesis_table_8_high_risk_multiclass_error_taxonomy.csv`

## Figure Panels

```text
Panel A: true fall -> predicted non-fall activity
Panel B: true non-fall activity -> predicted fall
```

## Missed-Fall Pathway Summary

| Condition | lie down | walk | pickup | run | sit down | stand up | Total missed-fall pathways |
|---|---:|---:|---:|---:|---:|---:|---:|
| Undefended clean | 0 | 12 | 0 | 20 | 0 | 0 | 32 |
| Undefended FGSM | 6 | 60 | 0 | 17 | 0 | 6 | 89 |
| Undefended PGD | 9 | 54 | 0 | 15 | 11 | 0 | 89 |
| Defended clean | 0 | 39 | 0 | 14 | 0 | 0 | 53 |
| Defended FGSM | 14 | 42 | 3 | 19 | 1 | 10 | 89 |
| Defended PGD | 25 | 27 | 4 | 16 | 4 | 13 | 89 |

## False-Fall-Alarm Pathway Summary

| Condition | lie down -> fall | walk -> fall | pickup -> fall | run -> fall | sit down -> fall | stand up -> fall | Total false-alarm pathways |
|---|---:|---:|---:|---:|---:|---:|---:|
| Undefended clean | 0 | 0 | 17 | 2 | 2 | 11 | 32 |
| Undefended FGSM | 11 | 36 | 3 | 50 | 9 | 10 | 119 |
| Undefended PGD | 20 | 35 | 0 | 34 | 10 | 16 | 115 |
| Defended clean | 0 | 1 | 8 | 3 | 0 | 10 | 22 |
| Defended FGSM | 9 | 5 | 1 | 37 | 4 | 16 | 72 |
| Defended PGD | 7 | 1 | 1 | 31 | 5 | 11 | 56 |

## Interpretation

Figure 10 simplifies the dense seven-class confusion matrices into fall-relevant error pathways. Panel A shows where true fall windows go when they are missed. Panel B shows which non-fall activities become false fall alarms.

This figure is useful for thesis explanation because it connects binary safety-proxy degradation to the original multiclass activity-recognition task. It helps answer whether attacks mainly convert falls into specific non-fall activities, and which non-fall activities are most often converted into false fall alarms.

These are window-level error-pathway counts only. They should not be interpreted as event-level fall validation, clinical diagnosis, long-lie validation, or false alarms per hour/day.
