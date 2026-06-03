# Thesis Table 4: Epsilon Sweep Summary Table

This table summarizes the FGSM and PGD epsilon sweep results side by side using window-level fall-vs-non-fall safety-proxy metrics.

The purpose is to show the dose-response relationship between perturbation strength and fall-safety degradation.

## Claim Boundary

This is a research implementation using window-level safety-proxy metrics and software-level processed-tensor adversarial perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Table

| Epsilon | FGSM Missed Fall Rate | PGD Missed Fall Rate | FGSM Recall/Sensitivity | PGD Recall/Sensitivity | FGSM F1-Score | PGD F1-Score | FGSM False Alarms | PGD False Alarms | FGSM Prediction Change Rate | PGD Prediction Change Rate |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 0.3596 | 0.3596 | 0.6404 | 0.6404 | 0.6404 | 0.6404 | 32 | 32 | 0.0000 | 0.0000 |
| 0.005 | 0.7416 | 0.7865 | 0.2584 | 0.2135 | 0.3026 | 0.2517 | 40 | 43 | 0.2871 | 0.3102 |
| 0.010 | 0.9888 | 1.0000 | 0.0112 | 0.0000 | 0.0148 | 0.0000 | 45 | 70 | 0.4839 | 0.5612 |
| 0.020 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 100 | 111 | 0.6827 | 0.7460 |
| 0.030 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 119 | 115 | 0.7440 | 0.7781 |

## Interpretation

The epsilon sweep table shows a clear dose-response pattern. As epsilon increases, missed fall rate increases and recall/sensitivity decreases. At epsilon 0.030, both FGSM and PGD reach missed fall rate 1.0000 and recall/sensitivity 0.0000.

False fall alarm counts also increase under attack. At epsilon 0.030, FGSM produces 119 false fall alarms and PGD produces 115 false fall alarms.

This table supports the thesis framing that adversarial impact should be reported in fall-safety proxy terms, not only as aggregate model accuracy degradation.

## Output Files

- `results/thesis_table_4_epsilon_sweep_summary.csv`
- `notes/thesis_table_4_epsilon_sweep_summary.md`
- Input: `results/fgsm_epsilon_sweep_summary.csv`
- Input: `results/pgd_epsilon_sweep_summary.csv`
