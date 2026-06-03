\# Defended vs Undefended Safety-Proxy Comparison Plan



This note defines the plan for Priority 8 of the WiFi CSI Fall Attack-Safety Demo.



Priority 8 compares the current undefended clean and attacked results against a software-level FGSM adversarial-training defense baseline.



The goal is to determine whether a defended model reduces fall-focused safety-proxy degradation under software-level adversarial perturbation.



\---



\## 1. Purpose



Previous steps completed:



```text

clean SenseFi UT-HAR LeNet baseline

clean prediction export

clean fall-vs-non-fall safety-proxy metrics

FGSM attacked prediction export

FGSM safety-proxy metrics

FGSM epsilon sweep

PGD attacked prediction export

PGD safety-proxy metrics

PGD epsilon sweep

FGSM vs PGD comparison

FGSM adversarial training defense baseline

```



However, the FGSM adversarial training step currently only saves training metrics.



It does not yet answer the main defense question:



```text

Does the defended model reduce missed fall rate, improve recall, improve F1-score,

reduce false fall alarms, or improve balanced accuracy under attack?

```



Priority 8 will answer that question using exported defended predictions and safety-proxy metrics.



\---



\## 2. Comparison Groups



The planned comparison groups are:



```text

undefended clean model

undefended FGSM-attacked model

undefended PGD-attacked model

defended clean model

defended FGSM-attacked model

defended PGD-attacked model

```



The first three groups already exist from the previous clean, FGSM, and PGD workflow.



The next step is to generate defended clean and defended attacked predictions.



\---



\## 3. Defended Model



The defended model is trained using the FGSM adversarial training baseline from Priority 7.



Current defense training configuration:



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

```



The current output file from Priority 7 is:



```text

results/fgsm\_adversarial\_training\_short\_metrics.csv

```



This file confirms that the defended training loop runs, but it is not enough for safety-proxy comparison.



\---



\## 4. Required New Outputs



Priority 8 should generate the following new files:



```text

results/defended\_predictions\_short.csv

results/defended\_fgsm\_predictions\_short\_epsilon\_0\_03.csv

results/defended\_pgd\_predictions\_short\_epsilon\_0\_03.csv

results/defended\_safety\_proxy\_metrics.csv

results/defended\_vs\_undefended\_safety\_comparison.csv

figures/defended\_vs\_undefended\_safety\_comparison.png

notes/defended\_vs\_undefended\_safety\_comparison\_log.md

```



Additional epsilon-sweep outputs can be added later after the single-epsilon defended comparison works.



\---



\## 5. First Implementation Step



The first implementation step is to create a defended prediction export script.



Planned script:



```text

scripts/export\_defended\_predictions\_short.py

```



The script should:



```text

train the FGSM adversarial-training defended model

evaluate defended clean predictions

evaluate defended FGSM-attacked predictions at epsilon 0.03

evaluate defended PGD-attacked predictions at epsilon 0.03

save prediction-level outputs to CSV

```



\---



\## 6. Prediction Columns



The defended prediction export should save:



```text

sample\_id

true\_label

true\_class\_name

defended\_clean\_predicted\_label

defended\_clean\_predicted\_class\_name

defended\_fgsm\_predicted\_label

defended\_fgsm\_predicted\_class\_name

defended\_pgd\_predicted\_label

defended\_pgd\_predicted\_class\_name

fall\_true\_binary

fall\_pred\_binary\_clean\_defended

fall\_pred\_binary\_fgsm\_defended

fall\_pred\_binary\_pgd\_defended

prediction\_confidence\_clean\_defended

prediction\_confidence\_fgsm\_defended

prediction\_confidence\_pgd\_defended

correct\_clean\_defended

correct\_fgsm\_defended

correct\_pgd\_defended

```



\---



\## 7. Safety-Proxy Metrics



The defended-vs-undefended comparison should compute:



```text

total windows

fall windows

non-fall windows

TP

FN

FP

TN

binary accuracy

recall / sensitivity

missed fall rate

specificity

false positive rate

precision

F1-score

balanced accuracy

prediction change rate

```



The key safety-proxy metrics are:



```text

missed fall rate

recall

F1-score

false fall alarm count

balanced accuracy

prediction change rate

```



\---



\## 8. Planned Figures



The planned Priority 8 figures are:



```text

defended vs undefended missed fall rate

defended vs undefended recall

defended vs undefended F1-score

defended vs undefended false alarm count

defended vs undefended balanced accuracy

```



The preferred GitHub/thesis figure is one combined summary figure:



```text

figures/defended\_vs\_undefended\_safety\_comparison.png

```



This figure should compare:



```text

undefended clean

undefended FGSM attacked

undefended PGD attacked

defended clean

defended FGSM attacked

defended PGD attacked

```



\---



\## 9. Claim Boundary



This is a software-level defended vs undefended research comparison.



It is not:



```text

clinical validation

medical-device validation

diagnostic evidence

regulatory evaluation

real patient deployment evidence

event-level fall validation

long-lie validation

physical-layer defense validation

packet-level defense validation

preamble-level defense validation

SDR validation

over-the-air defense validation

```



The defended model is trained and evaluated on processed CSI tensors.



It does not modify WiFi packets, preambles, firmware, radios, or over-the-air transmissions.



\---



\## 10. Current Status



Status:



```text

planned

```



Next step:



```text

create scripts/export\_defended\_predictions\_short.py

```

