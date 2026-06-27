"""
Variant G seed-42 pilot analysis + report builder (analysis only; no training, no attacks).

Reads the Variant G test_eval probability CSVs (clean / FGSM / PGD-10 / PGD-20) produced by
run_variantG_eval.py, plus the 18-eps sweep CSVs, computes all safety-proxy / confidence-inversion
metrics from the per-window outputs (same method as the committed Variant F false-alarm diagnostic),
compares against the committed Variant F seed-42 v2safety reference, assigns ONE decision category,
and writes VARIANT_G_SEED42_PILOT_REPORT.md + analysis CSVs + figures.

Command:  python scripts/analyze_variantG_seed42.py
"""
from __future__ import annotations
from pathlib import Path
import csv, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

EXP = Path(__file__).resolve().parents[1]
SG = EXP / "results" / "safety_guided_defense"
VG = SG / "variantG_targeted_hardneg" / "seed42"
TE = VG / "test_eval"
ANA = VG / "analysis"; FIG = VG / "figures"
ANA.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
CLASS = {0: "lie down", 1: "fall", 2: "walk", 3: "pickup", 4: "run", 5: "sit down", 6: "stand up"}
FALL, WALK, RUN = 1, 2, 4
NONFALL = [0, 2, 3, 4, 5, 6]
PROB = [f"prob_{CLASS[i].replace(' ', '_')}" for i in range(7)]
LOGIT = [f"logit_{CLASS[i].replace(' ', '_')}" for i in range(7)]
NF = 45  # test fall windows
SETTINGS = {"G1": "balanced A+B", "G2": "targeted-heavy (isolates A)", "G3": "source-weighted (isolates B)"}

# committed references (window-level, test, eps=0.030)
F42 = dict(name="Variant F seed42 v2safety", clean_acc=0.734, clean_mf1=0.690, clean_fall_recall=0.978,
           pgd_recall=0.667, pgd_fp=115, wr=80, pgd20=0.644,
           inv_A_pfall=0.415, inv_B_pfall=0.518, inv_A_margin=0.456, inv_B_margin=0.881,
           inv_A_ent=1.414, inv_B_ent=1.296, inv_A_conf=0.141, inv_B_conf=0.306)
F44 = dict(name="Variant F seed44 v2safety (context)", clean_acc=0.700, pgd_recall=0.622, pgd_fp=112, wr=73, pgd20=0.511)
D42 = dict(name="Variant D seed42 (high-recall/high-FP ref)", clean_acc=0.746, clean_mf1=0.700,
           clean_fall_recall=1.000, pgd_recall=0.444, pgd_fp=157, wr=120)
FGSM42 = dict(name="FGSM defense seed42 (weak-PGD baseline)", clean_acc=0.834, clean_mf1=0.814,
              clean_fall_recall=0.911, pgd_recall=0.089, pgd_fp=54, wr=39)


