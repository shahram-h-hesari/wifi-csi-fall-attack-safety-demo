# Adversarial Training Defense Plan

This note defines the first defense extension for the WiFi CSI Fall Attack-Safety Demo.

The current project has completed a clean SenseFi / UT-HAR / LeNet baseline, clean prediction export, FGSM attack evaluation, PGD attack evaluation, epsilon sweeps, FGSM vs PGD comparison, and fall-vs-non-fall safety-proxy metric translation.

The next goal is to add a simple adversarial training defense baseline and compare defended vs undefended behavior using the same safety-proxy metrics.

---

## 1. Defense Goal

The goal is to evaluate whether software-level adversarial training can reduce fall-focused safety-proxy degradation under adversarial perturbation.

The defense question is:

> If the LeNet model is trained with FGSM-perturbed CSI windows during training, does it become more robust when evaluated under FGSM and PGD attacks?

This is a research implementation baseline.

It is not clinical validation, medical-device validation, physical-layer defense validation, packet-level defense validation, preamble-level defense validation, SDR validation, over-the-air validation, or real patient deployment evidence.

---

## 2. Why FGSM Adversarial Training First

The first defense baseline will use FGSM adversarial training.

FGSM is the best first defense step because it is:

- simpler than PGD adversarial training
- faster to run on CPU
- easier to explain in GitHub documentation
- directly connected to the existing FGSM attack pipeline
- useful as a first software-level robustness baseline

PGD adversarial training can be added later after the FGSM defense workflow is working.

---

## 3. Current Undefended Baseline

The current undefended 5-epoch baseline produced the following clean window-level fall-vs-non-fall safety-proxy result:

```text
fall windows: 89
non-fall windows: 907
detected fall windows: 57
missed fall windows: 32
false fall alarms: 32
recall / sensitivity: 0.6404
missed fall rate: 0.3596
F1-score: 0.6404
balanced accuracy: 0.8026
```

Under stronger FGSM and PGD perturbations, the undefended model showed complete loss of fall recall in the current shortened baseline setting.

This motivates testing whether adversarial training can improve robustness.

---

## 4. First Defense Method

The first defense method will train LeNet using both clean and FGSM-perturbed training batches.

The basic training idea is:

```text
1. Load a clean UT-HAR training batch.
2. Compute the normal clean training loss.
3. Generate FGSM adversarial examples from the same batch.
4. Compute adversarial training loss on the perturbed batch.
5. Combine clean loss and adversarial loss.
6. Update the model using the combined loss.
```

The first simple loss design is:

```text
total loss = 0.5 * clean loss + 0.5 * FGSM adversarial loss
```

This keeps the defended model connected to both clean accuracy and adversarial robustness.

---

## 5. Initial Defense Configuration

The first defense run should stay short and reproducible.

Initial configuration:

```text
benchmark: SenseFi / WiFi-CSI-Sensing-Benchmark
dataset: UT_HAR_data
model: LeNet
device: CPU
epochs: 5
defense type: FGSM adversarial training
training epsilon: 0.005
clean loss weight: 0.5
adversarial loss weight: 0.5
```

The training epsilon is intentionally conservative for the first defense baseline.

The current attack sweeps showed that epsilon 0.005 already causes meaningful degradation, while epsilon 0.010 and above can cause near-complete or complete fall-recall loss in the shortened undefended baseline.

---

## 6. Evaluation Plan

After training the defended model, the defended model should be evaluated using the same window-level safety-proxy framework used for the undefended model.

The defended model should be evaluated under:

```text
clean evaluation
FGSM attack evaluation
PGD attack evaluation
FGSM epsilon sweep
PGD epsilon sweep
```

The same epsilon values should be used for comparability:

```text
0.000
0.005
0.010
0.020
0.030
```

---

## 7. Safety-Proxy Metrics

The defended model should be compared using the same fall-vs-non-fall metrics:

```text
detected fall windows
missed fall windows
false fall alarms
correct non-fall windows
recall / sensitivity
missed fall rate
specificity
false positive rate
precision
F1-score
balanced accuracy
prediction change rate
```

This keeps the defense evaluation aligned with the existing attack-safety workflow.

---

## 8. Main Comparison

The key comparison for Priority 8 will be:

```text
undefended clean model
undefended model under FGSM
undefended model under PGD
FGSM-adversarially-trained defended model under FGSM
FGSM-adversarially-trained defended model under PGD
```

The main research question is:

> Does FGSM adversarial training reduce missed fall rate, improve recall, improve F1-score, or reduce prediction instability under attack?

---

## 9. Planned Priority 7 Files

Planned Priority 7 files:

```text
scripts/train_fgsm_adversarial_defense_short.py
results/fgsm_adversarial_training_short_metrics.csv
results/defended_clean_predictions_short.csv
results/defended_fgsm_predictions_short_epsilon_0_03.csv
results/defended_pgd_predictions_short_epsilon_0_03.csv
results/defended_fgsm_safety_proxy_metrics_epsilon_0_03.csv
results/defended_pgd_safety_proxy_metrics_epsilon_0_03.csv
notes/adversarial_training_defense_plan.md
notes/fgsm_adversarial_training_log.md
```

---

## 10. Planned Priority 8 Files

Planned Priority 8 files:

```text
scripts/compare_undefended_vs_defended.py
results/undefended_vs_defended_safety_comparison.csv
figures/undefended_vs_defended_safety_comparison.png
notes/undefended_vs_defended_comparison_summary.md
```

---

## 11. Claim Boundary

This defense extension supports:

```text
software-level adversarial training baseline
processed CSI tensor adversarial training
window-level fall-vs-non-fall safety-proxy evaluation
clean vs attacked comparison
defended vs undefended comparison
```

This defense extension does not claim:

```text
clinical validation
medical-device validation
diagnostic evidence
regulatory evaluation
real patient deployment evidence
event-level fall validation
long-lie validation
time-to-alarm validation
false alarms per day or user-day
physical-layer attack defense
packet-level defense
preamble-level defense
SDR validation
over-the-air validation
```

The current defense is a software-level model robustness baseline, not a validated healthcare deployment defense.

---

## 12. Success Criteria

Priority 7 will be considered complete when the project has:

```text
documented FGSM adversarial training plan
runnable FGSM adversarial training script
saved defended training metrics
saved defended prediction outputs
saved defended fall-vs-non-fall safety-proxy metrics
short defense log explaining the result
README updated with the defense baseline status
```

Priority 8 will then compare defended vs undefended safety-proxy metrics.

---

## 13. Current Step Status

Status:

```text
defense plan note drafted
implementation pending
```