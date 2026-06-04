# Thesis Table 10: Extended Window-Level Diagnostic Safety Metrics

This table reports additional diagnostic-style safety-proxy metrics computed from the binary fall-vs-non-fall confusion matrix for clean, attacked, and defended conditions.

## Claim Boundary

Research implementation only; window-level diagnostic-style safety-proxy metrics; software-level processed-tensor perturbations only; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Input File

- `results/defended_vs_undefended_safety_comparison.csv`

## Output File

- `results/thesis_table_10_extended_diagnostic_safety_metrics.csv`

## Metrics

The table includes:

```text
negative predictive value
false omission rate
false discovery rate
positive likelihood ratio
negative likelihood ratio
diagnostic odds ratio
Matthews correlation coefficient
Cohen's kappa
fall-window prevalence
false-alarm-to-detected-fall ratio
missed-fall-to-detected-fall ratio
```

## Interpretation

Table 10 strengthens the thesis by adding diagnostic-style window-level metrics beyond recall, precision, F1-score, and balanced accuracy. These metrics help explain whether the model is becoming less trustworthy when it predicts non-fall, whether fall alerts are more likely to be false, and whether attacks cause asymmetric safety burden.

These values should be described as window-level diagnostic-style safety-proxy metrics. They should not be described as clinical diagnostic validation.

`NA` means the ratio is undefined because the denominator is zero, commonly because there were no detected fall windows in that condition.

## Table Preview

| Condition | NPV | FOR | FDR | PLR | NLR | DOR | MCC | Kappa | Fall Prevalence | FP/TP | FN/TP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Undefended clean | 0.964719 | 0.035281 | 0.359551 | 18.152739 | 0.372700 | 48.706055 | 0.605168 | 0.605168 | 0.089357 | 0.561404 | 0.561404 |
| Undefended FGSM epsilon 0.03 | 0.898518 | 0.101482 | 1.000000 | 0.000000 | 1.151015 | 0.000000 | -0.115389 | -0.113890 | 0.089357 | NA | NA |
| Undefended PGD epsilon 0.03 | 0.898978 | 0.101022 | 1.000000 | 0.000000 | 1.145202 | 0.000000 | -0.113175 | -0.112033 | 0.089357 | NA | NA |
| Defended clean | 0.943497 | 0.056503 | 0.379310 | 16.676200 | 0.610309 | 27.324185 | 0.463169 | 0.451090 | 0.089357 | 0.611111 | 1.472222 |
| Defended FGSM epsilon 0.03 | 0.903680 | 0.096320 | 1.000000 | 0.000000 | 1.086228 | 0.000000 | -0.087442 | -0.086865 | 0.089357 | NA | NA |
| Defended PGD epsilon 0.03 | 0.905319 | 0.094681 | 1.000000 | 0.000000 | 1.065805 | 0.000000 | -0.076458 | -0.074138 | 0.089357 | NA | NA |
