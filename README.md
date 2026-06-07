# Fall Detection Attack-Safety Demo

This folder is the practical experiment workspace for evaluating WiFi CSI fall-related activity recognition under clean, adversarial, and defended software-level conditions.

The goal is to reproduce a clean WiFi CSI baseline, save clean, attacked, and defended predictions, and translate model degradation into fall-focused safety-proxy metrics.

Current status:

```text
Clean SenseFi UT-HAR LeNet baseline completed.
Clean prediction export completed.
Clean fall-vs-non-fall safety-proxy metrics completed.
FGSM attacked prediction export completed.
FGSM fall-vs-non-fall safety-proxy metrics completed.
FGSM epsilon sweep completed.
FGSM epsilon sweep figures completed.
PGD attacked prediction export completed.
PGD fall-vs-non-fall safety-proxy metrics completed.
PGD epsilon sweep completed.
PGD epsilon sweep figures completed.
FGSM vs PGD comparison completed.
Final FGSM/PGD attack-safety lab report completed.
Window-level vs event-level limitation note completed.
FGSM adversarial training defense baseline completed.
Defended clean, FGSM, and PGD prediction export completed.
Defended safety-proxy metrics completed.
Defended vs undefended safety-proxy comparison completed.
Defended vs undefended comparison figures completed.
```

This is a research implementation demo. It is not clinical validation, medical-device validation, real patient deployment, diagnostic evidence, regulatory evaluation, physical-layer attack validation, SDR validation, packet-level validation, preamble-level validation, event-level fall validation, long-lie validation, or over-the-air validation.

---

## 1. Research Goal

Most WiFi CSI fall-detection and adversarial sensing papers report technical metrics such as accuracy, F1-score, or attack success rate.

This experiment asks a more safety-oriented question:

> If a WiFi CSI fall-related activity-recognition model is degraded by adversarial perturbation, does it miss more fall windows, create more false fall alarms, reduce alert trustworthiness, or reduce recall?

The central translation pathway is:

```text
WiFi CSI sensing output
-> ML prediction
-> clean, attacked, or defended prediction error
-> fall-vs-non-fall safety-proxy metric
-> adversarial safety degradation
```

---

## 2. Repository Roles

This work uses two related repositories with different purposes.

| Repository | Role |
|---|---|
| `ai-ml-wifi-sensing-hub` | Evidence hub, literature mapping, clinical-safety metric framework, and research gap documentation |
| `secure-wifi-csi-healthcare-sensing` | Implementation repo for experiments, scripts, notebooks, prediction files, metrics, figures, and lab reports |
| `wifi-csi-fall-attack-safety-demo` | Standalone public demo repo for making the fall attack-safety workflow easier to view as an independent project |

The evidence hub explains why safety-oriented metrics matter.

This implementation repo shows how to calculate them.

The standalone repo makes the completed demo easier to review as a focused GitHub portfolio/research artifact.

---

## 3. Experiment Scope

This first practical demo focuses on:

```text
fall vs non-fall safety-proxy evaluation
```

The current clean-vs-attacked-vs-defended comparison uses:

```text
clean baseline
FGSM processed-tensor attack
FGSM epsilon sweep
PGD processed-tensor attack
PGD epsilon sweep
FGSM vs PGD comparison
short FGSM adversarial-training defense baseline
defended clean/FGSM/PGD prediction export
defended vs undefended safety-proxy comparison
```

The first safety-proxy metrics include:

```text
missed fall rate
false alarm count
precision
recall / sensitivity
specificity
F1-score
balanced accuracy
prediction change rate
```

Metrics that require timestamps, event IDs, fall impact times, or monitoring duration are not claimed yet:

```text
event-level recall
event-level missed fall rate
false alarms per day or user-day
detection latency
delayed detection rate
long-lie risk proxy
```

---

## 4. Dataset and Model

This first baseline uses SenseFi / WiFi-CSI-Sensing-Benchmark.

| Item | Current Choice |
|---|---|
| Benchmark | SenseFi / WiFi-CSI-Sensing-Benchmark |
| Dataset | UT_HAR_data |
| Model | LeNet |
| Device | CPU |
| Short baseline epochs | 5 |
| Original SenseFi setting | 200 epochs |
| Prediction split | SenseFi validation + test loader |
| Prediction rows | 996 |
| Dataset storage | Local only, not committed to GitHub |
| Third-party benchmark clone | Local only, ignored by Git |

The shortened 5-epoch run is used for reproducibility testing, pipeline development, and first defense comparison. It should not be interpreted as final benchmark performance.

---

## 5. UT-HAR Label Mapping

UT-HAR contains seven activity classes:

```text
0 = lie down
1 = fall
2 = walk
3 = pickup
4 = run
5 = sit down
6 = stand up
```

For the safety-proxy layer, the labels are mapped into binary fall-vs-non-fall labels:

```text
fall = class 1
non-fall = classes 0, 2, 3, 4, 5, 6
```

---

## 6. Completed Implementation Milestones

| Milestone | Status | Main Files |
|---|---|---|
| SenseFi smoke test | Complete | `scripts/run_sensefi_smoke_test.py`, `notes/smoke_test_log.md` |
| Short clean baseline | Complete | `scripts/run_sensefi_clean_baseline_short.py`, `results/clean_baseline_short_metrics.csv`, `notes/clean_baseline_short_log.md` |
| Clean prediction export | Complete | `scripts/export_clean_predictions_short.py`, `results/clean_predictions_short.csv` |
| Clean safety-proxy metrics | Complete | `scripts/compute_clean_safety_metrics.py`, `results/clean_safety_proxy_metrics.csv`, `notes/clean_safety_proxy_metrics_log.md` |
| FGSM attacked prediction export | Complete | `scripts/export_fgsm_predictions_short.py`, `results/fgsm_predictions_short_epsilon_0_03.csv` |
| FGSM safety-proxy metrics | Complete | `scripts/compute_fgsm_safety_metrics.py`, `results/fgsm_safety_proxy_metrics_epsilon_0_03.csv`, `notes/fgsm_safety_proxy_metrics_log.md` |
| FGSM epsilon sweep | Complete | `scripts/run_fgsm_epsilon_sweep_short.py`, `results/fgsm_epsilon_sweep_summary.csv`, `notes/fgsm_epsilon_sweep_log.md` |
| FGSM epsilon sweep figures | Complete | `scripts/plot_fgsm_epsilon_sweep.py`, `scripts/plot_fgsm_epsilon_combined_summary.py`, `figures/fgsm_epsilon_combined_safety_summary.png`, `notes/fgsm_epsilon_sweep_figures_summary.md` |
| PGD attacked prediction export | Complete | `scripts/export_pgd_predictions_short.py`, `results/pgd_predictions_short_epsilon_0_03.csv`, `notes/pgd_prediction_export_log.md` |
| PGD safety-proxy metrics | Complete | `scripts/compute_pgd_safety_metrics.py`, `results/pgd_safety_proxy_metrics_epsilon_0_03.csv`, `notes/pgd_safety_proxy_metrics_log.md` |
| PGD epsilon sweep | Complete | `scripts/run_pgd_epsilon_sweep_short.py`, `results/pgd_epsilon_sweep_summary.csv`, `notes/pgd_epsilon_sweep_log.md` |
| PGD epsilon sweep figures | Complete | `scripts/plot_pgd_epsilon_sweep.py`, `figures/pgd_epsilon_combined_safety_summary.png`, `notes/pgd_epsilon_sweep_figures_summary.md` |
| FGSM vs PGD comparison | Complete | `scripts/plot_fgsm_vs_pgd_comparison.py`, `results/fgsm_vs_pgd_epsilon_comparison.csv`, `figures/fgsm_vs_pgd_safety_comparison.png`, `notes/fgsm_vs_pgd_comparison_summary.md` |
| Final attack-safety lab report | Complete | `notes/final_fgsm_pgd_attack_safety_lab_report.md` |
| Window-level vs event-level limitation note | Complete | `notes/window_level_vs_event_level_limitations.md` |
| FGSM adversarial training defense baseline | Complete | `scripts/train_fgsm_adversarial_defense_short.py`, `results/fgsm_adversarial_training_short_metrics.csv`, `notes/adversarial_training_defense_plan.md`, `notes/fgsm_adversarial_training_defense_log.md` |
| Defended prediction export | Complete | `scripts/export_defended_predictions_short.py`, `results/defended_predictions_short.csv`, `results/defended_fgsm_predictions_short_epsilon_0_03.csv`, `results/defended_pgd_predictions_short_epsilon_0_03.csv` |
| Defended safety-proxy metrics | Complete | `scripts/compute_defended_safety_metrics.py`, `results/defended_safety_proxy_metrics.csv` |
| Defended vs undefended comparison | Complete | `scripts/compare_defended_vs_undefended_safety_metrics.py`, `results/defended_vs_undefended_safety_comparison.csv`, `notes/defended_vs_undefended_safety_comparison_plan.md`, `notes/defended_vs_undefended_safety_comparison_log.md` |
| Defended vs undefended figures | Complete | `scripts/plot_defended_vs_undefended_safety_comparison.py`, `figures/defended_vs_undefended_*.png` |

---

## 7. Clean Short Baseline Result

The shortened clean baseline completed successfully.

```text
Epoch 01/5 | train_acc=0.2858, train_loss=1.8020 | test_acc=0.2942, test_loss=1.7874
Epoch 02/5 | train_acc=0.2946, train_loss=1.7870 | test_acc=0.2942, test_loss=1.7805
Epoch 03/5 | train_acc=0.3233, train_loss=1.7412 | test_acc=0.4207, test_loss=1.6117
Epoch 04/5 | train_acc=0.4919, train_loss=1.4322 | test_acc=0.5161, test_loss=1.2782
Epoch 05/5 | train_acc=0.6142, train_loss=1.0603 | test_acc=0.6596, test_loss=1.0014
```

The model improved from approximately 29% seven-class test accuracy after the first epoch to approximately 66% after five epochs.

---

## 8. Clean Fall-vs-Non-Fall Safety-Proxy Metrics

The clean binary safety-proxy evaluation produced:

```text
Total windows: 996
Fall windows: 89
Non-fall windows: 907

TP / detected falls: 57
FN / missed falls: 32
FP / false fall alarms: 32
TN / correct non-falls: 875

Accuracy: 0.9357
Recall / sensitivity: 0.6404
Missed fall rate: 0.3596
Specificity: 0.9647
False positive rate: 0.0353
Precision: 0.6404
F1-score: 0.6404
Balanced accuracy: 0.8026
```

Note: this binary accuracy is fall-vs-non-fall accuracy, not seven-class activity recognition accuracy.

---

## 9. FGSM Attack Scope

The FGSM perturbation in this demo is applied to processed CSI tensors inside the model evaluation pipeline.

This experiment evaluates:

```text
processed CSI tensor perturbation
```

It does not evaluate:

```text
physical-layer transmission attack
packet-level attack
preamble-level attack
OFDM waveform attack
SDR attack
over-the-air attack
real-world deployment attack
```

Physical-layer and preamble-based attacks remain part of the literature-grounded threat motivation unless explicitly reproduced in later signal-level or hardware experiments.

---

## 10. FGSM Safety-Proxy Result at Epsilon 0.03

At epsilon 0.03, the FGSM attack produced strong degradation.

Clean binary metrics:

```text
TP / detected falls: 57
FN / missed falls: 32
FP / false fall alarms: 32
TN / correct non-falls: 875

Recall / sensitivity: 0.6404
Missed fall rate: 0.3596
Precision: 0.6404
F1-score: 0.6404
Balanced accuracy: 0.8026
```

FGSM-attacked binary metrics:

```text
TP / detected falls: 0
FN / missed falls: 89
FP / false fall alarms: 119
TN / correct non-falls: 788

Recall / sensitivity: 0.0000
Missed fall rate: 1.0000
Precision: 0.0000
F1-score: 0.0000
Balanced accuracy: 0.4344
```

Clean-to-FGSM safety degradation:

```text
Missed fall rate change: +0.6404
False alarm count change: +87
Recall change: -0.6404
F1-score change: -0.6404
Balanced accuracy change: -0.3682
```

---

## 11. FGSM Epsilon Sweep Summary

The epsilon sweep tested:

```text
epsilon = 0.000
epsilon = 0.005
epsilon = 0.010
epsilon = 0.020
epsilon = 0.030
```

Summary:

```text
epsilon=0.000 | seven_class_acc=0.659639 | missed_fall_rate=0.359551 | false_alarms=32  | recall=0.640449 | f1=0.640449 | prediction_change_rate=0.000000
epsilon=0.005 | seven_class_acc=0.411647 | missed_fall_rate=0.741573 | false_alarms=40  | recall=0.258427 | f1=0.302632 | prediction_change_rate=0.287149
epsilon=0.010 | seven_class_acc=0.238956 | missed_fall_rate=0.988764 | false_alarms=45  | recall=0.011236 | f1=0.014815 | prediction_change_rate=0.483936
epsilon=0.020 | seven_class_acc=0.062249 | missed_fall_rate=1.000000 | false_alarms=100 | recall=0.000000 | f1=0.000000 | prediction_change_rate=0.682731
epsilon=0.030 | seven_class_acc=0.010040 | missed_fall_rate=1.000000 | false_alarms=119 | recall=0.000000 | f1=0.000000 | prediction_change_rate=0.743976
```

The sweep shows that safety-proxy degradation increases as perturbation strength increases. This is stronger than reporting one attack setting only because it shows how missed fall rate, false alarms, recall, F1-score, and prediction instability change across perturbation levels.

