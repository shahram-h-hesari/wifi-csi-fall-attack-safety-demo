"""
Variant H dual-tail safety-budget defense (smoke-only implementation).

Implements VARIANT_H_IMPLEMENTATION_SPEC.md. Reuses the frozen Variant G foundation
(scripts/train_variantG_targeted_hardneg.py) unchanged -- data loading, LeNet, class constants, seed
handling, targeted-to-fall PGD, source weighting, the Variant G margin terms, and selection-v2 -- and adds
two TopK (tail-aware) terms:

    L_H = L_FWCE
        + lam_f * L_fall            (Variant G fall-preservation margin)
        + lam_s * L_src             (Variant G source-weighted motion margin)
        + lam_t * L_tgt             (Variant G targeted nonfall->fall hard-negative)
        + lam_b * L_nonfall_budget  (NEW: TopKMean over adv nonfall of relu(z_f - z_y + gamma_b))
        + lam_r * L_fall_rescue     (NEW: TopKMean over adv fall    of relu(gamma_r + max_{c!=f}z_c - z_f))

First-implementation decision (spec sec.3): both budget terms use the UNTARGETED PGD adversarial sub-batch;
targeted-to-fall examples remain covered by L_tgt only. The frozen Variant G base uses G1 settings
(lam_s=lam_f=lam_t=1.0, w_wr=2.0, gammas=0.5, fall weight 3). Only (lam_b, lam_r) vary per Variant H setting.

Scope: seed 42 ONLY (smoke); LeNet only; same UT-HAR/SenseFi split. Window-level, digital-domain,
white-box; NOT solved/certified/clinical/over-the-air. THIS FILE IS SMOKE-ONLY: full pilot training is
intentionally gated.

Modes:
    --self-check  class asserts + targeted-PGD sign check + TopK correctness + loss finite/nonzero +
                  directionality checks (no training, no .pt)
    --smoke       1-2 epoch tiny seed-42 H1 run to a `_smoke` namespace (code correctness only; no claims)
    (default)     full training -- GATED, refuses to launch

Commands:
    python scripts/train_variantH_dual_tail_budget.py --setting H1 --self-check
    python scripts/train_variantH_dual_tail_budget.py --setting H1 --smoke --epochs 2 --smoke-batches 5
"""
from __future__ import annotations
from pathlib import Path
import argparse, csv, json, math, platform, sys, time
from datetime import datetime, timezone
import numpy as np
import torch, torch.nn as nn, torch.optim as optim


def import_variantG():
    sd = Path(__file__).resolve().parent
    if str(sd) not in sys.path:
        sys.path.insert(0, str(sd))
    import train_variantG_targeted_hardneg as tvg
    return tvg


tvg = import_variantG()
WALK, RUN = tvg.WALK, tvg.RUN
NONFALL_EXPECTED = tvg.NONFALL_EXPECTED
V2_GUARD_ACC, V2_GUARD_F1 = tvg.V2_GUARD_ACC, tvg.V2_GUARD_F1

# Frozen Variant G G1 base (reused unchanged for the first four terms).
BASE_LAM_S, BASE_LAM_F, BASE_LAM_T, BASE_W_WR = tvg.LAM_S, tvg.LAM_F, 1.0, 2.0
# Variant H new-term defaults (spec sec.4; only lam_b/lam_r vary per setting).
K_FRAC, GAMMA_B, GAMMA_R = 0.25, 0.5, 0.5
SETTINGS = {
    "H1": {"lam_b": 0.5, "lam_r": 0.5, "desc": "balanced dual-tail"},
    "H2": {"lam_b": 1.0, "lam_r": 0.5, "desc": "nonfall-budget-heavy"},
    "H3": {"lam_b": 0.5, "lam_r": 1.0, "desc": "fall-rescue-heavy"},
}


# --------------------------------------------------------------------------- TopK reducer (spec sec.3)
def _resolve_k(n, k_frac=None, k_abs=None):
    if n == 0:
        return 0
    k = int(k_abs) if k_abs is not None else int(math.ceil((k_frac if k_frac is not None else 1.0) * n))
    return max(1, min(k, n))


def topk_mean(values, k_frac=None, k_abs=None):
    """Mean of the K largest entries of `values` (a >=0 hinge vector). Deterministic (torch.topk);
    gradients flow only through the selected entries; empty input -> zero on the right device/dtype."""
    n = values.numel()
    if n == 0:
        return torch.zeros((), device=values.device, dtype=values.dtype)
    k = _resolve_k(n, k_frac, k_abs)
    return torch.topk(values, k, largest=True, sorted=False).values.mean()


