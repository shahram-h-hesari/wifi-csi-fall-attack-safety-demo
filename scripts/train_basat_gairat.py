"""
BASAT Stage 2 -- GAIRAT-only pilot. Frozen Variant G G1 objective with ONE new ingredient:
boundary-margin instance reweighting of the adversarial cross-entropy (GAIRAT-style, adapted to the
fall<->locomotion safety boundary). NOT full BASAT; NO SAT selection, NO MART multiplier, NO TRADES
consistency here. Isolates whether reweighting WHICH adversarial windows drive training moves the
PGD-conditional fall frontier -- a different mechanism from the (closed) Stage-1 consistency term.

Objective (per batch):
    L = base_FWCE_reweighted + lam_s*L_src + lam_f*L_fall + lam_t*L_tgt   (G1 margin terms UNCHANGED)
where base_FWCE_reweighted = sum_i (mult_i * cw_{y_i} * ce_i) / sum_i (mult_i * cw_{y_i}),
  mult_i = 1 for CLEAN windows, mult_i = w_i for ADV windows; cw = G1 class weights (fall weight 3);
  ce_i = per-sample (unweighted) cross-entropy. At w_i==1 this is EXACTLY G1's base CE (verified in
  --self-check), so GAIRAT is a pure reweighting of the adversarial CE, not a rescaling.

GAIRAT weights (margin-based, NOT kappa-steps-to-flip -> smoother + less gradient-masking-prone):
  per ADV window, safety margin   mu_i = z_fall - max_{c!=fall} z_c        (true fall)
                                       = z_true - z_fall                    (non-fall)
  g_i = g_min + (g_max - g_min) * 0.5*(1 + tanh(-lam_g * mu_i))            (small/neg margin -> high)
  optional locomotion emphasis    g_i *= rho   if y_i in {walk, run}
  weights are DETACHED (constants) and mean-normalized to 1 over the adv sub-batch (w = g * n_adv / sum g).
  Burn-in: w_i == 1 for the first `burn_in` epochs (early-training margins are noise; recall ~0 until ~ep27).

Scope: seed 42 ONLY, LeNet only, same UT-HAR split, same FGSM/PGD eps=0.030, same clean guard +
selection-v2 as G1. Window-level, digital-domain, white-box; NOT solved/certified/clinical/OTA.
VALIDATION-only for go/no-go. NO test set used in training or selection.

Go/no-go bar (validation, best G1 checkpoint): val PGD AUROC of P(fall) > 0.906; recall@FAR<=10% >= 0.477;
clean guard held; PGD-20 no masking. Computed post-hoc via export_probability_predictions.py (--split val).

Modes:
    --self-check  class asserts + targeted-PGD sign check + GAIRAT weight monotonicity + reduces-to-G1
                  check (w==1) + finite loss decomposition. No training, no .pt.
    --smoke       2-epoch tiny seed-42 run to a `_smoke` namespace (code correctness + runtime).
    --pilot       approved seed-42 full pilot -> boundary_aware_selective_at/gairat/seed42 namespace.
    (default)     GATED.

Commands:
    python scripts/train_basat_gairat.py --setting GR1 --self-check
    python scripts/train_basat_gairat.py --setting GR1 --smoke --epochs 2 --smoke-batches 5
    python scripts/train_basat_gairat.py --setting GR1 --pilot
"""
from __future__ import annotations
from pathlib import Path
import argparse, csv, json, platform, sys, time
from datetime import datetime, timezone
import numpy as np
import torch
import torch.nn.functional as Fnn


def import_variantG():
    sd = Path(__file__).resolve().parent
    if str(sd) not in sys.path:
        sys.path.insert(0, str(sd))
    import train_variantG_targeted_hardneg as tvg
    return tvg


tvg = import_variantG()
WALK, RUN = tvg.WALK, tvg.RUN
V2_GUARD_ACC, V2_GUARD_F1 = tvg.V2_GUARD_ACC, tvg.V2_GUARD_F1
G1 = tvg.SETTINGS["G1"]
BASE_LAM_S, BASE_LAM_F = tvg.LAM_S, tvg.LAM_F
BASE_LAM_T, BASE_W_WR = G1["lam_t"], G1["w_wr"]