---

## 12. PGD Attack Scope

The PGD perturbation in this demo is also applied to processed CSI tensors inside the model evaluation pipeline.

PGD is an iterative adversarial attack. In this implementation, it is applied to processed UT-HAR CSI tensors after data preprocessing.

Unlike FGSM, which applies a single gradient-sign update, PGD applies multiple smaller gradient-based updates and projects the perturbation back inside the allowed epsilon range after each step. This makes PGD a stronger iterative software-level adversarial attack for this research implementation.

This experiment evaluates:

```text
processed CSI tensor perturbation
iterative software-level adversarial attack behavior
window-level fall-vs-non-fall safety-proxy degradation
```

It does not evaluate:

```text
physical-layer transmission attack
packet-level attack
preamble-level attack
OFDM waveform attack
SDR attack
over-the-air attack
real-world deployment attack
```

PGD single-epsilon configuration:

```text
epsilon = 0.030
alpha = 0.005
pgd_steps = 10
epochs = 5
device = CPU
```

---

## 13. PGD Safety-Proxy Result at Epsilon 0.03

At epsilon 0.03, the PGD attack produced strong degradation in the window-level fall-vs-non-fall safety-proxy evaluation.

PGD-attacked binary metrics:

```text
Total windows: 996
Fall windows: 89
Non-fall windows: 907

TP / detected falls: 0
FN / missed falls: 89
FP / false fall alarms: 115
TN / correct non-falls: 792

Seven-class accuracy: 0.0000
Binary accuracy: 0.7952
Recall / sensitivity: 0.0000
Missed fall rate: 1.0000
Specificity: 0.8732
False positive rate: 0.1268
Precision: 0.0000
F1-score: 0.0000
Balanced accuracy: 0.4366
```

Clean-to-PGD safety degradation:

```text
Detected falls decreased from 57 to 0
Missed falls increased from 32 to 89
False fall alarms increased from 32 to 115
Recall decreased from 0.6404 to 0.0000
Missed fall rate increased from 0.3596 to 1.0000
F1-score decreased from 0.6404 to 0.0000
Balanced accuracy decreased from 0.8026 to 0.4366
```

At this epsilon, PGD caused complete loss of fall recall in the window-level binary safety-proxy evaluation.

---

## 14. PGD Epsilon Sweep Summary

The PGD epsilon sweep tested:

```text
epsilon = 0.000
epsilon = 0.005
epsilon = 0.010
epsilon = 0.020
epsilon = 0.030
```

PGD was implemented as a software-level iterative adversarial perturbation applied to processed UT-HAR CSI tensors.

For this sweep:

```text
pgd_steps = 10
alpha = epsilon / 6
epochs = 5
device = CPU
```

Summary:

```text
epsilon=0.000 | seven_class_acc=0.659639 | missed_fall_rate=0.359551 | false_alarms=32  | recall=0.640449 | f1=0.640449 | prediction_change_rate=0.000000
epsilon=0.005 | seven_class_acc=0.389558 | missed_fall_rate=0.786517 | false_alarms=43  | recall=0.213483 | f1=0.251656 | prediction_change_rate=0.310241
epsilon=0.010 | seven_class_acc=0.172691 | missed_fall_rate=1.000000 | false_alarms=70  | recall=0.000000 | f1=0.000000 | prediction_change_rate=0.561245
epsilon=0.020 | seven_class_acc=0.013052 | missed_fall_rate=1.000000 | false_alarms=111 | recall=0.000000 | f1=0.000000 | prediction_change_rate=0.745984
epsilon=0.030 | seven_class_acc=0.000000 | missed_fall_rate=1.000000 | false_alarms=115 | recall=0.000000 | f1=0.000000 | prediction_change_rate=0.778112
```

The PGD sweep shows that fall-focused safety-proxy degradation increases as perturbation strength increases. At `epsilon = 0.010` and above, PGD caused complete loss of fall recall in the window-level fall-vs-non-fall proxy evaluation.

---

## 15. PGD Epsilon Sweep Figures

The PGD epsilon sweep figures visualize how safety-proxy metrics change as PGD perturbation strength increases.

Generated PGD figures:

```text
figures/pgd_epsilon_vs_missed_fall_rate.png
figures/pgd_epsilon_vs_false_alarm_count.png
figures/pgd_epsilon_vs_recall.png
figures/pgd_epsilon_vs_f1_score.png
figures/pgd_epsilon_combined_safety_summary.png
```

The individual figures show:

```text
PGD epsilon vs missed fall rate
PGD epsilon vs false fall alarm count
PGD epsilon vs recall / sensitivity
PGD epsilon vs F1-score
```

The combined figure summarizes:

```text
missed fall rate
recall / sensitivity
F1-score
prediction change rate
```

The main visual trend is that missed fall rate rises sharply and recall falls to zero by `epsilon = 0.010`.

---

## 16. FGSM vs PGD Comparison Summary

The experiment now includes a direct FGSM vs PGD epsilon-sweep comparison.

Compared files:

```text
results/fgsm_epsilon_sweep_summary.csv
results/pgd_epsilon_sweep_summary.csv
```

Generated comparison outputs:

```text
results/fgsm_vs_pgd_epsilon_comparison.csv
figures/fgsm_vs_pgd_safety_comparison.png
notes/fgsm_vs_pgd_comparison_summary.md
```

Summary:

```text
epsilon=0.000 | FGSM missed=0.359551 | PGD missed=0.359551 | FGSM recall=0.640449 | PGD recall=0.640449 | FGSM F1=0.640449 | PGD F1=0.640449
epsilon=0.005 | FGSM missed=0.741573 | PGD missed=0.786517 | FGSM recall=0.258427 | PGD recall=0.213483 | FGSM F1=0.302632 | PGD F1=0.251656
epsilon=0.010 | FGSM missed=0.988764 | PGD missed=1.000000 | FGSM recall=0.011236 | PGD recall=0.000000 | FGSM F1=0.014815 | PGD F1=0.000000
epsilon=0.020 | FGSM missed=1.000000 | PGD missed=1.000000 | FGSM recall=0.000000 | PGD recall=0.000000 | FGSM F1=0.000000 | PGD F1=0.000000
epsilon=0.030 | FGSM missed=1.000000 | PGD missed=1.000000 | FGSM recall=0.000000 | PGD recall=0.000000 | FGSM F1=0.000000 | PGD F1=0.000000
```

At `epsilon = 0.005`, PGD caused slightly stronger degradation than FGSM in missed fall rate, recall, and F1-score.

At `epsilon = 0.010`, PGD reached complete fall-recall loss, while FGSM was already nearly fully degraded.

At `epsilon = 0.020` and `epsilon = 0.030`, both attacks caused complete fall-recall loss in this shortened baseline setting.

This comparison supports the current research goal: translating adversarial WiFi CSI model degradation into window-level fall-focused safety-proxy metrics instead of reporting seven-class accuracy alone.

Claim boundary: this is a software-level processed-tensor adversarial comparison. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment evidence, physical-layer attack validation, packet-level attack validation, preamble-level attack validation, SDR validation, or over-the-air validation.

---

## 17. FGSM Adversarial Training Defense Baseline

The experiment now includes a first FGSM adversarial-training defense baseline.

The purpose of this step is to test whether a model trained with simple FGSM-perturbed examples becomes more robust for later attacked fall-vs-non-fall safety-proxy evaluation.

Defense training configuration:

```text
dataset = UT_HAR_data
model = LeNet
epochs = 5
optimizer = Adam
learning rate = 0.001
FGSM training epsilon = 0.005
clean loss weight = 0.50
adversarial loss weight = 0.50
device = CPU
evaluation split = SenseFi validation+test loader
```

The defense training loop uses both clean CSI tensors and FGSM-perturbed CSI tensors during training.

Generated defense baseline files:

```text
scripts/train_fgsm_adversarial_defense_short.py
results/fgsm_adversarial_training_short_metrics.csv
notes/adversarial_training_defense_plan.md
notes/fgsm_adversarial_training_defense_log.md
```

Final short defense training output:

```text
Epoch 01/5 | train_clean_acc=0.2845 | train_adv_acc=0.2845 | test_clean_acc=0.2942
Epoch 02/5 | train_clean_acc=0.2946 | train_adv_acc=0.2946 | test_clean_acc=0.2952
Epoch 03/5 | train_clean_acc=0.3569 | train_adv_acc=0.3337 | test_clean_acc=0.4468
Epoch 04/5 | train_clean_acc=0.5015 | train_adv_acc=0.4259 | test_clean_acc=0.5110
Epoch 05/5 | train_clean_acc=0.5658 | train_adv_acc=0.4536 | test_clean_acc=0.5753
```

This step confirms that the defense training loop runs and saves metrics. The next step was to evaluate whether the defended model improves safety-proxy behavior under FGSM and PGD attack.

Claim boundary: this is a software-level processed-tensor adversarial training baseline. It is not a physical-layer defense, packet-level defense, preamble-level defense, SDR defense, or over-the-air defense.

---

## 18. Defended vs Undefended Safety-Proxy Comparison

The experiment now includes a defended-vs-undefended comparison using the short FGSM adversarial-training defense baseline.

The comparison evaluates:

```text
undefended clean model
undefended FGSM-attacked model
undefended PGD-attacked model
FGSM-adversarial-trained defended clean model
FGSM-adversarial-trained defended model under FGSM attack
FGSM-adversarial-trained defended model under PGD attack
```

Generated Priority 8 files:

```text
scripts/export_defended_predictions_short.py
scripts/compute_defended_safety_metrics.py
scripts/compare_defended_vs_undefended_safety_metrics.py
scripts/plot_defended_vs_undefended_safety_comparison.py

results/defended_predictions_short.csv
results/defended_fgsm_predictions_short_epsilon_0_03.csv
results/defended_pgd_predictions_short_epsilon_0_03.csv
results/defended_safety_proxy_metrics.csv
results/defended_vs_undefended_safety_comparison.csv

figures/defended_vs_undefended_balanced_accuracy.png
figures/defended_vs_undefended_f1_score.png
figures/defended_vs_undefended_false_alarm_count.png
figures/defended_vs_undefended_missed_fall_rate.png
figures/defended_vs_undefended_prediction_change_rate.png
figures/defended_vs_undefended_recall.png

notes/defended_vs_undefended_safety_comparison_plan.md
notes/defended_vs_undefended_safety_comparison_log.md
```

Main comparison table:

| Condition | Attack | TP | FN | FP | TN | Missed Fall Rate | Recall | F1-score | Balanced Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Undefended clean | none | 57 | 32 | 32 | 875 | 0.3596 | 0.6404 | 0.6404 | 0.8026 |
| Undefended FGSM, epsilon 0.03 | FGSM | 0 | 89 | 119 | 788 | 1.0000 | 0.0000 | 0.0000 | 0.4344 |
| Undefended PGD, epsilon 0.03 | PGD | 0 | 89 | 115 | 792 | 1.0000 | 0.0000 | 0.0000 | 0.4366 |
| Defended clean | none | 36 | 53 | 22 | 885 | 0.5955 | 0.4045 | 0.4898 | 0.6901 |
| Defended FGSM, epsilon 0.03 | FGSM | 0 | 89 | 72 | 835 | 1.0000 | 0.0000 | 0.0000 | 0.4603 |
| Defended PGD, epsilon 0.03 | PGD | 0 | 89 | 56 | 851 | 1.0000 | 0.0000 | 0.0000 | 0.4691 |

Main finding:

```text
The first short FGSM adversarial-training defense reduced false fall alarms under attack,
but it did not recover fall recall at epsilon 0.03.
```

False fall alarm comparison:

```text
undefended FGSM false fall alarms = 119
defended FGSM false fall alarms = 72
change = -47 false fall alarms

undefended PGD false fall alarms = 115
defended PGD false fall alarms = 56
change = -59 false fall alarms
```

However, both defended attacked conditions still produced:

```text
TP = 0
FN = 89
recall = 0.0000
missed fall rate = 1.0000
F1-score = 0.0000
```

This means the first short defense baseline reduced false alarm burden under attack but did not restore fall sensitivity.

The defended clean model also had lower clean fall-detection performance than the undefended clean model:

```text
undefended clean recall = 0.6404
defended clean recall = 0.4045

undefended clean missed fall rate = 0.3596
defended clean missed fall rate = 0.5955

undefended clean F1-score = 0.6404
defended clean F1-score = 0.4898

undefended clean balanced accuracy = 0.8026
defended clean balanced accuracy = 0.6901
```

This suggests a clean-performance tradeoff from the short 5-epoch FGSM adversarial-training setup.

This result does not prove that adversarial training is ineffective in general. A stronger conclusion would require longer clean training, longer defended training, different FGSM training epsilon values, PGD adversarial training, defended epsilon sweeps, and comparison against a longer-trained undefended baseline.

Claim boundary: this is a window-level software comparison on processed CSI tensors. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, physical-layer defense validation, packet-level defense validation, preamble-level defense validation, SDR validation, or over-the-air defense validation.

---

## 19. Current File Guide

### Scripts

