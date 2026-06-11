# FGSM Epsilon Sweep Log



## Purpose



This note records the first FGSM epsilon sweep for the WiFi CSI fall detection attack-safety demo.



The goal of this step was to test whether increasing software-level FGSM perturbation strength causes gradual degradation in both seven-class activity recognition accuracy and binary fall-vs-non-fall safety-proxy metrics.



This is a processed-tensor adversarial stress test. It is not a physical-layer, packet-level, preamble-level, SDR, or over-the-air attack validation.



## Input and Output Files



The script used for this sweep was:



```text

scripts/run_fgsm_epsilon_sweep_short.py

```



The generated summary file was:



```text

results/fgsm_epsilon_sweep_summary.csv

```



## Dataset and Model Context



\- Benchmark: SenseFi / WiFi-CSI-Sensing-Benchmark

\- Dataset: UT_HAR_data

\- Model: LeNet

\- Device: CPU

\- Training duration: 5 epochs

\- Original SenseFi training setting: 200 epochs

\- Prediction split: SenseFi validation + test loader

\- Total prediction rows per epsilon: 996



This is still a shortened reproducibility and attack-safety stress-test run, not final benchmark performance.



## FGSM Epsilon Values



The sweep tested:



```text

epsilon = 0.000

epsilon = 0.005

epsilon = 0.010

epsilon = 0.020

epsilon = 0.030

```



## Binary Fall Mapping



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



For the safety-proxy layer, the labels were mapped into:



```text

fall = class 1

non-fall = classes 0, 2, 3, 4, 5, 6

```



## Sweep Summary



```text

epsilon=0.000 | seven_class_acc=0.659639 | missed_fall_rate=0.359551 | false_alarms=32  | recall=0.640449 | f1=0.640449 | prediction_change_rate=0.000000

epsilon=0.005 | seven_class_acc=0.411647 | missed_fall_rate=0.741573 | false_alarms=40  | recall=0.258427 | f1=0.302632 | prediction_change_rate=0.287149

epsilon=0.010 | seven_class_acc=0.238956 | missed_fall_rate=0.988764 | false_alarms=45  | recall=0.011236 | f1=0.014815 | prediction_change_rate=0.483936

epsilon=0.020 | seven_class_acc=0.062249 | missed_fall_rate=1.000000 | false_alarms=100 | recall=0.000000 | f1=0.000000 | prediction_change_rate=0.682731

epsilon=0.030 | seven_class_acc=0.010040 | missed_fall_rate=1.000000 | false_alarms=119 | recall=0.000000 | f1=0.000000 | prediction_change_rate=0.743976

```



## Interpretation



The epsilon sweep shows a clear degradation trend.



As FGSM perturbation strength increased, seven-class activity recognition accuracy decreased from approximately 66% at epsilon 0.000 to approximately 1% at epsilon 0.030.



The fall-focused safety-proxy metrics also degraded strongly. The missed fall rate increased from approximately 36% at epsilon 0.000 to approximately 74% at epsilon 0.005, approximately 99% at epsilon 0.010, and 100% at epsilon 0.020 and 0.030.



False fall alarms also increased as epsilon became stronger. The false alarm count increased from 32 at epsilon 0.000 to 119 at epsilon 0.030.



This is important because the experiment shows that adversarial degradation is not only a general accuracy problem. It can be translated into safety-relevant outputs:



```text

missed fall windows

false fall alarms

recall loss

F1-score loss

prediction instability

```



## Key Research Takeaway



The epsilon sweep provides stronger evidence than a single attack setting because it shows how fall-focused safety-proxy metrics change as perturbation strength increases.



This supports the research direction:



```text

clean WiFi CSI sensing output

â†’ adversarial perturbation

â†’ degraded model predictions

â†’ fall-vs-non-fall safety-proxy metric change

```



## Claim Boundary



This result is a window-level research safety-proxy evaluation.



It is not clinical validation, medical-device validation, real patient deployment, diagnostic evidence, regulatory evaluation, physical-layer attack validation, SDR validation, packet-level validation, preamble-level validation, or over-the-air validation.



The FGSM perturbation was applied to processed CSI tensors inside the model evaluation pipeline.



## Next Step



The next step is to summarize the clean baseline, FGSM attack, and epsilon sweep in the experiment README so the GitHub folder clearly communicates the current implementation milestone.


