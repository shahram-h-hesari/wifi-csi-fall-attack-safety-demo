# Thesis Figure 2: FGSM vs PGD Epsilon Sweep Curves

This figure compares FGSM and PGD epsilon-sweep behavior using window-level fall-vs-non-fall safety-proxy metrics.

The figure includes four dose-response curves:

- Missed fall rate vs epsilon
- Recall/sensitivity vs epsilon
- F1-score vs epsilon
- False fall alarm count vs epsilon

## Claim Boundary

This is a research implementation using window-level safety-proxy metrics and software-level processed-tensor adversarial perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Summary Table

| Epsilon | FGSM Missed Fall Rate | PGD Missed Fall Rate | FGSM Recall | PGD Recall | FGSM F1 | PGD F1 | FGSM False Alarms | PGD False Alarms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 0.3596 | 0.3596 | 0.6404 | 0.6404 | 0.6404 | 0.6404 | 32 | 32 |
| 0.005 | 0.7416 | 0.7865 | 0.2584 | 0.2135 | 0.3026 | 0.2517 | 40 | 43 |
| 0.010 | 0.9888 | 1.0000 | 0.0112 | 0.0000 | 0.0148 | 0.0000 | 45 | 70 |
| 0.020 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 100 | 111 |
| 0.030 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 119 | 115 |

## Interpretation

The epsilon sweep shows the dose-response relationship between perturbation strength and fall-safety degradation. As epsilon increases, missed fall rate increases and recall/sensitivity and F1-score decrease. False fall alarm counts also change with perturbation strength. This supports the thesis framing that adversarial degradation should be interpreted using safety-proxy metrics, not only aggregate model accuracy.

## Output Files

- `figures/thesis_figure_2_fgsm_pgd_epsilon_sweep.png`
- `notes/thesis_figure_2_fgsm_pgd_epsilon_sweep.md`
- Input: `results/fgsm_epsilon_sweep_summary.csv`
- Input: `results/pgd_epsilon_sweep_summary.csv`