# GAIRAT settings (only GR1 runnable for the first pilot). g_min/g_max/lam_g fixed; rho=1 (loco off).
SETTINGS = {
    "GR1": {"lam_g": 1.0, "g_min": 0.5, "g_max": 2.0, "rho": 1.0, "burn_in": 10, "desc": "margin GAIRAT, loco off"},
    "GR2": {"lam_g": 1.0, "g_min": 0.5, "g_max": 2.0, "rho": 1.5, "burn_in": 10, "desc": "margin GAIRAT + loco emphasis (BLOCKED until approved)"},
    "GR3": {"lam_g": 2.0, "g_min": 0.25, "g_max": 3.0, "rho": 1.0, "burn_in": 10, "desc": "sharper margin GAIRAT (BLOCKED until approved)"},
}
RUNNABLE = {"GR1"}


# --------------------------------------------------------------------------- GAIRAT margin weights
def gairat_margin_weights(adv_logits, adv_lab, fall_idx, lam_g, g_min, g_max, rho, device):
    """DETACHED, mean-1-normalized per-adv-window boundary weights. Returns (w[n_adv], diag)."""
    n = adv_lab.numel()
    if n == 0:
        return torch.ones(0, device=device), {"n": 0, "mean_w": float("nan"), "w_fall": float("nan"),
                                              "w_nonfall": float("nan"), "mean_mu_fall": float("nan")}
    z = adv_logits.detach()
    f = adv_lab == fall_idx
    mu = torch.empty(n, device=device)
    # non-fall: mu = z_true - z_fall
    if (~f).any():
        zt = z[~f].gather(1, adv_lab[~f].unsqueeze(1)).squeeze(1)
        mu[~f] = zt - z[~f][:, fall_idx]
    # fall: mu = z_fall - max_{c!=fall} z_c
    if f.any():
        zf = z[f].clone()
        zfall = zf[:, fall_idx].clone()
        zf[:, fall_idx] = float("-inf")
        mu[f] = zfall - zf.max(dim=1).values
    g = g_min + (g_max - g_min) * 0.5 * (1.0 + torch.tanh(-lam_g * mu))
    if rho != 1.0:
        loco = (adv_lab == WALK) | (adv_lab == RUN)
        g = torch.where(loco, g * rho, g)
    w = g * (n / g.sum().clamp_min(1e-12))           # mean-normalize to 1
    diag = {"n": int(n), "mean_w": float(w.mean().item()),
            "w_fall": float(w[f].mean().item()) if f.any() else float("nan"),
            "w_nonfall": float(w[~f].mean().item()) if (~f).any() else float("nan"),
            "mean_mu_fall": float(mu[f].mean().item()) if f.any() else float("nan")}
    return w, diag


def reweighted_base_loss(outputs, batch_y, n_clean, adv_weights, class_weights):
    """sum_i mult_i cw_{y_i} ce_i / sum_i mult_i cw_{y_i}; mult=1 clean, w_i adv. ==G1 base at w==1."""
    ce = Fnn.cross_entropy(outputs, batch_y, reduction="none")     # per-sample, UNweighted
    cw = class_weights[batch_y]
    mult = torch.ones_like(cw)
    if adv_weights.numel() > 0:
        mult[n_clean:] = adv_weights
    den = (mult * cw).sum().clamp_min(1e-12)
    return (mult * cw * ce).sum() / den