```text
scripts/run_sensefi_smoke_test.py
scripts/run_sensefi_clean_baseline_short.py
scripts/export_clean_predictions_short.py
scripts/compute_clean_safety_metrics.py
scripts/export_fgsm_predictions_short.py
scripts/compute_fgsm_safety_metrics.py
scripts/run_fgsm_epsilon_sweep_short.py
scripts/plot_fgsm_epsilon_sweep.py
scripts/plot_fgsm_epsilon_combined_summary.py
scripts/export_pgd_predictions_short.py
scripts/compute_pgd_safety_metrics.py
scripts/run_pgd_epsilon_sweep_short.py
scripts/plot_pgd_epsilon_sweep.py
scripts/plot_fgsm_vs_pgd_comparison.py
scripts/train_fgsm_adversarial_defense_short.py
scripts/export_defended_predictions_short.py
scripts/compute_defended_safety_metrics.py
scripts/compare_defended_vs_undefended_safety_metrics.py
scripts/plot_defended_vs_undefended_safety_comparison.py
```

### Results

```text
results/clean_baseline_short_metrics.csv
results/clean_predictions_short.csv
results/clean_safety_proxy_metrics.csv
results/fgsm_predictions_short_epsilon_0_03.csv
results/fgsm_safety_proxy_metrics_epsilon_0_03.csv
results/fgsm_epsilon_sweep_summary.csv
results/pgd_predictions_short_epsilon_0_03.csv
results/pgd_safety_proxy_metrics_epsilon_0_03.csv
results/pgd_epsilon_sweep_summary.csv
results/fgsm_vs_pgd_epsilon_comparison.csv
results/fgsm_adversarial_training_short_metrics.csv
results/defended_predictions_short.csv
results/defended_fgsm_predictions_short_epsilon_0_03.csv
results/defended_pgd_predictions_short_epsilon_0_03.csv
results/defended_safety_proxy_metrics.csv
results/defended_vs_undefended_safety_comparison.csv
```

### Figures

```text
figures/fgsm_epsilon_combined_safety_summary.png
figures/fgsm_epsilon_vs_missed_fall_rate.png
figures/fgsm_epsilon_vs_false_alarm_count.png
figures/fgsm_epsilon_vs_recall.png
figures/fgsm_epsilon_vs_f1_score.png
figures/pgd_epsilon_combined_safety_summary.png
figures/pgd_epsilon_vs_missed_fall_rate.png
figures/pgd_epsilon_vs_false_alarm_count.png
figures/pgd_epsilon_vs_recall.png
figures/pgd_epsilon_vs_f1_score.png
figures/fgsm_vs_pgd_safety_comparison.png
figures/defended_vs_undefended_balanced_accuracy.png
figures/defended_vs_undefended_f1_score.png
figures/defended_vs_undefended_false_alarm_count.png
figures/defended_vs_undefended_missed_fall_rate.png
figures/defended_vs_undefended_prediction_change_rate.png
figures/defended_vs_undefended_recall.png
```

### Notes

```text
notes/smoke_test_log.md
notes/clean_baseline_short_log.md
notes/clean_safety_proxy_metrics_log.md
notes/fgsm_safety_proxy_metrics_log.md
notes/fgsm_epsilon_sweep_log.md
notes/fgsm_epsilon_sweep_figures_summary.md
notes/experiment_status_summary.md
notes/pgd_prediction_export_log.md
notes/pgd_safety_proxy_metrics_log.md
notes/pgd_epsilon_sweep_log.md
notes/pgd_epsilon_sweep_figures_summary.md
notes/fgsm_vs_pgd_comparison_summary.md
notes/final_fgsm_pgd_attack_safety_lab_report.md
notes/window_level_vs_event_level_limitations.md
notes/adversarial_training_defense_plan.md
notes/fgsm_adversarial_training_defense_log.md
notes/defended_vs_undefended_safety_comparison_plan.md
notes/defended_vs_undefended_safety_comparison_log.md
```

### Local ignored files

The following are local-only and should not be committed:

```text
third_party/
sensefi_env/
Data/
*.zip
*.pt
*.pth
*.ckpt
```

---

## 20. Reproducibility Commands

From this folder:

```powershell
python scripts\run_sensefi_smoke_test.py
python scripts\run_sensefi_clean_baseline_short.py
python scripts\export_clean_predictions_short.py
python scripts\compute_clean_safety_metrics.py
python scripts\export_fgsm_predictions_short.py
python scripts\compute_fgsm_safety_metrics.py
python scripts\run_fgsm_epsilon_sweep_short.py
python scripts\plot_fgsm_epsilon_sweep.py
python scripts\plot_fgsm_epsilon_combined_summary.py
python scripts\export_pgd_predictions_short.py
python scripts\compute_pgd_safety_metrics.py
python scripts\run_pgd_epsilon_sweep_short.py
python scripts\plot_pgd_epsilon_sweep.py
python scripts\plot_fgsm_vs_pgd_comparison.py
python scripts\train_fgsm_adversarial_defense_short.py
python scripts\export_defended_predictions_short.py
python scripts\compute_defended_safety_metrics.py
python scripts\compare_defended_vs_undefended_safety_metrics.py
python scripts\plot_defended_vs_undefended_safety_comparison.py
```

These commands assume the SenseFi benchmark clone and UT-HAR dataset are already available locally under the ignored `third_party/` directory.

---

## 21. Claim Boundary

This experiment is a window-level research implementation baseline for WiFi CSI fall-related activity recognition and safety-proxy metric translation.

It is not:

```text
clinical validation
medical-device validation
real patient deployment
diagnostic evidence
regulatory evaluation
physical-layer attack validation
physical-layer defense validation
packet-level attack validation
packet-level defense validation
preamble-level attack validation
preamble-level defense validation
SDR validation
over-the-air validation
event-level fall validation
long-lie validation
time-to-detection validation
```

The current contribution is a reproducible software pipeline for showing how clean, adversarial, and defended WiFi CSI model outputs can be translated into fall-focused safety-proxy metrics.

---

## 22. Next Planned Work

Planned next steps:

```text
update experiment status summary with defended-vs-undefended comparison
copy Priority 8 outputs to standalone repo
mark Priority 8 project card/status if needed
prepare thesis-ready tables and figures one by one
evaluate whether longer clean training changes robustness
rerun FGSM and PGD sweeps on a longer-trained model later
evaluate stronger defense settings later
```
---

## 23. Thesis-Ready Outputs

This experiment now includes the first thesis-ready table for summarizing clean, attacked, and defended fall-vs-non-fall safety-proxy metrics.

### Thesis Table 1: Clean, Attacked, and Defended Fall Safety-Proxy Metrics

Table 1 compares:

```text
undefended clean model
undefended FGSM-attacked model at epsilon 0.03
undefended PGD-attacked model at epsilon 0.03
FGSM-adversarial-trained defended clean model
FGSM-adversarial-trained defended model under FGSM attack at epsilon 0.03
FGSM-adversarial-trained defended model under PGD attack at epsilon 0.03
```

Generated files:

```text
scripts/create_thesis_table_1_safety_metrics.py
results/thesis_table_1_safety_metrics.csv
notes/thesis_table_1_safety_metrics.md
```

The table reports:

```text
TP
FN
FP
TN
missed fall rate
recall / sensitivity
precision
F1-score
balanced accuracy
```

Main thesis-ready finding:

```text
The first short FGSM adversarial-training defense reduced false fall alarms under FGSM and PGD attack, but it did not recover fall recall at epsilon 0.03.
```

This table is a window-level software comparison on processed CSI tensors.

It is not:

```text
clinical validation
medical-device validation
diagnostic evidence
regulatory evaluation
event-level fall validation
physical-layer validation
packet-level validation
preamble-level validation
SDR validation
over-the-air validation
```

---

### Thesis Figure 1: Defended vs Undefended Safety Tradeoff

Figure 1 summarizes the first thesis-ready visual comparison of missed fall rate and false fall alarm count across clean, attacked, and defended conditions.

The figure compares:

```text
undefended clean model
undefended FGSM-attacked model at epsilon 0.03
undefended PGD-attacked model at epsilon 0.03
FGSM-adversarial-trained defended clean model
FGSM-adversarial-trained defended model under FGSM attack at epsilon 0.03
FGSM-adversarial-trained defended model under PGD attack at epsilon 0.03
```

Generated files:

```text
scripts/create_thesis_figure_1_safety_tradeoff.py
figures/thesis_figure_1_safety_tradeoff.png
notes/thesis_figure_1_safety_tradeoff.md
```

The figure shows two fall-focused safety-proxy outcomes:

```text
missed fall rate
false fall alarm count
```

Main thesis-ready interpretation:

```text
The defended model reduced false fall alarms under FGSM and PGD attack, but it did not recover fall recall at epsilon 0.03. Therefore, missed fall rate remained 1.0 under defended FGSM and defended PGD attack.
```

This figure is a window-level software comparison on processed CSI tensors. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, event-level fall validation, physical-layer validation, packet-level validation, preamble-level validation, SDR validation, or over-the-air validation.


### Thesis Table 2: Attack Impact Delta Table

This thesis-ready table summarizes the clean-to-attacked degradation for the software-level FGSM and PGD attacks at epsilon 0.030.

It reports changes in missed fall rate, recall/sensitivity, F1-score, false fall alarm count, balanced accuracy, and prediction change rate.

Files:

- Script: [`scripts/create_thesis_table_2_attack_impact_delta.py`](scripts/create_thesis_table_2_attack_impact_delta.py)
- CSV table: [`results/thesis_table_2_attack_impact_delta.csv`](results/thesis_table_2_attack_impact_delta.csv)
- Markdown note: [`notes/thesis_table_2_attack_impact_delta.md`](notes/thesis_table_2_attack_impact_delta.md)

Main result:

- FGSM increased missed fall rate by `+0.6404`, reduced recall/sensitivity by `-0.6404`, reduced F1-score by `-0.6404`, and increased false fall alarms by `+87`.
- PGD increased missed fall rate by `+0.6404`, reduced recall/sensitivity by `-0.6404`, reduced F1-score by `-0.6404`, and increased false fall alarms by `+83`.

Claim boundary: this is a window-level safety-proxy research implementation using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.


### Thesis Figure 2: FGSM vs PGD Epsilon Sweep Curves

This thesis-ready figure compares FGSM and PGD epsilon-sweep behavior using window-level fall-vs-non-fall safety-proxy metrics.

The figure shows how perturbation strength affects:

- Missed fall rate
- Recall/sensitivity
- F1-score
- False fall alarm count

Files:

- Script: [`scripts/create_thesis_figure_2_fgsm_pgd_epsilon_sweep.py`](scripts/create_thesis_figure_2_fgsm_pgd_epsilon_sweep.py)
- Figure: [`figures/thesis_figure_2_fgsm_pgd_epsilon_sweep.png`](figures/thesis_figure_2_fgsm_pgd_epsilon_sweep.png)
- Markdown note: [`notes/thesis_figure_2_fgsm_pgd_epsilon_sweep.md`](notes/thesis_figure_2_fgsm_pgd_epsilon_sweep.md)

Main result:

- At epsilon `0.000`, both FGSM and PGD match the clean baseline with missed fall rate `0.3596`, recall/sensitivity `0.6404`, and F1-score `0.6404`.
- As epsilon increases, missed fall rate increases and recall/sensitivity decreases.
- At epsilon `0.030`, both FGSM and PGD reach missed fall rate `1.0000` and recall/sensitivity `0.0000`.
- False fall alarms also increase under attack, reaching `119` for FGSM and `115` for PGD at epsilon `0.030`.

Claim boundary: this is a window-level safety-proxy research implementation using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Table 3: Defense Tradeoff Table

This thesis-ready table summarizes the tradeoff between the undefended baseline and the first short 5-epoch FGSM adversarial-training defense.

It compares clean, FGSM-attacked, and PGD-attacked conditions using window-level fall-vs-non-fall safety-proxy metrics.

Files:

- Script: [`scripts/create_thesis_table_3_defense_tradeoff.py`](scripts/create_thesis_table_3_defense_tradeoff.py)
- CSV table: [`results/thesis_table_3_defense_tradeoff.csv`](results/thesis_table_3_defense_tradeoff.csv)
- Markdown note: [`notes/thesis_table_3_defense_tradeoff.md`](notes/thesis_table_3_defense_tradeoff.md)

Main result:

- Clean defended vs undefended: false fall alarms decreased by `10`, but recall/sensitivity decreased by `-0.2360`, missed fall rate increased by `+0.2360`, and F1-score decreased by `-0.1507`.
- FGSM defended vs undefended at epsilon `0.030`: false fall alarms decreased by `47`, but recall/sensitivity recovery remained `0.0000`.
- PGD defended vs undefended at epsilon `0.030`: false fall alarms decreased by `59`, but recall/sensitivity recovery remained `0.0000`.

Interpretation: the first short 5-epoch FGSM adversarial-training defense reduced false fall alarm burden under attack, but it did not recover fall recall at epsilon `0.030`. The clean defended model also showed a clean-performance tradeoff compared with the undefended clean baseline.

Claim boundary: this is a window-level safety-proxy research implementation using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Table 4: Epsilon Sweep Summary Table

This thesis-ready table summarizes the FGSM and PGD epsilon sweep results side by side.

It uses window-level fall-vs-non-fall safety-proxy metrics to show the dose-response relationship between perturbation strength and fall-safety degradation.

Files:

- Script: [`scripts/create_thesis_table_4_epsilon_sweep_summary.py`](scripts/create_thesis_table_4_epsilon_sweep_summary.py)
- CSV table: [`results/thesis_table_4_epsilon_sweep_summary.csv`](results/thesis_table_4_epsilon_sweep_summary.csv)
- Markdown note: [`notes/thesis_table_4_epsilon_sweep_summary.md`](notes/thesis_table_4_epsilon_sweep_summary.md)

