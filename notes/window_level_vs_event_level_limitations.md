# Window-Level vs Event-Level Fall Evaluation Limitation Note



This note explains the difference between the current window-level safety-proxy evaluation and a future event-level fall-detection evaluation.



The current WiFi CSI Fall Attack-Safety Demo uses SenseFi / UT-HAR / LeNet and evaluates clean, FGSM-attacked, and PGD-attacked model behavior using window-level labels and predictions.



This is useful for a first reproducible research workflow, but it should not be interpreted as event-level fall validation or clinical validation.



---
## 1. Current Evaluation Level



The current demo evaluates individual CSI windows.



Each evaluated row represents one model input window with:



```text

sample\_id

true activity label

predicted activity label

binary fall vs non-fall true label

binary fall vs non-fall predicted label

clean or attacked prediction result

```



The binary mapping used in the current workflow is:



```text

fall = UT-HAR class 1

non-fall = UT-HAR classes 0, 2, 3, 4, 5, 6

```



The current safety-proxy metrics are calculated from window-level true and predicted labels.



---
## 2. Current Window-Level Safety-Proxy Metrics



The current workflow supports:



```text

window-level detected falls

window-level missed falls

window-level false fall alarms

window-level correct non-falls

window-level recall / sensitivity

window-level missed fall rate

window-level specificity

window-level false positive rate

window-level precision

window-level F1-score

window-level balanced accuracy

window-level prediction change rate

```



These metrics help translate adversarial model degradation into fall-focused safety-proxy language.



For example, instead of only reporting seven-class accuracy loss, the workflow reports whether the attacked model produces more missed fall windows, more false fall alarms, lower recall, lower F1-score, or higher prediction instability.



---
## 3. What Event-Level Fall Evaluation Would Require



A full event-level fall-detection evaluation would require more information than the current UT-HAR workflow provides.



Event-level evaluation would need:



```text

unique fall event IDs

timestamps for each CSI window

fall start time

fall impact time

fall end time

monitoring duration

subject/session identifiers

room or environment identifiers

window-to-event grouping

alarm generation logic

allowed detection time window

```



With this information, a future workflow could evaluate whether each real fall event was detected within an acceptable time window.



---
## 4. Event-Level Metrics Not Claimed Yet



The current demo does not claim:



```text

event-level fall recall

event-level missed fall rate

false alarms per day

false alarms per user-day

detection latency

time-to-fall detection

delayed detection rate

long-lie risk proxy

clinical alarm reliability

real-world fall monitoring performance

```



These metrics require timestamps, event IDs, fall timing, and monitoring-duration information.



The current UT-HAR-based workflow does not provide enough metadata to calculate these event-level metrics responsibly.



---
## 5. Why This Distinction Matters



Window-level metrics answer:



```text

For each CSI input window, did the model classify fall vs non-fall correctly?

```



Event-level metrics answer:



```text

For each real fall event, did the system detect the fall within a clinically meaningful time window?

```



These are different evaluation questions.



A model can perform reasonably at the window level but still fail at the event level if its detections are too late, unstable, fragmented, or too noisy for reliable alerting.



Similarly, an adversarial perturbation can degrade window-level recall and increase missed fall windows, but that does not automatically prove event-level missed falls unless event timing and alarm logic are available.



---
## 6. Current Claim Boundary



The current demo supports:



```text

window-level fall-vs-non-fall safety-proxy evaluation

clean vs FGSM-attacked comparison

clean vs PGD-attacked comparison

FGSM vs PGD comparison

processed CSI tensor adversarial perturbation analysis

```



The current demo does not support:



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

physical-layer attack validation

packet-level attack validation

preamble-level attack validation

SDR validation

over-the-air validation

```



---
## 7. Relation to the Current FGSM/PGD Results



The completed first implementation phase showed that software-level FGSM and PGD perturbations can strongly degrade window-level fall-vs-non-fall safety-proxy metrics.



In the current shortened 5-epoch baseline, the clean model produced:



```text

fall windows = 89

non-fall windows = 907

detected fall windows = 57

missed fall windows = 32

false fall alarms = 32

recall / sensitivity = 0.6404

missed fall rate = 0.3596

F1-score = 0.6404

balanced accuracy = 0.8026

```



At epsilon 0.03, the FGSM-attacked model produced:



```text

detected fall windows = 0

missed fall windows = 89

false fall alarms = 119

recall / sensitivity = 0.0000

missed fall rate = 1.0000

F1-score = 0.0000

balanced accuracy = 0.4344

```



At epsilon 0.03, the PGD-attacked model produced:



```text

detected fall windows = 0

missed fall windows = 89

false fall alarms = 115

recall / sensitivity = 0.0000

missed fall rate = 1.0000

F1-score = 0.0000

balanced accuracy = 0.4366

```



These results support the project’s current goal: translating adversarial degradation into window-level safety-proxy metrics.



They do not prove event-level missed falls, delayed rescue, long-lie risk, or real-world clinical alarm behavior.



---
## 8. Future Extension



A future event-level version of this work could use a dataset or experiment design that includes timestamps, subject/session IDs, event IDs, fall onset, fall impact time, and monitoring duration.



That would allow the workflow to extend from:



```text

window-level prediction error

```



to:



```text

event-level fall detection reliability

```



and eventually to:



```text

missed events

false alarms per monitoring duration

time-to-detection

delayed alarm behavior

long-lie risk proxy

```



This would be a stronger clinical-safety translation layer, but it is outside the claim boundary of the current first implementation phase.



---
## 9. Current Step Status



This limitation note documents the boundary between the current window-level safety-proxy workflow and future event-level fall-detection evaluation.



Status:



```text

complete

```