# --------------------------------------------------------------------------- L_nonfall-budget (spec sec.3)
def nonfall_budget_loss(logits_adv, y, fall_idx, gamma_b, k_frac, source_weights=None):
    """TopKMean_{y in N}[ relu(z_f - z_y + gamma_b) ] over adversarial NON-FALL windows.
    Returns (scalar loss, diagnostics)."""
    device = logits_adv.device
    nf = y != fall_idx
    valid = int(nf.sum())
    if valid == 0:
        return torch.zeros((), device=device), {"valid": 0, "selected": 0,
                                                 "mean_raw_margin": float("nan"), "mean_selected_hinge": 0.0}
    zo = logits_adv[nf]
    zf = zo[:, fall_idx]
    zy = zo.gather(1, y[nf].unsqueeze(1)).squeeze(1)
    r = zf - zy                                   # fall-vs-true-class margin r_y
    hinge = torch.relu(r + gamma_b)
    if source_weights is not None:
        hinge = source_weights * hinge
    k = _resolve_k(hinge.numel(), k_frac=k_frac)
    L = topk_mean(hinge, k_abs=k)
    diag = {"valid": valid, "selected": int(k), "mean_raw_margin": float(r.mean().item()),
            "mean_selected_hinge": float(L.item())}
    return L, diag


# --------------------------------------------------------------------------- L_fall-rescue (spec sec.3)
def fall_rescue_loss(logits_adv, y, fall_idx, gamma_r, k_frac):
    """TopKMean_{y=f}[ relu(gamma_r + max_{c!=f} z_c - z_f) ] over the HARDEST adversarial FALL windows.
    Returns (scalar loss, diagnostics)."""
    device = logits_adv.device
    f = y == fall_idx
    valid = int(f.sum())
    if valid == 0:
        return torch.zeros((), device=device), {"valid": 0, "selected": 0,
                                                 "mean_fall_margin": float("nan"), "mean_selected_hinge": 0.0}
    zo = logits_adv[f].clone()
    zf = zo[:, fall_idx].clone()
    zo[:, fall_idx] = float("-inf")
    max_nf = zo.max(dim=1).values
    m_f = zf - max_nf                              # fall margin (positive = fall on top)
    hinge = torch.relu(gamma_r + (max_nf - zf))    # = relu(gamma_r - m_f); largest on the hardest falls
    k = _resolve_k(hinge.numel(), k_frac=k_frac)
    L = topk_mean(hinge, k_abs=k)
    diag = {"valid": valid, "selected": int(k), "mean_fall_margin": float(m_f.mean().item()),
            "mean_selected_hinge": float(L.item())}
    return L, diag


# --------------------------------------------------------------------------- all components (spec sec.3)
def variantH_margin_terms(adv_out, adv_lab, tgt_out, tgt_lab, w_wr, fall_idx,
                          gamma_b, gamma_r, k_frac, device):
    """Returns dict of the five Variant H loss components + budget/rescue diagnostics.
    Reuses Variant G for src_motion / fall_margin / targeted (unchanged)."""
    L_src, L_fall, L_tgt = tvg.variantG_margin_terms(adv_out, adv_lab, tgt_out, tgt_lab, w_wr, fall_idx, device)
    nf = adv_lab != fall_idx
    sw = tvg.source_weights(adv_lab[nf], w_wr, device) if nf.any() else None
    L_budget, d_b = nonfall_budget_loss(adv_out, adv_lab, fall_idx, gamma_b, k_frac, source_weights=sw)
    L_rescue, d_r = fall_rescue_loss(adv_out, adv_lab, fall_idx, gamma_r, k_frac)
    return {"src_motion": L_src, "fall_margin": L_fall, "targeted": L_tgt,
            "nonfall_budget": L_budget, "fall_rescue": L_rescue, "budget_diag": d_b, "rescue_diag": d_r}