Main result:

- At epsilon `0.000`, FGSM and PGD match the clean baseline with missed fall rate `0.3596`, recall/sensitivity `0.6404`, and F1-score `0.6404`.
- At epsilon `0.005`, missed fall rate increases to `0.7416` for FGSM and `0.7865` for PGD.
- At epsilon `0.010`, PGD reaches missed fall rate `1.0000`, while FGSM reaches `0.9888`.
- At epsilon `0.020` and `0.030`, both FGSM and PGD reach missed fall rate `1.0000` and recall/sensitivity `0.0000`.
- At epsilon `0.030`, FGSM produces `119` false fall alarms and PGD produces `115` false fall alarms.

Interpretation: Table 4 shows a clear perturbation-strength dose-response pattern. As epsilon increases, missed fall rate increases, recall/sensitivity decreases, F1-score decreases, and false fall alarm burden increases.

Claim boundary: this is a window-level safety-proxy research implementation using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Figure 3: Defense Effect Summary

This thesis-ready figure summarizes the effect of the first short 5-epoch FGSM adversarial-training defense under FGSM and PGD attack.

The figure compares:

- False fall alarm count under attack before and after defense
- Missed fall rate under attack before and after defense

Files:

- Script: [`scripts/create_thesis_figure_3_defense_effect_summary.py`](scripts/create_thesis_figure_3_defense_effect_summary.py)
- Figure: [`figures/thesis_figure_3_defense_effect_summary.png`](figures/thesis_figure_3_defense_effect_summary.png)
- Markdown note: [`notes/thesis_figure_3_defense_effect_summary.md`](notes/thesis_figure_3_defense_effect_summary.md)

Main result:

- FGSM false fall alarms decreased from `119` to `72`, a reduction of `47`.
- PGD false fall alarms decreased from `115` to `56`, a reduction of `59`.
- FGSM missed fall rate remained `1.0000` after defense at epsilon `0.030`.
- PGD missed fall rate remained `1.0000` after defense at epsilon `0.030`.
- FGSM and PGD recall/sensitivity both remained `0.0000` after defense at epsilon `0.030`.

Interpretation: the first short 5-epoch FGSM adversarial-training defense reduced false fall alarm burden under attack, but it did not recover missed-fall performance. This shows that the defense improved one safety-proxy failure mode while leaving the most critical attacked condition unresolved.

Claim boundary: this is a window-level safety-proxy research implementation using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.


### Thesis Figure 4: Clean vs Defended Clean Tradeoff

This thesis-ready figure compares the undefended clean baseline against the defended clean model.

The purpose is to show the clean-performance cost of the first short 5-epoch FGSM adversarial-training defense.

The figure compares:

- Recall/sensitivity
- Missed fall rate
- Precision
- F1-score
- Balanced accuracy
- False fall alarm count

Files:

- Script: [`scripts/create_thesis_figure_4_clean_defense_tradeoff.py`](scripts/create_thesis_figure_4_clean_defense_tradeoff.py)
- Figure: [`figures/thesis_figure_4_clean_defense_tradeoff.png`](figures/thesis_figure_4_clean_defense_tradeoff.png)
- Markdown note: [`notes/thesis_figure_4_clean_defense_tradeoff.md`](notes/thesis_figure_4_clean_defense_tradeoff.md)

Main result:

- Recall/sensitivity decreased from `0.6404` to `0.4045`.
- Missed fall rate increased from `0.3596` to `0.5955`.
- Precision decreased slightly from `0.6404` to `0.6207`.
- F1-score decreased from `0.6404` to `0.4898`.
- Balanced accuracy decreased from `0.8026` to `0.6901`.
- False fall alarms decreased from `32` to `22`.

Interpretation: the defended clean model reduced false fall alarms, but this came with lower fall recall/sensitivity, higher missed fall rate, lower F1-score, and lower balanced accuracy. This clean-condition tradeoff is important because a defense that reduces false alarms may still be undesirable if it increases missed falls.

Claim boundary: this is a window-level safety-proxy research implementation using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Figure 5: Binary Fall-vs-Non-Fall Confusion Matrices

This thesis-ready figure shows binary fall-vs-non-fall confusion matrices for clean, FGSM-attacked, and PGD-attacked conditions before and after defense.

The figure compares:

- Undefended clean
- Undefended FGSM at epsilon `0.030`
- Undefended PGD at epsilon `0.030`
- Defended clean
- Defended FGSM at epsilon `0.030`
- Defended PGD at epsilon `0.030`

Matrix layout:

```text
Rows = true class
Columns = predicted class

                 Predicted Fall    Predicted Non-Fall
True Fall              TP                  FN
True Non-Fall          FP                  TN
```

Files:

- Script: [`scripts/create_thesis_figure_5_confusion_matrices.py`](scripts/create_thesis_figure_5_confusion_matrices.py)
- Figure: [`figures/thesis_figure_5_confusion_matrices.png`](figures/thesis_figure_5_confusion_matrices.png)
- Markdown note: [`notes/thesis_figure_5_confusion_matrices.md`](notes/thesis_figure_5_confusion_matrices.md)

Main result:

- Undefended clean: TP `57`, FN `32`, FP `32`, TN `875`.
- Undefended FGSM: TP `0`, FN `89`, FP `119`, TN `788`.
- Undefended PGD: TP `0`, FN `89`, FP `115`, TN `792`.
- Defended clean: TP `36`, FN `53`, FP `22`, TN `885`.
- Defended FGSM: TP `0`, FN `89`, FP `72`, TN `835`.
- Defended PGD: TP `0`, FN `89`, FP `56`, TN `851`.

Interpretation: under FGSM and PGD attack, true detected falls drop to zero and missed falls rise to all `89` fall windows. The defended model reduces false fall alarms under attack, but it does not recover detected falls at epsilon `0.030`. The clean defended model also reduces false alarms but increases missed falls from `32` to `53`.

Claim boundary: this is a window-level safety-proxy research implementation using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Table 5: Reproducibility Configuration Table

This thesis-ready table documents the key configuration choices used in the WiFi CSI Fall Attack-Safety Demo.

The purpose is to make the first clean-to-attack-to-defense workflow easier to reproduce, audit, and extend to another dataset.

Files:

- Script: [`scripts/create_thesis_table_5_reproducibility_configuration.py`](scripts/create_thesis_table_5_reproducibility_configuration.py)
- CSV table: [`results/thesis_table_5_reproducibility_configuration.csv`](results/thesis_table_5_reproducibility_configuration.csv)
- Markdown note: [`notes/thesis_table_5_reproducibility_configuration.md`](notes/thesis_table_5_reproducibility_configuration.md)

Main configuration:

- Baseline library: SenseFi / WiFi-CSI-Sensing-Benchmark.
- Dataset: `UT_HAR_data` / UT-HAR.
- Model: LeNet / `UT_HAR_LeNet`.
- Evaluation unit: window-level processed CSI tensor.
- Evaluated windows: `996` total windows, including `89` fall windows and `907` non-fall windows.
- Clean baseline epochs: `5`.
- Defense method: FGSM adversarial training.
- Defense epochs: `5`.
- FGSM evaluation epsilon: `0.030`.
- FGSM epsilon sweep values: `0.000`, `0.005`, `0.010`, `0.020`, `0.030`.
- PGD evaluation epsilon: `0.030`.
- PGD evaluation alpha: `0.005`.
- PGD evaluation steps: `10`.
- PGD epsilon sweep values: `0.000`, `0.005`, `0.010`, `0.020`, `0.030`.
- FGSM training epsilon for defense: `0.005`.
- Adversarial loss weight: `0.5`.

Interpretation: Table 5 records the experimental scope and parameter values behind the thesis-ready tables and figures. It is useful for repeating the workflow with another WiFi CSI dataset because it separates dataset choice, model choice, attack settings, defense settings, evaluation metrics, and claim boundaries.

Claim boundary: this is a window-level safety-proxy research implementation using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Table 6: Thesis Output Index / Evidence Contribution Table

This thesis-ready table indexes the tables, figures, notes, scripts, and evidence contributions generated for the WiFi CSI Fall Attack-Safety Demo.

The purpose is to make the repository easier to navigate, explain what each output contributes to the thesis, and separate quantitative results, visual summaries, defense analysis, epsilon-sweep analysis, confusion-matrix analysis, metadata limitations, robustness-threshold analysis, confidence/error-confidence analysis, matched attack-defense analysis, and safety-translation documentation.

Files:

- `scripts/create_thesis_table_6_output_index.py`
- `results/thesis_table_6_output_index.csv`
- `notes/thesis_table_6_output_index.md`

Table 6 currently indexes:

```text
Table 1  - Clean, attacked, and defended fall safety-proxy metrics
Figure 1 - Defended vs undefended safety tradeoff
Table 2  - Attack impact delta table
Figure 2 - FGSM vs PGD epsilon sweep curves
Table 3  - Defense tradeoff table
Table 4  - Epsilon sweep summary table
Figure 3 - Defense effect summary
Figure 4 - Clean vs defended clean tradeoff
Figure 5 - Binary fall-vs-non-fall confusion matrices
Table 5  - Reproducibility configuration table
Table 6  - Thesis output index / evidence contribution table
Audit 1  - UT-HAR dataset metadata audit
Table 7  - Safety metric availability and data requirement table
Table 8  - High-risk multiclass error taxonomy
Figure 6 - Seven-class confusion matrix figure
Table 9  - Robustness failure threshold table
Figure 7 - Failure threshold / robustness collapse plot
Figure 8 - Safety translation pipeline diagram
Table 10 - Extended window-level diagnostic safety metrics
Figure 9 - Safety error burden composition across conditions
Table 11 - Attack-induced safety risk amplification ratios
Figure 10 - High-risk multiclass fall error pathways
Table 12 - Model confidence and error confidence summary
Figure 11 - High-confidence missed-fall error comparison
Figure 12 - Confidence-safety failure map
Table 13 - Confidence-safety failure ranking
Figure 13 - Confidence-safety failure ranking bar chart
Table 14 - Matched attack defense effect summary
Figure 14 - Matched attack defense effect comparison
```

Table 6 shows that the current thesis-ready output set covers ten major evidence roles:

```text
1. core clean, attacked, and defended safety-proxy metrics
2. attack-impact and epsilon-sweep degradation analysis
3. defended-vs-undefended tradeoff analysis
4. binary and seven-class confusion-matrix analysis
5. reproducibility configuration for repeating the workflow with another dataset
6. dataset metadata auditing and metric-availability boundaries
7. robustness failure-threshold analysis
8. safety-translation pipeline documentation
9. confidence/error-confidence analysis for missed-fall failures
10. matched attack-defense effect analysis
```

Interpretation: Table 6 functions as the navigation index for the thesis-ready evidence package. It also makes the research boundary clear: the current outputs are strong for window-level safety-proxy analysis, while event-level fall detection, time-to-detection, delayed detection, long-lie proxy, false alarms per hour/day, subject-level robustness, and trial-level robustness require richer metadata than the current local UT-HAR copy provides.

Claim boundary: this is a window-level safety-proxy research implementation using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, false alarms per hour/day, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### UT-HAR Dataset Metadata Audit

This note audits the local SenseFi / UT-HAR files used in this demo to check whether the dataset supports event-level clinical-safety metrics.

Result: the local UT-HAR copy contains processed window-level CSI arrays and labels, but no timestamp, duration, subject ID, trial ID, event ID, recording ID, fall start/end, window start/end, annotation, or metadata files were found.

Files:

- `notes/ut_har_dataset_metadata_audit.md`

Interpretation: the current dataset supports window-level fall-vs-non-fall safety-proxy metrics, but it does not support event-level metrics such as detection latency, time-to-detection, delayed detection rate, long-lie proxy, or false alarms per hour/day without additional metadata or a future dataset/collaboration.

### Thesis Table 7: Safety Metric Availability and Data Requirement Table

This thesis-ready table separates safety metrics that are computable from the current SenseFi / UT-HAR window-level outputs from metrics that require additional event-level, timing, subject, trial, room/session, or recording-duration metadata.

Files:

- `scripts/create_thesis_table_7_metric_availability.py`
- `results/thesis_table_7_metric_availability.csv`
- `notes/thesis_table_7_metric_availability.md`

Table 7 summarizes:

```text
12 metrics are computable now from the current window-level outputs.
1 metric is partially computable as a window-level multiclass error-taxonomy analysis.
10 metrics require additional event-level, timing, subject, trial, room/session, or recording-duration metadata.
```

Computable now:

```text
seven-class accuracy
binary fall-vs-non-fall accuracy
TP, FN, FP, TN
recall / sensitivity
missed fall rate
specificity
false positive rate
precision / positive predictive value
F1-score
balanced accuracy
false fall alarm count
prediction change rate under attack
```

Partially computable now:

```text
high-risk multiclass confusion pattern
```

This metric is partially computable because the current workflow has seven-class labels and model predictions, but it does not include event timing or clinical severity labels. It should be reported as a window-level multiclass error-taxonomy analysis, not as event-level clinical validation.

Not computable yet without richer metadata:

```text
event-level fall detection rate
event-level missed fall count
detection latency / time-to-detection
delayed detection rate
long-lie risk proxy
false alarms per hour/day
subject-level robustness
trial-level robustness
cross-subject generalization
room/session-level robustness
```

