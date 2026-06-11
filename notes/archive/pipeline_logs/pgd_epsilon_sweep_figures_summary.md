\# PGD Epsilon Sweep Figures Summary



This note documents the figures generated from the Projected Gradient Descent (PGD) epsilon sweep for the WiFi CSI Fall Attack-Safety Demo.



\## Experiment Context



\* Repository: `secure-wifi-csi-healthcare-sensing`

\* Experiment folder: `experiments/fall\_detection\_attack\_safety\_demo`

\* Dataset: `UT\_HAR\_data`

\* Model: `LeNet`

\* Attack: PGD applied to processed UT-HAR CSI tensors

\* Evaluation type: window-level fall-vs-non-fall safety-proxy analysis



\## Input File



```text

results/pgd\_epsilon\_sweep\_summary.csv

```



\## Plotting Script



```text

scripts/plot\_pgd\_epsilon\_sweep.py

```



\## Generated Figures



```text

figures/pgd\_epsilon\_vs\_missed\_fall\_rate.png

figures/pgd\_epsilon\_vs\_false\_alarm\_count.png

figures/pgd\_epsilon\_vs\_recall.png

figures/pgd\_epsilon\_vs\_f1\_score.png

figures/pgd\_epsilon\_combined\_safety\_summary.png

```



\## Figure Meanings



The PGD figure set visualizes how window-level fall-safety proxy metrics change as PGD perturbation strength increases.



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



\## Main Visual Trend



The PGD sweep figures show that increasing PGD epsilon causes strong degradation in fall-focused safety-proxy metrics.



The most important trend is that the missed fall rate rises sharply and recall falls to zero by `epsilon = 0.010`.



```text

epsilon=0.000 | missed\_fall\_rate=0.359551 | recall=0.640449 | f1=0.640449

epsilon=0.005 | missed\_fall\_rate=0.786517 | recall=0.213483 | f1=0.251656

epsilon=0.010 | missed\_fall\_rate=1.000000 | recall=0.000000 | f1=0.000000

epsilon=0.020 | missed\_fall\_rate=1.000000 | recall=0.000000 | f1=0.000000

epsilon=0.030 | missed\_fall\_rate=1.000000 | recall=0.000000 | f1=0.000000

```



\## Safety-Proxy Interpretation



These figures help translate adversarial model degradation into safety-oriented questions:



```text

Does the attacked model miss more fall windows?

Does fall recall collapse under stronger perturbation?

Does the false alarm burden increase?

Does the model become unstable under perturbation?

```



This is more informative than reporting seven-class accuracy alone because it shows how adversarial degradation affects fall-focused safety-proxy outcomes.



\## Claim Boundary



These figures summarize a software-level PGD perturbation experiment on processed UT-HAR CSI tensors.



They are not:



\* clinical validation

\* medical-device validation

\* diagnostic evidence

\* regulatory evaluation

\* real patient deployment evidence

\* event-level fall detection validation

\* long-lie validation

\* physical-layer attack validation

\* packet-level attack validation

\* preamble-level attack validation

\* SDR validation

\* over-the-air validation



\## Current Step Status



The PGD epsilon sweep figure generation step is complete.



New files from this step:



```text

scripts/plot\_pgd\_epsilon\_sweep.py

figures/pgd\_epsilon\_vs\_missed\_fall\_rate.png

figures/pgd\_epsilon\_vs\_false\_alarm\_count.png

figures/pgd\_epsilon\_vs\_recall.png

figures/pgd\_epsilon\_vs\_f1\_score.png

figures/pgd\_epsilon\_combined\_safety\_summary.png

notes/pgd\_epsilon\_sweep\_figures\_summary.md

```



Recommended commit message:



```text

Add PGD epsilon sweep figures

```