def train_one_epoch_gairat(model, loader, class_weights, atk_criterion, optimizer, device,
                           train_epsilons, train_pgd_steps, rng, tsg, cfg, fall_idx, epoch,
                           max_batches=None):
    model.train()
    use_w = epoch > cfg["burn_in"]
    tot_loss = tot = 0.0
    s = {"base": 0.0, "src": 0.0, "fall": 0.0, "tgt": 0.0}
    wd = {"mean": 0.0, "wf": 0.0, "wn": 0.0, "muf": 0.0, "nb": 0}
    nb = 0
    for bi, (inputs, labels) in enumerate(loader):
        if max_batches is not None and bi >= max_batches:
            break
        inputs = inputs.to(device).float()
        labels = labels.type(torch.LongTensor).to(device)
        bs = labels.size(0)
        eps = float(rng.choice(train_epsilons)); pgd_alpha = eps / 4.0
        n_clean = bs // 2; n_fgsm = (bs - n_clean) // 2
        clean_x = inputs[:n_clean]
        fgsm_src, fgsm_lbl = inputs[n_clean:n_clean + n_fgsm], labels[n_clean:n_clean + n_fgsm]
        pgd_src, pgd_lbl = inputs[n_clean + n_fgsm:], labels[n_clean + n_fgsm:]

        model.eval()
        fgsm_adv = tsg.fgsm_perturb(model, fgsm_src, fgsm_lbl, atk_criterion, eps)
        pgd_adv = tsg.pgd_perturb(model, pgd_src, pgd_lbl, atk_criterion, eps, train_pgd_steps, pgd_alpha)
        nf_mask = labels != fall_idx
        if BASE_LAM_T > 0 and nf_mask.any():
            tgt_adv = tvg.targeted_fall_pgd(model, inputs[nf_mask], fall_idx, atk_criterion, eps, train_pgd_steps, pgd_alpha)
            tgt_lab = labels[nf_mask]
        else:
            tgt_adv, tgt_lab = None, labels[:0]
        model.train()

        batch_x = torch.cat([clean_x, fgsm_adv, pgd_adv], dim=0)
        batch_y = labels
        n_clean = clean_x.size(0)

        optimizer.zero_grad()
        outputs = model(batch_x).float()
        adv_out, adv_lab = outputs[n_clean:], batch_y[n_clean:]
        if use_w:
            w, d = gairat_margin_weights(adv_out, adv_lab, fall_idx, cfg["lam_g"], cfg["g_min"], cfg["g_max"], cfg["rho"], device)
            wd["mean"] += d["mean_w"]; wd["wf"] += (d["w_fall"] if np.isfinite(d["w_fall"]) else 0.0)
            wd["wn"] += (d["w_nonfall"] if np.isfinite(d["w_nonfall"]) else 0.0)
            wd["muf"] += (d["mean_mu_fall"] if np.isfinite(d["mean_mu_fall"]) else 0.0); wd["nb"] += 1
        else:
            w = torch.ones(adv_lab.numel(), device=device)
        base = reweighted_base_loss(outputs, batch_y, n_clean, w, class_weights)
        tgt_out = model(tgt_adv).float() if (tgt_adv is not None and tgt_adv.numel() > 0) else None
        L_src, L_fall, L_tgt = tvg.variantG_margin_terms(adv_out, adv_lab, tgt_out, tgt_lab, BASE_W_WR, fall_idx, device)
        loss = base + BASE_LAM_S * L_src + BASE_LAM_F * L_fall + BASE_LAM_T * L_tgt
        loss.backward(); optimizer.step()

        tot_loss += loss.item() * bs; tot += bs; nb += 1
        s["base"] += float(base.item()); s["src"] += float(L_src.item())
        s["fall"] += float(L_fall.item()); s["tgt"] += float(L_tgt.item())
    d = max(1, nb); dw = max(1, wd["nb"])
    return {"train_loss": tot_loss / max(1, tot), "mean_base": s["base"] / d, "mean_src_motion": s["src"] / d,
            "mean_fall_margin": s["fall"] / d, "mean_targeted": s["tgt"] / d, "weights_active": int(use_w),
            "mean_w": wd["mean"] / dw, "mean_w_fall": wd["wf"] / dw, "mean_w_nonfall": wd["wn"] / dw,
            "mean_mu_fall": wd["muf"] / dw, "batches": nb}