Interpretation: Table 7 prevents overclaiming by clearly identifying what the current dataset supports and what requires future dataset access or collaboration. The current workflow supports window-level safety-proxy reporting, while event-level clinical-safety metrics require timestamps, event IDs, trial IDs, subject IDs, recording duration, room/session identifiers, or related metadata.

Claim boundary: this is a window-level safety-proxy research implementation using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.


### Thesis Table 8: High-Risk Multiclass Error Taxonomy

This thesis-ready table identifies fall-relevant seven-class error patterns from the existing prediction CSV files.

The table separates two high-risk window-level error families:

```text
missed-fall multiclass errors:
true class = fall
predicted class = non-fall activity

false-fall-alarm multiclass errors:
true class = non-fall activity
predicted class = fall
```

Files:

- `scripts/create_thesis_table_8_high_risk_multiclass_error_taxonomy.py`
- `results/thesis_table_8_high_risk_multiclass_error_taxonomy.csv`
- `notes/thesis_table_8_high_risk_multiclass_error_taxonomy.md`

Table 8 summary:

```text
Undefended clean baseline: 64 total high-risk multiclass errors
Undefended FGSM, epsilon 0.030: 208 total high-risk multiclass errors
Undefended PGD, epsilon 0.030: 204 total high-risk multiclass errors
Defended clean baseline: 75 total high-risk multiclass errors
Defended FGSM, epsilon 0.030: 161 total high-risk multiclass errors
Defended PGD, epsilon 0.030: 145 total high-risk multiclass errors
```

Missed-fall multiclass errors:

```text
A true fall window is predicted as a non-fall activity such as lie down, walk, pickup, run, sit down, or stand up.
```

False-fall-alarm multiclass errors:

```text
A true non-fall window is predicted as fall.
```

Interpretation: Table 8 provides the multiclass explanation behind the binary fall-vs-non-fall safety-proxy metrics. It shows whether attacks and defenses change the pathway of failure, such as converting fall windows into walk or run, or converting non-fall activities into false fall alarms.

Claim boundary: this is a window-level multiclass error-taxonomy analysis using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.


### Thesis Figure 6: Seven-Class Confusion Matrix Figure

This thesis-ready figure visualizes seven-class confusion matrices for the clean, attacked, and defended conditions in the WiFi CSI Fall Attack-Safety Demo.

Files:

- `scripts/create_thesis_figure_6_seven_class_confusion_matrices.py`
- `figures/thesis_figure_6_seven_class_confusion_matrices.png`
- `notes/thesis_figure_6_seven_class_confusion_matrices.md`

Figure 6 includes six conditions:

```text
Undefended clean baseline
Undefended FGSM, epsilon = 0.030
Undefended PGD, epsilon = 0.030
Defended clean baseline
Defended FGSM, epsilon = 0.030
Defended PGD, epsilon = 0.030
```

Figure 6 summary:

```text
Undefended clean: accuracy = 0.6596, missed fall windows = 32, false fall alarms = 32
Undefended FGSM: accuracy = 0.0100, missed fall windows = 89, false fall alarms = 119
Undefended PGD: accuracy = 0.0000, missed fall windows = 89, false fall alarms = 115
Defended clean: accuracy = 0.6074, missed fall windows = 53, false fall alarms = 22
Defended FGSM: accuracy = 0.1526, missed fall windows = 89, false fall alarms = 72
Defended PGD: accuracy = 0.0773, missed fall windows = 89, false fall alarms = 56
```

Interpretation: Figure 6 complements Table 8 by showing the full seven-class confusion-matrix structure behind the binary fall-vs-non-fall safety-proxy metrics. It helps identify whether attacks and defenses mainly convert fall windows into specific non-fall classes, or convert non-fall activities into false fall alarms.

Claim boundary: this is a window-level seven-class confusion-matrix visualization using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Table 9: Robustness Failure Threshold Table

This thesis-ready table converts the FGSM and PGD epsilon sweeps into robustness-threshold evidence.

Instead of only reporting metrics at each epsilon, Table 9 identifies the first observed epsilon where each attack crosses predefined window-level failure thresholds.

Files:

- `scripts/create_thesis_table_9_robustness_failure_thresholds.py`
- `results/thesis_table_9_robustness_failure_thresholds.csv`
- `notes/thesis_table_9_robustness_failure_thresholds.md`

Input file:

- `results/fgsm_vs_pgd_epsilon_comparison.csv`

Table 9 key results:

```text
FGSM severe missed-fall threshold, missed_fall_rate >= 0.75:
first reached at epsilon = 0.0100

FGSM near-complete missed-fall threshold, missed_fall_rate >= 0.95:
first reached at epsilon = 0.0100

FGSM complete fall-detection collapse, missed_fall_rate >= 1.00:
first reached at epsilon = 0.0200

PGD severe missed-fall threshold, missed_fall_rate >= 0.75:
first reached at epsilon = 0.0050

PGD near-complete missed-fall threshold, missed_fall_rate >= 0.95:
first reached at epsilon = 0.0100

PGD complete fall-detection collapse, missed_fall_rate >= 1.00:
first reached at epsilon = 0.0100
```

Additional robustness thresholds:

```text
FGSM recall collapse, recall_sensitivity <= 0.05:
first reached at epsilon = 0.0100

PGD recall collapse, recall_sensitivity <= 0.05:
first reached at epsilon = 0.0100

FGSM prediction instability, prediction_change_rate >= 0.50:
first reached at epsilon = 0.0200

PGD prediction instability, prediction_change_rate >= 0.50:
first reached at epsilon = 0.0100

FGSM high false-fall alarm burden, false_alarm_count >= 100:
first reached at epsilon = 0.0200

PGD high false-fall alarm burden, false_alarm_count >= 100:
first reached at epsilon = 0.0200
```

Interpretation: Table 9 shows that robustness failure appears at low perturbation strengths in this window-level experiment. PGD reaches the severe missed-fall threshold earlier than FGSM, while both FGSM and PGD reach near-complete missed-fall behavior by epsilon `0.010`. This supports the thesis argument that attack impact should be translated into safety-proxy failure thresholds, not only reported as aggregate accuracy degradation.

Claim boundary: this is a window-level robustness-threshold analysis using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation. False-alarm thresholds are reported as window counts only and are not converted into false alarms per hour/day because recording-duration metadata is unavailable.


### Thesis Figure 7: Failure Threshold / Robustness Collapse Plot

This thesis-ready figure visualizes FGSM and PGD epsilon-sweep behavior against predefined window-level robustness failure thresholds.

Files:

- `scripts/create_thesis_figure_7_failure_threshold_plot.py`
- `figures/thesis_figure_7_failure_threshold_plot.png`
- `notes/thesis_figure_7_failure_threshold_plot.md`

Input file:

- `results/fgsm_vs_pgd_epsilon_comparison.csv`

Figure 7 includes four panels:

```text
missed fall rate
fall recall / sensitivity
false fall alarm count
prediction change rate
```

Key threshold crossings:

```text
FGSM missed_fall_rate >= 0.75:
first reached at epsilon = 0.0100

PGD missed_fall_rate >= 0.75:
first reached at epsilon = 0.0050

FGSM missed_fall_rate >= 0.95:
first reached at epsilon = 0.0100

PGD missed_fall_rate >= 0.95:
first reached at epsilon = 0.0100

FGSM recall_sensitivity <= 0.05:
first reached at epsilon = 0.0100

PGD recall_sensitivity <= 0.05:
first reached at epsilon = 0.0100

FGSM prediction_change_rate >= 0.50:
first reached at epsilon = 0.0200

PGD prediction_change_rate >= 0.50:
first reached at epsilon = 0.0100

FGSM false_alarm_count >= 100:
first reached at epsilon = 0.0200

PGD false_alarm_count >= 100:
first reached at epsilon = 0.0200
```

Interpretation: Figure 7 complements Table 9 by showing robustness-collapse behavior visually. PGD reaches the severe missed-fall threshold earlier than FGSM, while both attacks reach near-complete missed-fall behavior by epsilon `0.010`. The figure also shows increasing false fall alarm counts and prediction instability as epsilon increases.

Claim boundary: this is a window-level robustness-collapse visualization using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation. False-alarm results are window counts only and are not false alarms per hour/day because recording-duration metadata is unavailable.



### Thesis Figure 8: Safety Translation Pipeline Diagram

This thesis-ready conceptual figure summarizes the safety-translation pipeline used in the WiFi CSI Fall Attack-Safety Demo.

The figure separates three layers:

```text
Layer 1: current computable workflow
Layer 2: current thesis evidence generated from window-level outputs
Layer 3: metadata gap and future event-level extension
```

Files:

- `scripts/create_thesis_figure_8_safety_translation_pipeline.py`
- `figures/thesis_figure_8_safety_translation_pipeline.png`
- `notes/thesis_figure_8_safety_translation_pipeline.md`

Figure 8 shows the current pipeline:

```text
processed WiFi CSI windows
-> clean model prediction
-> software-level FGSM / PGD perturbation
-> attacked prediction
-> binary fall-vs-non-fall mapping
-> window-level safety-proxy metrics
```

Current thesis evidence generated from this workflow includes:

```text
robustness threshold translation
multiclass error taxonomy
safety-proxy summary metrics
reproducible GitHub artifacts
```

The figure also identifies the metadata gap that prevents event-level clinical-safety analysis in the current UT-HAR workflow:

```text
no timestamp
no event ID
no subject/trial ID
no recording duration
no fall onset time
no alert time
```

Future datasets or collaborations with richer metadata could support:

```text
event-level fall detection rate
time-to-detection
delayed detection
long-lie proxy
false alarms per hour/day
subject-level robustness
trial-level robustness
```

Interpretation: Figure 8 clearly separates the current research contribution from future clinical-safety extensions. The current contribution is a reproducible workflow for translating adversarial degradation into window-level fall safety-proxy metrics.

Claim boundary: this is a conceptual safety-translation pipeline for a window-level research implementation using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.


### Thesis Table 10: Extended Window-Level Diagnostic Safety Metrics

This thesis-ready table reports additional diagnostic-style safety-proxy metrics computed from the binary fall-vs-non-fall confusion matrix for clean, attacked, and defended conditions.

Files:

- `scripts/create_thesis_table_10_extended_diagnostic_safety_metrics.py`
- `results/thesis_table_10_extended_diagnostic_safety_metrics.csv`
- `notes/thesis_table_10_extended_diagnostic_safety_metrics.md`

Input file:

- `results/defended_vs_undefended_safety_comparison.csv`

Table 10 includes:

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

Key interpretation:

```text
Undefended clean:
NPV = 0.964719
MCC = 0.605168
Cohen's kappa = 0.605168

Undefended FGSM epsilon 0.03:
NPV = 0.898518
MCC = -0.115389
Cohen's kappa = -0.113890

Undefended PGD epsilon 0.03:
NPV = 0.898978
MCC = -0.113175
Cohen's kappa = -0.112033

Defended clean:
NPV = 0.943497
MCC = 0.463169
Cohen's kappa = 0.451090

Defended FGSM epsilon 0.03:
NPV = 0.903680
MCC = -0.087442
Cohen's kappa = -0.086865

Defended PGD epsilon 0.03:
NPV = 0.905319
MCC = -0.076458
Cohen's kappa = -0.074138
```
Interpretation: Table 10 extends the safety-proxy analysis beyond recall, precision, F1-score, and balanced accuracy. The clean undefended model has stronger agreement-style metrics than the attacked and defended-attacked conditions. Under FGSM and PGD attack at epsilon `0.030`, TP becomes zero, which causes the false-alarm-to-detected-fall and missed-fall-to-detected-fall ratios to be undefined. This is reported as `NA` rather than fabricated.

Claim boundary: these are window-level diagnostic-style safety-proxy metrics. They are not clinical diagnostic validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.


### Thesis Figure 9: Safety Error Burden Composition Across Conditions

This thesis-ready figure visualizes how the window-level safety-error burden changes across clean, attacked, and defended conditions.

Files:

- `scripts/create_thesis_figure_9_safety_error_burden_composition.py`
- `figures/thesis_figure_9_safety_error_burden_composition.png`
- `notes/thesis_figure_9_safety_error_burden_composition.md`

Input file:

- `results/defended_vs_undefended_safety_comparison.csv`

Figure 9 visualizes four binary fall-vs-non-fall confusion-matrix components:

```text
detected fall windows = TP
missed fall windows = FN
false fall alarm windows = FP
correct non-fall windows = TN
```

Window-count summary:

```text
Undefended clean:
TP = 57, FN = 32, FP = 32, TN = 875

Undefended FGSM epsilon 0.03:
TP = 0, FN = 89, FP = 119, TN = 788

Undefended PGD epsilon 0.03:
TP = 0, FN = 89, FP = 115, TN = 792

Defended clean:
TP = 36, FN = 53, FP = 22, TN = 885

Defended FGSM epsilon 0.03:
TP = 0, FN = 89, FP = 72, TN = 835

Defended PGD epsilon 0.03:
TP = 0, FN = 89, FP = 56, TN = 851
```

Interpretation: Figure 9 complements the binary confusion matrices by showing the safety burden as a stacked composition of detected fall windows, missed fall windows, false fall alarm windows, and correct non-fall windows. Under FGSM and PGD attack at epsilon `0.030`, detected fall windows collapse to zero while missed fall windows reach all 89 true fall windows. The defended attacked conditions reduce false fall alarm windows compared with the undefended attacked conditions, but still do not recover detected fall windows at epsilon `0.030`.

Claim boundary: this is a window-level safety-error burden visualization using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation. Counts are window counts only and are not false alarms per hour/day because recording-duration metadata is unavailable.


