# FGSM Fall-vs-Non-Fall Safety-Proxy Metrics Log



## Purpose



This note records the first clean-vs-FGSM fall-vs-non-fall safety-proxy metric calculation for the WiFi CSI fall detection attack-safety demo.



The goal of this step was to evaluate whether a software-level FGSM adversarial perturbation applied to processed UT-HAR CSI tensors changes fall-focused safety-proxy metrics.



This is a research stress-test experiment. It is not a physical-world attack, not an SDR attack, not packet injection, not preamble manipulation, and not over-the-air validation.



## Input Files



The FGSM prediction export file was:



```text

results/fgsm_predictions_short_epsilon_0_03.csv

```



The generated safety-proxy metrics file was:



```text

results/fgsm_safety_proxy_metrics_epsilon_0_03.csv

```



The script used to compute the metrics was:



```text

scripts/compute_fgsm_safety_metrics.py

```



## Dataset and Model Context



\- Benchmark: SenseFi / WiFi-CSI-Sensing-Benchmark

\- Dataset: UT_HAR_data

\- Model: LeNet

\- Training duration: 5 epochs

\- Device: CPU

\- Prediction split: SenseFi validation + test loader

\- Total prediction rows: 996

\- FGSM epsilon: 0.03



The original SenseFi configuration uses 200 epochs, so this result should be treated as a shortened reproducibility and attack-safety stress-test baseline, not final benchmark performance.



## Attack Scope



The FGSM perturbation was applied to processed CSI tensors inside the model evaluation pipeline.



This means the experiment evaluates:



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



Physical-layer and preamble-based attacks remain part of the literature-grounded threat motivation unless they are explicitly reproduced in later hardware or signal-level experiments.



## Binary Fall Mapping



UT-HAR is a seven-class activity recognition dataset:



```text

0 = lie down

1 = fall

2 = walk

3 = pickup

4 = run

5 = sit down

6 = stand up

```



For the safety-proxy layer, the labels were mapped into a binary fall-vs-non-fall task:



```text

fall = class 1

non-fall = classes 0, 2, 3, 4, 5, 6

```



## Clean Binary Safety-Proxy Metrics



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



## FGSM-Attacked Binary Safety-Proxy Metrics



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



## Clean-to-FGSM Safety Degradation



```text

Missed fall rate change: +0.6404

False alarm count change: +87

Recall change: -0.6404

F1-score change: -0.6404

Balanced accuracy change: -0.3682

```



## Interpretation



Under this first FGSM setting, the model missed all fall windows in the binary fall-vs-non-fall safety-proxy evaluation.



The clean model detected 57 out of 89 fall windows and missed 32. After FGSM perturbation with epsilon 0.03, the attacked model detected 0 out of 89 fall windows and missed all 89 fall windows.



The attack also increased false fall alarms from 32 to 119. This means the perturbation harmed both safety-relevant directions:



```text

more missed fall windows

more false fall alarms

```



This result shows why evaluating only general model accuracy is not enough. The clinically motivated safety-proxy view shows whether degradation creates missed fall risk, false alarm burden, or loss of alert trustworthiness.



## Important Caution



The epsilon value of 0.03 produced a very strong degradation in this first stress test. Later experiments should evaluate smaller epsilon values, such as:



```text

0.005

0.010

0.020

0.030

```



This will help show whether the safety-proxy degradation changes gradually as perturbation strength increases.



## Claim Boundary



This result is a window-level research safety-proxy evaluation.



It is not clinical validation, medical-device validation, real patient deployment, diagnostic evidence, regulatory evaluation, physical-layer attack validation, SDR validation, packet-level validation, preamble-level validation, or over-the-air validation.



The result supports the research question:



```text

How can adversarial degradation in WiFi CSI sensing be translated into fall-focused safety-proxy metrics?

```



## Next Step



The next technical step is to test multiple FGSM epsilon values and compare how safety-proxy metrics change as perturbation strength increases.



The planned comparison is:



```text

epsilon = 0.005

epsilon = 0.010

epsilon = 0.020

epsilon = 0.030



clean missed fall rate vs attacked missed fall rate

clean false alarms vs attacked false alarms

clean recall vs attacked recall

clean F1-score vs attacked F1-score

```