def parse_args():
    p = argparse.ArgumentParser(description="BASAT Stage 2 -- GAIRAT-only (G1 + boundary-margin adv reweighting).")
    p.add_argument("--setting", choices=sorted(SETTINGS.keys()), default="GR1")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=70)
    p.add_argument("--patience", type=int, default=15)
    p.add_argument("--min-epochs", type=int, default=35)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--train-pgd-steps", type=int, default=7)
    p.add_argument("--fall-weight", type=float, default=3.0)
    p.add_argument("--self-check", action="store_true")
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--smoke-batches", type=int, default=5)
    p.add_argument("--pilot", action="store_true")
    return p.parse_args()


def _class_weights(F, fall_weight):
    cw = torch.ones(F["num_classes"], device=F["device"]); cw[F["fall_idx"]] = fall_weight
    return cw


def run_self_check(args, F):
    cfg = SETTINGS[args.setting]; device = F["device"]; fall_idx = F["fall_idx"]
    print("=" * 78); print(f"BASAT Stage 2 GAIRAT --self-check  setting={args.setting} ({cfg['desc']})")
    assert fall_idx == 1 and F["num_classes"] == 7 and (WALK, RUN) == (2, 4)
    print(f"  class-index assertions PASSED: FALL={fall_idx} WALK={WALK} RUN={RUN}")
    sc, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], fall_idx, device)
    print(f"  targeted-PGD sign check: clean P(fall)={sc['clean_median_p_fall']:.4f} -> "
          f"targeted={sc['targeted_median_p_fall']:.4f}  increased={sc['increased']}")
    if not ok:
        raise SystemExit("SIGN CHECK FAILED.")
    # GAIRAT weight monotonicity: smaller margin -> larger weight; mean-normalized to 1.
    z = torch.zeros(6, 7, device=device)
    lab = torch.tensor([fall_idx, fall_idx, fall_idx, 2, 2, 2], device=device)  # 3 fall, 3 walk
    # construct decreasing fall margins for falls and decreasing true-vs-fall margins for walks
    z[0, fall_idx] = 3.0; z[1, fall_idx] = 1.0; z[2, fall_idx] = -1.0          # fall margins 3,1,-1
    z[3, 2] = 3.0; z[4, 2] = 1.0; z[5, 2] = -1.0                                # walk z_true; z_fall=0
    w, d = gairat_margin_weights(z, lab, fall_idx, cfg["lam_g"], cfg["g_min"], cfg["g_max"], cfg["rho"], device)
    print(f"  GAIRAT weights (margins 3,1,-1 per role): {[round(float(x),3) for x in w.tolist()]}  mean={d['mean_w']:.3f}")
    assert w[0] < w[1] < w[2] and w[3] < w[4] < w[5], "weight must increase as margin decreases (near boundary)"
    assert abs(d["mean_w"] - 1.0) < 1e-5, "weights must be mean-normalized to 1"
    print("  monotonicity + mean-1 normalization PASSED")
    # reduces-to-G1 at w==1
    F["model"].train()
    inputs, labels = next(iter(F["train_loader"]))
    inputs = inputs.to(device).float(); labels = labels.type(torch.LongTensor).to(device)
    bs = labels.size(0); n_clean = bs // 2; n_fgsm = (bs - n_clean) // 2
    eps = float(F["rng"].choice(F["train_epsilons"])); a = eps / 4.0
    fgsm = F["tsg"].fgsm_perturb(F["model"], inputs[n_clean:n_clean + n_fgsm], labels[n_clean:n_clean + n_fgsm], F["atk_criterion"], eps)
    pgd = F["tsg"].pgd_perturb(F["model"], inputs[n_clean + n_fgsm:], labels[n_clean + n_fgsm:], F["atk_criterion"], eps, args.train_pgd_steps, a)
    outputs = F["model"](torch.cat([inputs[:n_clean], fgsm, pgd], 0)).float()
    cw = _class_weights(F, args.fall_weight)
    n_adv = labels.numel() - n_clean
    base_w1 = reweighted_base_loss(outputs, labels, n_clean, torch.ones(n_adv, device=device), cw)
    g1_base = torch.nn.CrossEntropyLoss(weight=cw)(outputs, labels)
    print(f"  reduces-to-G1 at w==1: reweighted={base_w1.item():.6f}  G1_CE={g1_base.item():.6f}  "
          f"|diff|={abs(base_w1.item()-g1_base.item()):.2e}")
    assert abs(base_w1.item() - g1_base.item()) < 1e-5, "must equal G1 base CE when adv weights==1"
    # finite full loss with real GAIRAT weights
    adv_out, adv_lab = outputs[n_clean:], labels[n_clean:]
    w, _ = gairat_margin_weights(adv_out, adv_lab, fall_idx, cfg["lam_g"], cfg["g_min"], cfg["g_max"], cfg["rho"], device)
    base = reweighted_base_loss(outputs, labels, n_clean, w, cw)
    nf = labels != fall_idx
    tgt_out = F["model"](tvg.targeted_fall_pgd(F["model"], inputs[nf], fall_idx, F["atk_criterion"], eps, args.train_pgd_steps, a)).float()
    L_src, L_fall, L_tgt = tvg.variantG_margin_terms(adv_out, adv_lab, tgt_out, labels[nf], BASE_W_WR, fall_idx, device)
    total = base + L_src + L_fall + L_tgt
    for nm, v in (("base", base), ("L_src", L_src), ("L_fall", L_fall), ("L_tgt", L_tgt), ("total", total)):
        print(f"    {nm:7s} = {v.item():.5f}"); assert np.isfinite(v.item())
    assert L_tgt.item() > 0
    print("  PASS: class indices, sign check, weight monotonicity, mean-1, reduces-to-G1, finite losses.")
    print("=" * 78)