### Thesis Table 11: Attack-Induced Safety Risk Amplification Ratios

This thesis-ready table translates clean-to-attacked and clean-to-defended changes into window-level safety-risk amplification and performance-retention ratios.

Files:

- `scripts/create_thesis_table_11_attack_induced_safety_risk_amplification.py`
- `results/thesis_table_11_attack_induced_safety_risk_amplification.csv`
- `notes/thesis_table_11_attack_induced_safety_risk_amplification.md`

Input file:

- `results/defended_vs_undefended_safety_comparison.csv`

Reference condition:

```text
reference condition = undefended clean
reference missed fall rate = 0.359551
reference false fall alarm count = 32
reference recall/sensitivity = 0.640449
reference F1-score = 0.640449
reference balanced accuracy = 0.802584
```

Table 11 includes these ratio definitions:

```text
missed fall rate ratio = condition missed fall rate / clean missed fall rate
false alarm count ratio = condition false alarm count / clean false alarm count
recall retention = condition recall / clean recall
F1 retention = condition F1-score / clean F1-score
balanced accuracy retention = condition balanced accuracy / clean balanced accuracy
```

Key ratio summary:

```text
Undefended clean reference:
missed fall ratio = 1.000000
false alarm ratio = 1.000000
recall retention = 1.000000
F1 retention = 1.000000
balanced accuracy retention = 1.000000

Undefended FGSM epsilon 0.03:
missed fall ratio = 2.781247
false alarm ratio = 3.718750
recall retention = 0.000000
F1 retention = 0.000000
balanced accuracy retention = 0.541251

Undefended PGD epsilon 0.03:
missed fall ratio = 2.781247
false alarm ratio = 3.593750
recall retention = 0.000000
F1 retention = 0.000000
balanced accuracy retention = 0.543998

Defended clean:
missed fall ratio = 1.656249
false alarm ratio = 0.687500
recall retention = 0.631579
F1 retention = 0.764770
balanced accuracy retention = 0.859871

Defended FGSM epsilon 0.03:
missed fall ratio = 2.781247
false alarm ratio = 2.250000
recall retention = 0.000000
F1 retention = 0.000000
balanced accuracy retention = 0.573534

Defended PGD epsilon 0.03:
missed fall ratio = 2.781247
false alarm ratio = 1.750000
recall retention = 0.000000
F1 retention = 0.000000
balanced accuracy retention = 0.584523
```

Interpretation: Table 11 provides a compact way to describe how much window-level safety-relevant risk increases, and how much useful model performance is retained, relative to the undefended clean baseline. A missed fall rate ratio above `1.0` means the condition has more missed fall behavior than the clean baseline. A recall, F1, or balanced accuracy retention below `1.0` means the condition retains less of the clean baseline performance.

The attacked conditions show severe missed-fall amplification because the missed fall rate increases from `0.359551` in the clean baseline to `1.000000` under FGSM and PGD at epsilon `0.030`. The defended attacked conditions reduce false fall alarm burden relative to the undefended attacked conditions, but still do not recover fall recall or F1-score at epsilon `0.030`.

Claim boundary: these are window-level safety-proxy amplification and retention ratios. They are not clinical risk ratios, clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.


### Thesis Figure 10: High-Risk Multiclass Fall Error Pathways

This thesis-ready figure summarizes the most fall-relevant multiclass error pathways behind the binary fall-vs-non-fall safety-proxy results.

Files:

- `scripts/create_thesis_figure_10_high_risk_multiclass_fall_error_pathways.py`
- `figures/thesis_figure_10_high_risk_multiclass_fall_error_pathways.png`
- `notes/thesis_figure_10_high_risk_multiclass_fall_error_pathways.md`

Input file:

- `results/thesis_table_8_high_risk_multiclass_error_taxonomy.csv`

Figure 10 includes two panels:

```text
Panel A: true fall -> predicted non-fall activity
Panel B: true non-fall activity -> predicted fall
```

Missed-fall pathway summary:

```text
Undefended clean:
fall -> walk = 12
fall -> run = 20
total missed-fall pathways = 32

Undefended FGSM epsilon 0.03:
fall -> lie down = 6
fall -> walk = 60
fall -> run = 17
fall -> stand up = 6
total missed-fall pathways = 89

Undefended PGD epsilon 0.03:
fall -> lie down = 9
fall -> walk = 54
fall -> run = 15
fall -> sit down = 11
total missed-fall pathways = 89

Defended clean:
fall -> walk = 39
fall -> run = 14
total missed-fall pathways = 53

Defended FGSM epsilon 0.03:
fall -> lie down = 14
fall -> walk = 42
fall -> pickup = 3
fall -> run = 19
fall -> sit down = 1
fall -> stand up = 10
total missed-fall pathways = 89

Defended PGD epsilon 0.03:
fall -> lie down = 25
fall -> walk = 27
fall -> pickup = 4
fall -> run = 16
fall -> sit down = 4
fall -> stand up = 13
total missed-fall pathways = 89
```

False-fall-alarm pathway summary:

```text
Undefended clean:
pickup -> fall = 17
run -> fall = 2
sit down -> fall = 2
stand up -> fall = 11
total false-alarm pathways = 32

Undefended FGSM epsilon 0.03:
lie down -> fall = 11
walk -> fall = 36
pickup -> fall = 3
run -> fall = 50
sit down -> fall = 9
stand up -> fall = 10
total false-alarm pathways = 119

Undefended PGD epsilon 0.03:
lie down -> fall = 20
walk -> fall = 35
run -> fall = 34
sit down -> fall = 10
stand up -> fall = 16
total false-alarm pathways = 115

Defended clean:
walk -> fall = 1
pickup -> fall = 8
run -> fall = 3
stand up -> fall = 10
total false-alarm pathways = 22

Defended FGSM epsilon 0.03:
lie down -> fall = 9
walk -> fall = 5
pickup -> fall = 1
run -> fall = 37
sit down -> fall = 4
stand up -> fall = 16
total false-alarm pathways = 72

Defended PGD epsilon 0.03:
lie down -> fall = 7
walk -> fall = 1
pickup -> fall = 1
run -> fall = 31
sit down -> fall = 5
stand up -> fall = 11
total false-alarm pathways = 56
```

Interpretation: Figure 10 simplifies the dense seven-class confusion matrices into fall-relevant error pathways. Panel A shows where true fall windows go when they are missed. Panel B shows which non-fall activities become false fall alarms. This helps connect binary safety-proxy degradation to the original multiclass activity-recognition task.

Under FGSM and PGD attack at epsilon `0.030`, all 89 true fall windows are missed. The missed-fall pathways shift mainly toward non-fall activity classes such as `walk`, `run`, `lie down`, `sit down`, and `stand up`, depending on the condition. The false-alarm pathways also increase under attack, especially from activities such as `run`, `walk`, `lie down`, and `stand up`.

Claim boundary: these are window-level multiclass error-pathway counts only. They are not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, false alarms per hour/day, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.


### Thesis Table 12: Model Confidence and Error Confidence Summary

This thesis-ready table summarizes model-reported prediction confidence for correct predictions, incorrect predictions, missed fall windows, false fall alarm windows, and other clinically motivated window groups.

Files:

- `scripts/create_thesis_table_12_model_confidence_error_summary.py`
- `results/thesis_table_12_model_confidence_error_summary.csv`
- `notes/thesis_table_12_model_confidence_error_summary.md`

Input files:

- `results/clean_predictions_short.csv`
- `results/fgsm_predictions_short_epsilon_0_03.csv`
- `results/pgd_predictions_short_epsilon_0_03.csv`
- `results/defended_predictions_short.csv`

Confidence meaning:

```text
The confidence values are model-reported predicted-class confidence values exported from the prediction files.
They should be interpreted as model output confidence, not calibrated clinical certainty.
```

Confidence thresholds:

```text
high-confidence threshold = 0.80
low-confidence threshold = 0.50
```

Main confidence summary:

```text
Undefended clean:
all windows mean confidence = 0.660882
correct predictions mean confidence = 0.721284
incorrect predictions mean confidence = 0.543818
missed fall windows mean confidence = 0.663120
false fall alarm windows mean confidence = 0.403927

Undefended FGSM epsilon 0.03:
all windows mean confidence = 0.715659
correct predictions mean confidence = 0.402359
incorrect predictions mean confidence = 0.718836
missed fall windows mean confidence = 0.775721
false fall alarm windows mean confidence = 0.566919

Undefended PGD epsilon 0.03:
all windows mean confidence = 0.816495
correct predictions mean confidence = NA
incorrect predictions mean confidence = 0.816495
missed fall windows mean confidence = 0.872827
false fall alarm windows mean confidence = 0.669228

Defended clean:
all windows mean confidence = 0.504646
correct predictions mean confidence = 0.564123
incorrect predictions mean confidence = 0.412617
missed fall windows mean confidence = 0.462122
false fall alarm windows mean confidence = 0.287155

Defended FGSM epsilon 0.03:
all windows mean confidence = 0.478099
correct predictions mean confidence = 0.416649
incorrect predictions mean confidence = 0.489166
missed fall windows mean confidence = 0.439962
false fall alarm windows mean confidence = 0.389254

Defended PGD epsilon 0.03:
all windows mean confidence = 0.522286
correct predictions mean confidence = 0.385887
incorrect predictions mean confidence = 0.533714
missed fall windows mean confidence = 0.455713
false fall alarm windows mean confidence = 0.417461
```

Missed-fall confidence focus:

```text
Undefended clean:
missed fall windows = 32
mean confidence = 0.663120
median confidence = 0.688591
high-confidence missed-fall rate = 0.281250

Undefended FGSM epsilon 0.03:
missed fall windows = 89
mean confidence = 0.775721
median confidence = 0.833032
high-confidence missed-fall rate = 0.606742

Undefended PGD epsilon 0.03:
missed fall windows = 89
mean confidence = 0.872827
median confidence = 0.953281
high-confidence missed-fall rate = 0.820225

Defended clean:
missed fall windows = 53
mean confidence = 0.462122
median confidence = 0.415679
high-confidence missed-fall rate = 0.000000

Defended FGSM epsilon 0.03:
missed fall windows = 89
mean confidence = 0.439962
median confidence = 0.357259
high-confidence missed-fall rate = 0.123596

Defended PGD epsilon 0.03:
missed fall windows = 89
mean confidence = 0.455713
median confidence = 0.376572
high-confidence missed-fall rate = 0.134831
```

Interpretation: Table 12 adds a confidence dimension to the safety-proxy analysis. It helps identify whether the model is merely wrong, or wrong with high model-reported confidence. This is important because high-confidence missed fall windows may be more concerning than low-confidence missed fall windows in a safety-monitoring context. Similarly, high-confidence false fall alarms may reduce trust in alerts.

The undefended attacked conditions show the strongest confidence concern. Under FGSM at epsilon `0.030`, the high-confidence missed-fall rate increases to `0.606742`. Under PGD at epsilon `0.030`, the high-confidence missed-fall rate increases further to `0.820225`, with median missed-fall confidence `0.953281`. This suggests that under attack, missed fall predictions may be confidently wrong at the window level.

The defended attacked conditions still miss all 89 fall windows at epsilon `0.030`, but their missed-fall confidence is lower than the undefended attacked conditions. This supports a careful interpretation: the short defended model did not recover fall recall, but it reduced the model-reported confidence of missed-fall errors.

Claim boundary: these values are window-level model-reported predicted-class confidence summaries. They are not calibrated clinical confidence, diagnostic certainty, clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, false alarms per hour/day, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.



### Thesis Figure 11: High-Confidence Missed-Fall Error Comparison

This thesis-ready figure visualizes whether missed fall windows are associated with high model-reported prediction confidence across clean, attacked, and defended conditions.

Files:

- `scripts/create_thesis_figure_11_high_confidence_missed_fall_comparison.py`
- `figures/thesis_figure_11_high_confidence_missed_fall_comparison.png`
- `notes/thesis_figure_11_high_confidence_missed_fall_comparison.md`

Input file:

- `results/thesis_table_12_model_confidence_error_summary.csv`

Figure 11 visualizes:

```text
mean missed-fall confidence
median missed-fall confidence
high-confidence missed-fall rate
```

Missed-fall confidence summary:

```text
Undefended clean:
missed fall windows = 32
mean confidence = 0.663120
median confidence = 0.688591
high-confidence missed-fall rate = 0.281250

Undefended FGSM epsilon 0.03:
missed fall windows = 89
mean confidence = 0.775721
median confidence = 0.833032
high-confidence missed-fall rate = 0.606742

Undefended PGD epsilon 0.03:
missed fall windows = 89
mean confidence = 0.872827
median confidence = 0.953281
high-confidence missed-fall rate = 0.820225

Defended clean:
missed fall windows = 53
mean confidence = 0.462122
median confidence = 0.415679
high-confidence missed-fall rate = 0.000000

Defended FGSM epsilon 0.03:
missed fall windows = 89
mean confidence = 0.439962
median confidence = 0.357259
high-confidence missed-fall rate = 0.123596

Defended PGD epsilon 0.03:
missed fall windows = 89
mean confidence = 0.455713
median confidence = 0.376572
high-confidence missed-fall rate = 0.134831
```

Interpretation: Figure 11 shows that adversarial attacks can convert missed-fall errors into high-confidence missed-fall errors. Under FGSM and PGD at epsilon `0.030`, all 89 fall windows are missed in the undefended model. PGD produces the strongest overconfident failure mode, with median missed-fall confidence `0.953281` and high-confidence missed-fall rate `0.820225`.