def train_one_epoch_variantH(model, loader, train_criterion, atk_criterion, optimizer, device,
                             train_epsilons, train_pgd_steps, rng, tsg, lam_b, lam_r, fall_idx,
                             max_batches=None):
    """Variant G batch-split FGSM+PGD + targeted/source terms, PLUS the two Variant H TopK terms."""
    model.train()
    tot_loss = tot = 0.0
    s = {"base": 0.0, "src": 0.0, "fall": 0.0, "tgt": 0.0, "budget": 0.0, "rescue": 0.0}
    ksel = {"budget": 0, "rescue": 0}; nb = 0
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
        base = train_criterion(outputs, batch_y)
        adv_out, adv_lab = outputs[n_clean:], batch_y[n_clean:]
        tgt_out = model(tgt_adv).float() if (tgt_adv is not None and tgt_adv.numel() > 0) else None

        H = variantH_margin_terms(adv_out, adv_lab, tgt_out, tgt_lab, BASE_W_WR, fall_idx, GAMMA_B, GAMMA_R, K_FRAC, device)
        loss = (base + BASE_LAM_S * H["src_motion"] + BASE_LAM_F * H["fall_margin"] + BASE_LAM_T * H["targeted"]
                + lam_b * H["nonfall_budget"] + lam_r * H["fall_rescue"])
        loss.backward(); optimizer.step()

        tot_loss += loss.item() * bs; tot += bs; nb += 1
        s["base"] += float(base.item()); s["src"] += float(H["src_motion"].item())
        s["fall"] += float(H["fall_margin"].item()); s["tgt"] += float(H["targeted"].item())
        s["budget"] += float(H["nonfall_budget"].item()); s["rescue"] += float(H["fall_rescue"].item())
        ksel["budget"] += H["budget_diag"]["selected"]; ksel["rescue"] += H["rescue_diag"]["selected"]
    d = max(1, nb)
    return {"train_loss": tot_loss / max(1, tot), "mean_base": s["base"] / d, "mean_src_motion": s["src"] / d,
            "mean_fall_margin": s["fall"] / d, "mean_targeted": s["tgt"] / d,
            "mean_nonfall_budget": s["budget"] / d, "mean_fall_rescue": s["rescue"] / d,
            "topk_budget_selected": ksel["budget"] / d, "topk_rescue_selected": ksel["rescue"] / d, "batches": nb}


def parse_args():
    p = argparse.ArgumentParser(description="Variant H dual-tail safety-budget defense (smoke-only).")
    p.add_argument("--setting", choices=sorted(SETTINGS.keys()), required=True,
                   help="H1 balanced | H2 nonfall-budget-heavy | H3 fall-rescue-heavy")
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
    p.add_argument("--pilot", action="store_true",
                   help="run the approved H1 seed-42 full pilot (H1 + seed 42 ONLY; requires explicit --pilot)")
    return p.parse_args()


# ----------------------------------------------------------------------------- self-check (spec sec.5)
def _check_topk_correctness():
    """TopK correctness on a deterministic synthetic tensor: selection, count, empty-safe, gradient flow."""
    v = torch.tensor([0.1, 5.0, 0.2, 3.0, 0.0], requires_grad=True)
    out = topk_mean(v, k_frac=0.4)                      # k = ceil(0.4*5)=2 -> {5.0, 3.0} -> mean 4.0
    sel_ok = abs(out.item() - 4.0) < 1e-6
    out.backward()
    grad = v.grad.detach()
    # gradient should be 0.5 on the two selected (largest) entries, 0 elsewhere
    grad_ok = bool(grad[1].item() > 0 and grad[3].item() > 0 and grad[0].item() == 0
                   and grad[2].item() == 0 and grad[4].item() == 0)
    empty = topk_mean(torch.zeros(0), k_frac=0.25)
    empty_ok = (empty.item() == 0.0)
    k1 = _resolve_k(7, k_frac=0.0)                       # k>=1 when valid samples exist
    return {"select_mean_top2_is_4.0": sel_ok, "grad_only_selected": grad_ok,
            "empty_returns_zero": empty_ok, "k_at_least_1": k1 >= 1, "selected_count": _resolve_k(5, 0.4)}


def _directionality_check(device):
    """Minimizing each TopK loss moves its margin the right way, isolated on a synthetic logit tensor
    (treat logits as the optimized variable, independent of the model)."""
    fall_idx = 1
    # non-fall budget: y in N; a gradient step minimizing the loss should reduce r_y = z_f - z_y
    torch.manual_seed(0)
    Zb = torch.randn(8, 7, device=device, requires_grad=True)
    yb = torch.tensor([2, 4, 2, 4, 0, 3, 5, 6], device=device)        # all non-fall
    Lb, _ = nonfall_budget_loss(Zb, yb, fall_idx, GAMMA_B, K_FRAC, source_weights=None)
    r_before = float((Zb[:, fall_idx] - Zb.gather(1, yb[:, None]).squeeze(1)).mean().item())
    g = torch.autograd.grad(Lb, Zb)[0]
    Zb2 = (Zb - 0.5 * g).detach()
    r_after = float((Zb2[:, fall_idx] - Zb2.gather(1, yb[:, None]).squeeze(1)).mean().item())
    # fall rescue: y=f; a gradient step should increase m_f = z_f - max_{c!=f} z_c
    Zr = torch.randn(8, 7, device=device, requires_grad=True)
    yr = torch.full((8,), fall_idx, device=device)
    Lr, _ = fall_rescue_loss(Zr, yr, fall_idx, GAMMA_R, K_FRAC)
    def mf(Z):
        zo = Z.clone(); zf = zo[:, fall_idx].clone(); zo[:, fall_idx] = float("-inf")
        return float((zf - zo.max(1).values).mean().item())
    mf_before = mf(Zr)
    g2 = torch.autograd.grad(Lr, Zr)[0]
    mf_after = mf((Zr - 0.5 * g2).detach())
    return {"budget_r_before": r_before, "budget_r_after": r_after, "budget_reduced_r": r_after < r_before,
            "rescue_mf_before": mf_before, "rescue_mf_after": mf_after, "rescue_increased_mf": mf_after > mf_before}