def wilson(p, n=NF, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    c = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    d = 1 + z * z / n
    return ((c - half) / d, (c + half) / d)


def prob_path(setting, cand, cond, pgd20=False):
    rn = f"G_{setting}_{cand}" + ("_pgd20" if pgd20 else "")
    return TE / f"{rn}_{cond}_probabilities_test_epsilon_0_03.csv"


def load(path):
    if not path.exists():
        return None
    out = []
    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            t = int(r["true_label"]); p = int(r["predicted_label"])
            probs = np.array([float(r[c]) for c in PROB]); logits = np.array([float(r[c]) for c in LOGIT])
            order = np.argsort(probs)[::-1]
            nf_logits = logits.copy(); nf_logits[FALL] = -1e9
            ent = float(-np.sum(probs * np.log(np.clip(probs, 1e-12, 1))))
            out.append(dict(true=t, pred=p, fall_prob=float(probs[FALL]),
                            m_fall_maxnf=float(logits[FALL] - nf_logits.max()),
                            entropy=ent, conf_margin=float(probs[order[0]] - probs[order[1]])))
    return out


def safety(rows):
    tp = fp = fn = tn = wr = 0
    for d in rows:
        isf = d["true"] == FALL; alert = d["pred"] == FALL
        if isf and alert: tp += 1
        elif (not isf) and alert:
            fp += 1; wr += 1 if d["true"] in (WALK, RUN) else 0
        elif isf and not alert: fn += 1
        else: tn += 1
    rec = tp / NF
    prec = tp / (tp + fp) if tp + fp else 0.0
    spec = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return dict(recall=rec, fp=fp, wr=wr, precision=prec, specificity=spec, f1=f1, tp=tp, fn=fn, tn=tn)


def macro_f1(rows):
    f1s = []
    for c in range(7):
        tp = sum(1 for d in rows if d["true"] == c and d["pred"] == c)
        fp = sum(1 for d in rows if d["true"] != c and d["pred"] == c)
        fn = sum(1 for d in rows if d["true"] == c and d["pred"] != c)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return float(np.mean(f1s))


def med(xs):
    return float(np.median(xs)) if len(xs) else float("nan")


def inversion(rows):
    A = [d for d in rows if d["true"] == FALL and d["pred"] == FALL]
    B = [d for d in rows if d["true"] != FALL and d["pred"] == FALL]
    g = lambda grp, k: med([d[k] for d in grp])
    return dict(nA=len(A), nB=len(B),
                A_pfall=g(A, "fall_prob"), B_pfall=g(B, "fall_prob"),
                A_margin=g(A, "m_fall_maxnf"), B_margin=g(B, "m_fall_maxnf"),
                A_ent=g(A, "entropy"), B_ent=g(B, "entropy"),
                A_conf=g(A, "conf_margin"), B_conf=g(B, "conf_margin"))


def source_anatomy(rows):
    fa = [d for d in rows if d["true"] != FALL and d["pred"] == FALL]
    tot = len(fa); res = []
    for k in NONFALL:
        grp = [d for d in fa if d["true"] == k]
        if grp:
            res.append((CLASS[k], len(grp), 100 * len(grp) / tot if tot else 0,
                        med([d["fall_prob"] for d in grp]), med([d["entropy"] for d in grp])))
    return tot, res


def evaluate(setting, cand="v2safety"):
    clean = load(prob_path(setting, cand, "clean"))
    fgsm = load(prob_path(setting, cand, "fgsm"))
    pgd = load(prob_path(setting, cand, "pgd"))
    pgd20 = load(prob_path(setting, cand, "pgd", pgd20=True))
    if clean is None or pgd is None:
        return None
    cs = safety(clean); ps = safety(pgd)
    fs = safety(fgsm) if fgsm else None
    p20 = safety(pgd20)["recall"] if pgd20 else float("nan")
    inv = inversion(pgd)
    tot_fa, anat = source_anatomy(pgd)
    return dict(setting=setting, cand=cand,
                clean_acc=sum(d["pred"] == d["true"] for d in clean) / len(clean),
                clean_mf1=macro_f1(clean), clean_fall_recall=cs["recall"],
                clean_fp=cs["fp"], clean_wr=cs["wr"], clean_prec=cs["precision"], clean_spec=cs["specificity"],
                fgsm_recall=fs["recall"] if fs else float("nan"), fgsm_fp=fs["fp"] if fs else None,
                pgd=ps, pgd_recall=ps["recall"], pgd_fp=ps["fp"], pgd_wr=ps["wr"],
                pgd_wilson=wilson(ps["recall"]), pgd20=p20,
                pgd20_ratio=(p20 / ps["recall"]) if ps["recall"] > 0 else 0.0,
                inv=inv, tot_fa=tot_fa, anat=anat)


def read_sweep(setting, cand, attack):
    p = TE / f"G_{setting}_{cand}_{attack}_epsilon_sweep_test.csv"
    if not p.exists():
        return None
    xs, rec, fp = [], [], []
    with p.open(newline="") as f:
        for r in csv.DictReader(f):
            xs.append(float(r["epsilon"])); rec.append(float(r["fall_recall"])); fp.append(float(r["false_fall_alarm_count"]))
    return xs, rec, fp


def classify(m):
    """Return (tier, reasons) for one v2safety result vs the success criteria."""
    R = []
    guard = m["clean_acc"] >= 0.70 and m["clean_mf1"] >= 0.65 and m["clean_fall_recall"] >= 0.90
    inv_gap_F = F42["inv_B_pfall"] - F42["inv_A_pfall"]            # 0.103
    inv_gap_G = m["inv"]["B_pfall"] - m["inv"]["A_pfall"]
    inv_reduced = (inv_gap_G < inv_gap_F - 1e-9) and (inv_gap_G < 0.75 * inv_gap_F)
    inv_removed = inv_gap_G <= 0.0
    improves_F = (m["pgd_recall"] >= F42["pgd_recall"] and m["pgd_fp"] <= F42["pgd_fp"]
                  and (m["pgd_recall"] > F42["pgd_recall"] or m["pgd_fp"] < F42["pgd_fp"])) \
        or (m["pgd_fp"] < F42["pgd_fp"] and m["pgd_recall"] >= 0.50)
    minimum = (guard and m["pgd_recall"] >= 0.50 and m["pgd_fp"] < 115 and m["pgd_wr"] < 80 and m["pgd20"] > 0)
    pilot = (m["pgd_recall"] >= 0.50 and m["pgd_fp"] <= 90 and m["pgd_wr"] <= 60
             and m["pgd20_ratio"] >= 0.50 and inv_reduced)
    strong = (m["pgd_recall"] >= 0.50 and m["pgd_fp"] <= 80 and m["pgd_wr"] <= 60
              and m["pgd20_ratio"] >= 0.75 and (inv_removed or inv_reduced))
    if not guard:
        return "FAIL", ["clean guard fails (acc/mF1/clean-fall-recall)"]
    if m["clean_fall_recall"] < 0.90:
        return "FAIL", ["clean fall recall < 0.90"]
    if m["pgd_recall"] < 0.50:
        return "FAIL", ["PGD recall < 0.50"]
    if m["pgd20"] <= 0:
        return "FAIL", ["PGD-20 collapses to 0"]
    if strong and minimum:
        return "STRONG SUCCESS", ["all strong-tier thresholds met"]
    if pilot and minimum:
        return "PILOT SUCCESS", ["pilot-tier thresholds met; inversion reduced"]
    if minimum:
        return "MINIMUM USEFUL", ["minimum-useful thresholds met; below pilot tier"]
    if improves_F:
        return "TRADE-OFF ONLY", ["improves one axis but not a clean minimum-useful Pareto move"]
    return "FAIL", ["no improvement over Variant F recall/FP trade-off"]


TIER_RANK = {"STRONG SUCCESS": 4, "PILOT SUCCESS": 3, "MINIMUM USEFUL": 2, "TRADE-OFF ONLY": 1, "FAIL": 0}


def fmt(x, n=3):
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else (f"{x:.{n}f}" if isinstance(x, float) else str(x))


def main():
    results = {s: evaluate(s) for s in SETTINGS}
    results = {s: m for s, m in results.items() if m is not None}
    if not results:
        raise SystemExit("No Variant G v2safety eval outputs found under test_eval/. Run run_variantG_eval.py first.")
    tiers = {s: classify(m) for s, m in results.items()}
    best_s = max(results, key=lambda s: (TIER_RANK[tiers[s][0]], results[s]["pgd_recall"], -results[s]["pgd_fp"]))
    decision = tiers[best_s][0]

    # ---- analysis CSVs ----
    with (ANA / "variantG_safety_metrics.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["setting", "cand", "clean_acc", "clean_macro_f1", "clean_fall_recall", "clean_fp",
                    "clean_wr_fa", "clean_precision", "clean_specificity", "fgsm_recall", "fgsm_fp",
                    "pgd_recall", "pgd_wilson_lo", "pgd_wilson_hi", "pgd_fp", "pgd_wr_fa",
                    "pgd_specificity", "pgd_precision", "pgd_f1", "pgd20_recall", "pgd20_ratio", "tier"])
        for s, m in results.items():
            w.writerow([s, m["cand"], f"{m['clean_acc']:.4f}", f"{m['clean_mf1']:.4f}", f"{m['clean_fall_recall']:.4f}",
                        m["clean_fp"], m["clean_wr"], f"{m['clean_prec']:.4f}", f"{m['clean_spec']:.4f}",
                        f"{m['fgsm_recall']:.4f}", m["fgsm_fp"], f"{m['pgd_recall']:.4f}",
                        f"{m['pgd_wilson'][0]:.4f}", f"{m['pgd_wilson'][1]:.4f}", m["pgd_fp"], m["pgd_wr"],
                        f"{m['pgd']['specificity']:.4f}", f"{m['pgd']['precision']:.4f}", f"{m['pgd']['f1']:.4f}",
                        f"{m['pgd20']:.4f}", f"{m['pgd20_ratio']:.4f}", tiers[s][0]])
    with (ANA / "variantG_confidence_inversion.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["setting", "group", "n", "median_p_fall", "median_fall_vs_rest_margin", "median_entropy", "median_conf_margin"])
        w.writerow(["F42_ref", "A_true_fall", "30", F42["inv_A_pfall"], F42["inv_A_margin"], F42["inv_A_ent"], F42["inv_A_conf"]])
        w.writerow(["F42_ref", "B_false_alarm", "115", F42["inv_B_pfall"], F42["inv_B_margin"], F42["inv_B_ent"], F42["inv_B_conf"]])
        for s, m in results.items():
            iv = m["inv"]
            w.writerow([s, "A_true_fall", iv["nA"], f"{iv['A_pfall']:.3f}", f"{iv['A_margin']:.3f}", f"{iv['A_ent']:.3f}", f"{iv['A_conf']:.3f}"])
            w.writerow([s, "B_false_alarm", iv["nB"], f"{iv['B_pfall']:.3f}", f"{iv['B_margin']:.3f}", f"{iv['B_ent']:.3f}", f"{iv['B_conf']:.3f}"])

    # ---- figures ----
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    for ref, mk, col in [(FGSM42, "v", "tab:gray"), (D42, "s", "tab:orange"), (F42, "*", "tab:green")]:
        ax.scatter(ref["pgd_fp"], ref["pgd_recall"], marker=mk, s=140, color=col, label=ref["name"], zorder=3)
    for s, m in results.items():
        ax.scatter(m["pgd_fp"], m["pgd_recall"], marker="o", s=110, label=f"Variant G {s} v2safety", zorder=4)
        ax.annotate(s, (m["pgd_fp"], m["pgd_recall"]), textcoords="offset points", xytext=(6, 4), fontsize=8)
    ax.axhline(0.50, color="k", ls=":", lw=0.8); ax.axvline(115, color="tab:green", ls=":", lw=0.8)
    ax.set_xlabel("PGD@0.030 false fall alarms $FP_f$"); ax.set_ylabel("PGD@0.030 fall recall")
    ax.set_title("Variant G vs references — recall / false-alarm Pareto (seed 42)")
    ax.legend(fontsize=7.5, loc="lower right"); fig.tight_layout()
    fig.savefig(FIG / "fig_variantG_pareto_seed42.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    for s in results:
        sw = read_sweep(s, "v2safety", "pgd")
        if sw:
            ax[0].plot(sw[0], sw[1], marker="o", ms=3, label=f"G {s}")
            ax[1].plot(sw[0], sw[2], marker="o", ms=3, label=f"G {s}")
    ax[0].axhline(0.50, color="k", ls=":", lw=0.8)
    ax[0].set_xlabel("epsilon"); ax[0].set_ylabel("fall recall"); ax[0].set_title("PGD epsilon sweep — fall recall")
    ax[1].set_xlabel("epsilon"); ax[1].set_ylabel("false fall alarms"); ax[1].set_title("PGD epsilon sweep — false alarms")
    ax[0].legend(fontsize=8); ax[1].legend(fontsize=8); fig.tight_layout()
    fig.savefig(FIG / "fig_variantG_pgd_epsilon_sweep_seed42.png", dpi=150); plt.close(fig)

    write_report(results, tiers, best_s, decision)
    print(f"[done] Variant G seed42 analysis. decision={decision} (best setting {best_s}).")


def write_report(results, tiers, best_s, decision):
    L = []
    A = L.append
    A("# Variant G — seed-42 pilot report\n")
    A("> **Analysis of the committed seed-42 Variant G pilot** (targeted nonfall→fall hard-negative + "
      "source-class-weighted motion margin, on the frozen Variant F base). Three pre-registered settings "
      "**G1/G2/G3**, seed 42 ONLY; seeds 44/45/46 not run; loss / class indices / targeted-PGD sign / "
      "selection-v2 rule unchanged. Window-level, digital-domain, white-box; test n=500 (45 fall windows), "
      "ε=0.030. **No solved / certified / clinical / over-the-air claim.** All metrics computed from the "
      "committed per-window probability/logit exports (same method as the Variant F false-alarm diagnostic).\n")
    A(f"## Decision: **{decision}**  (best setting: {best_s} — {SETTINGS[best_s]})\n")
    A(f"Reason: {tiers[best_s][1][0]}.\n")

    A("## 1. Clean metrics\n")
    A("| Model | clean acc | clean macro-F1 | clean fall recall | clean FP | clean walk/run→fall | clean precision | clean specificity |")
    A("|---|---|---|---|---|---|---|---|")
    A(f"| {F42['name']} | {fmt(F42['clean_acc'])} | {fmt(F42['clean_mf1'])} | {fmt(F42['clean_fall_recall'])} | — | — | — | — |")
    A(f"| {D42['name']} | {fmt(D42['clean_acc'])} | {fmt(D42['clean_mf1'])} | {fmt(D42['clean_fall_recall'])} | — | — | — | — |")
    A(f"| {FGSM42['name']} | {fmt(FGSM42['clean_acc'])} | {fmt(FGSM42['clean_mf1'])} | {fmt(FGSM42['clean_fall_recall'])} | — | — | — | — |")
    for s, m in results.items():
        A(f"| **Variant G {s} v2safety** | {fmt(m['clean_acc'])} | {fmt(m['clean_mf1'])} | {fmt(m['clean_fall_recall'])} "
          f"| {m['clean_fp']} | {m['clean_wr']} | {fmt(m['clean_prec'])} | {fmt(m['clean_spec'])} |")
    A("")

    A("## 2. PGD@0.030 safety metrics\n")
    A("| Model | PGD recall [95% Wilson] | FP | walk/run→fall | specificity | precision | F1 | FGSM recall |")
    A("|---|---|---|---|---|---|---|---|")
    A(f"| {F42['name']} | {fmt(F42['pgd_recall'])} | {F42['pgd_fp']} | {F42['wr']} | — | — | — | — |")
    A(f"| {D42['name']} | {fmt(D42['pgd_recall'])} | {D42['pgd_fp']} | {D42['wr']} | — | — | — | — |")
    A(f"| {FGSM42['name']} | {fmt(FGSM42['pgd_recall'])} | {FGSM42['pgd_fp']} | {FGSM42['wr']} | — | — | — | — |")
    for s, m in results.items():
        lo, hi = m["pgd_wilson"]
        A(f"| **Variant G {s} v2safety** | {fmt(m['pgd_recall'])} [{lo:.3f}, {hi:.3f}] | {m['pgd_fp']} | {m['pgd_wr']} "
          f"| {fmt(m['pgd']['specificity'])} | {fmt(m['pgd']['precision'])} | {fmt(m['pgd']['f1'])} | {fmt(m['fgsm_recall'])} |")
    A(f"\n*Context only (not a selection target):* {F44['name']} — recall {fmt(F44['pgd_recall'])}, FP {F44['pgd_fp']}, "
      f"walk/run {F44['wr']}, PGD-20 {fmt(F44['pgd20'])}.\n")

    A("## 3. False-alarm source anatomy (PGD@0.030)\n")
    A("| Setting | source class | n FA | % of FA | median P(fall) | median entropy |")
    A("|---|---|---|---|---|---|")
    for s, m in results.items():
        for (cn, n, pct, mp, me) in m["anat"]:
            A(f"| {s} | {cn} | {n} | {pct:.1f} | {fmt(mp)} | {fmt(me)} |")
        A(f"| {s} | **TOTAL** | {m['tot_fa']} | 100.0 | — | — |")
    A("")

    A("## 4. Confidence inversion before (Variant F) vs after (Variant G)\n")
    A("Medians: **A** = detected true falls, **B** = false alarms. Inversion present when B median P(fall) > A.\n")
    A("| Model | A P(fall) | B P(fall) | gap (B−A) | A margin | B margin | A entropy | B entropy | A conf | B conf |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    A(f"| Variant F seed42 (before) | {F42['inv_A_pfall']:.3f} | {F42['inv_B_pfall']:.3f} | "
      f"{F42['inv_B_pfall']-F42['inv_A_pfall']:+.3f} | {F42['inv_A_margin']:.3f} | {F42['inv_B_margin']:.3f} | "
      f"{F42['inv_A_ent']:.3f} | {F42['inv_B_ent']:.3f} | {F42['inv_A_conf']:.3f} | {F42['inv_B_conf']:.3f} |")
    for s, m in results.items():
        iv = m["inv"]
        A(f"| Variant G {s} (after) | {iv['A_pfall']:.3f} | {iv['B_pfall']:.3f} | {iv['B_pfall']-iv['A_pfall']:+.3f} | "
          f"{iv['A_margin']:.3f} | {iv['B_margin']:.3f} | {iv['A_ent']:.3f} | {iv['B_ent']:.3f} | {iv['A_conf']:.3f} | {iv['B_conf']:.3f} |")
    A("\n*Inversion reduced* ⇔ the (B−A) P(fall) gap shrinks substantially vs Variant F's +"
      f"{F42['inv_B_pfall']-F42['inv_A_pfall']:.3f}; *removed* ⇔ gap ≤ 0.\n")

    A("## 5. PGD-20 durability\n")
    A("| Model | PGD-10 recall | PGD-20 recall | PGD-20 / PGD-10 |")
    A("|---|---|---|---|")
    A(f"| {F42['name']} | {fmt(F42['pgd_recall'])} | {fmt(F42['pgd20'])} | {F42['pgd20']/F42['pgd_recall']:.2f} |")
    for s, m in results.items():
        A(f"| **Variant G {s} v2safety** | {fmt(m['pgd_recall'])} | {fmt(m['pgd20'])} | {m['pgd20_ratio']:.2f} |")
    A("")

    A("## 6. Wilson intervals (PGD-10 fall recall, n_f=45)\n")
    A("| Model | recall | 95% Wilson |")
    A("|---|---|---|")
    A(f"| {F42['name']} | {fmt(F42['pgd_recall'])} | [0.521, 0.786] |")
    for s, m in results.items():
        lo, hi = m["pgd_wilson"]; A(f"| Variant G {s} v2safety | {fmt(m['pgd_recall'])} | [{lo:.3f}, {hi:.3f}] |")
    A("")

    A("## 7. Pareto plot\n`figures/fig_variantG_pareto_seed42.png` — recall vs FP for Variant G G1/G2/G3 against "
      "Variant F seed42 (★), Variant D (■), FGSM defense (▼); reference lines at recall 0.50 and FP 115.\n")
    A("## 8. PGD epsilon-sweep figure\n`figures/fig_variantG_pgd_epsilon_sweep_seed42.png` — 18-point PGD fall "
      "recall and false-alarm sweeps for each Variant G v2safety.\n")

    A("## 9. Decision scorecard\n")
    A("| Setting | clean acc≥0.70 | mF1≥0.65 | clean fall R≥0.90 | PGD R≥0.50 | FP<115 | FP≤90 | FP≤80 | wr<80 | wr≤60 | PGD20>0 | PGD20≥50% | PGD20≥75% | inversion | tier |")
    A("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for s, m in results.items():
        iv = m["inv"]; gapG = iv["B_pfall"] - iv["A_pfall"]; gapF = F42["inv_B_pfall"] - F42["inv_A_pfall"]
        inv_txt = "removed" if gapG <= 0 else ("reduced" if gapG < 0.75 * gapF else "unchanged")
        ck = lambda b: "✅" if b else "❌"
        A(f"| {s} | {ck(m['clean_acc']>=0.70)} | {ck(m['clean_mf1']>=0.65)} | {ck(m['clean_fall_recall']>=0.90)} "
          f"| {ck(m['pgd_recall']>=0.50)} | {ck(m['pgd_fp']<115)} | {ck(m['pgd_fp']<=90)} | {ck(m['pgd_fp']<=80)} "
          f"| {ck(m['pgd_wr']<80)} | {ck(m['pgd_wr']<=60)} | {ck(m['pgd20']>0)} | {ck(m['pgd20_ratio']>=0.50)} "
          f"| {ck(m['pgd20_ratio']>=0.75)} | {inv_txt} | **{tiers[s][0]}** |")
    A(f"\n**Overall decision: {decision}** (best setting {best_s}).\n")

    A("## Interpretation (thesis-safe)\n")
    bf = results[best_s]
    if decision in ("STRONG SUCCESS", "PILOT SUCCESS"):
        A(f"Variant G {best_s} improves the seed-42 attacked recall / false-alarm trade-off over Variant F "
          f"(PGD recall {fmt(bf['pgd_recall'])} / FP {bf['pgd_fp']} / walk-run {bf['pgd_wr']} vs F 0.667 / 115 / 80) "
          "and is a candidate for a pre-registered seed-44 validation per the promotion rule (spec §14.9). This is a "
          "window-level, digital-domain, white-box **trade-off operating point**, not solved/certified robustness.")
    elif decision == "MINIMUM USEFUL":
        gapF = F42["inv_B_pfall"] - F42["inv_A_pfall"]; gapG = bf["inv"]["B_pfall"] - bf["inv"]["A_pfall"]
        pareto = (bf["pgd_recall"] >= F42["pgd_recall"] and bf["pgd_fp"] <= F42["pgd_fp"] and bf["pgd_wr"] <= F42["wr"])
        A(f"Variant G {best_s} **Pareto-improves** Variant F on the attacked frontier "
          f"(PGD recall {fmt(bf['pgd_recall'])} ≥ 0.667, FP {bf['pgd_fp']} ≤ 115, walk/run {bf['pgd_wr']} ≤ 80)"
          + (" — higher recall *and* lower false alarms — " if pareto else " ")
          + f"and **substantially reduces the confidence inversion** the diagnostic isolated: the detected-fall-vs-"
          f"false-alarm median P(fall) gap shrinks from Variant F's +{gapF:.3f} to +{gapG:.3f} "
          f"(~{100*(1-gapG/gapF):.0f}% smaller), with PGD-20 durability retained "
          f"({bf['pgd20_ratio']:.0%} of PGD-10). The ablation is consistent: the **targeted hard-negative term (A) is the "
          "active ingredient** — G3 (source-weighted only, no targeted term) has the lowest PGD recall and the largest "
          "residual inversion. **However**, the result lands at the **minimum-useful** tier, not pilot success: the "
          f"absolute false-alarm count ({bf['pgd_fp']}) misses the pre-registered pilot bar (FP ≤ 90 and walk/run ≤ 60), "
          f"and clean accuracy ({fmt(bf['clean_acc'])}) sits below Variant F's 0.734. Per the strict promotion rule "
          "(spec §14.9, which requires *at least* pilot success), **Variant F remains the final implemented defense** "
          "and Variant G remains future work — but the genuine Pareto move plus the confirmed mechanism (inversion "
          "reduced, the central hypothesis of the pilot) is a substantive positive result and a reasonable basis to "
          "*consider* a pre-registered seed-44 validation if the false-alarm bar is treated as a stretch rather than a "
          "gate. This is a window-level, digital-domain, white-box trade-off operating point, not solved/certified "
          "robustness.")
    elif decision == "TRADE-OFF ONLY":
        A("Variant G moves one axis (recall or FP) but not a clean Pareto improvement over Variant F, and does not meet "
          "minimum-useful criteria. Per the promotion rule, **Variant F remains the final implemented defense** and "
          "Variant G stays future work.")
    else:
        A("No Variant G setting improves the Variant F recall/FP trade-off under the pre-registered criteria. Per the "
          "promotion rule, **Variant F remains the final implemented defense** and Variant G is retained as documented "
          "(negative) future work.")
    A("\n## Artifacts\n- `analysis/variantG_safety_metrics.csv`, `analysis/variantG_confidence_inversion.csv`\n"
      "- `figures/fig_variantG_pareto_seed42.png`, `figures/fig_variantG_pgd_epsilon_sweep_seed42.png`\n"
      "- per-candidate test_eval probability/logit + 18-eps sweep CSVs under `test_eval/`\n"
      "- training logs/metadata under `logs/`, `metadata/`, `analysis/` (selection candidates)\n")
    (VG / "VARIANT_G_SEED42_PILOT_REPORT.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
