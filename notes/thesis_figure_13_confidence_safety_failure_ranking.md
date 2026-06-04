# Thesis Figure 13: Confidence-Safety Failure Ranking

This figure visualizes the Table 13 confidence-safety failure ranking as a horizontal bar chart.

## Claim Boundary

Research implementation only; window-level confidence-safety failure ranking visualization; the confidence-safety failure score is a descriptive product of missed fall rate and high-confidence missed-fall rate, not a clinical risk score; model confidence means predicted-class probability/confidence from the model output, not calibrated clinical confidence; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Output Figure

- `figures/thesis_figure_13_confidence_safety_failure_ranking.png`

## Input File

- `results/thesis_table_13_confidence_safety_failure_ranking.csv`

## Descriptive Score Definition

```text
confidence-safety failure score = missed fall rate * high-confidence missed-fall rate
```

This score is a descriptive ranking score only. It is not a clinical risk score, diagnostic score, regulatory score, calibrated confidence score, or medical-device safety score.

## Figure Data

| Rank | Condition | Missed Fall Rate | High-Confidence Missed-Fall Rate | Failure Score | Recall | F1-score | Balanced Accuracy |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | Undefended PGD epsilon 0.03 | 1.000000 | 0.820225 | 0.820225 | 0.000000 | 0.000000 | 0.436604 |
| 2 | Undefended FGSM epsilon 0.03 | 1.000000 | 0.606742 | 0.606742 | 0.000000 | 0.000000 | 0.434399 |
| 3 | Defended PGD epsilon 0.03 | 1.000000 | 0.134831 | 0.134831 | 0.000000 | 0.000000 | 0.469129 |
| 4 | Defended FGSM epsilon 0.03 | 1.000000 | 0.123596 | 0.123596 | 0.000000 | 0.000000 | 0.460309 |
| 5 | Undefended clean | 0.359551 | 0.281250 | 0.101124 | 0.640449 | 0.640449 | 0.802584 |
| 6 | Defended clean | 0.595506 | 0.000000 | 0.000000 | 0.404494 | 0.489796 | 0.690119 |

## Interpretation

Figure 13 is the visual companion to Table 13. It makes the confidence-safety failure ranking easier to interpret.

The undefended PGD condition ranks highest because it combines missed fall rate 1.000000 with high-confidence missed-fall rate 0.820225. The undefended FGSM condition ranks second because it also misses all fall windows but has a lower high-confidence missed-fall rate.

The defended attacked conditions still miss all 89 fall windows, but their confidence-safety failure scores are much lower than the undefended attacked conditions because their high-confidence missed-fall rates are lower.

This supports the same careful interpretation as Figure 12 and Table 13: the short defended model reduced overconfident missed-fall behavior, but it did not restore fall-detection safety performance.

This figure should be interpreted as a window-level descriptive ranking only. It does not estimate clinical risk, event-level fall risk, long-lie risk, time-to-alarm risk, or medical-device safety.
