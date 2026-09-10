"""
AFAC 2x2 ablation -- analysis.

Order of operations is deliberate and enforced by construction:

  STAGE 1 (threshold-free).  Score-quality metrics that involve NO binary decision at all:
      AUROC, standardized partial AUROC over FAR in [0, 0.20], fall/non-fall score distributions,
      distributional separation, and the seven-class argmax metrics. This is the stage that
      answers "did TRAINING change the learned fall-score representation?"

  STAGE 2 (threshold).  ONE common validation-only threshold rule, identical for all four
      variants: tau = argmax validation fall recall subject to validation FAR <= 0.12,
      tie-break 1 = lower FAR, tie-break 2 = higher tau. Selected per (variant, seed, ckpt,
      epsilon) on the VAL PGD export only, frozen, then applied unmodified to the test export.

  STAGE 3 (contrasts).  Paired per-seed differences for the floor effect (V10-V00, V11-V01),
      the adaptive-controller effect (V01-V00, V11-V10), and the interaction.

  STAGE 4 (threshold-contribution decomposition).  For each model, how much of the attacked
      fall recall comes from TRAINING versus from MOVING THE DECISION THRESHOLD -- computed as
      the gap between argmax recall (fall_pred_binary) and recall at the validation-selected tau.

Threshold selection reads VAL files only; the test read is a single application of an already
frozen number. `select_threshold` is never called on a test file (asserted at runtime).

Split-integrity note (honest labeling): the UT-HAR test split has been examined many times over
the history of this project. It is treated and labeled here as a CONFIRMATORY BENCHMARK, not as a
pristine unseen held-out set, and no new blindness claim is made.

Commands:
    python scripts/ablation_afac_mechanisms/analyze_ablation.py --seeds 42
    python scripts/ablation_afac_mechanisms/analyze_ablation.py --seeds 42 43 44 45 46
"""
from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import statistics as st

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "ablation_afac_mechanisms" / "_analysis"
VARIANTS = ("V00", "V10", "V01", "V11")
VLABEL = {"V00": "CONTROL (no floor, fixed lam_b)", "V10": "FLOOR ONLY",
          "V01": "ADAPTIVE ONLY", "V11": "FLOOR+ADAPTIVE (=Option B)"}
CKPTS = ("last", "maxscore")
EPS = {0.015: "0_015", 0.03: "0_03"}
FAR_CAP = 0.12          # the one common validation FAR cap (user-specified primary protocol)
PAUC_MAX_FAR = 0.20     # low-FAR region for the partial AUROC


# ------------------------------------------------------------------ io
def load_scores(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"empty CSV: {path}")
    y = [int(r["fall_true_binary"]) for r in rows]
    s = [float(r["fall_probability"]) for r in rows]
    argmax_fall = [int(r["fall_pred_binary"]) for r in rows]
    true_lab = [int(r["true_label"]) for r in rows]
    pred_lab = [int(r["predicted_label"]) for r in rows]
    src = [r["true_class_name"] for r in rows]
    return y, s, argmax_fall, true_lab, pred_lab, src


def score_path(variant, seed, ckpt, eps, split, cond):
    tok = EPS[eps]
    run = f"{variant}_seed{seed}_{ckpt}_eps{tok}"
    return (REPO / "results" / "ablation_afac_mechanisms" / variant / f"seed{seed}" / "eval"
            / split / f"{run}_{cond}_probabilities_{split}_epsilon_{tok}.csv")