def run_smoke(args, F):
    cfg = SETTINGS[args.setting]; tsg, s1 = F["tsg"], F["s1"]; cw = _class_weights(F, args.fall_weight)
    run = f"seed{args.seed}_basat_gairat_{args.setting}_smoke"
    base = F["exp"] / "results" / "safety_guided_defense" / "boundary_aware_selective_at" / "gairat" / "_smoke" / f"seed{args.seed}"
    base.mkdir(parents=True, exist_ok=True)
    print("=" * 78); print(f"BASAT Stage 2 GAIRAT --smoke  setting={args.setting}  run={run}")
    print(f"  G1 base + GAIRAT: lam_g={cfg['lam_g']} g=[{cfg['g_min']},{cfg['g_max']}] rho={cfg['rho']} burn_in={cfg['burn_in']}")
    history = []; start = time.time()
    for epoch in range(1, args.epochs + 1):
        tr = train_one_epoch_gairat(F["model"], F["train_loader"], cw, F["atk_criterion"], F["optimizer"],
                                    F["device"], F["train_epsilons"], args.train_pgd_steps, F["rng"], tsg, cfg,
                                    F["fall_idx"], epoch, max_batches=args.smoke_batches)
        vb = tsg.compute_validation_bundle(s1, F["model"], F["val_loader"], F["atk_criterion"], F["device"])
        for k in ("train_loss", "mean_base", "mean_src_motion", "mean_fall_margin", "mean_targeted"):
            assert np.isfinite(tr[k]), f"{k} not finite at epoch {epoch}"
        history.append({"epoch": epoch, **{k: tr[k] for k in tr if k != "batches"},
                        "val_clean_accuracy": vb["val_clean_accuracy"], "val_clean_fall_recall": vb["val_clean_fall_recall"],
                        "val_pgd_fall_recall": vb["val_pgd_fall_recall"], "val_pgd_false_fall_alarms": vb["val_pgd_false_fall_alarms"]})
        print(f"  epoch {epoch}/{args.epochs} | loss={tr['train_loss']:.3f} base={tr['mean_base']:.3f} "
              f"wact={tr['weights_active']} w(f/nf)={tr['mean_w_fall']:.2f}/{tr['mean_w_nonfall']:.2f} "
              f"| acc={vb['val_clean_accuracy']:.3f} cFR={vb['val_clean_fall_recall']:.3f} "
              f"pgd_fr={vb['val_pgd_fall_recall']:.3f} pgd_FP={vb['val_pgd_false_fall_alarms']}")
    elapsed = time.time() - start
    with (base / f"{run}_log.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(history[0].keys())); w.writeheader()
        for r in history:
            w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in history[0]})
    summary = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "stage": "basat_gairat_smoke",
               "setting": args.setting, "cfg": cfg, "seed": args.seed, "epochs": args.epochs,
               "smoke_batches": args.smoke_batches, "elapsed_seconds": elapsed,
               "per_epoch_seconds_estimate": elapsed / max(1, args.epochs), "test_set_used": False,
               "device": str(F["device"]), "python_version": platform.python_version(), "torch_version": torch.__version__,
               "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(F["exp"])),
               "note": "SMOKE ONLY -- code-correctness + runtime; weights inactive during burn_in; no .pt persisted."}
    with (base / f"{run}_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  smoke done in {elapsed:.1f}s ({summary['per_epoch_seconds_estimate']:.2f}s/epoch on {args.smoke_batches} batches)")
    print("=" * 78)
    return summary