def run_self_check(args, F):
    cfg = SETTINGS[args.setting]
    out = {"setting": args.setting, "desc": cfg["desc"]}
    print("=" * 74); print(f"Variant H --self-check  setting={args.setting} ({cfg['desc']})")
    # class constants
    assert F["fall_idx"] == 1 and F["num_classes"] == 7 and (WALK, RUN) == (2, 4)
    assert {c for c in range(7) if c != 1} == NONFALL_EXPECTED
    print(f"  class-index assertions PASSED: FALL={F['fall_idx']} NUM={F['num_classes']} WALK={WALK} RUN={RUN} nonfall={sorted(NONFALL_EXPECTED)}")
    out["class_index_ok"] = True
    # targeted-PGD sign check (reuse Variant G's; train/val data only -> no test leakage)
    sc, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
    pct = None
    print("  targeted-PGD sign check (nonfall windows):")
    print(f"    clean    median fall_logit={sc['clean_median_fall_logit']:.4f}  median P(fall)={sc['clean_median_p_fall']:.4f}")
    print(f"    targeted median fall_logit={sc['targeted_median_fall_logit']:.4f}  median P(fall)={sc['targeted_median_p_fall']:.4f}")
    print(f"    increased={sc['increased']}  (n_nonfall={sc['n_nonfall']})")
    out["sign_check"] = sc
    if not ok:
        raise SystemExit("SIGN CHECK FAILED (spec sec.5): targeted PGD did not raise fall logit/P(fall).")
    # TopK correctness
    tk = _check_topk_correctness()
    print(f"  TopK correctness: {tk}")
    assert all(tk[k] for k in ("select_mean_top2_is_4.0", "grad_only_selected", "empty_returns_zero", "k_at_least_1"))
    out["topk"] = tk
    # loss finite/nonzero on a deterministic real (train) batch
    F["model"].train()
    inputs, labels = next(iter(F["train_loader"]))
    inputs = inputs.to(F["device"]).float(); labels = labels.type(torch.LongTensor).to(F["device"])
    bs = labels.size(0); eps = float(F["rng"].choice(F["train_epsilons"])); a = eps / 4.0
    n_clean = bs // 2; n_fgsm = (bs - n_clean) // 2
    fgsm = F["tsg"].fgsm_perturb(F["model"], inputs[n_clean:n_clean + n_fgsm], labels[n_clean:n_clean + n_fgsm], F["atk_criterion"], eps)
    pgd = F["tsg"].pgd_perturb(F["model"], inputs[n_clean + n_fgsm:], labels[n_clean + n_fgsm:], F["atk_criterion"], eps, args.train_pgd_steps, a)
    nf = labels != F["fall_idx"]
    tgt_adv = tvg.targeted_fall_pgd(F["model"], inputs[nf], F["fall_idx"], F["atk_criterion"], eps, args.train_pgd_steps, a)
    outputs = F["model"](torch.cat([inputs[:n_clean], fgsm, pgd], 0)).float()
    base = F["train_criterion"](outputs, labels)
    H = variantH_margin_terms(outputs[n_clean:], labels[n_clean:], F["model"](tgt_adv).float(), labels[nf],
                              BASE_W_WR, F["fall_idx"], GAMMA_B, GAMMA_R, K_FRAC, F["device"])
    comp = {"FWCE_base": base.item(), "src_motion": H["src_motion"].item(), "fall_margin": H["fall_margin"].item(),
            "targeted": H["targeted"].item(), "nonfall_budget": H["nonfall_budget"].item(),
            "fall_rescue": H["fall_rescue"].item(), "budget_diag": H["budget_diag"], "rescue_diag": H["rescue_diag"]}
    print("  one-batch loss components:")
    for k in ("FWCE_base", "src_motion", "fall_margin", "targeted", "nonfall_budget", "fall_rescue"):
        print(f"    {k:16s} = {comp[k]:.5f}")
    print(f"    budget_diag = {comp['budget_diag']}")
    print(f"    rescue_diag = {comp['rescue_diag']}")
    for k in ("FWCE_base", "src_motion", "fall_margin", "targeted", "nonfall_budget", "fall_rescue"):
        assert np.isfinite(comp[k]), f"{k} not finite"
    assert comp["nonfall_budget"] > 0, "nonfall_budget must be > 0 when nonfall examples exist"
    assert comp["fall_rescue"] > 0, "fall_rescue must be > 0 when fall examples exist"
    if comp["budget_diag"]["valid"] > 0:
        assert comp["rescue_diag"]["valid"] >= 0
    out["components"] = comp
    # directionality
    dc = _directionality_check(F["device"])
    print("  directionality checks:")
    print(f"    nonfall-budget: r_y {dc['budget_r_before']:.4f} -> {dc['budget_r_after']:.4f}  reduced={dc['budget_reduced_r']}")
    print(f"    fall-rescue:    m_f {dc['rescue_mf_before']:.4f} -> {dc['rescue_mf_after']:.4f}  increased={dc['rescue_increased_mf']}")
    assert dc["budget_reduced_r"], "minimizing nonfall_budget must reduce (z_f - z_y)"
    assert dc["rescue_increased_mf"], "minimizing fall_rescue must increase (z_f - max_nonfall)"
    out["directionality"] = dc
    out["no_test_leakage"] = "self-check used train batches + a synthetic directionality probe only; test set untouched"
    print("  PASS: class indices, sign check, TopK, finite/nonzero losses, directionality all OK.")
    print("=" * 74)
    return out