# ------------------------------------------------------------------ threshold-free metrics
def auroc(y, s):
    pairs = sorted(zip(s, y))
    n = len(pairs); ranks = [0.0] * n; i = 0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    n_pos = sum(v for _, v in pairs); n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    rs = sum(r for r, (_, v) in zip(ranks, pairs) if v == 1)
    return (rs - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def roc_points(y, s):
    """(FPR, TPR) points swept over descending unique scores, starting at (0,0)."""
    P = sum(y); N = len(y) - P
    if P == 0 or N == 0:
        return []
    order = sorted(range(len(s)), key=lambda i: -s[i])
    pts = [(0.0, 0.0)]
    tp = fp = 0; i = 0
    while i < len(order):
        cur = s[order[i]]
        while i < len(order) and s[order[i]] == cur:
            if y[order[i]] == 1:
                tp += 1
            else:
                fp += 1
            i += 1
        pts.append((fp / N, tp / P))
    return pts


def partial_auroc(y, s, max_far=PAUC_MAX_FAR):
    """Standardized partial AUROC over FPR in [0, max_far]: AREA / max_far = the MEAN TPR across
    the low-FAR region.

    Interpretation scale -- NOT the same baseline as AUROC:
        perfect classifier -> 1.00
        chance classifier  -> max_far / 2   (= 0.10 when max_far = 0.20), because TPR = FPR
                              on the chance line, so the mean TPR over [0, max_far] is max_far/2.
    Read this metric against 0.10, never against 0.50."""
    pts = roc_points(y, s)
    if not pts:
        return float("nan")
    area = 0.0
    prev_f, prev_t = 0.0, 0.0
    for f, t in pts[1:]:
        if f <= max_far:
            area += (f - prev_f) * (prev_t + t) / 2.0
            prev_f, prev_t = f, t
        else:
            if prev_f < max_far:           # interpolate to the boundary
                frac = (max_far - prev_f) / (f - prev_f) if f > prev_f else 0.0
                t_at = prev_t + frac * (t - prev_t)
                area += (max_far - prev_f) * (prev_t + t_at) / 2.0
                prev_f, prev_t = max_far, t_at
            break
    if prev_f < max_far:                   # ROC ended before the cap; extend flat
        area += (max_far - prev_f) * prev_t
    return area / max_far


def dist_stats(vals):
    if not vals:
        return {}
    q = sorted(vals)
    def pct(p):
        k = (len(q) - 1) * p
        lo, hi = int(k), min(int(k) + 1, len(q) - 1)
        return q[lo] + (k - lo) * (q[hi] - q[lo])
    return {"n": len(q), "mean": st.fmean(q), "median": pct(0.5), "sd": (st.pstdev(q) if len(q) > 1 else 0.0),
            "p25": pct(0.25), "p75": pct(0.75), "min": q[0], "max": q[-1]}


def separation(y, s):
    f = [si for si, yi in zip(s, y) if yi == 1]
    nf = [si for si, yi in zip(s, y) if yi == 0]
    fs, ns = dist_stats(f), dist_stats(nf)
    pooled = (((fs["sd"] ** 2) + (ns["sd"] ** 2)) / 2.0) ** 0.5 if f and nf else float("nan")
    d = (fs["mean"] - ns["mean"]) / pooled if pooled and pooled > 1e-12 else float("nan")
    return {"fall": fs, "nonfall": ns, "median_gap": fs["median"] - ns["median"], "cohens_d": d}


def argmax_metrics(true_lab, pred_lab, y, argmax_fall):
    acc = sum(1 for a, b in zip(true_lab, pred_lab) if a == b) / len(true_lab)
    tp = sum(1 for yi, ai in zip(y, argmax_fall) if yi == 1 and ai == 1)
    fn = sum(1 for yi, ai in zip(y, argmax_fall) if yi == 1 and ai == 0)
    fp = sum(1 for yi, ai in zip(y, argmax_fall) if yi == 0 and ai == 1)
    tn = sum(1 for yi, ai in zip(y, argmax_fall) if yi == 0 and ai == 0)
    return {"argmax_acc7": acc, "argmax_fall_recall": tp / (tp + fn) if (tp + fn) else float("nan"),
            "argmax_false_fall_alarms": fp,
            "argmax_far": fp / (fp + tn) if (fp + tn) else float("nan"),
            "argmax_TP": tp, "argmax_FN": fn, "argmax_FP": fp, "argmax_TN": tn}


# ------------------------------------------------------------------ threshold (VALIDATION ONLY)
def confusion(y, s, tau):
    tp = fn = fp = tn = 0
    for yi, si in zip(y, s):
        p = si >= tau
        if yi == 1:
            tp += p; fn += not p
        else:
            fp += p; tn += not p
    return tp, fn, fp, tn


def rates(tp, fn, fp, tn):
    rec = tp / (tp + fn) if (tp + fn) else float("nan")
    far = fp / (fp + tn) if (fp + tn) else float("nan")
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return rec, far, prec, f1


def select_threshold(y, s, cap=FAR_CAP, _src: Path | None = None):
    """Max recall s.t. FAR <= cap; tie-break lower FAR, then higher tau. VALIDATION ONLY."""
    if _src is not None:
        assert "test" not in _src.parts[-2:], f"threshold selection attempted on a test file: {_src}"
    best = None
    for tau in sorted(set(s), reverse=True):
        tp, fn, fp, tn = confusion(y, s, tau)
        rec, far, _, _ = rates(tp, fn, fp, tn)
        if far > cap:
            continue
        key = (rec, -far, tau)
        if best is None or key > best[0]:
            best = (key, tau, tp, fn, fp, tn, rec, far)
    if best is None:
        return None
    _, tau, tp, fn, fp, tn, rec, far = best
    return {"tau": tau, "TP": tp, "FN": fn, "FP": fp, "TN": tn, "recall": rec, "FAR": far}


# ------------------------------------------------------------------ main
def analyze_one(variant, seed, ckpt, eps):
    rec = {"variant": variant, "variant_label": VLABEL[variant], "seed": seed,
           "checkpoint": ckpt, "epsilon": eps}

    vp = score_path(variant, seed, ckpt, eps, "val", "pgd")
    vc = score_path(variant, seed, ckpt, eps, "val", "clean")
    tp_ = score_path(variant, seed, ckpt, eps, "test", "pgd")
    tc = score_path(variant, seed, ckpt, eps, "test", "clean")
    for p in (vp, vc, tp_, tc):
        if not p.exists():
            return None

    # ---------- STAGE 1: threshold-free ----------
    y_v, s_v, am_v, tl_v, pl_v, _ = load_scores(vp)
    y_t, s_t, am_t, tl_t, pl_t, src_t = load_scores(tp_)
    y_vc, s_vc, am_vc, tl_vc, pl_vc, _ = load_scores(vc)
    y_tc, s_tc, am_tc, tl_tc, pl_tc, _ = load_scores(tc)

    assert len(y_v) == 496 and sum(y_v) == 44, f"val split drift: {len(y_v)}/{sum(y_v)}"
    assert len(y_t) == 500 and sum(y_t) == 45, f"test split drift: {len(y_t)}/{sum(y_t)}"

    for tag, (yy, ss, am, tl, pl) in {
            "val_pgd": (y_v, s_v, am_v, tl_v, pl_v), "test_pgd": (y_t, s_t, am_t, tl_t, pl_t),
            "val_clean": (y_vc, s_vc, am_vc, tl_vc, pl_vc),
            "test_clean": (y_tc, s_tc, am_tc, tl_tc, pl_tc)}.items():
        rec[f"{tag}_auroc"] = auroc(yy, ss)
        rec[f"{tag}_pauroc_far020"] = partial_auroc(yy, ss)
        sep = separation(yy, ss)
        rec[f"{tag}_fall_score_median"] = sep["fall"]["median"]
        rec[f"{tag}_nonfall_score_median"] = sep["nonfall"]["median"]
        rec[f"{tag}_fall_score_mean"] = sep["fall"]["mean"]
        rec[f"{tag}_nonfall_score_mean"] = sep["nonfall"]["mean"]
        rec[f"{tag}_median_gap"] = sep["median_gap"]
        rec[f"{tag}_cohens_d"] = sep["cohens_d"]
        am_m = argmax_metrics(tl, pl, yy, am)
        for k, v in am_m.items():
            rec[f"{tag}_{k}"] = v

    # ---------- STAGE 2: one common validation-only threshold ----------
    sel = select_threshold(y_v, s_v, FAR_CAP, _src=vp)
    if sel is None:
        rec["tau_frozen"] = ""
        rec["threshold_feasible"] = False
        return rec
    tau = sel["tau"]
    rec.update({"threshold_feasible": True, "tau_frozen": tau,
                "val_sel_TP": sel["TP"], "val_sel_FN": sel["FN"], "val_sel_FP": sel["FP"],
                "val_sel_TN": sel["TN"], "val_sel_recall": sel["recall"], "val_sel_FAR": sel["FAR"]})

    ttp, tfn, tfp, ttn = confusion(y_t, s_t, tau)          # single application of a frozen number
    trec, tfar, tprec, tf1 = rates(ttp, tfn, tfp, ttn)
    rec.update({"test_TP": ttp, "test_FN": tfn, "test_FP": tfp, "test_TN": ttn,
                "test_recall": trec, "test_FAR": tfar, "test_precision": tprec, "test_F1": tf1})

    ctp, cfn, cfp, ctn = confusion(y_tc, s_tc, tau)
    crec, cfar, _, _ = rates(ctp, cfn, cfp, ctn)
    rec.update({"test_clean_recall_at_tau": crec, "test_clean_FAR_at_tau": cfar})
    vctp, vcfn, vcfp, vctn = confusion(y_vc, s_vc, tau)
    vcrec, vcfar, _, _ = rates(vctp, vcfn, vcfp, vctn)
    rec.update({"val_clean_recall_at_tau": vcrec, "val_clean_FAR_at_tau": vcfar})

    # ---------- STAGE 4: threshold-contribution decomposition ----------
    rec["test_pgd_recall_gain_from_threshold"] = trec - rec["test_pgd_argmax_fall_recall"]
    rec["test_pgd_far_change_from_threshold"] = tfar - rec["test_pgd_argmax_far"]
    rec["val_pgd_recall_gain_from_threshold"] = sel["recall"] - rec["val_pgd_argmax_fall_recall"]

    # false-alarm source anatomy at the frozen tau (test, PGD)
    fp_src = {}
    for yi, si, sc in zip(y_t, s_t, src_t):
        if yi == 0 and si >= tau:
            fp_src[sc] = fp_src.get(sc, 0) + 1
    rec["test_fp_sources"] = ";".join(f"{k}={v}" for k, v in sorted(fp_src.items(), key=lambda kv: -kv[1]))
    return rec


def paired_contrast(rows, a, b, metric, ckpt, eps):
    """metric[a] - metric[b], paired within seed."""
    idx = {(r["variant"], r["seed"]): r for r in rows
           if r["checkpoint"] == ckpt and r["epsilon"] == eps}
    seeds = sorted({s for (v, s) in idx if v == a} & {s for (v, s) in idx if v == b})
    diffs = []
    for s in seeds:
        ra, rb = idx[(a, s)], idx[(b, s)]
        if metric in ra and metric in rb and isinstance(ra[metric], (int, float)) \
                and isinstance(rb[metric], (int, float)):
            diffs.append((s, ra[metric] - rb[metric]))
    return diffs


def main():
    p = argparse.ArgumentParser(description="Analyze the AFAC 2x2 ablation.")
    p.add_argument("--seeds", type=int, nargs="+", required=True)
    args = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    for variant in VARIANTS:
        for seed in args.seeds:
            for ckpt in CKPTS:
                for eps in EPS:
                    r = analyze_one(variant, seed, ckpt, eps)
                    if r:
                        rows.append(r)
    if not rows:
        raise SystemExit("no complete (variant, seed, ckpt, eps) cells found -- run exports first.")

    keys, seen = [], set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k); keys.append(k)
    with (OUT / "ablation_per_model_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for r in rows:
            w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r.get(k, "")) for k in keys})
    print(f"[write] ablation_per_model_metrics.csv ({len(rows)} rows)")

    # contrasts
    PRIMARY = ["test_pgd_pauroc_far020", "test_pgd_auroc", "test_recall", "test_FAR",
               "val_pgd_pauroc_far020", "val_pgd_auroc", "val_sel_recall",
               "test_pgd_cohens_d", "test_clean_recall_at_tau", "test_pgd_argmax_acc7"]
    CONTRASTS = [("floor", "V10", "V00"), ("floor", "V11", "V01"),
                 ("adaptive", "V01", "V00"), ("adaptive", "V11", "V10")]
    crows = []
    for ckpt in CKPTS:
        for eps in EPS:
            for effect, a, b in CONTRASTS:
                for m in PRIMARY:
                    d = paired_contrast(rows, a, b, m, ckpt, eps)
                    if not d:
                        continue
                    vals = [v for _, v in d]
                    crows.append({
                        "effect": effect, "contrast": f"{a}-{b}", "checkpoint": ckpt,
                        "epsilon": eps, "metric": m, "n_seeds": len(vals),
                        "mean_diff": st.fmean(vals), "median_diff": st.median(vals),
                        "sd_diff": st.pstdev(vals) if len(vals) > 1 else 0.0,
                        "min_diff": min(vals), "max_diff": max(vals),
                        "n_positive": sum(1 for v in vals if v > 0),
                        "n_negative": sum(1 for v in vals if v < 0),
                        "per_seed": ";".join(f"{s}:{v:+.4f}" for s, v in d)})
    with (OUT / "ablation_paired_contrasts.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(crows[0].keys())); w.writeheader(); w.writerows(crows)
    print(f"[write] ablation_paired_contrasts.csv ({len(crows)} rows)")

    # interaction: (V11-V10) - (V01-V00)  == does adding adaptive help MORE when the floor is on?
    irows = []
    for ckpt in CKPTS:
        for eps in EPS:
            for m in PRIMARY:
                d1 = dict(paired_contrast(rows, "V11", "V10", m, ckpt, eps))
                d0 = dict(paired_contrast(rows, "V01", "V00", m, ckpt, eps))
                common = sorted(set(d1) & set(d0))
                if not common:
                    continue
                inter = [d1[s] - d0[s] for s in common]
                irows.append({"checkpoint": ckpt, "epsilon": eps, "metric": m,
                              "n_seeds": len(inter), "mean_interaction": st.fmean(inter),
                              "median_interaction": st.median(inter),
                              "per_seed": ";".join(f"{s}:{d1[s]-d0[s]:+.4f}" for s in common)})
    if irows:
        with (OUT / "ablation_interaction.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(irows[0].keys())); w.writeheader(); w.writerows(irows)
        print(f"[write] ablation_interaction.csv ({len(irows)} rows)")

    with (OUT / "ablation_rows.json").open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, default=float)
    print("[done] analysis complete. Thresholds were selected on VALIDATION only.")


if __name__ == "__main__":
    main()