The defended attacked conditions still miss all 89 fall windows at epsilon `0.030`, so the short defended model does not recover fall recall. However, the defended model substantially lowers the confidence of missed-fall errors compared with the undefended attacked model. This supports a careful interpretation: the defense reduced overconfident missed-fall behavior, but did not restore fall-detection safety performance.

Claim boundary: these values are window-level model-reported predicted-class confidence summaries. They are not calibrated clinical confidence, diagnostic certainty, clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, false alarms per hour/day, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.



### Thesis Figure 12: Confidence-Safety Failure Map

This thesis-ready figure combines window-level missed-fall safety failure with model-reported confidence behavior.

Files:

- `scripts/create_thesis_figure_12_confidence_safety_failure_map.py`
- `figures/thesis_figure_12_confidence_safety_failure_map.png`
- `notes/thesis_figure_12_confidence_safety_failure_map.md`

Input files:

- `results/defended_vs_undefended_safety_comparison.csv`
- `results/thesis_table_12_model_confidence_error_summary.csv`

Figure 12 includes two panels:

```text
Panel A = overall confidence-safety map
Panel B = zoomed view of defended attacked conditions
```

Axes:

```text
x-axis = missed fall rate
y-axis = high-confidence missed-fall rate
circle = clean
triangle = FGSM
square = PGD
point labels report high-confidence missed-fall rate
no clinical threshold lines are shown
```

Figure data:

```text
Undefended clean:
missed fall rate = 0.359551
missed fall windows = 32
mean missed-fall confidence = 0.663120
median missed-fall confidence = 0.688591
high-confidence missed-fall rate = 0.281250

Undefended FGSM epsilon 0.03:
missed fall rate = 1.000000
missed fall windows = 89
mean missed-fall confidence = 0.775721
median missed-fall confidence = 0.833032
high-confidence missed-fall rate = 0.606742

Undefended PGD epsilon 0.03:
missed fall rate = 1.000000
missed fall windows = 89
mean missed-fall confidence = 0.872827
median missed-fall confidence = 0.953281
high-confidence missed-fall rate = 0.820225

Defended clean:
missed fall rate = 0.595506
missed fall windows = 53
mean missed-fall confidence = 0.462122
median missed-fall confidence = 0.415679
high-confidence missed-fall rate = 0.000000

Defended FGSM epsilon 0.03:
missed fall rate = 1.000000
missed fall windows = 89
mean missed-fall confidence = 0.439962
median missed-fall confidence = 0.357259
high-confidence missed-fall rate = 0.123596

Defended PGD epsilon 0.03:
missed fall rate = 1.000000
missed fall windows = 89
mean missed-fall confidence = 0.455713
median missed-fall confidence = 0.376572
high-confidence missed-fall rate = 0.134831
```

Interpretation: Figure 12 combines safety failure and confidence failure into one map. Moving right means the condition misses more fall windows. Moving upward means missed fall windows are more often high-confidence errors.

The upper-right area of Panel A represents the highest-concern region because both missed fall rate and high-confidence missed-fall rate are high. In this experiment, the undefended PGD condition is the strongest confidence-safety failure case: it misses all 89 fall windows and has a high-confidence missed-fall rate of `0.820225`.

The defended attacked conditions remain far to the right because they still miss all 89 fall windows at epsilon `0.030`. However, they are much lower on the y-axis because their high-confidence missed-fall rates are much lower than the undefended attacked conditions. Panel B separates defended FGSM and defended PGD so their small difference is visible.

Claim boundary: these values are window-level model-reported confidence and safety-proxy metrics only. They are not clinical risk estimates, calibrated clinical confidence, diagnostic certainty, clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, false alarms per hour/day, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.



### Thesis Table 13: Confidence-Safety Failure Ranking

This thesis-ready table ranks clean, attacked, and defended conditions by a descriptive window-level confidence-safety failure score.

Files:

- `scripts/create_thesis_table_13_confidence_safety_failure_ranking.py`
- `results/thesis_table_13_confidence_safety_failure_ranking.csv`
- `notes/thesis_table_13_confidence_safety_failure_ranking.md`

Input files:

- `results/defended_vs_undefended_safety_comparison.csv`
- `results/thesis_table_12_model_confidence_error_summary.csv`

Descriptive score definition:

```text
confidence-safety failure score = missed fall rate * high-confidence missed-fall rate
```

This score is a descriptive ranking score only. It is not a clinical risk score, diagnostic score, regulatory score, calibrated confidence score, or medical-device safety score.

Ranked result:

```text
Rank 1:
condition = Undefended PGD epsilon 0.03
missed fall rate = 1.000000
high-confidence missed-fall rate = 0.820225
confidence-safety failure score = 0.820225
recall = 0.000000
F1-score = 0.000000
balanced accuracy = 0.436604

Rank 2:
condition = Undefended FGSM epsilon 0.03
missed fall rate = 1.000000
high-confidence missed-fall rate = 0.606742
confidence-safety failure score = 0.606742
recall = 0.000000
F1-score = 0.000000
balanced accuracy = 0.434399

Rank 3:
condition = Defended PGD epsilon 0.03
missed fall rate = 1.000000
high-confidence missed-fall rate = 0.134831
confidence-safety failure score = 0.134831
recall = 0.000000
F1-score = 0.000000
balanced accuracy = 0.469129

Rank 4:
condition = Defended FGSM epsilon 0.03
missed fall rate = 1.000000
high-confidence missed-fall rate = 0.123596
confidence-safety failure score = 0.123596
recall = 0.000000
F1-score = 0.000000
balanced accuracy = 0.460309

Rank 5:
condition = Undefended clean
missed fall rate = 0.359551
high-confidence missed-fall rate = 0.281250
confidence-safety failure score = 0.101124
recall = 0.640449
F1-score = 0.640449
balanced accuracy = 0.802584

Rank 6:
condition = Defended clean
missed fall rate = 0.595506
high-confidence missed-fall rate = 0.000000
confidence-safety failure score = 0.000000
recall = 0.404494
F1-score = 0.489796
balanced accuracy = 0.690119
```

Interpretation: Table 13 provides a ranked numeric companion to Figure 12. It identifies conditions that combine missed-fall safety failure with high model-reported confidence in the wrong prediction.

The undefended PGD condition ranks highest because it has missed fall rate `1.000000` and high-confidence missed-fall rate `0.820225`, producing the largest confidence-safety failure score. The undefended FGSM condition ranks second because it also misses all 89 fall windows but has a lower high-confidence missed-fall rate than PGD.

The defended attacked conditions still miss all 89 fall windows, but they rank lower because their high-confidence missed-fall rates are much lower than the undefended attacked conditions. This supports the careful interpretation that the short defended model reduced overconfident missed-fall behavior but did not restore fall-detection safety performance.

Claim boundary: this is a window-level descriptive ranking only. It is not a clinical risk score, diagnostic score, regulatory score, calibrated confidence score, event-level fall-risk estimate, long-lie risk estimate, time-to-alarm risk estimate, or medical-device safety score.



### Thesis Figure 13: Confidence-Safety Failure Ranking

This thesis-ready figure visualizes the Table 13 confidence-safety failure ranking as a horizontal bar chart.

Files:

- `scripts/create_thesis_figure_13_confidence_safety_failure_ranking.py`
- `figures/thesis_figure_13_confidence_safety_failure_ranking.png`
- `notes/thesis_figure_13_confidence_safety_failure_ranking.md`

Input file:

- `results/thesis_table_13_confidence_safety_failure_ranking.csv`

Descriptive score definition:

```text
confidence-safety failure score = missed fall rate * high-confidence missed-fall rate
```

The x-axis reports the confidence-safety failure score. Higher values indicate worse window-level confidence-safety failure.

Ranked visual result:

```text
Rank 1:
condition = Undefended PGD epsilon 0.03
confidence-safety failure score = 0.820225

Rank 2:
condition = Undefended FGSM epsilon 0.03
confidence-safety failure score = 0.606742

Rank 3:
condition = Defended PGD epsilon 0.03
confidence-safety failure score = 0.134831

Rank 4:
condition = Defended FGSM epsilon 0.03
confidence-safety failure score = 0.123596

Rank 5:
condition = Undefended clean
confidence-safety failure score = 0.101124

Rank 6:
condition = Defended clean
confidence-safety failure score = 0.000000
```

Interpretation: Figure 13 is the visual companion to Table 13. It makes the confidence-safety failure ranking easier to interpret.

The undefended PGD condition ranks highest because it combines missed fall rate `1.000000` with high-confidence missed-fall rate `0.820225`. The undefended FGSM condition ranks second because it also misses all fall windows but has a lower high-confidence missed-fall rate.

The defended attacked conditions still miss all 89 fall windows, but their confidence-safety failure scores are much lower than the undefended attacked conditions because their high-confidence missed-fall rates are lower. This supports the same careful interpretation as Figure 12 and Table 13: the short defended model reduced overconfident missed-fall behavior, but it did not restore fall-detection safety performance.

Claim boundary: this is a window-level descriptive ranking visualization only. The score is not a clinical risk score, diagnostic score, regulatory score, calibrated confidence score, event-level fall-risk estimate, long-lie risk estimate, time-to-alarm risk estimate, or medical-device safety score.



### Thesis Table 14: Matched Attack Defense Effect Summary

This thesis-ready table directly compares matched undefended and defended attack conditions to summarize the observed defense effect.

Files:

- `scripts/create_thesis_table_14_matched_attack_defense_effect_summary.py`
- `results/thesis_table_14_matched_attack_defense_effect_summary.csv`
- `notes/thesis_table_14_matched_attack_defense_effect_summary.md`

Input files:

- `results/defended_vs_undefended_safety_comparison.csv`
- `results/thesis_table_12_model_confidence_error_summary.csv`
- `results/thesis_table_13_confidence_safety_failure_ranking.csv`

Matched comparisons:

```text
Undefended FGSM epsilon 0.03 vs Defended FGSM epsilon 0.03
Undefended PGD epsilon 0.03 vs Defended PGD epsilon 0.03
```

Summary result:

```text
FGSM epsilon 0.03:
missed fall rate: 1.000000 -> 1.000000
high-confidence missed-fall rate: 0.606742 -> 0.123596
confidence-safety failure score: 0.606742 -> 0.123596
false fall alarms: 119 -> 72
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

PGD epsilon 0.03:
missed fall rate: 1.000000 -> 1.000000
high-confidence missed-fall rate: 0.820225 -> 0.134831
confidence-safety failure score: 0.820225 -> 0.134831
false fall alarms: 115 -> 56
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

Interpretation: Table 14 directly compares matched attack conditions. In both FGSM and PGD cases, the defended model does not restore fall recall because missed fall rate remains `1.000000`. However, the defended attacked conditions have much lower high-confidence missed-fall rates and lower confidence-safety failure scores than the corresponding undefended attacked conditions.

For FGSM, the high-confidence missed-fall rate drops from `0.606742` to `0.123596`, a `79.63%` reduction. For PGD, the high-confidence missed-fall rate drops from `0.820225` to `0.134831`, an `83.56%` reduction.

This supports a careful thesis statement: the short defended model reduced overconfident missed-fall behavior, but it did not restore window-level fall-detection safety performance.

Claim boundary: this is a matched window-level attack-defense effect summary only. These values are not clinical defense-effectiveness claims, clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall-risk reduction, long-lie risk reduction, time-to-alarm improvement, false alarms per hour/day, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.



### Thesis Figure 14: Matched Attack Defense Effect Comparison

This thesis-ready figure visualizes the matched attack-defense effect summary from Table 14.

Files:

- `scripts/create_thesis_figure_14_matched_attack_defense_effect_comparison.py`
- `figures/thesis_figure_14_matched_attack_defense_effect_comparison.png`
- `notes/thesis_figure_14_matched_attack_defense_effect_comparison.md`

Input file:

- `results/thesis_table_14_matched_attack_defense_effect_summary.csv`

Figure panels:

```text
Panel A: high-confidence missed-fall rate
Panel B: median missed-fall confidence
Panel C: false fall alarm count
```

Important context:

```text
Missed fall rate remained 1.000000 for all matched attacked conditions:

Undefended FGSM epsilon 0.03
Defended FGSM epsilon 0.03
Undefended PGD epsilon 0.03
Defended PGD epsilon 0.03
```

Because missed fall rate did not improve, Figure 14 focuses on defense effects that did improve.

Summary result:

```text
FGSM epsilon 0.03:
high-confidence missed-fall rate: 0.606742 -> 0.123596
median missed-fall confidence: 0.833032 -> 0.357259
false fall alarms: 119 -> 72
missed fall rate change = 0.000000
recall change = 0.000000