def run_smoke(args, F):
    cfg = SETTINGS[args.setting]; tsg, s1 = F["tsg"], F["s1"]
    run = f"seed{args.seed}_variantH_{args.setting}_smoke"
    base = F["exp"] / "results" / "safety_guided_defense" / "variantH_dual_tail_budget" / "_smoke" / f"seed{args.seed}"
    base.mkdir(parents=True, exist_ok=True)
    print("=" * 74); print(f"Variant H --smoke  setting={args.setting} ({cfg['desc']})  run={run}")
    print(f"  base(VariantG G1): lam_s={BASE_LAM_S} lam_f={BASE_LAM_F} lam_t={BASE_LAM_T} w_wr={BASE_W_WR} | "
          f"NEW lam_b={cfg['lam_b']} lam_r={cfg['lam_r']} k_frac={K_FRAC} gamma_b={GAMMA_B} gamma_r={GAMMA_R} | "
          f"epochs={args.epochs} smoke_batches={args.smoke_batches}")
    history = []; start = time.time(); collapse = False; fp_drop_by_collapse = False
    for epoch in range(1, args.epochs + 1):
        tr = train_one_epoch_variantH(F["model"], F["train_loader"], F["train_criterion"], F["atk_criterion"],
                                      F["optimizer"], F["device"], F["train_epsilons"], args.train_pgd_steps,
                                      F["rng"], tsg, cfg["lam_b"], cfg["lam_r"], F["fall_idx"],
                                      max_batches=args.smoke_batches)
        vb = tsg.compute_validation_bundle(s1, F["model"], F["val_loader"], F["atk_criterion"], F["device"])
        acc, f1 = vb["val_clean_accuracy"], vb["val_clean_macro_f1"]
        rec, fpv = vb["val_pgd_fall_recall"], vb["val_pgd_false_fall_alarms"]
        clean_fr = vb["val_clean_fall_recall"]
        collapse = collapse or (clean_fr < 0.50)
        fp_drop_by_collapse = fp_drop_by_collapse or (fpv == 0 and rec == 0)
        for k in ("train_loss", "mean_base", "mean_src_motion", "mean_fall_margin", "mean_targeted",
                  "mean_nonfall_budget", "mean_fall_rescue"):
            assert np.isfinite(tr[k]), f"{k} not finite at epoch {epoch} (smoke failure: NaN/inf)"
        history.append({"epoch": epoch, **{k: tr[k] for k in tr if k != "batches"},
                        "val_clean_accuracy": acc, "val_clean_macro_f1": f1, "val_clean_fall_recall": clean_fr,
                        "val_pgd_fall_recall": rec, "val_pgd_false_fall_alarms": fpv})
        print(f"  epoch {epoch}/{args.epochs} | loss={tr['train_loss']:.3f} base={tr['mean_base']:.3f} "
              f"src={tr['mean_src_motion']:.3f} fall={tr['mean_fall_margin']:.3f} tgt={tr['mean_targeted']:.3f} "
              f"budget={tr['mean_nonfall_budget']:.3f} rescue={tr['mean_fall_rescue']:.3f} "
              f"| ksel(b/r)={tr['topk_budget_selected']:.1f}/{tr['topk_rescue_selected']:.1f} "
              f"| acc={acc:.3f} f1={f1:.3f} cleanFR={clean_fr:.3f} pgd_fr={rec:.3f} pgd_FP={fpv}")
    elapsed = time.time() - start
    with (base / f"{run}_log.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(history[0].keys())); w.writeheader()
        for r in history:
            w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in history[0]})
    summary = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "stage": "variantH_smoke",
               "setting": args.setting, "desc": cfg["desc"], "seed": args.seed,
               "lam_s": BASE_LAM_S, "lam_f": BASE_LAM_F, "lam_t": BASE_LAM_T, "w_wr": BASE_W_WR,
               "lam_b": cfg["lam_b"], "lam_r": cfg["lam_r"], "k_frac": K_FRAC, "gamma_b": GAMMA_B, "gamma_r": GAMMA_R,
               "epochs": args.epochs, "smoke_batches": args.smoke_batches, "elapsed_seconds": elapsed,
               "final": {k: history[-1][k] for k in ("train_loss", "mean_nonfall_budget", "mean_fall_rescue",
                                                     "val_clean_fall_recall", "val_pgd_fall_recall", "val_pgd_false_fall_alarms")},
               "clean_fall_recall_collapsed": bool(collapse),
               "fp_dropped_only_by_recall_collapse": bool(fp_drop_by_collapse),
               "test_set_used": False, "device": str(F["device"]),
               "python_version": platform.python_version(), "torch_version": torch.__version__,
               "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(F["exp"])),
               "note": ("SMOKE ONLY -- code-correctness check, NOT a pilot or convergence result. "
                        "The epoch-2 clean_fall_recall_collapsed flag is the EXPECTED cold-start "
                        "(Variant G/G1 began identically, recall 0 until it recovered around epoch 27); "
                        "it is NOT a convergence conclusion. No full-training / pilot conclusion may be "
                        "drawn from smoke results. No .pt persisted; no scientific claim is made.")}
    with (base / f"{run}_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  smoke done in {elapsed:.1f}s | clean_fall_recall_collapsed={collapse} "
          f"fp_dropped_only_by_recall_collapse={fp_drop_by_collapse}")
    print(f"  summary -> {base / (run + '_summary.json')}")
    print("=" * 74)
    return summary