def run_pilot(args, F):
    assert args.seed == 42, "pilot is seed 42 ONLY"
    cfg = SETTINGS[args.setting]; tsg, s1 = F["tsg"], F["s1"]; device = F["device"]; cw = _class_weights(F, args.fall_weight)
    run = f"seed{args.seed}_basat_gairat_{args.setting}"
    base = F["exp"] / "results" / "safety_guided_defense" / "boundary_aware_selective_at" / "gairat" / f"seed{args.seed}" / args.setting
    ck_dir = F["exp"] / "checkpoints" / "safety_guided_defense" / "boundary_aware_selective_at" / "gairat" / f"seed{args.seed}" / args.setting
    logs_dir = base / "logs"; ana_dir = base / "analysis"; meta_dir = base / "metadata"
    for d in (ck_dir, logs_dir, ana_dir, meta_dir):
        d.mkdir(parents=True, exist_ok=True)
    ck = {k: ck_dir / f"{run}_{k}_best.pt" for k in ("v2safety", "v2maxrec", "v2lowFA", "v2macroF1")}
    ck_last = ck_dir / f"{run}_last.pt"

    print("=" * 78); print(f"BASAT Stage 2 GAIRAT FULL PILOT  setting={args.setting} ({cfg['desc']})  run={run}")
    print(f"  G1 base + GAIRAT: lam_g={cfg['lam_g']} g=[{cfg['g_min']},{cfg['g_max']}] rho={cfg['rho']} "
          f"burn_in={cfg['burn_in']} fw={args.fall_weight}")
    print(f"  guard acc>={V2_GUARD_ACC} & mF1>={V2_GUARD_F1} | epochs={args.epochs} patience={args.patience} "
          f"min={args.min_epochs} eps={F['train_epsilons']}")
    print("=" * 78)

    history = []
    best = {"v2safety": (-1e9, -1), "v2maxrec": ((-1e9, 1e9), -1), "v2lowFA": ((1e9, -1e9), -1), "v2macroF1": (-1e9, -1)}
    best_rec = {}; no_improve = 0; start = time.time(); w_ever_active = False

    for epoch in range(1, args.epochs + 1):
        tr = train_one_epoch_gairat(F["model"], F["train_loader"], cw, F["atk_criterion"], F["optimizer"], device,
                                    F["train_epsilons"], args.train_pgd_steps, F["rng"], tsg, cfg, F["fall_idx"], epoch)
        for k in ("train_loss", "mean_base", "mean_src_motion", "mean_fall_margin", "mean_targeted"):
            if not np.isfinite(tr[k]):
                raise SystemExit(f"STOP (numerical): {k} not finite at epoch {epoch}.")
        w_ever_active = w_ever_active or bool(tr["weights_active"])
        vb = tsg.compute_validation_bundle(s1, F["model"], F["val_loader"], F["atk_criterion"], device)
        sc = tvg.safety_score(vb)
        acc = vb["val_clean_accuracy"]; f1 = vb["val_clean_macro_f1"]
        rec = vb["val_pgd_fall_recall"]; fpv = vb["val_pgd_false_fall_alarms"]
        eligible = (acc >= V2_GUARD_ACC and f1 >= V2_GUARD_F1)

        def save(key):
            torch.save({"epoch": epoch, "model_state_dict": F["model"].state_dict(), "selection_method": key,
                        "val_bundle": vb, "safety_score": sc, "run_name": run, "setting": args.setting,
                        "cfg": cfg, "args": vars(args)}, ck[key])

        flags = {k: 0 for k in ck}
        if eligible:
            if sc > best["v2safety"][0]:
                best["v2safety"] = (sc, epoch); best_rec["v2safety"] = vb; save("v2safety"); flags["v2safety"] = 1; no_improve = 0
            if (rec, -fpv) > best["v2maxrec"][0]:
                best["v2maxrec"] = ((rec, -fpv), epoch); best_rec["v2maxrec"] = vb; save("v2maxrec"); flags["v2maxrec"] = 1
            if rec >= tvg.LOWFA_RECALL_FLOOR and (fpv, -rec) < best["v2lowFA"][0]:
                best["v2lowFA"] = ((fpv, -rec), epoch); best_rec["v2lowFA"] = vb; save("v2lowFA"); flags["v2lowFA"] = 1
        if not flags["v2safety"] and best["v2safety"][1] > 0:
            no_improve += 1
        if f1 > best["v2macroF1"][0]:
            best["v2macroF1"] = (f1, epoch); best_rec["v2macroF1"] = vb; save("v2macroF1"); flags["v2macroF1"] = 1

        history.append({"epoch": epoch, "train_loss": tr["train_loss"], "mean_base": tr["mean_base"],
                        "mean_src_motion": tr["mean_src_motion"], "mean_fall_margin": tr["mean_fall_margin"],
                        "mean_targeted": tr["mean_targeted"], "weights_active": tr["weights_active"],
                        "mean_w_fall": tr["mean_w_fall"], "mean_w_nonfall": tr["mean_w_nonfall"], "mean_mu_fall": tr["mean_mu_fall"],
                        "val_clean_accuracy": acc, "val_clean_macro_f1": f1, "val_clean_fall_recall": vb["val_clean_fall_recall"],
                        "val_fgsm_fall_recall": vb["val_fgsm_fall_recall"], "val_pgd_fall_recall": rec,
                        "val_fgsm_false_fall_alarms": vb["val_fgsm_false_fall_alarms"], "val_pgd_false_fall_alarms": fpv,
                        "val_normalized_false_alarm_burden": vb["val_normalized_false_alarm_burden"], "safety_score": sc,
                        "v2_eligible": int(eligible), "sel_v2safety": flags["v2safety"], "sel_v2maxrec": flags["v2maxrec"],
                        "sel_v2lowFA": flags["v2lowFA"], "sel_v2macroF1": flags["v2macroF1"]})
        print(f"Epoch {epoch:03d}/{args.epochs} | loss={tr['train_loss']:.3f} base={tr['mean_base']:.3f} "
              f"wact={tr['weights_active']} w(f/nf)={tr['mean_w_fall']:.2f}/{tr['mean_w_nonfall']:.2f} muF={tr['mean_mu_fall']:.2f} | "
              f"acc={acc:.3f} f1={f1:.3f} cFR={vb['val_clean_fall_recall']:.3f} pgd_fr={rec:.3f} pgd_FP={fpv} "
              f"score={sc:.3f} v2elig={int(eligible)} "
              f"[{'S' if flags['v2safety'] else '.'}{'R' if flags['v2maxrec'] else '.'}"
              f"{'L' if flags['v2lowFA'] else '.'}{'F' if flags['v2macroF1'] else '.'}]")
        if args.patience > 0 and epoch >= args.min_epochs and no_improve >= args.patience:
            print(f"Early stopping at epoch {epoch} (best v2safety epoch {best['v2safety'][1]})."); break

    if not w_ever_active:
        raise SystemExit("STOP: GAIRAT weights never activated (burn_in >= epochs run?).")
    elapsed = time.time() - start
    last_epoch = history[-1]["epoch"]
    torch.save({"epoch": last_epoch, "model_state_dict": F["model"].state_dict(), "selection_method": "last",
                "run_name": run, "setting": args.setting, "cfg": cfg, "args": vars(args)}, ck_last)
    fields = list(history[0].keys())
    with (logs_dir / f"{run}_training_log.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in history:
            w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in fields})
    with (ana_dir / f"{run}_selection_candidates.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["selection", "selected_epoch", "val_clean_acc", "val_clean_macro_f1",
                    "val_pgd_recall", "val_pgd_false_alarms", "safety_score"])
        for k in ck:
            ep = best[k][1]; vbk = best_rec.get(k, {})
            w.writerow([k, ep, f"{vbk.get('val_clean_accuracy', float('nan')):.4f}",
                        f"{vbk.get('val_clean_macro_f1', float('nan')):.4f}",
                        f"{vbk.get('val_pgd_fall_recall', float('nan')):.4f}",
                        vbk.get('val_pgd_false_fall_alarms', ''), f"{tvg.safety_score(vbk):.4f}" if vbk else ""])
    meta = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "stage": f"basat_gairat_{args.setting}_seed{args.seed}_pilot",
            "method": "BASAT Stage 2 GAIRAT-only (G1 + margin-based adv reweighting)", "namespace": "boundary_aware_selective_at/gairat",
            "run_name": run, "setting": args.setting, "cfg": cfg, "seed": args.seed, "fall_weight": args.fall_weight,
            "lam_s": BASE_LAM_S, "lam_f": BASE_LAM_F, "lam_t": BASE_LAM_T, "w_wr": BASE_W_WR,
            "objective": "reweighted base FWCE (mult=1 clean, w_i adv; ==G1 at w==1) + lam_s*L_src + lam_f*L_fall + lam_t*L_tgt; "
                         "w_i = margin GAIRAT g_min+(g_max-g_min)*0.5*(1+tanh(-lam_g*mu)), detached, mean-1, burn_in epochs",
            "v2_guard": {"min_clean_accuracy": V2_GUARD_ACC, "min_clean_macro_f1": V2_GUARD_F1},
            "train_epsilons": F["train_epsilons"], "train_pgd_steps": args.train_pgd_steps,
            "epochs_run": last_epoch, "split_sizes": F["split_sizes"], "test_set_used": False,
            "selected_epochs": {k: best[k][1] for k in ck}, "checkpoints": {k: str(v) for k, v in ck.items()},
            "go_no_go_ref": "results/safety_guided_defense/boundary_aware_selective_at/seed42/g1_baseline_val_frontier.json",
            "claim_boundary": "window-level digital-domain white-box; seed42/LeNet only; not solved/certified/clinical/OTA",
            "device": str(device), "python_version": platform.python_version(), "torch_version": torch.__version__,
            "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(F["exp"])), "elapsed_seconds": elapsed}
    with (meta_dir / f"{run}_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("-" * 78)
    print(f"Done in {elapsed:.1f}s ({last_epoch} epochs). selected epochs: " + ", ".join(f"{k}={best[k][1]}" for k in ck))
    print("  NEXT: export val PGD probabilities for selected checkpoints; compute val PGD AUROC vs the 0.906 bar.")
    print("=" * 78)


def main():
    args = parse_args()
    if args.seed != 42:
        raise SystemExit(f"GAIRAT Stage 2 is seed-42 ONLY for now (got seed {args.seed}).")
    if args.setting not in RUNNABLE and (args.pilot or args.smoke):
        raise SystemExit(f"Only {sorted(RUNNABLE)} is approved to run; {args.setting} is defined but blocked.")
    F = tvg.load_foundation(args)
    if args.self_check:
        run_self_check(args, F); return
    if args.smoke:
        _, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
        if not ok:
            raise SystemExit("SIGN CHECK FAILED before smoke.")
        run_smoke(args, F); return
    if args.pilot:
        _, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
        if not ok:
            raise SystemExit("SIGN CHECK FAILED before pilot.")
        run_pilot(args, F); return
    raise SystemExit("Gated: pass --self-check, --smoke, or --pilot.")


if __name__ == "__main__":
    main()
