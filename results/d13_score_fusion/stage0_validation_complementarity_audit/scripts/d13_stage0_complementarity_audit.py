"""
D13 Step 0A - VALIDATION-ONLY saved-score complementarity audit.

Purpose: diagnostic only. Decides whether AFAC-score, D10 (GAIRAT GR1_v2macroF1), and D11b
(SAT SA1_v2lowFA) have enough validation-only complementarity to justify a later, separately
pre-registered Stage 1 score-fusion experiment. Cannot claim F20. Can only authorize / reject /
mark inconclusive a later experiment.

Reads ONLY validation PGD epsilon=0.030 saved-score CSVs (paths hard-coded below; no test-split
path appears anywhere in this file - grep-verifiable). No training. No fusion-weight fitting.

Seed: 1337 (bootstrap only; threshold selection and Oracle-B search are deterministic/exhaustive).
"""

from __future__ import annotations

import csv
import json
import random
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "d13_score_fusion" / "stage0_validation_complementarity_audit"

# VALIDATION-ONLY input paths. No test-split path exists in this file.
VAL_FILES = {
    "AFAC": REPO / "results/afac_score_frozen_threshold_followup/val_eval/optionB_maxscore_pgd_probabilities_val_epsilon_0_03.csv",
    "D10": REPO / "results/safety_guided_defense/boundary_aware_selective_at/gairat/seed42/GR1/val_eval/GR1_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv",
    "D11b": REPO / "results/safety_guided_defense/boundary_aware_selective_at/sat/seed42/SA1/val_eval/SA1_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv",
}
MODEL_ORDER = ["AFAC", "D10", "D11b"]

FAR_CAPS = {"0.18": 0.18, "0.20": 0.20}
SEED = 1337
N_BOOTSTRAP = 2000  # documented choice: 2000, not 10000, to keep full-audit runtime reasonable
                     # (per-resample: 3 model recall + Oracle-B pattern reselection + P0 recall)

MOBILITY_CLASSES = {"run", "walk"}


def load_rows(path: Path):
    for part in path.parts:
        assert "test" not in part.lower(), f"REFUSING: path looks test-related: {path}"
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"empty CSV: {path}")
    return rows


def extract(rows):
    y = [int(r["fall_true_binary"]) for r in rows]
    s = [float(r["fall_probability"]) for r in rows]
    true_cls = [r["true_class_name"] for r in rows]
    pred_cls = [r["predicted_class_name"] for r in rows]
    sample_id = [int(r["sample_id"]) for r in rows]
    return y, s, true_cls, pred_cls, sample_id


def check_split(y, n_total, n_fall, label):
    if len(y) != n_total or sum(y) != n_fall:
        raise AssertionError(f"{label}: expected {n_total}/{n_fall}, got {len(y)}/{sum(y)}")


def confusion(y, s, tau):
    tp = fn = fp = tn = 0
    for yi, si in zip(y, s):
        pred = si >= tau
        if yi == 1:
            tp += pred
            fn += not pred
        else:
            fp += pred
            tn += not pred
    return tp, fn, fp, tn


def rates(tp, fn, fp, tn):
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    far = fp / (fp + tn) if (fp + tn) else float("nan")
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return recall, far, precision, f1


def auroc(y, s):
    pairs = sorted(zip(s, y))
    n = len(pairs)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1
    n_pos = sum(yy for _, yy in pairs)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    rank_sum_pos = sum(r for r, (_, yy) in zip(ranks, pairs) if yy == 1)
    u = rank_sum_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def roc_points(y, s):
    """Full ROC curve (FAR, recall) sorted by descending threshold, including (0,0) and (1,1)."""
    thresholds = sorted(set(s), reverse=True)
    pts = [(0.0, 0.0)]
    for tau in thresholds:
        tp, fn, fp, tn = confusion(y, s, tau)
        recall, far, _, _ = rates(tp, fn, fp, tn)
        pts.append((far, recall))
    pts.append((1.0, 1.0))
    # ensure monotonic-by-FAR, dedupe by taking max recall per FAR, sort
    best_by_far = {}
    for far, rec in pts:
        if far not in best_by_far or rec > best_by_far[far]:
            best_by_far[far] = rec
    pts = sorted(best_by_far.items())
    return pts


