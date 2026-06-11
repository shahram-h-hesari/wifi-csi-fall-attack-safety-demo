\# Defended vs Undefended Safety-Proxy Comparison Log



This note documents the Priority 8 defended-vs-undefended comparison for the WiFi CSI Fall Attack-Safety Demo.



The goal of this step was to compare the existing undefended clean, FGSM-attacked, and PGD-attacked results against a first software-level FGSM adversarial-training defense baseline.



\---



\## 1. Step Summary



Priority 8 compares:



```text

undefended clean model

undefended FGSM-attacked model

undefended PGD-attacked model

FGSM-adversarial-trained defended clean model

FGSM-adversarial-trained defended model under FGSM attack

FGSM-adversarial-trained defended model under PGD attack

```



The comparison uses window-level fall-vs-non-fall safety-proxy metrics.



This step does not claim clinical validation, medical-device validation, real patient deployment, event-level fall validation, long-lie validation, physical-layer validation, SDR validation, packet-level validation, preamble-level validation, or over-the-air defense validation.



\---



\## 2. Defense Method



The defended model uses a first short FGSM adversarial-training baseline.



Configuration:



```text

dataset = UT\_HAR\_data

model = LeNet

epochs = 5

optimizer = Adam

learning rate = 0.001

FGSM training epsilon = 0.005

clean loss weight = 0.50

adversarial loss weight = 0.50

device = CPU

evaluation split = SenseFi validation+test loader

evaluated windows = 996

```



The defense is applied during training on processed CSI tensors.



It is not a physical-layer defense and does not modify WiFi packets, preambles, firmware, radios, or over-the-air transmissions.



\---



\## 3. Files Created



Scripts:



```text

scripts/export\_defended\_predictions\_short.py

scripts/compute\_defended\_safety\_metrics.py

scripts/compare\_defended\_vs\_undefended\_safety\_metrics.py

scripts/plot\_defended\_vs\_undefended\_safety\_comparison.py

```



Results:



```text

results/defended\_predictions\_short.csv

results/defended\_fgsm\_predictions\_short\_epsilon\_0\_03.csv

results/defended\_pgd\_predictions\_short\_epsilon\_0\_03.csv

results/defended\_safety\_proxy\_metrics.csv

results/defended\_vs\_undefended\_safety\_comparison.csv

```



Figures:



```text

figures/defended\_vs\_undefended\_balanced\_accuracy.png

figures/defended\_vs\_undefended\_f1\_score.png

figures/defended\_vs\_undefended\_false\_alarm\_count.png

figures/defended\_vs\_undefended\_missed\_fall\_rate.png

figures/defended\_vs\_undefended\_prediction\_change\_rate.png

figures/defended\_vs\_undefended\_recall.png

```



\---



\## 4. Main Comparison Table



| Condition | Attack | TP | FN | FP | TN | Missed Fall Rate | Recall | F1-score | Balanced Accuracy |

|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|

| Undefended clean | none | 57 | 32 | 32 | 875 | 0.3596 | 0.6404 | 0.6404 | 0.8026 |

| Undefended FGSM, epsilon 0.03 | FGSM | 0 | 89 | 119 | 788 | 1.0000 | 0.0000 | 0.0000 | 0.4344 |

| Undefended PGD, epsilon 0.03 | PGD | 0 | 89 | 115 | 792 | 1.0000 | 0.0000 | 0.0000 | 0.4366 |

| Defended clean | none | 36 | 53 | 22 | 885 | 0.5955 | 0.4045 | 0.4898 | 0.6901 |

| Defended FGSM, epsilon 0.03 | FGSM | 0 | 89 | 72 | 835 | 1.0000 | 0.0000 | 0.0000 | 0.4603 |

| Defended PGD, epsilon 0.03 | PGD | 0 | 89 | 56 | 851 | 1.0000 | 0.0000 | 0.0000 | 0.4691 |



\---



\## 5. Main Finding



The first 5-epoch FGSM adversarial-training defense did not recover fall recall at epsilon 0.03.



Both defended attacked conditions still produced:



```text

TP = 0

FN = 89

recall = 0.0000

missed fall rate = 1.0000

F1-score = 0.0000

```



This means the defended model still missed all fall windows under the tested FGSM and PGD attacks at epsilon 0.03.



However, the defense reduced false fall alarms under attack.



False fall alarm comparison:



```text

undefended FGSM false fall alarms = 119

defended FGSM false fall alarms = 72

change = -47 false fall alarms



undefended PGD false fall alarms = 115

defended PGD false fall alarms = 56

change = -59 false fall alarms

```



So, in this short 5-epoch experiment, the defense reduced false alarm burden under attack but did not restore fall sensitivity.



\---



\## 6. Clean-Model Tradeoff



The defended clean model also performed worse than the undefended clean model for fall detection.



Clean comparison:



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



This suggests a clean-performance tradeoff from the short FGSM adversarial-training setup.



This result should be interpreted carefully because this was only a short 5-epoch defense baseline.



\---



\## 7. Interpretation



The current result supports three careful conclusions:



```text

1\. A short FGSM adversarial-training defense can be implemented in the current SenseFi / UT-HAR / LeNet workflow.



2\. The first short defense baseline reduced false fall alarms under FGSM and PGD attack at epsilon 0.03.



3\. The first short defense baseline did not recover attacked fall recall, missed fall rate, or F1-score at epsilon 0.03.

```



The result does not prove that adversarial training is ineffective in general.



A stronger conclusion would require:



```text

longer clean training

longer defended training

different FGSM training epsilon values

PGD adversarial training

epsilon sweeps for defended models

comparison against a longer-trained undefended baseline

possibly a second dataset or model

```



\---



\## 8. Claim Boundary



This comparison is a window-level research implementation.



It is not:



```text

clinical validation

medical-device validation

diagnostic evidence

regulatory evaluation

real patient deployment evidence

event-level fall validation

long-lie validation

time-to-detection validation

physical-layer defense validation

packet-level defense validation

preamble-level defense validation

SDR validation

over-the-air validation

```



The reported metrics are safety-proxy metrics derived from model predictions on processed CSI tensors.



\---



\## 9. Current Status



Priority 8 progress:



```text

defended prediction export completed

defended safety-proxy metrics completed

defended vs undefended comparison CSV completed

defended vs undefended plots completed

result log note created

```



Next steps:



```text

update README with Priority 8 outputs

copy Priority 8 outputs to standalone repo

mark GitHub Project card/status if needed

then move to Priority 9 thesis-ready tables and figures

```

