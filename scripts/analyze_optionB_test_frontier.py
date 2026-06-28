"""
Option B seed-42 — Gate-5 frontier diagnostic (ANALYSIS ONLY).

Reads ONLY already-created CSVs (no torch, no attacks, no checkpoint loading, no .pt, no model eval):
  * test probabilities:  results/.../optionB/seed42/test_eval/optionB_{cand}_{cond}_probabilities_test_*.csv
  * training log (val):  results/.../optionB/seed42/logs/seed42_optionB_training_log.csv

Produces under results/.../optionB/seed42/test_eval/diagnostics/:
  * optionB_threshold_frontier_sweep.csv     (per-checkpoint PGD threshold sweep: thr, TP, FP, recall, FAR)
  * optionB_score_distribution_summary.csv   (adv fall vs adv nonfall P(fall) median/IQR per checkpoint+cond)
  * optionB_error_routing.csv                (PGD missed-fall predicted classes; false-alarm source classes)
  * optionB_val_vs_test.csv                  (validation vs test clean/PGD metrics per selected checkpoint)
  * optionB_frontier_diagnostic_summary.md   (human-readable findings)

Target (joint): TP >= 37/45 (recall >= 0.80) AND FP <= 45/455 (FAR <= 10%). Decision rule for the sweep is a
one-vs-rest threshold on P(fall) (`fall_probability`), i.e. predict FALL iff P(fall) >= thr. This is post-hoc
threshold analysis, NOT the pre-registered argmax operating point.
"""
from __future__ import annotations
from pathlib import Path
import csv, statistics

EXP = Path(__file__).resolve().parents[1]
B = EXP / "results" / "safety_guided_defense" / "variantH_dual_tail_budget" / \
    "adaptive_lagrangian_far_constrained" / "optionB" / "seed42"
TE = B / "test_eval"
DIAG = TE / "diagnostics"
CANDS = ["maxscore", "maxrec", "minFA"]
SEL_EPOCH = {"maxscore": 68, "maxrec": 70, "minFA": 66}
N_FALL, N_NONFALL = 45, 455
TP_TARGET, FP_TARGET = 37, 45      # recall>=0.80, FAR<=10%


def load(cand, cond):
    f = TE / f"optionB_{cand}_{cond}_probabilities_test_epsilon_0_03.csv"
    with f.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def pfall(rows, fall_true):
    return [float(r["fall_probability"]) for r in rows if (r["fall_true_binary"] == "1") == fall_true]


def iqr_summary(xs):
    if not xs:
        return (float("nan"),) * 4
    xs = sorted(xs)
    q1 = statistics.quantiles(xs, n=4)[0] if len(xs) > 1 else xs[0]
    q3 = statistics.quantiles(xs, n=4)[2] if len(xs) > 1 else xs[0]
    return (statistics.median(xs), q1, q3, max(xs))


def sweep(rows):
    """One-vs-rest threshold sweep on P(fall). Returns list of (thr, TP, FP, recall, FAR)."""
    fall_p = pfall(rows, True)
    nonfall_p = pfall(rows, False)
    thrs = sorted(set([0.0] + fall_p + nonfall_p + [1.0]))
    out = []
    for t in thrs:
        tp = sum(1 for p in fall_p if p >= t)
        fp = sum(1 for p in nonfall_p if p >= t)
        out.append((t, tp, fp, tp / N_FALL, fp / N_NONFALL))
    return out