def partial_auc_mcclish(y, s, far_max=0.20):
    """McClish-normalized partial AUC over FAR in [0, far_max].
    Raw partial AUC via trapezoid over the ROC restricted to FAR<=far_max, normalized so that
    a random classifier scores 0.5 and a perfect classifier scores 1.0 (McClish 1989)."""
    pts = roc_points(y, s)
    # restrict / interpolate to [0, far_max]
    restricted = []
    for i in range(len(pts) - 1):
        (f0, r0), (f1, r1) = pts[i], pts[i + 1]
        if f1 <= far_max:
            restricted.append((f0, r0))
            if i == len(pts) - 2:
                restricted.append((f1, r1))
        elif f0 < far_max < f1:
            restricted.append((f0, r0))
            frac = (far_max - f0) / (f1 - f0) if f1 > f0 else 0.0
            r_interp = r0 + frac * (r1 - r0)
            restricted.append((far_max, r_interp))
            break
        else:
            restricted.append((f0, r0))
            break
    if not restricted or restricted[-1][0] < far_max:
        restricted.append((far_max, restricted[-1][1] if restricted else 0.0))
    raw = 0.0
    for i in range(len(restricted) - 1):
        f0, r0 = restricted[i]
        f1, r1 = restricted[i + 1]
        raw += (f1 - f0) * (r0 + r1) / 2.0
    min_area = 0.5 * far_max * far_max
    max_area = far_max * 1.0 - 0.5 * far_max * far_max
    if max_area <= min_area:
        return float("nan")
    mcclish = 0.5 * (1.0 + (raw - min_area) / (max_area - min_area))
    return mcclish


def select_threshold(y, s, cap):
    """Grid = midpoints between consecutive sorted unique scores. Max recall s.t. FAR<=cap.
    Tie-break 1: lower FAR. Tie-break 2: higher threshold."""
    uniq = sorted(set(s))
    grid = [(uniq[i] + uniq[i + 1]) / 2.0 for i in range(len(uniq) - 1)]
    grid = [uniq[0] - 1e-9] + grid + [uniq[-1] + 1e-9]
    best = None
    for tau in grid:
        tp, fn, fp, tn = confusion(y, s, tau)
        recall, far, _, _ = rates(tp, fn, fp, tn)
        if far > cap:
            continue
        key = (recall, -far, tau)
        if best is None or key > best[0]:
            best = (key, tau, tp, fn, fp, tn, recall, far)
    if best is None:
        return None
    _, tau, tp, fn, fp, tn, recall, far = best
    return tau, tp, fn, fp, tn, recall, far


