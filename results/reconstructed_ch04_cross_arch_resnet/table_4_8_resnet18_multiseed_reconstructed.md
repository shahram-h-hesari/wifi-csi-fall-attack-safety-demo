# Reconstructed Table 4.8

Source: results/cross_architecture/resnet/resnet18_clean_qualified_summary.csv

| Condition | Metric | Mean +/- SD | 95% CI |
| --- | --- | --- | --- |
| Clean | Fall recall | 0.978 +/- 0.016 | [0.958, 0.997] |
| Clean | False-fall alarms | 1.40 +/- 0.89 | [0.3, 2.5] |
| FGSM epsilon=0.03 | Fall recall | 0.009 +/- 0.012 | [0, 0.024] |
| FGSM epsilon=0.03 | False-fall alarms | 32.2 +/- 20.3 | [7.0, 57.4] |
| PGD epsilon=0.03 | Fall recall | 0.000 +/- 0.000 | [0.000, 0.000] |
| PGD epsilon=0.03 | False-fall alarms | 54.0 +/- 32.0 | [14.2, 93.8] |

## Seed Panel

| Seed | Status | Clean acc. | Clean fall recall | PGD eps=0.03 fall recall |
| --- | --- | --- | --- | --- |
| 42 | clean-qualified | 0.942 | 0.978 | 0.000 |
| 43 | clean-qualified | 0.964 | 0.956 | 0.000 |
| 44 | clean-qualified | 0.984 | 0.978 | 0.000 |
| 46 | clean-qualified | 0.982 | 0.978 | 0.000 |
| 48 | clean-qualified | 0.978 | 1.000 | 0.000 |
| 45 | non-converged | 0.294 | 0.000 | --- (excluded) |
| 47 | non-converged | 0.294 | 0.000 | --- (excluded) |