def main():
    DIAG.mkdir(parents=True, exist_ok=True)

    # ---- 1+2. threshold frontier sweep -------------------------------------------------------------
    sweep_rows = []
    per_cand = {}
    for cand in CANDS:
        pg = load(cand, "pgd")
        sw = sweep(pg)
        for (t, tp, fp, rec, far) in sw:
            sweep_rows.append([cand, f"{t:.6f}", tp, fp, f"{rec:.4f}", f"{far:.4f}"])
        # joint target reachable?
        joint = [(t, tp, fp) for (t, tp, fp, rec, far) in sw if tp >= TP_TARGET and fp <= FP_TARGET]
        # best TP s.t. FP<=45
        best_tp_fp45 = max(((tp, fp, t) for (t, tp, fp, rec, far) in sw if fp <= FP_TARGET), default=(0, 0, None))
        # lowest FP s.t. TP>=37
        low_fp_tp37 = min(((fp, tp, t) for (t, tp, fp, rec, far) in sw if tp >= TP_TARGET), default=(None, None, None))
        # best recall s.t. FAR<=10%
        best_rec_far10 = max(((tp, fp, t) for (t, tp, fp, rec, far) in sw if far <= 0.10), default=(0, 0, None))
        # closest point to target (min normalized L1 distance to (TP=37, FP=45) among TP>=1)
        def dist(tp, fp):
            return max(0, TP_TARGET - tp) / N_FALL + max(0, fp - FP_TARGET) / N_NONFALL
        closest = min(sw, key=lambda r: dist(r[1], r[2]))
        per_cand[cand] = dict(joint=joint, best_tp_fp45=best_tp_fp45, low_fp_tp37=low_fp_tp37,
                              best_rec_far10=best_rec_far10, closest=closest)

    with (DIAG / "optionB_threshold_frontier_sweep.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["checkpoint", "threshold", "TP", "FP", "recall", "FAR"])
        w.writerows(sweep_rows)

    # ---- 3. score-distribution summary --------------------------------------------------------------
    dist_rows = []
    for cand in CANDS:
        for cond in ("clean", "pgd"):
            rows = load(cand, cond)
            fm, fq1, fq3, fmax = iqr_summary(pfall(rows, True))
            nm, nq1, nq3, nmax = iqr_summary(pfall(rows, False))
            dist_rows.append([cand, cond, f"{fm:.4f}", f"{fq1:.4f}", f"{fq3:.4f}",
                              f"{nm:.4f}", f"{nq1:.4f}", f"{nq3:.4f}"])
    with (DIAG / "optionB_score_distribution_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["checkpoint", "condition", "fall_Pfall_median", "fall_q1", "fall_q3",
                    "nonfall_Pfall_median", "nonfall_q1", "nonfall_q3"])
        w.writerows(dist_rows)

    # ---- 4. validation vs test ----------------------------------------------------------------------
    log = {}
    with (B / "logs" / "seed42_optionB_training_log.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            log[int(r["epoch"])] = r
    vt_rows = []
    for cand in CANDS:
        e = SEL_EPOCH[cand]; lr = log[e]
        cl = load(cand, "clean"); pg = load(cand, "pgd")
        n = len(cl)
        acc = sum(1 for r in cl if r["true_label"] == r["predicted_label"]) / n
        ctp = sum(1 for r in cl if r["fall_true_binary"] == "1" and r["fall_pred_binary"] == "1")
        cfr = ctp / N_FALL
        ptp = sum(1 for r in pg if r["fall_true_binary"] == "1" and r["fall_pred_binary"] == "1")
        pfp = sum(1 for r in pg if r["fall_true_binary"] == "0" and r["fall_pred_binary"] == "1")
        vt_rows.append([cand, e,
                        f"{float(lr['val_clean_accuracy']):.4f}", f"{acc:.4f}",
                        f"{float(lr['val_clean_fall_recall']):.4f}", f"{cfr:.4f}",
                        f"{float(lr['val_pgd_fall_recall']):.4f}", f"{ptp / N_FALL:.4f}",
                        lr['val_pgd_false_fall_alarms'], pfp,
                        f"{float(lr['far_val_pgd10']):.4f}", f"{pfp / N_NONFALL:.4f}"])
    with (DIAG / "optionB_val_vs_test.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["checkpoint", "epoch", "val_clean_acc", "test_clean_acc",
                    "val_clean_fall_recall", "test_clean_fall_recall",
                    "val_pgd_recall", "test_pgd_recall", "val_pgd_FP", "test_pgd_FP",
                    "val_FAR", "test_FAR"])
        w.writerows(vt_rows)

    # ---- 5. error routing (PGD argmax decisions) ----------------------------------------------------
    er_rows = []
    for cand in CANDS:
        pg = load(cand, "pgd")
        missed = {}      # missed falls -> predicted class
        fa_src = {}      # false alarms -> true source class
        for r in pg:
            if r["fall_true_binary"] == "1" and r["fall_pred_binary"] == "0":
                missed[r["predicted_class_name"]] = missed.get(r["predicted_class_name"], 0) + 1
            if r["fall_true_binary"] == "0" and r["fall_pred_binary"] == "1":
                fa_src[r["true_class_name"]] = fa_src.get(r["true_class_name"], 0) + 1
        for cls, n in sorted(missed.items(), key=lambda x: -x[1]):
            er_rows.append([cand, "missed_fall_predicted_as", cls, n])
        for cls, n in sorted(fa_src.items(), key=lambda x: -x[1]):
            er_rows.append([cand, "false_alarm_true_source", cls, n])
    with (DIAG / "optionB_error_routing.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["checkpoint", "kind", "class", "count"]); w.writerows(er_rows)

    # ---- summary markdown ---------------------------------------------------------------------------
    L = []
    L.append("# Option B seed-42 — Gate-5 frontier diagnostic summary (analysis-only)\n")
    L.append("> Reads only committed test/val CSVs. No training, no attacks, no checkpoint loading, no `.pt`. "
             "Threshold sweep = one-vs-rest on P(fall) (post-hoc, NOT the pre-registered argmax operating "
             "point). Target: TP >= 37/45 AND FP <= 45/455.\n")
    L.append("## 1-2. Threshold/frontier sweep (PGD test)\n")
    L.append("| ckpt | joint TP>=37 & FP<=45 reachable? | best TP @FP<=45 | lowest FP @TP>=37 | "
             "best recall @FAR<=10% | closest point to target |")
    L.append("|---|---|---|---|---|---|")
    for cand in CANDS:
        d = per_cand[cand]
        joint = "YES " + str(d["joint"][:1]) if d["joint"] else "**NO**"
        bt = d["best_tp_fp45"]; lf = d["low_fp_tp37"]; br = d["best_rec_far10"]; cz = d["closest"]
        bt_s = f"TP={bt[0]} (FP={bt[1]}, thr={bt[2]:.3f})" if bt[2] is not None else "none"
        lf_s = f"FP={lf[0]} (TP={lf[1]}, thr={lf[2]:.3f})" if lf[0] is not None else "**none (TP>=37 unreachable)**"
        br_s = f"TP={br[0]}/recall={br[0]/N_FALL:.3f} (FP={br[1]}, thr={br[2]:.3f})" if br[2] is not None else "none"
        cz_s = f"TP={cz[1]}, FP={cz[2]} (thr={cz[0]:.3f})"
        L.append(f"| {cand} | {joint} | {bt_s} | {lf_s} | {br_s} | {cz_s} |")
    L.append("")
    L.append("## 3. Attacked P(fall) score distributions (median [q1,q3])\n")
    L.append("| ckpt | cond | adv-fall P(fall) | adv-nonfall P(fall) |")
    L.append("|---|---|---|---|")
    for row in dist_rows:
        cand, cond, fm, fq1, fq3, nm, nq1, nq3 = row
        L.append(f"| {cand} | {cond} | {fm} [{fq1},{fq3}] | {nm} [{nq1},{nq3}] |")
    L.append("")
    L.append("## 4. Validation vs test (selected epochs)\n")
    L.append("| ckpt | ep | val acc | test acc | val PGD rec | test PGD rec | val FP | test FP | val FAR | test FAR |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in vt_rows:
        L.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[6]} | {r[7]} | {r[8]} | {r[9]} | {r[10]} | {r[11]} |")
    L.append("")
    L.append("## 5. Error routing (PGD argmax)\n")
    L.append("| ckpt | kind | class | count |")
    L.append("|---|---|---|---|")
    for r in er_rows:
        L.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |")
    L.append("")
    any_joint = any(per_cand[c]["joint"] for c in CANDS)
    L.append("## Conclusion\n")
    if any_joint:
        L.append("- A post-hoc threshold DOES reach TP>=37 & FP<=45 on at least one checkpoint (reported "
                 "above). This is **post-hoc threshold evidence only**, NOT the pre-registered argmax "
                 "operating point.\n")
    else:
        L.append("- **No threshold on any checkpoint reaches TP>=37 AND FP<=45 simultaneously.** The failure "
                 "is **representation/frontier-level**, not merely checkpoint selection: the attacked "
                 "fall-score and non-fall fall-score distributions overlap too much to separate by any "
                 "single P(fall) threshold.\n")
    L.append("- The validation-vs-test table quantifies the **clean-guard generalization gap** (test clean "
             "acc below the 0.70 guard for all three checkpoints despite validation passing).\n")
    L.append("- Option B remains **dominated by the best prior frontier G1 seed44 (recall 0.600, FP 65, "
             "guard held)**; this diagnostic does not change the REJECT verdict.\n")
    (DIAG / "optionB_frontier_diagnostic_summary.md").write_text("\n".join(L), encoding="utf-8")

    # console digest
    print("Joint-target (TP>=37 & FP<=45) reachable by any P(fall) threshold:")
    for cand in CANDS:
        d = per_cand[cand]
        print(f"  {cand:9}: {'YES '+str(d['joint'][:1]) if d['joint'] else 'NO'} | "
              f"closest TP={d['closest'][1]}, FP={d['closest'][2]} (thr={d['closest'][0]:.3f}) | "
              f"best recall@FAR<=10%: TP={d['best_rec_far10'][0]} FP={d['best_rec_far10'][1]}")
    print(f"[done] diagnostics -> {DIAG}")


if __name__ == "__main__":
    main()
