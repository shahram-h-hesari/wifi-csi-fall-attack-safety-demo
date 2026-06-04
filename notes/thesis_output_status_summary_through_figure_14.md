# Thesis Output Status Summary Through Figure 14

This note summarizes the current thesis-ready output set for the WiFi CSI Fall Attack-Safety Demo.

The experiment implements a window-level research workflow using SenseFi / UT-HAR, LeNet, software-level FGSM and PGD perturbations, a short adversarial-training defense baseline, and safety-proxy evaluation for binary fall-vs-non-fall outcomes.

## Claim Boundary

Research implementation only; window-level safety-proxy evaluation; software-level processed-tensor perturbations only; model confidence means model-reported predicted-class confidence, not calibrated clinical confidence; not clinical validation, not medical-device validation, not diagnostic evidence, not real patient deployment, not regulatory evaluation, not event-level fall validation, not long-lie validation, not time-to-alarm validation, not false alarms per hour/day, and not physical-layer / packet-level / preamble-level / SDR / over-the-air validation.

## Repositories Updated

This output set is maintained in two repositories:

```text
Main experiment folder:
secure-wifi-csi-healthcare-sensing/experiments/fall_detection_attack_safety_demo
Standalone public demo repo:
wifi-csi-fall-attack-safety-demo
```

## Current Thesis-Ready Output Set

The current output set is indexed in:

```text
Table 6: Thesis Output Index / Evidence Contribution Table
```

Table 6 now indexes outputs through:

```text
Table 14: Matched Attack Defense Effect Summary
Figure 14: Matched Attack Defense Effect Comparison
```

The indexed output set includes:

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

## Main Experimental Finding

The current workflow shows that software-level adversarial perturbations can convert a window-level WiFi CSI fall-detection model from partial fall detection into complete fall-miss behavior under the tested FGSM and PGD epsilon 0.030 conditions.

For the undefended clean model:

```text
TP = 57
FN = 32
FP = 32
TN = 875
recall / sensitivity = 0.640449
missed fall rate = 0.359551
F1-score = 0.640449
balanced accuracy = 0.802584
```

For the undefended attacked model:

```text
FGSM epsilon 0.030:
TP = 0
FN = 89
FP = 119
TN = 788
missed fall rate = 1.000000
recall / sensitivity = 0.000000
F1-score = 0.000000
PGD epsilon 0.030:
TP = 0
FN = 89
FP = 115
TN = 792
missed fall rate = 1.000000
recall / sensitivity = 0.000000
F1-score = 0.000000
```

This supports the thesis argument that aggregate model degradation should be translated into safety-proxy outcomes such as missed-fall rate, false fall alarm burden, recall collapse, and high-risk confusion patterns.

## Defense Finding

The short defended model reduced some attacked error-burden metrics, but it did not restore fall recall.

For matched FGSM attack-defense comparison:

```text
missed fall rate: 1.000000 -> 1.000000
high-confidence missed-fall rate: 0.606742 -> 0.123596
confidence-safety failure score: 0.606742 -> 0.123596
false fall alarms: 119 -> 72
high-confidence missed-fall rate reduction = 79.63%
recall change = 0.000000
```

For matched PGD attack-defense comparison:

```text
missed fall rate: 1.000000 -> 1.000000
high-confidence missed-fall rate: 0.820225 -> 0.134831
confidence-safety failure score: 0.820225 -> 0.134831
false fall alarms: 115 -> 56
high-confidence missed-fall rate reduction = 83.56%
recall change = 0.000000
```

Careful interpretation: the short defended model reduced overconfident missed-fall behavior and false fall alarms, but it did not recover window-level fall-detection recall under the tested FGSM and PGD conditions.

## Confidence-Safety Finding

The confidence/error-confidence analysis adds a second safety-proxy dimension beyond whether a fall was missed.

The strongest confidence-safety failure condition is:

```text
Undefended PGD epsilon 0.030
missed fall rate = 1.000000
high-confidence missed-fall rate = 0.820225
confidence-safety failure score = 0.820225
median missed-fall confidence = 0.953281
```

The next strongest condition is:

```text
Undefended FGSM epsilon 0.030
missed fall rate = 1.000000
high-confidence missed-fall rate = 0.606742
confidence-safety failure score = 0.606742
median missed-fall confidence = 0.833032
```

This supports the argument that adversarial WiFi CSI sensing evaluation should not only ask whether falls are missed, but also whether missed-fall errors are made with high model confidence.

## Multiclass Error-Pathway Finding

The binary fall-vs-non-fall results are explained further by seven-class error pathways.

Under attack, true fall windows are redirected into non-fall activity labels, and non-fall activities are also sometimes converted into false fall alarms.

Figure 10 and Table 8 show these two high-risk window-level error families:

```text
missed-fall pathway:
true fall -> predicted non-fall activity
false-fall-alarm pathway:
true non-fall activity -> predicted fall
```

This helps connect binary clinical-safety proxy results to the original multiclass activity-recognition task.

## Dataset and Metric Availability Finding

The UT-HAR metadata audit found that the current local dataset supports window-level analysis but does not provide the metadata needed for event-level clinical-safety metrics.

Current dataset supports:

```text
window-level fall-vs-non-fall metrics
binary confusion matrix
seven-class confusion matrix
missed fall rate
false fall alarm count
recall / sensitivity
precision
F1-score
balanced accuracy
prediction change rate
confidence/error-confidence summaries
```

Current dataset does not support, without additional metadata:

```text
event-level fall detection rate
event-level missed fall count
detection latency / time-to-detection
delayed detection rate
long-lie risk proxy
false alarms per hour/day
subject-level robustness
trial-level robustness
room/session-level robustness
cross-subject generalization
```

This is an important future dataset-selection and collaboration opportunity.

## Thesis Contribution So Far

The current demo contributes a reproducible window-level safety-proxy evaluation layer for adversarial WiFi CSI fall sensing.

The contribution is not that the attack itself is new. The contribution is the translation layer:

```text
WiFi CSI model predictions
-> clean and attacked predictions
-> fall-vs-non-fall confusion matrix
-> safety-proxy metrics
-> confidence/error-confidence analysis
-> matched defense-effect analysis
-> claim-bounded thesis-ready tables and figures
```

This directly supports the broader thesis goal: evaluating adversarial robustness of WiFi CSI sensing in a healthcare-relevant way without overclaiming clinical validation.

## Recommended Next Research Steps

The next research steps should be prioritized as follows:

```text
1. Repeat the workflow on another dataset or baseline if feasible.
2. Add a longer-trained clean baseline and compare whether results change.
3. Run stronger or longer adversarial training to test whether recall can be recovered.
4. Search for datasets with event IDs, timestamps, subject IDs, trial IDs, or recording duration.
5. If richer metadata becomes available, add event-level fall detection, detection latency, delayed detection, long-lie proxy, and false alarms per hour/day.
6. Keep this current UT-HAR workflow as the first reproducible baseline and thesis evidence package.
```

## Current Status

As of this summary, the demo has a complete first thesis-ready output package through Table 14 and Figure 14.

Both repositories should remain synchronized after each new table, figure, note, or README update.