def spearman(a, b):
    n = len(a)
    def rank(v):
        idx = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(idx):
            j = i
            while j + 1 < len(idx) and v[idx[j + 1]] == v[idx[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[idx[k]] = avg
            i = j + 1
        return r
    ra, rb = rank(a), rank(b)
    mean_ra, mean_rb = sum(ra) / n, sum(rb) / n
    cov = sum((x - mean_ra) * (y - mean_rb) for x, y in zip(ra, rb))
    var_a = sum((x - mean_ra) ** 2 for x in ra)
    var_b = sum((y - mean_rb) ** 2 for y in rb)
    if var_a == 0 or var_b == 0:
        return float("nan")
    return cov / (var_a * var_b) ** 0.5


def class_bucket(cls):
    return cls if cls in MOBILITY_CLASSES else "other"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = {}
    for name in MODEL_ORDER:
        rows = load_rows(VAL_FILES[name])
        y, s, true_cls, pred_cls, sid = extract(rows)
        check_split(y, 496, 44, name)
        data[name] = {"y": y, "s": s, "true_cls": true_cls, "pred_cls": pred_cls, "sid": sid}
    print("[check] all three validation files: 496 windows, 44 fall, 452 non-fall - OK")

    y_ref = data[MODEL_ORDER[0]]["y"]
    sid_ref = data[MODEL_ORDER[0]]["sid"]
    for name in MODEL_ORDER[1:]:
        assert data[name]["y"] == y_ref, f"{name} label order mismatch vs {MODEL_ORDER[0]}"
        assert data[name]["sid"] == sid_ref, f"{name} sample_id order mismatch"

    # ---------- per-model metrics at both FAR caps ----------
    model_metrics = []
    thresholds_018 = {}
    for name in MODEL_ORDER:
        y, s = data[name]["y"], data[name]["s"]
        a = auroc(y, s)
        pauc = partial_auc_mcclish(y, s, 0.20)
        for cap_label, cap in FAR_CAPS.items():
            sel = select_threshold(y, s, cap)
            if sel is None:
                continue
            tau, tp, fn, fp, tn, recall, far = sel
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            model_metrics.append({
                "model": name, "far_cap": cap_label, "threshold": f"{tau:.6f}",
                "TP": tp, "FN": fn, "FP": fp, "TN": tn,
                "recall": f"{recall:.6f}", "FAR": f"{far:.6f}",
                "precision": f"{precision:.6f}", "F1": f"{f1:.6f}",
                "AUROC": f"{a:.6f}", "pAUC_McClish_0_20": f"{pauc:.6f}",
            })
            if cap_label == "0.18":
                thresholds_018[name] = tau

    def write_csv(path, rows):
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"[write] {path.relative_to(REPO)} ({len(rows)} rows)")

    write_csv(OUT / "d13_stage0_model_metrics.csv", model_metrics)

    # ---------- decisions at FAR<=0.18 thresholds ----------
    decisions = {}
    for name in MODEL_ORDER:
        tau = thresholds_018[name]
        decisions[name] = [1 if si >= tau else 0 for si in data[name]["s"]]

    n = len(y_ref)
    fp_sets, fn_sets = {}, {}
    for name in MODEL_ORDER:
        y = data[name]["y"]
        dec = decisions[name]
        fp_sets[name] = set(sid_ref[i] for i in range(n) if y[i] == 0 and dec[i] == 1)
        fn_sets[name] = set(sid_ref[i] for i in range(n) if y[i] == 1 and dec[i] == 0)

    def jaccard(a, b):
        u = len(a | b)
        return (len(a & b) / u) if u else float("nan")

    overlap_rows = []
    pairs = [(MODEL_ORDER[0], MODEL_ORDER[1]), (MODEL_ORDER[0], MODEL_ORDER[2]),
             (MODEL_ORDER[1], MODEL_ORDER[2])]
    for a, b in pairs:
        overlap_rows.append({
            "set_type": "FP", "pair": f"{a}&{b}",
            "intersection": len(fp_sets[a] & fp_sets[b]), "union": len(fp_sets[a] | fp_sets[b]),
            "jaccard": f"{jaccard(fp_sets[a], fp_sets[b]):.6f}",
        })
        overlap_rows.append({
            "set_type": "FN", "pair": f"{a}&{b}",
            "intersection": len(fn_sets[a] & fn_sets[b]), "union": len(fn_sets[a] | fn_sets[b]),
            "jaccard": f"{jaccard(fn_sets[a], fn_sets[b]):.6f}",
        })
    fp_all3 = fp_sets[MODEL_ORDER[0]] & fp_sets[MODEL_ORDER[1]] & fp_sets[MODEL_ORDER[2]]
    fp_union3 = fp_sets[MODEL_ORDER[0]] | fp_sets[MODEL_ORDER[1]] | fp_sets[MODEL_ORDER[2]]
    fn_all3 = fn_sets[MODEL_ORDER[0]] & fn_sets[MODEL_ORDER[1]] & fn_sets[MODEL_ORDER[2]]
    fn_union3 = fn_sets[MODEL_ORDER[0]] | fn_sets[MODEL_ORDER[1]] | fn_sets[MODEL_ORDER[2]]
    overlap_rows.append({"set_type": "FP", "pair": "three-way",
                          "intersection": len(fp_all3), "union": len(fp_union3),
                          "jaccard": f"{jaccard(fp_all3, fp_union3):.6f}"})
    overlap_rows.append({"set_type": "FN", "pair": "three-way",
                          "intersection": len(fn_all3), "union": len(fn_union3),
                          "jaccard": f"{jaccard(fn_all3, fn_union3):.6f}"})
    write_csv(OUT / "d13_stage0_overlap_metrics.csv", overlap_rows)

    # FP source-class / FN destination-class breakdown per model
    fp_fn_breakdown = []
    for name in MODEL_ORDER:
        y, true_cls, pred_cls = data[name]["y"], data[name]["true_cls"], data[name]["pred_cls"]
        dec = decisions[name]
        fp_buckets, fn_buckets = {}, {}
        for i in range(n):
            if y[i] == 0 and dec[i] == 1:
                b = class_bucket(true_cls[i])
                fp_buckets[b] = fp_buckets.get(b, 0) + 1
            if y[i] == 1 and dec[i] == 0:
                b = pred_cls[i]
                fn_buckets[b] = fn_buckets.get(b, 0) + 1
        for b, cnt in sorted(fp_buckets.items()):
            fp_fn_breakdown.append({"model": name, "type": "FP_source", "class_or_bucket": b, "count": cnt})
        for b, cnt in sorted(fn_buckets.items()):
            fp_fn_breakdown.append({"model": name, "type": "FN_destination", "class_or_bucket": b, "count": cnt})
    write_csv(OUT / "d13_stage0_fp_fn_breakdown.csv", fp_fn_breakdown)

    # ---------- Spearman correlations ----------
    corr_rows = []
    for a, b in pairs:
        sa, sb = data[a]["s"], data[b]["s"]
        rho_all = spearman(sa, sb)
        idx_subset = [i for i in range(n) if data[a]["y"][i] == 1
                      or class_bucket(data[a]["true_cls"][i]) in MOBILITY_CLASSES]
        rho_sub = spearman([sa[i] for i in idx_subset], [sb[i] for i in idx_subset])
        corr_rows.append({"pair": f"{a}&{b}", "subset": "all_validation",
                           "n": n, "spearman_rho": f"{rho_all:.6f}"})
        corr_rows.append({"pair": f"{a}&{b}", "subset": "fall_run_walk",
                           "n": len(idx_subset), "spearman_rho": f"{rho_sub:.6f}"})
    write_csv(OUT / "d13_stage0_rank_correlations.csv", corr_rows)

    # ---------- vote-pattern analysis ----------
    vote_rows = []
    pattern_groups = {}
    for i in range(n):
        pat = tuple(decisions[m][i] for m in MODEL_ORDER)
        pattern_groups.setdefault(pat, []).append(i)
    for pat in sorted(product([0, 1], repeat=3)):
        idxs = pattern_groups.get(pat, [])
        fall_idxs = [i for i in idxs if y_ref[i] == 1]
        nonfall_idxs = [i for i in idxs if y_ref[i] == 0]
        nonfall_src = {}
        for i in nonfall_idxs:
            b = class_bucket(data[MODEL_ORDER[0]]["true_cls"][i])
            nonfall_src[b] = nonfall_src.get(b, 0) + 1
        fall_dest = {}
        for i in fall_idxs:
            b = data[MODEL_ORDER[0]]["pred_cls"][i]
            fall_dest[b] = fall_dest.get(b, 0) + 1
        total = len(idxs)
        vote_rows.append({
            "AFAC": pat[0], "D10": pat[1], "D11b": pat[2],
            "fall_count": len(fall_idxs), "nonfall_count": len(nonfall_idxs),
            "total": total,
            "nonfall_source_breakdown": json.dumps(nonfall_src, sort_keys=True),
            "fall_destination_breakdown": json.dumps(fall_dest, sort_keys=True),
            "UNSTABLE": total < 3,
        })
    write_csv(OUT / "d13_stage0_vote_patterns.csv", vote_rows)

    # ---------- Oracle A (naive set oracle) ----------
    oracle_rows = []
    for cap_label, cap in FAR_CAPS.items():
        if cap_label == "0.18":
            dec_cap = decisions
        else:
            dec_cap = {}
            for name in MODEL_ORDER:
                sel = select_threshold(data[name]["y"], data[name]["s"], cap)
                tau = sel[0]
                dec_cap[name] = [1 if si >= tau else 0 for si in data[name]["s"]]
        fall_idxs = [i for i in range(n) if y_ref[i] == 1]
        nonfall_idxs = [i for i in range(n) if y_ref[i] == 0]
        tp_a = sum(1 for i in fall_idxs if any(dec_cap[m][i] for m in MODEL_ORDER))
        fp_a = sum(1 for i in nonfall_idxs if all(dec_cap[m][i] for m in MODEL_ORDER))
        fn_a = len(fall_idxs) - tp_a
        tn_a = len(nonfall_idxs) - fp_a
        recall_a, far_a = tp_a / len(fall_idxs), fp_a / len(nonfall_idxs)
        oracle_rows.append({
            "oracle": "A_naive_set_OPTIMISTIC_UNATTAINABLE", "far_cap": cap_label,
            "TP": tp_a, "FN": fn_a, "FP": fp_a, "TN": tn_a,
            "recall": f"{recall_a:.6f}", "FAR": f"{far_a:.6f}",
        })

        # Oracle B: pattern-level decision fusion bound
        pat_stats = {}
        for pat in product([0, 1], repeat=3):
            idxs = pattern_groups.get(pat, []) if cap_label == "0.18" else None
            if idxs is None:
                idxs = [i for i in range(n) if tuple(dec_cap[m][i] for m in MODEL_ORDER) == pat]
            fall_n = sum(1 for i in idxs if y_ref[i] == 1)
            nonfall_n = sum(1 for i in idxs if y_ref[i] == 0)
            pat_stats[pat] = (fall_n, nonfall_n)
        best_tp, best_fp, best_assign = -1, None, None
        for assign_bits in product([0, 1], repeat=8):
            pats = list(product([0, 1], repeat=3))
            tp = sum(pat_stats[pats[k]][0] for k in range(8) if assign_bits[k] == 1)
            fp = sum(pat_stats[pats[k]][1] for k in range(8) if assign_bits[k] == 1)
            far_b = fp / len(nonfall_idxs)
            if far_b <= cap and tp > best_tp:
                best_tp, best_fp, best_assign = tp, fp, assign_bits
        fn_b = len(fall_idxs) - best_tp
        tn_b = len(nonfall_idxs) - best_fp
        recall_b, far_b = best_tp / len(fall_idxs), best_fp / len(nonfall_idxs)
        oracle_rows.append({
            "oracle": "B_pattern_level_DECISION_FUSION_BOUND", "far_cap": cap_label,
            "TP": best_tp, "FN": fn_b, "FP": best_fp, "TN": tn_b,
            "recall": f"{recall_b:.6f}", "FAR": f"{far_b:.6f}",
        })
    write_csv(OUT / "d13_stage0_oracle_bounds.csv", oracle_rows)

    # ---------- P0 zero-parameter score probe ----------
    ecdf_maps = {}
    for name in MODEL_ORDER:
        s = data[name]["s"]
        uniq_sorted = sorted(set(s))
        rank_of = {v: (i + 1) / len(uniq_sorted) for i, v in enumerate(uniq_sorted)}
        ecdf_maps[name] = (uniq_sorted, rank_of)

    def ecdf_transform(name, value):
        uniq_sorted, rank_of = ecdf_maps[name]
        if value in rank_of:
            return rank_of[value]
        import bisect
        pos = bisect.bisect_left(uniq_sorted, value)
        if pos == 0:
            return 0.0
        if pos >= len(uniq_sorted):
            return 1.0
        return pos / len(uniq_sorted)

    p0_scores = []
    for i in range(n):
        vals = [ecdf_transform(m, data[m]["s"][i]) for m in MODEL_ORDER]
        p0_scores.append(sum(vals) / 3.0)

    p0_rows = []
    a_p0 = auroc(y_ref, p0_scores)
    pauc_p0 = partial_auc_mcclish(y_ref, p0_scores, 0.20)
    for cap_label, cap in FAR_CAPS.items():
        sel = select_threshold(y_ref, p0_scores, cap)
        tau, tp, fn, fp, tn, recall, far = sel
        p0_rows.append({
            "far_cap": cap_label, "threshold_on_ecdf_mean": f"{tau:.6f}",
            "TP": tp, "FN": fn, "FP": fp, "TN": tn,
            "recall": f"{recall:.6f}", "FAR": f"{far:.6f}",
            "AUROC": f"{a_p0:.6f}", "pAUC_McClish_0_20": f"{pauc_p0:.6f}",
            "caveat": "saved-score feasibility probe (per-model independent adversarial examples), not deployment-equivalent fusion",
        })
    write_csv(OUT / "d13_stage0_p0_probe.csv", p0_rows)

    # ---------- bootstrap ----------
    rng = random.Random(SEED)
    fall_idx_all = [i for i in range(n) if y_ref[i] == 1]
    nonfall_idx_all = [i for i in range(n) if y_ref[i] == 0]

    def best_single_model_tp(idxs_fall, idxs_all):
        best = -1
        for name in MODEL_ORDER:
            tau = thresholds_018[name]
            s = data[name]["s"]
            tp = sum(1 for i in idxs_fall if s[i] >= tau)
            if tp > best:
                best = tp
        return best

    def per_model_recall(idxs_fall):
        out = {}
        for name in MODEL_ORDER:
            tau = thresholds_018[name]
            s = data[name]["s"]
            tp = sum(1 for i in idxs_fall if s[i] >= tau)
            out[name] = tp / len(idxs_fall) if idxs_fall else float("nan")
        return out

    def oracle_b_tp(idxs_fall, idxs_nonfall, cap=0.18):
        pat_stats = {}
        for pat in product([0, 1], repeat=3):
            f_n = sum(1 for i in idxs_fall
                      if tuple(1 if data[m]["s"][i] >= thresholds_018[m] else 0 for m in MODEL_ORDER) == pat)
            nf_n = sum(1 for i in idxs_nonfall
                       if tuple(1 if data[m]["s"][i] >= thresholds_018[m] else 0 for m in MODEL_ORDER) == pat)
            pat_stats[pat] = (f_n, nf_n)
        best_tp = -1
        for assign_bits in product([0, 1], repeat=8):
            pats = list(product([0, 1], repeat=3))
            tp = sum(pat_stats[pats[k]][0] for k in range(8) if assign_bits[k] == 1)
            fp = sum(pat_stats[pats[k]][1] for k in range(8) if assign_bits[k] == 1)
            far_b = fp / len(idxs_nonfall) if idxs_nonfall else 0.0
            if far_b <= cap and tp > best_tp:
                best_tp = tp
        return best_tp

    def p0_tp(idxs_fall, idxs_nonfall, tau):
        tp = sum(1 for i in idxs_fall if p0_scores[i] >= tau)
        return tp

    p0_tau_018 = select_threshold(y_ref, p0_scores, 0.18)[0]

    boot_recalls = {name: [] for name in MODEL_ORDER}
    boot_oracleb_gain, boot_p0_gain = [], []
    for _ in range(N_BOOTSTRAP):
        f_sample = [rng.choice(fall_idx_all) for _ in fall_idx_all]
        nf_sample = [rng.choice(nonfall_idx_all) for _ in nonfall_idx_all]
        rec = per_model_recall(f_sample)
        for name in MODEL_ORDER:
            boot_recalls[name].append(rec[name])
        best_tp = best_single_model_tp(f_sample, f_sample + nf_sample)
        ob_tp = oracle_b_tp(f_sample, nf_sample, cap=0.18)
        p0tp = p0_tp(f_sample, nf_sample, p0_tau_018)
        boot_oracleb_gain.append(ob_tp - best_tp)
        boot_p0_gain.append(p0tp - best_tp)

    def ci95(vals):
        v = sorted(vals)
        n_v = len(v)
        lo, hi = int(0.025 * n_v), min(int(0.975 * n_v), n_v - 1)
        return v[n_v // 2], v[lo], v[hi]

    boot_rows = []
    for name in MODEL_ORDER:
        med, lo, hi = ci95(boot_recalls[name])
        boot_rows.append({"metric": f"{name}_recall_at_FAR0.18", "median": f"{med:.6f}",
                           "ci95_lo": f"{lo:.6f}", "ci95_hi": f"{hi:.6f}", "n_boot": N_BOOTSTRAP})
    med, lo, hi = ci95(boot_oracleb_gain)
    frac_ge2_ob = sum(1 for g in boot_oracleb_gain if g >= 2) / N_BOOTSTRAP
    boot_rows.append({"metric": "OracleB_TP_gain_over_best_single", "median": f"{med:.4f}",
                       "ci95_lo": f"{lo:.4f}", "ci95_hi": f"{hi:.4f}", "n_boot": N_BOOTSTRAP})
    boot_rows.append({"metric": "OracleB_frac_resamples_gain_ge_2", "median": f"{frac_ge2_ob:.4f}",
                       "ci95_lo": "", "ci95_hi": "", "n_boot": N_BOOTSTRAP})
    med, lo, hi = ci95(boot_p0_gain)
    frac_ge2_p0 = sum(1 for g in boot_p0_gain if g >= 2) / N_BOOTSTRAP
    boot_rows.append({"metric": "P0_TP_gain_over_best_single", "median": f"{med:.4f}",
                       "ci95_lo": f"{lo:.4f}", "ci95_hi": f"{hi:.4f}", "n_boot": N_BOOTSTRAP})
    boot_rows.append({"metric": "P0_frac_resamples_gain_ge_2", "median": f"{frac_ge2_p0:.4f}",
                       "ci95_lo": "", "ci95_hi": "", "n_boot": N_BOOTSTRAP})
    write_csv(OUT / "d13_stage0_bootstrap_summary.csv", boot_rows)

    # ---------- 2-fold cross-fit of Oracle-B (optional, NOISE-DOMINATED) ----------
    rng2 = random.Random(SEED + 1)
    fall_shuffled = fall_idx_all[:]
    nonfall_shuffled = nonfall_idx_all[:]
    rng2.shuffle(fall_shuffled)
    rng2.shuffle(nonfall_shuffled)
    fold_a_fall, fold_b_fall = fall_shuffled[::2], fall_shuffled[1::2]
    fold_a_nonfall, fold_b_nonfall = nonfall_shuffled[::2], nonfall_shuffled[1::2]

    def oracle_b_assignment(idxs_fall, idxs_nonfall, cap=0.18):
        pat_stats = {}
        for pat in product([0, 1], repeat=3):
            f_n = sum(1 for i in idxs_fall
                      if tuple(1 if data[m]["s"][i] >= thresholds_018[m] else 0 for m in MODEL_ORDER) == pat)
            nf_n = sum(1 for i in idxs_nonfall
                       if tuple(1 if data[m]["s"][i] >= thresholds_018[m] else 0 for m in MODEL_ORDER) == pat)
            pat_stats[pat] = (f_n, nf_n)
        best_tp, best_assign = -1, None
        for assign_bits in product([0, 1], repeat=8):
            pats = list(product([0, 1], repeat=3))
            tp = sum(pat_stats[pats[k]][0] for k in range(8) if assign_bits[k] == 1)
            fp = sum(pat_stats[pats[k]][1] for k in range(8) if assign_bits[k] == 1)
            far_b = fp / len(idxs_nonfall) if idxs_nonfall else 0.0
            if far_b <= cap and tp > best_tp:
                best_tp, best_assign = tp, assign_bits
        return best_assign

    def apply_assignment(assign_bits, idxs_fall, idxs_nonfall):
        pats = list(product([0, 1], repeat=3))
        positive_pats = {pats[k] for k in range(8) if assign_bits[k] == 1}
        tp = sum(1 for i in idxs_fall
                 if tuple(1 if data[m]["s"][i] >= thresholds_018[m] else 0 for m in MODEL_ORDER) in positive_pats)
        fp = sum(1 for i in idxs_nonfall
                 if tuple(1 if data[m]["s"][i] >= thresholds_018[m] else 0 for m in MODEL_ORDER) in positive_pats)
        return tp, fp

    assign_a = oracle_b_assignment(fold_a_fall, fold_a_nonfall)
    tp_b_using_a, fp_b_using_a = apply_assignment(assign_a, fold_b_fall, fold_b_nonfall)
    assign_b = oracle_b_assignment(fold_b_fall, fold_b_nonfall)
    tp_a_using_b, fp_a_using_b = apply_assignment(assign_b, fold_a_fall, fold_a_nonfall)
    crossfit_note = {
        "label": "NOISE-DOMINATED - not used for gating",
        "fold_A_size": {"fall": len(fold_a_fall), "nonfall": len(fold_a_nonfall)},
        "fold_B_size": {"fall": len(fold_b_fall), "nonfall": len(fold_b_nonfall)},
        "assign_on_A_applied_to_B": {"TP": tp_b_using_a, "FP": fp_b_using_a,
                                      "FAR": fp_b_using_a / len(fold_b_nonfall) if fold_b_nonfall else None},
        "assign_on_B_applied_to_A": {"TP": tp_a_using_b, "FP": fp_a_using_b,
                                      "FAR": fp_a_using_b / len(fold_a_nonfall) if fold_a_nonfall else None},
    }

    # ---------- FP/FN sets JSON ----------
    fp_fn_json = {
        "note": "sample_id values are validation-split indices (0-495), consistent across all three files",
        "thresholds_far_cap_0_18": {k: v for k, v in thresholds_018.items()},
        "fp_sets": {k: sorted(v) for k, v in fp_sets.items()},
        "fn_sets": {k: sorted(v) for k, v in fn_sets.items()},
        "crossfit_oracle_b_2fold": crossfit_note,
    }
    with (OUT / "d13_stage0_fp_fn_sets.json").open("w", encoding="utf-8") as f:
        json.dump(fp_fn_json, f, indent=2, sort_keys=True)
    print(f"[write] {(OUT / 'd13_stage0_fp_fn_sets.json').relative_to(REPO)}")

    print("[done] Step 0A complete. NO test file was read at any point.")


if __name__ == "__main__":
    main()
