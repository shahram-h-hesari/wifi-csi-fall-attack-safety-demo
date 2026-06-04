# Thesis Table 13: Confidence-Safety Failure Ranking

This table ranks clean, attacked, and defended conditions by a descriptive window-level confidence-safety failure score.

## Claim Boundary

Research implementation only; window-level confidence-safety failure ranking; the confidence-safety failure score is a descriptive product of missed fall rate and high-confidence missed-fall rate, not a clinical risk score; model confidence means predicted-class probability/confidence from the model output, not calibrated clinical confidence; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Output File

- `results/thesis_table_13_confidence_safety_failure_ranking.csv`

## Input Files

- `results/defended_vs_undefended_safety_comparison.csv`
- `results/thesis_table_12_model_confidence_error_summary.csv`

## Descriptive Score Definition

```text
confidence-safety failure score = missed fall rate * high-confidence missed-fall rate
```

This score is a descriptive ranking score only. It is not a clinical risk score, diagnostic score, regulatory score, calibrated confidence score, or medical-device safety score.

## Ranked Table Preview

| Rank | Condition | Missed Fall Rate | High-Confidence Missed-Fall Rate | Failure Score | Recall | F1-score | Balanced Accuracy |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | Undefended PGD epsilon 0.03 | 1.000000 | 0.820225 | 0.820225 | 0.000000 | 0.000000 | 0.436604 |
| 2 | Undefended FGSM epsilon 0.03 | 1.000000 | 0.606742 | 0.606742 | 0.000000 | 0.000000 | 0.434399 |
| 3 | Defended PGD epsilon 0.03 | 1.000000 | 0.134831 | 0.134831 | 0.000000 | 0.000000 | 0.469129 |
| 4 | Defended FGSM epsilon 0.03 | 1.000000 | 0.123596 | 0.123596 | 0.000000 | 0.000000 | 0.460309 |
| 5 | Undefended clean | 0.359551 | 0.281250 | 0.101124 | 0.640449 | 0.640449 | 0.802584 |
| 6 | Defended clean | 0.595506 | 0.000000 | 0.000000 | 0.404494 | 0.489796 | 0.690119 |

## Interpretation

Table 13 provides a ranked numeric companion to Figure 12. It identifies conditions that combine missed-fall safety failure with high model-reported confidence in the wrong prediction.

The undefended PGD condition ranks highest because it has missed fall rate 1.000000 and high-confidence missed-fall rate 0.820225, producing the largest confidence-safety failure score.

The undefended FGSM condition ranks second because it also misses all 89 fall windows but has a lower high-confidence missed-fall rate than PGD.

The defended attacked conditions still miss all 89 fall windows, but they rank lower because their high-confidence missed-fall rates are much lower than the undefended attacked conditions. This supports the careful interpretation that the short defended model reduced overconfident missed-fall behavior but did not restore fall-detection safety performance.

This table should be interpreted as a window-level descriptive ranking only. It does not estimate clinical risk, event-level fall risk, long-lie risk, time-to-alarm risk, or medical-device safety.
