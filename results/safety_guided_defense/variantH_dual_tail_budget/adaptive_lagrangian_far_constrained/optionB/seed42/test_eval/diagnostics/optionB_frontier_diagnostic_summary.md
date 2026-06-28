# Option B seed-42 — Gate-5 frontier diagnostic summary (analysis-only)

> Reads only committed test/val CSVs. No training, no attacks, no checkpoint loading, no `.pt`. Threshold sweep = one-vs-rest on P(fall) (post-hoc, NOT the pre-registered argmax operating point). Target: TP >= 37/45 AND FP <= 45/455.

## 1-2. Threshold/frontier sweep (PGD test)

| ckpt | joint TP>=37 & FP<=45 reachable? | best TP @FP<=45 | lowest FP @TP>=37 | best recall @FAR<=10% | closest point to target |
|---|---|---|---|---|---|
| maxscore | **NO** | TP=12 (FP=45, thr=0.245) | FP=95 (TP=37, thr=0.147) | TP=12/recall=0.267 (FP=45, thr=0.245) | TP=37, FP=95 (thr=0.147) |
| maxrec | **NO** | TP=15 (FP=45, thr=0.298) | FP=107 (TP=37, thr=0.165) | TP=15/recall=0.333 (FP=45, thr=0.298) | TP=37, FP=107 (thr=0.165) |
| minFA | **NO** | TP=11 (FP=45, thr=0.181) | FP=122 (TP=37, thr=0.059) | TP=11/recall=0.244 (FP=45, thr=0.181) | TP=37, FP=122 (thr=0.059) |

## 3. Attacked P(fall) score distributions (median [q1,q3])

| ckpt | cond | adv-fall P(fall) | adv-nonfall P(fall) |
|---|---|---|---|
| maxscore | clean | 0.3294 [0.3166,0.3904] | 0.0102 [0.0009,0.0578] |
| maxscore | pgd | 0.1998 [0.1585,0.2535] | 0.0161 [0.0009,0.1130] |
| maxrec | clean | 0.3879 [0.3325,0.4512] | 0.0104 [0.0006,0.0668] |
| maxrec | pgd | 0.2656 [0.1726,0.3282] | 0.0167 [0.0005,0.1471] |
| minFA | clean | 0.3185 [0.2607,0.3789] | 0.0063 [0.0005,0.0341] |
| minFA | pgd | 0.1264 [0.0732,0.1816] | 0.0079 [0.0005,0.0664] |

## 4. Validation vs test (selected epochs)

| ckpt | ep | val acc | test acc | val PGD rec | test PGD rec | val FP | test FP | val FAR | test FAR |
|---|---|---|---|---|---|---|---|---|---|
| maxscore | 68 | 0.7258 | 0.6940 | 0.5000 | 0.4222 | 55 | 59 | 0.1217 | 0.1297 |
| maxrec | 70 | 0.7177 | 0.6680 | 0.6136 | 0.6667 | 76 | 85 | 0.1681 | 0.1868 |
| minFA | 66 | 0.7036 | 0.6980 | 0.2045 | 0.1333 | 33 | 36 | 0.0730 | 0.0791 |

## 5. Error routing (PGD argmax)

| ckpt | kind | class | count |
|---|---|---|---|
| maxscore | missed_fall_predicted_as | walk | 12 |
| maxscore | missed_fall_predicted_as | run | 10 |
| maxscore | missed_fall_predicted_as | lie down | 4 |
| maxscore | false_alarm_true_source | walk | 19 |
| maxscore | false_alarm_true_source | run | 17 |
| maxscore | false_alarm_true_source | stand up | 9 |
| maxscore | false_alarm_true_source | lie down | 8 |
| maxscore | false_alarm_true_source | pickup | 5 |
| maxscore | false_alarm_true_source | sit down | 1 |
| maxrec | missed_fall_predicted_as | walk | 8 |
| maxrec | missed_fall_predicted_as | lie down | 4 |
| maxrec | missed_fall_predicted_as | run | 2 |
| maxrec | missed_fall_predicted_as | stand up | 1 |
| maxrec | false_alarm_true_source | run | 33 |
| maxrec | false_alarm_true_source | walk | 24 |
| maxrec | false_alarm_true_source | lie down | 10 |
| maxrec | false_alarm_true_source | stand up | 10 |
| maxrec | false_alarm_true_source | pickup | 7 |
| maxrec | false_alarm_true_source | sit down | 1 |
| minFA | missed_fall_predicted_as | run | 21 |
| minFA | missed_fall_predicted_as | lie down | 8 |
| minFA | missed_fall_predicted_as | walk | 6 |
| minFA | missed_fall_predicted_as | stand up | 3 |
| minFA | missed_fall_predicted_as | pickup | 1 |
| minFA | false_alarm_true_source | run | 14 |
| minFA | false_alarm_true_source | walk | 9 |
| minFA | false_alarm_true_source | stand up | 8 |
| minFA | false_alarm_true_source | pickup | 3 |
| minFA | false_alarm_true_source | lie down | 2 |

## Conclusion

- **No threshold on any checkpoint reaches TP>=37 AND FP<=45 simultaneously.** The failure is **representation/frontier-level**, not merely checkpoint selection: the attacked fall-score and non-fall fall-score distributions overlap too much to separate by any single P(fall) threshold.

- The validation-vs-test table quantifies the **clean-guard generalization gap** (test clean acc below the 0.70 guard for all three checkpoints despite validation passing).

- Option B remains **dominated by the best prior frontier G1 seed44 (recall 0.600, FP 65, guard held)**; this diagnostic does not change the REJECT verdict.
