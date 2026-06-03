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