PGD epsilon 0.03:
high-confidence missed-fall rate: 0.820225 -> 0.134831
median missed-fall confidence: 0.953281 -> 0.376572
false fall alarms: 115 -> 56
missed fall rate change = 0.000000
recall change = 0.000000
```

Interpretation: Figure 14 shows that the defended attacked model reduced three error-burden metrics relative to the matched undefended attacked model: high-confidence missed-fall rate, median missed-fall confidence, and false fall alarm count.

For FGSM, the defended model reduced high-confidence missed-fall rate from `0.606742` to `0.123596`, reduced median missed-fall confidence from `0.833032` to `0.357259`, and reduced false fall alarms from `119` to `72`.

For PGD, the defended model reduced high-confidence missed-fall rate from `0.820225` to `0.134831`, reduced median missed-fall confidence from `0.953281` to `0.376572`, and reduced false fall alarms from `115` to `56`.

However, the figure must be interpreted carefully: missed fall rate remained `1.000000` under all matched attacked conditions, so the defense did not restore window-level fall recall.

This supports a careful thesis statement: the short defended model reduced overconfident error burden and false alarms, but it did not restore fall-detection safety performance.

Claim boundary: this is a matched window-level attack-defense effect visualization only. These values are not clinical defense-effectiveness claims, clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall-risk reduction, long-lie risk reduction, time-to-alarm improvement, false alarms per hour/day, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.








### Final Thesis Output Status Summary Through Figure 14

This note summarizes the complete first thesis-ready output package for the WiFi CSI Fall Attack-Safety Demo through Table 14 and Figure 14.

File:

- `notes/thesis_output_status_summary_through_figure_14.md`

The summary note covers:

```text
current thesis-ready output set
main experimental finding
defense finding
confidence-safety finding
multiclass error-pathway finding
dataset and metric availability finding
thesis contribution so far
recommended next research steps
```

Key thesis message: software-level FGSM and PGD perturbations caused complete window-level fall-miss behavior at epsilon `0.030` in the tested undefended model. The short defended model reduced overconfident missed-fall behavior and false fall alarms, but it did not restore fall recall.

Claim boundary: this is a window-level safety-proxy research implementation using software-level processed-tensor perturbations. It is not clinical validation, medical-device validation, diagnostic evidence, regulatory evaluation, real patient deployment, event-level fall validation, long-lie validation, time-to-alarm validation, false alarms per hour/day, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Table 15 and Figure 15: Paired Safety-State Transitions

Table 15 and Figure 15 add a paired same-window transition analysis across clean, attacked, and defended conditions.

Files:

```text
results/thesis_table_15_paired_safety_state_transition_table.csv
figures/thesis_figure_15_paired_safety_state_transition_heatmap.png
notes/thesis_table_15_figure_15_paired_safety_state_transitions.md
```

Purpose:

```text
clean safety state
-> attacked safety state
-> defended attacked safety state
```

This artifact tracks how each evaluated window changes between TP, FN, FP, and TN. It highlights transitions such as clean TP -> attacked FN, clean TN -> attacked FP, attacked FN -> defended FN, and attacked FP -> defended TN.

How to read the figure:

```text
Y-axis = source safety state before transition
X-axis = destination safety state after transition
cell percentage = transition count / total windows in the source safety-state row
```

The cell percentage is not the percentage of all evaluated windows.

The figure uses a shared color scale across all panels. Nonzero cells show the transition count and source-row percentage, while row labels show the source-state window total.

Claim boundary: this is a descriptive window-level safety-proxy paired transition analysis. It is not clinical validation, medical-device validation, event-level fall validation, long-lie validation, time-to-alarm validation, false alarms per hour/day, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Table 16 and Figure 16: Alert Trustworthiness

Table 16 and Figure 16 add an alert-trustworthiness view focused on predicted fall alerts.

Files:

```text
results/thesis_table_16_alert_trustworthiness.csv
figures/thesis_figure_16_fall_alert_composition.png
notes/thesis_table_16_figure_16_alert_trustworthiness.md
```

Purpose:

```text
When the model raises a fall alert, how often is it actually a fall?
```

Core definitions:

```text
predicted fall alerts = TP + FP
true fall alerts = TP
false fall alerts = FP
alert precision / PPV = TP / (TP + FP)
false-alert share among alerts = FP / (TP + FP)
missed fall count = FN
```

Figure 16 bars show predicted fall alerts only:

```text
bar height = TP + FP
```

FN is shown above each bar as missed-fall context and is not part of the bar height.

Important interpretation: PPV = 0.00 with TP = 0 and nonzero false fall alerts means fall alerts were raised, but every predicted fall alert was false. It does not mean no alerts were raised.

The defended FGSM and defended PGD conditions reduced false fall alarms compared with their matched undefended attack conditions, but PPV remained 0.00 because TP remained 0.

This artifact helps separate fall-alert trustworthiness from aggregate accuracy. It shows whether fall alerts were true fall detections or false fall alarms, and it reports missed fall count alongside alert precision.

Claim boundary: this is a descriptive window-level alert-trustworthiness analysis. It is not clinical validation, medical-device validation, event-level fall validation, false alarms per hour/day, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Table 17 and Figure 17: Class-Normalized False-Fall-Alarm Sources

Table 17 and Figure 17 add a class-normalized false-fall-alarm source analysis.

Files:

```text
results/thesis_table_17_class_normalized_false_fall_alarm_sources.csv
figures/thesis_figure_17_class_normalized_false_fall_alarm_heatmap.png
notes/thesis_table_17_figure_17_class_normalized_false_alarm_sources.md
```

Purpose:

```text
Which true non-fall activities are most likely to be falsely predicted as fall?
```

Metric definition:

```text
class-normalized false-fall-alarm rate =
false fall alerts from that true class / total true windows of that class
```

The heatmap cells show percentages. Counts and denominators are reported in Table 17.

This artifact avoids relying only on raw false-alert counts. It distinguishes whether a class is a false-alert source because it has many windows or because it has a high class-specific false-fall-alarm rate.

Claim boundary: this is a descriptive window-level class-normalized false-alert source analysis. It is not clinical validation, medical-device validation, event-level fall validation, false alarms per hour/day, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Table 18 and Figure 18: Class-Normalized Defense Effect

Table 18 and Figure 18 add a matched class-normalized defense-effect analysis for false-fall-alarm sources.

Files:

```text
results/thesis_table_18_class_normalized_defense_effect.csv
figures/thesis_figure_18_class_normalized_defense_effect_heatmap.png
notes/thesis_table_18_figure_18_class_normalized_defense_effect.md
```

Purpose:

```text
For each true non-fall activity, did the defended model reduce or increase false fall alarms compared with the matched attack?
```

Matched comparisons:

```text
FGSM Attack -> Defended FGSM
PGD Attack -> Defended PGD
```

Metric definition:

```text
class-normalized defense effect =
defended class-normalized false-alert rate - attacked class-normalized false-alert rate
```

Interpretation:

```text
negative value = defense reduced false-fall-alarm rate
positive value = defense increased false-fall-alarm rate
pp = percentage points
```

This artifact complements Table 16 and Figure 16 by showing that total false fall alerts decreased under defense, while Table 18 identifies which true non-fall classes drove those changes.

Claim boundary: this is a descriptive window-level matched defense-effect analysis. It is not clinical validation, medical-device validation, event-level fall validation, false alarms per hour/day, long-lie validation, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Table 19 and Figure 19: Missed-Fall Destination Classes

Table 19 and Figure 19 add a missed-fall destination-class analysis.

Files:

```text
results/thesis_table_19_missed_fall_destination_classes.csv
figures/thesis_figure_19_missed_fall_destination_heatmap.png
notes/thesis_table_19_figure_19_missed_fall_destination_classes.md
```

Purpose:

```text
When a true fall window is missed, what non-fall class does the model predict instead?
```

Metric definitions:

```text
destination rate among true fall windows =
true fall windows missed as that destination class / total true fall windows

share among missed fall windows =
true fall windows missed as that destination class / total missed fall windows
```

Figure 19 uses two complementary percentages: the top cell value is the destination rate among true fall windows, while the parenthetical value is the share among missed fall windows in that row.

This artifact complements missed-fall-rate analysis by showing the predicted non-fall destination class for false-negative fall windows.

Claim boundary: this is a descriptive window-level missed-fall destination analysis. It is not clinical validation, medical-device validation, event-level fall validation, long-lie validation, false alarms per hour/day, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Table 20 and Figure 20: Fall-Window Recovery and Failure Persistence

Table 20 and Figure 20 add a paired fall-window recovery and failure-persistence analysis.

Files:

```text
results/thesis_table_20_fall_window_recovery_persistence.csv
figures/thesis_figure_20_fall_window_recovery_persistence.png
notes/thesis_table_20_figure_20_fall_window_recovery_persistence.md
```

Purpose:

```text
For true fall windows, how many were detected cleanly, lost under attack, recovered by defense, or still missed after defense?
```

Definitions:

```text
TP = true fall window predicted as fall
FN = true fall window predicted as non-fall
Clean TP -> Attack FN = clean-detected fall window lost under attack
Attack FN -> Defended TP = attack-missed fall window recovered by defense
Attack FN -> Defended FN = attack-missed fall window still missed after defense
```

This artifact complements Figure 19 by showing whether fall-window detection itself was recovered after attack. The figure shows the shared clean baseline once and tracks the same fall-window sample IDs within each matched attack/defense path.

Claim boundary: this is a descriptive window-level paired recovery analysis. It is not clinical validation, medical-device validation, event-level fall validation, long-lie validation, false alarms per hour/day, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Table 21 and Figure 21: Claim Boundary and Evidence Strength Matrix

Table 21 and Figure 21 add a claim-boundary and evidence-strength summary.

Files:

```text
results/thesis_table_21_claim_boundary_evidence_matrix.csv
figures/thesis_figure_21_claim_boundary_evidence_matrix.png
notes/thesis_table_21_figure_21_claim_boundary_evidence_matrix.md
```

Purpose:

```text
What claims are supported by the current experiment, and what claims require future data, validation, or collaboration?
```

Evidence source:

```text
UT-HAR / SenseFi window-level research workflow.
```

This supports descriptive window-level proxy analysis and software-level adversarial stress testing. It does not support clinical validation, medical-device validation, event-level fall validation, deployment validation, or physical-layer / over-the-air validation.

Figure 21 separates the evidence into three vertical columns:

```text
A. Directly supported now
B. Window-level safety proxies
C. Future validation required
```

Directly supported now:

```text
software-level FGSM/PGD adversarial stress testing
defended-vs-undefended descriptive comparison
paired same-window transition analysis
reproducible table/figure workflow
```

Supported only as window-level proxies:

```text
window-level fall-vs-non-fall safety proxy
missed-fall-rate / recall degradation proxy
false-alert trustworthiness proxy
class-normalized false-alert source analysis
missed-fall destination analysis
fall-window recovery and persistence analysis
```

Not supported yet:

```text
clinical / regulatory / medical-device validation
event-level fall validation
long-lie validation
false alarms per hour/day
time-to-alarm validation
subject-level generalization
room-level generalization
physical-layer / packet-level / preamble-level / SDR / over-the-air validation
```

Claim boundary: this is a descriptive claim-boundary and evidence-strength summary based on the current window-level research workflow. It is not clinical validation, medical-device validation, event-level validation, long-lie validation, false alarms per hour/day, time-to-alarm validation, or physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

### Thesis Table 22 and Figure 22: End-to-End Evidence Map

Table 22 and Figure 22 add a meeting-friendly end-to-end evidence map for the fall attack-safety demo.

**Files**

- `results/thesis_table_22_thesis_artifact_evidence_map.csv`
- `figures/thesis_figure_22_thesis_artifact_evidence_map.png`
- `notes/thesis_table_22_figure_22_thesis_artifact_evidence_map.md`

**Purpose**

This artifact is designed to explain:

1. what was done in the demo,
2. what evidence products were produced,
3. and where collaboration with richer real-world datasets could add value.

**Figure structure**

The figure is organized into three large vertical columns:

- **Research Workflow**
- **Evidence Generated**
- **What Collaboration Could Enable**

**Main message**

Current evidence supports window-level fall-safety analysis and software-level FGSM/PGD stress testing. Richer datasets could enable event-level validation, alarm-burden analysis, long-lie analysis, subject/room generalization, and stronger clinical / care-setting relevance.

**Claim boundary**

The current package supports descriptive window-level proxy analysis and software-level stress testing. It does not by itself establish clinical, event-level, deployment, or physical-layer validation.

### Thesis Table 23 and Figure 23: Safety-Priority Sensitivity Analysis

Table 23 and Figure 23 add a missed-fall-priority sensitivity analysis.

**Files**

- `results/thesis_table_23_safety_priority_sensitivity.csv`
- `figures/thesis_figure_23_safety_priority_sensitivity_heatmap.png`
- `notes/thesis_table_23_figure_23_safety_priority_sensitivity.md`

**Purpose**

This artifact asks whether conclusions about clean, attacked, and defended conditions change when missed-fall windows are given increasing priority over false-alert windows.

**Important column mapping**

The FGSM CSV contains both clean and attacked prediction columns. This artifact uses `attacked_fall_pred_binary` for FGSM attack, not `clean_fall_pred_binary`.

**Metric**

```text
normalized safety-priority score =
FN weight × missed-fall rate + FP weight × false-positive rate
```

where:

```text
missed_fall_rate = FN / (TP + FN)
false_positive_rate = FP / (FP + TN)
```

**Scenario interpretation**

```text
1:1  = missed-fall errors and false-alert errors are weighted equally
2:1  = missed-fall errors are weighted 2× higher than false-alert errors
5:1  = missed-fall errors are weighted 5× higher than false-alert errors
10:1 = missed-fall errors are weighted 10× higher than false-alert errors
```

Lower score is better. Ranks compare the six model conditions within each scenario column.

**Claim boundary**

The weights are scenario assumptions, not clinical cost constants. This is a descriptive window-level sensitivity analysis using the current prediction outputs. It is not clinical validation, event-level fall validation, alarm-fatigue validation, time-to-alarm validation, health-economic analysis, or physical-layer / over-the-air validation.