def run_pilot(args, F):
    """Approved H1 seed-42 full pilot. Mirrors the frozen Variant G selection-v2 run_full protocol
    (guard 0.70/0.65; candidates v2safety/v2maxrec/v2lowFA/v2macroF1; same epochs/patience), only the
    per-batch loss adds the two Variant H TopK terms. Writes to the variantH H1/seed42 namespace.
    Hard-asserts H1+seed42 and stops immediately on NaN/inf or always-zero TopK terms (spec sec.4)."""
    assert args.setting == "H1" and args.seed == 42, "pilot is H1 + seed 42 ONLY"
    cfg = SETTINGS[args.setting]; tsg, s1 = F["tsg"], F["s1"]; device = F["device"]
    run = f"seed{args.seed}_variantH_{args.setting}"
    base = F["exp"] / "results" / "safety_guided_defense" / "variantH_dual_tail_budget" / args.setting / f"seed{args.seed}"
    ck_dir = F["exp"] / "checkpoints" / "safety_guided_defense" / "variantH_dual_tail_budget" / args.setting / f"seed{args.seed}"
    logs_dir = base / "logs"; ana_dir = base / "analysis"; meta_dir = base / "metadata"
    for d in (ck_dir, logs_dir, ana_dir, meta_dir):
        d.mkdir(parents=True, exist_ok=True)
    ck = {k: ck_dir / f"{run}_{k}_best.pt" for k in ("v2safety", "v2maxrec", "v2lowFA", "v2macroF1")}
    ck_last = ck_dir / f"{run}_last.pt"

    print("=" * 74)
    print(f"Variant H FULL PILOT  setting={args.setting} ({cfg['desc']})  run={run}")
    print(f"  base(VariantG G1): lam_s={BASE_LAM_S} lam_f={BASE_LAM_F} lam_t={BASE_LAM_T} w_wr={BASE_W_WR} | "
          f"NEW lam_b={cfg['lam_b']} lam_r={cfg['lam_r']} k_frac={K_FRAC} gamma_b={GAMMA_B} gamma_r={GAMMA_R} fw={args.fall_weight}")
    print(f"  guard acc>={V2_GUARD_ACC} & mF1>={V2_GUARD_F1} | epochs={args.epochs} patience={args.patience} "
          f"min={args.min_epochs} eps={F['train_epsilons']}")
    print("=" * 74)

    history = []
    best = {"v2safety": (-1e9, -1), "v2maxrec": ((-1e9, 1e9), -1),
            "v2lowFA": ((1e9, -1e9), -1), "v2macroF1": (-1e9, -1)}
    best_rec = {}; no_improve = 0; start = time.time()
    budget_ever_nz = rescue_ever_nz = False

    for epoch in range(1, args.epochs + 1):
        tr = train_one_epoch_variantH(F["model"], F["train_loader"], F["train_criterion"], F["atk_criterion"],
                                      F["optimizer"], device, F["train_epsilons"], args.train_pgd_steps,
                                      F["rng"], tsg, cfg["lam_b"], cfg["lam_r"], F["fall_idx"], max_batches=None)
        # spec sec.4 numerical stop conditions
        for k in ("train_loss", "mean_base", "mean_src_motion", "mean_fall_margin", "mean_targeted",
                  "mean_nonfall_budget", "mean_fall_rescue"):
            if not np.isfinite(tr[k]):
                raise SystemExit(f"STOP (numerical): {k} not finite at epoch {epoch} (NaN/inf).")
        budget_ever_nz = budget_ever_nz or (tr["mean_nonfall_budget"] > 0)
        rescue_ever_nz = rescue_ever_nz or (tr["mean_fall_rescue"] > 0)

        vb = tsg.compute_validation_bundle(s1, F["model"], F["val_loader"], F["atk_criterion"], device)
        sc = tvg.safety_score(vb)
        acc = vb["val_clean_accuracy"]; f1 = vb["val_clean_macro_f1"]
        rec = vb["val_pgd_fall_recall"]; fpv = vb["val_pgd_false_fall_alarms"]
        eligible = (acc >= V2_GUARD_ACC and f1 >= V2_GUARD_F1)

        def save(key):
            torch.save({"epoch": epoch, "model_state_dict": F["model"].state_dict(), "selection_method": key,
                        "val_bundle": vb, "safety_score": sc, "run_name": run, "args": vars(args)}, ck[key])

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
                        "mean_targeted": tr["mean_targeted"], "mean_nonfall_budget": tr["mean_nonfall_budget"],
                        "mean_fall_rescue": tr["mean_fall_rescue"], "topk_budget_selected": tr["topk_budget_selected"],
                        "topk_rescue_selected": tr["topk_rescue_selected"], "val_clean_accuracy": acc, "val_clean_macro_f1": f1,
                        "val_clean_fall_recall": vb["val_clean_fall_recall"], "val_fgsm_fall_recall": vb["val_fgsm_fall_recall"],
                        "val_pgd_fall_recall": rec, "val_fgsm_false_fall_alarms": vb["val_fgsm_false_fall_alarms"],
                        "val_pgd_false_fall_alarms": fpv, "val_normalized_false_alarm_burden": vb["val_normalized_false_alarm_burden"],
                        "safety_score": sc, "v2_eligible": int(eligible),
                        "sel_v2safety": flags["v2safety"], "sel_v2maxrec": flags["v2maxrec"],
                        "sel_v2lowFA": flags["v2lowFA"], "sel_v2macroF1": flags["v2macroF1"]})
        print(f"Epoch {epoch:03d}/{args.epochs} | loss={tr['train_loss']:.3f} base={tr['mean_base']:.3f} "
              f"src={tr['mean_src_motion']:.3f} fall={tr['mean_fall_margin']:.3f} tgt={tr['mean_targeted']:.3f} "
              f"budget={tr['mean_nonfall_budget']:.3f} rescue={tr['mean_fall_rescue']:.3f} "
              f"ksel={tr['topk_budget_selected']:.1f}/{tr['topk_rescue_selected']:.1f} | "
              f"acc={acc:.3f} f1={f1:.3f} cleanFR={vb['val_clean_fall_recall']:.3f} pgd_fr={rec:.3f} pgd_FP={fpv} "
              f"score={sc:.3f} v2elig={int(eligible)} "
              f"[{'S' if flags['v2safety'] else '.'}{'R' if flags['v2maxrec'] else '.'}"
              f"{'L' if flags['v2lowFA'] else '.'}{'F' if flags['v2macroF1'] else '.'}]")
        if args.patience > 0 and epoch >= args.min_epochs and no_improve >= args.patience:
            print(f"Early stopping at epoch {epoch} (best v2safety epoch {best['v2safety'][1]})."); break

    # spec sec.4: always-zero TopK term despite valid examples is a stop/flag condition
    if not budget_ever_nz:
        raise SystemExit("STOP: nonfall_budget was always zero across training despite valid nonfall examples.")
    if not rescue_ever_nz:
        raise SystemExit("STOP: fall_rescue was always zero across training despite valid fall examples.")

    elapsed = time.time() - start
    last_epoch = history[-1]["epoch"]
    torch.save({"epoch": last_epoch, "model_state_dict": F["model"].state_dict(),
                "selection_method": "last", "run_name": run, "args": vars(args)}, ck_last)
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
    meta = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "stage": "variantH_H1_seed42_pilot",
            "run_name": run, "setting": args.setting, "setting_desc": cfg["desc"], "seed": args.seed,
            "lam_s": BASE_LAM_S, "lam_f": BASE_LAM_F, "lam_t": BASE_LAM_T, "w_wr": BASE_W_WR,
            "lam_b": cfg["lam_b"], "lam_r": cfg["lam_r"], "k_frac": K_FRAC, "gamma_b": GAMMA_B, "gamma_r": GAMMA_R,
            "fall_weight": args.fall_weight,
            "objective": "L_FWCE + lam_s*src + lam_f*fall + lam_t*tgt (Variant G G1) "
                         "+ lam_b*TopKMean[relu(z_f-z_y+gb)][adv nonfall, src-weighted] "
                         "+ lam_r*TopKMean[relu(gr+max_nonfall-z_f)][adv fall]",
            "v2_guard": {"min_clean_accuracy": V2_GUARD_ACC, "min_clean_macro_f1": V2_GUARD_F1},
            "train_epsilons": F["train_epsilons"], "train_pgd_steps": args.train_pgd_steps,
            "epochs_run": last_epoch, "split_sizes": F["split_sizes"], "test_set_used": False,
            "selected_epochs": {k: best[k][1] for k in ck}, "checkpoints": {k: str(v) for k, v in ck.items()},
            "claim_boundary": "window-level digital-domain white-box; H1/seed42/LeNet only; not solved/certified/clinical/OTA",
            "device": str(device), "python_version": platform.python_version(), "torch_version": torch.__version__,
            "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(F["exp"])), "elapsed_seconds": elapsed}
    with (meta_dir / f"{run}_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("-" * 74)
    print(f"Done in {elapsed:.1f}s ({last_epoch} epochs). selected epochs: " + ", ".join(f"{k}={best[k][1]}" for k in ck))
    print("=" * 74)


def main():
    args = parse_args()
    if args.seed != 42:
        raise SystemExit(f"Variant H is seed-42 ONLY for now (got seed {args.seed}); seeds 44/45/46 are "
                         "blocked. seed-44 requires a separate committed pre-registration (spec sec.8).")
    if args.setting not in SETTINGS:
        raise SystemExit(f"Disallowed setting {args.setting!r}; permitted: {sorted(SETTINGS)}.")
    F = tvg.load_foundation(args)
    if args.self_check:
        out = run_self_check(args, F)
        base = F["exp"] / "results" / "safety_guided_defense" / "variantH_dual_tail_budget" / "_smoke" / f"seed{args.seed}"
        base.mkdir(parents=True, exist_ok=True)
        with (base / f"seed{args.seed}_variantH_{args.setting}_selfcheck.json").open("w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=float)
        return
    if args.smoke:
        if args.setting != "H1":
            raise SystemExit("Smoke is restricted to setting H1 (spec sec.6); H2/H3 are defined but not run.")
        _, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
        if not ok:
            raise SystemExit("SIGN CHECK FAILED before smoke (spec sec.5).")
        run_smoke(args, F); return
    if args.pilot:
        # ----- APPROVED H1 seed-42 pilot ONLY (code-review Decision A). H1+seed42 hard-required. -----
        if args.setting != "H1":
            raise SystemExit("Pilot is restricted to setting H1 (code-review Decision A); H2/H3 are NOT "
                             "approved to run. Re-review required before any H2/H3 pilot.")
        _, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
        if not ok:
            raise SystemExit("SIGN CHECK FAILED before pilot (spec sec.5).")
        run_pilot(args, F); return
    # ----- full training without --pilot: still GATED (no general full-training mode) -----
    raise SystemExit("Full Variant H training is intentionally gated. Pass --self-check, --smoke, or the "
                     "approved --pilot (H1+seed42 only). General full-training mode is not available.")


if __name__ == "__main__":
    main()
