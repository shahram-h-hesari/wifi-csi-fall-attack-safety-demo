"""
Safety-TRADES pilot / BASAT Stage 1 -- frozen G1 objective + a TRADES-style fall-probability
clean/adversarial CONSISTENCY term. This is NOT the full Boundary-Aware Selective AT (BASAT)
method: there is no SAT selection, no GAIRAT geometry weighting, and no MART reweighting here.
Stage 1 isolates the single TRADES-inspired ingredient (the only one that regularizes the boundary
rather than reweighting CE) to test whether it moves the PGD-conditional fall frontier.

Objective (per batch):
    L = L_G1                                   (frozen Variant G G1 objective, UNCHANGED)
      + beta * L_fallconsist
where L_G1 = L_FWCE + lam_s*L_src + lam_f*L_fall + lam_t*L_tgt  (tvg.variantG_margin_terms, G1 setting)
and   L_fallconsist = mean_{i in adv sub-batch, y_i = fall} ( sg[p_f(x_i^clean)] - p_f(x_i^adv) )^2
      (squared difference of FALL probability; clean side stop-gradient = fixed TRADES target;
       directly penalizes PGD dragging fall probability down on TRUE fall windows).

The clean side p_f(x_clean) is computed under no_grad on the adversarial sub-batch's pre-perturbation
sources (the same windows that become x_adv), so the pairing is per-window and the term costs one
extra grad-free forward on ~50% of the batch.

Scope: seed 42 ONLY, LeNet only, same UT-HAR/SenseFi split, same FGSM/PGD eps=0.030, same clean guard
and selection-v2 checkpoint rule as G1. Window-level, digital-domain, white-box; NOT solved/certified/
clinical/over-the-air. Validation-only for beta / go-no-go. NO test set used in training or selection.

Modes:
    --self-check  class asserts + targeted-PGD sign check + finite/nonzero loss decomposition +
                  consistency directionality check (minimizing L_fallconsist raises adv p_f). No training, no .pt.
    --smoke       2-epoch tiny seed-42 run to a `_smoke` namespace (code correctness only; no claims).
    --pilot       approved seed-42 full pilot (selection-v2; writes to the boundary_aware_selective_at namespace).
    (default)     GATED -- refuses to launch without a mode flag.

Commands:
    python scripts/train_basat.py --beta 3.0 --self-check
    python scripts/train_basat.py --beta 3.0 --smoke --epochs 2 --smoke-batches 5
    python scripts/train_basat.py --beta 3.0 --pilot
"""
from __future__ import annotations
from pathlib import Path
import argparse, csv, json, platform, sys, time
from datetime import datetime, timezone
import numpy as np
import torch


def import_variantG():
    sd = Path(__file__).resolve().parent
    if str(sd) not in sys.path:
        sys.path.insert(0, str(sd))
    import train_variantG_targeted_hardneg as tvg
    return tvg


tvg = import_variantG()
V2_GUARD_ACC, V2_GUARD_F1 = tvg.V2_GUARD_ACC, tvg.V2_GUARD_F1
# Frozen G1 base (reused unchanged): lam_s=lam_f=1.0, lam_t=1.0, w_wr=2.0, gammas=0.5, fall_weight=3.
G1 = tvg.SETTINGS["G1"]            # {"lam_t":1.0,"w_wr":2.0,...}
BASE_LAM_S, BASE_LAM_F = tvg.LAM_S, tvg.LAM_F
BASE_LAM_T, BASE_W_WR = G1["lam_t"], G1["w_wr"]
ALLOWED_BETAS = (1.0, 3.0, 6.0)


# --------------------------------------------------------------------------- L_fallconsist (TRADES-style)
def fall_consistency_loss(p_f_clean_detached, p_f_adv, adv_labels, fall_idx):
    """mean over adv TRUE-FALL windows of (sg[p_f_clean] - p_f_adv)^2. Empty -> 0. Returns (loss, diag)."""
    f = adv_labels == fall_idx
    valid = int(f.sum())
    if valid == 0:
        return torch.zeros((), device=p_f_adv.device), {"valid": 0, "mean_p_f_clean": float("nan"),
                                                         "mean_p_f_adv": float("nan"), "mean_sq_gap": 0.0}
    pc = p_f_clean_detached[f]
    pa = p_f_adv[f]
    L = ((pc - pa) ** 2).mean()
    diag = {"valid": valid, "mean_p_f_clean": float(pc.mean().item()),
            "mean_p_f_adv": float(pa.mean().item()), "mean_sq_gap": float(L.item())}
    return L, diag


def train_one_epoch_basat(model, loader, train_criterion, atk_criterion, optimizer, device,
                          train_epsilons, train_pgd_steps, rng, tsg, beta, fall_idx, max_batches=None):
    """G1 batch-split FGSM+PGD + G1 margin terms (unchanged) PLUS beta*L_fallconsist."""
    model.train()
    tot_loss = tot = 0.0
    s = {"base": 0.0, "src": 0.0, "fall": 0.0, "tgt": 0.0, "consist": 0.0}
    cdiag = {"pc": 0.0, "pa": 0.0, "nfall": 0.0}
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
        # clean-side fall probability for the adv sub-batch sources (stop-grad TRADES target).
        adv_sources = inputs[n_clean:]                      # the windows that became fgsm_adv|pgd_adv
        with torch.no_grad():
            p_f_clean = torch.softmax(model(adv_sources).float(), dim=1)[:, fall_idx]
        model.train()

        batch_x = torch.cat([clean_x, fgsm_adv, pgd_adv], dim=0)
        batch_y = labels
        n_clean = clean_x.size(0)

        optimizer.zero_grad()
        outputs = model(batch_x).float()
        base = train_criterion(outputs, batch_y)
        adv_out, adv_lab = outputs[n_clean:], batch_y[n_clean:]
        tgt_out = model(tgt_adv).float() if (tgt_adv is not None and tgt_adv.numel() > 0) else None

        L_src, L_fall, L_tgt = tvg.variantG_margin_terms(adv_out, adv_lab, tgt_out, tgt_lab, BASE_W_WR, fall_idx, device)
        p_f_adv = torch.softmax(adv_out, dim=1)[:, fall_idx]
        L_consist, dcon = fall_consistency_loss(p_f_clean, p_f_adv, adv_lab, fall_idx)

        loss = base + BASE_LAM_S * L_src + BASE_LAM_F * L_fall + BASE_LAM_T * L_tgt + beta * L_consist
        loss.backward(); optimizer.step()

        tot_loss += loss.item() * bs; tot += bs; nb += 1
        s["base"] += float(base.item()); s["src"] += float(L_src.item())
        s["fall"] += float(L_fall.item()); s["tgt"] += float(L_tgt.item()); s["consist"] += float(L_consist.item())
        if dcon["valid"] > 0:
            cdiag["pc"] += dcon["mean_p_f_clean"]; cdiag["pa"] += dcon["mean_p_f_adv"]; cdiag["nfall"] += 1
    d = max(1, nb); df = max(1, cdiag["nfall"])
    return {"train_loss": tot_loss / max(1, tot), "mean_base": s["base"] / d,
            "mean_src_motion": s["src"] / d, "mean_fall_margin": s["fall"] / d,
            "mean_targeted": s["tgt"] / d, "mean_fallconsist": s["consist"] / d,
            "consist_p_f_clean": cdiag["pc"] / df, "consist_p_f_adv": cdiag["pa"] / df, "batches": nb}


def parse_args():
    p = argparse.ArgumentParser(description="Safety-TRADES pilot / BASAT Stage 1 (G1 + fall-prob consistency).")
    p.add_argument("--beta", type=float, required=True, help="weight of L_fallconsist; run 3.0 first")
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
    p.add_argument("--pilot", action="store_true", help="approved seed-42 full pilot")
    return p.parse_args()


def _beta_tag(beta):
    return f"beta{str(beta).replace('.', 'p')}"


# ----------------------------------------------------------------------------- self-check
def run_self_check(args, F):
    print("=" * 78); print(f"Safety-TRADES / BASAT Stage 1 --self-check  beta={args.beta}")
    assert F["fall_idx"] == 1 and F["num_classes"] == 7 and (tvg.WALK, tvg.RUN) == (2, 4)
    print(f"  class-index assertions PASSED: FALL={F['fall_idx']} NUM={F['num_classes']} "
          f"WALK={tvg.WALK} RUN={tvg.RUN}")
    sc, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
    print(f"  targeted-PGD sign check: clean P(fall)={sc['clean_median_p_fall']:.4f} -> "
          f"targeted P(fall)={sc['targeted_median_p_fall']:.4f}  increased={sc['increased']}")
    if not ok:
        raise SystemExit("SIGN CHECK FAILED (targeted PGD did not raise fall logit/P(fall)).")
    # one-batch loss decomposition
    F["model"].train()
    inputs, labels = next(iter(F["train_loader"]))
    inputs = inputs.to(F["device"]).float(); labels = labels.type(torch.LongTensor).to(F["device"])
    bs = labels.size(0); eps = float(F["rng"].choice(F["train_epsilons"])); a = eps / 4.0
    n_clean = bs // 2; n_fgsm = (bs - n_clean) // 2
    fgsm = F["tsg"].fgsm_perturb(F["model"], inputs[n_clean:n_clean + n_fgsm], labels[n_clean:n_clean + n_fgsm], F["atk_criterion"], eps)
    pgd = F["tsg"].pgd_perturb(F["model"], inputs[n_clean + n_fgsm:], labels[n_clean + n_fgsm:], F["atk_criterion"], eps, args.train_pgd_steps, a)
    nf = labels != F["fall_idx"]
    tgt_adv = tvg.targeted_fall_pgd(F["model"], inputs[nf], F["fall_idx"], F["atk_criterion"], eps, args.train_pgd_steps, a)
    with torch.no_grad():
        p_f_clean = torch.softmax(F["model"](inputs[n_clean:]).float(), 1)[:, F["fall_idx"]]
    outputs = F["model"](torch.cat([inputs[:n_clean], fgsm, pgd], 0)).float()
    base = F["train_criterion"](outputs, labels)
    L_src, L_fall, L_tgt = tvg.variantG_margin_terms(outputs[n_clean:], labels[n_clean:],
                                                     F["model"](tgt_adv).float(), labels[nf], BASE_W_WR, F["fall_idx"], F["device"])
    p_f_adv = torch.softmax(outputs[n_clean:], 1)[:, F["fall_idx"]]
    L_consist, dcon = fall_consistency_loss(p_f_clean, p_f_adv, labels[n_clean:], F["fall_idx"])
    comp = {"FWCE_base": base.item(), "L_src": L_src.item(), "L_fall": L_fall.item(),
            "L_tgt": L_tgt.item(), "L_fallconsist": L_consist.item(), "consist_diag": dcon}
    print("  one-batch loss components:")
    for k in ("FWCE_base", "L_src", "L_fall", "L_tgt", "L_fallconsist"):
        print(f"    {k:14s} = {comp[k]:.5f}")
    print(f"    consist_diag = {dcon}")
    for k in ("FWCE_base", "L_src", "L_fall", "L_tgt", "L_fallconsist"):
        assert np.isfinite(comp[k]), f"{k} not finite"
    assert comp["L_tgt"] > 0, "L_tgt must be > 0 on targeted nonfall examples"
    # directionality: a gradient step minimizing ONLY beta*L_fallconsist should raise adv p_f toward clean p_f
    f = labels[n_clean:] == F["fall_idx"]
    if int(f.sum()) > 0:
        logits = outputs[n_clean:].detach().clone().requires_grad_(True)
        pfa = torch.softmax(logits, 1)[:, F["fall_idx"]]
        Lc, _ = fall_consistency_loss(p_f_clean, pfa, labels[n_clean:], F["fall_idx"])
        g = torch.autograd.grad(Lc, logits)[0]
        pfa_after = torch.softmax((logits - 0.5 * g).detach(), 1)[:, F["fall_idx"]]
        before = float(pfa[f].mean().item()); after = float(pfa_after[f].mean().item())
        gap_before = float((p_f_clean[f] - pfa[f]).abs().mean().item())
        gap_after = float((p_f_clean[f] - pfa_after[f]).abs().mean().item())
        print(f"  directionality: adv p_f {before:.4f} -> {after:.4f} (clean target {float(p_f_clean[f].mean()):.4f}); "
              f"|gap| {gap_before:.4f} -> {gap_after:.4f}")
        assert gap_after < gap_before + 1e-9, "minimizing L_fallconsist must not increase the clean/adv fall-prob gap"
    print("  PASS: class indices, sign check, finite losses, L_tgt>0, consistency directionality OK.")
    print("=" * 78)
    return comp


def run_smoke(args, F):
    tsg, s1 = F["tsg"], F["s1"]
    btag = _beta_tag(args.beta)
    run = f"seed{args.seed}_basat_stage1_{btag}_smoke"
    base = F["exp"] / "results" / "safety_guided_defense" / "boundary_aware_selective_at" / "_smoke" / f"seed{args.seed}"
    base.mkdir(parents=True, exist_ok=True)
    print("=" * 78); print(f"Safety-TRADES / BASAT Stage 1 --smoke  beta={args.beta}  run={run}")
    print(f"  G1 base: lam_s={BASE_LAM_S} lam_f={BASE_LAM_F} lam_t={BASE_LAM_T} w_wr={BASE_W_WR} | "
          f"NEW beta={args.beta} | epochs={args.epochs} smoke_batches={args.smoke_batches}")
    history = []; start = time.time()
    for epoch in range(1, args.epochs + 1):
        tr = train_one_epoch_basat(F["model"], F["train_loader"], F["train_criterion"], F["atk_criterion"],
                                   F["optimizer"], F["device"], F["train_epsilons"], args.train_pgd_steps,
                                   F["rng"], tsg, args.beta, F["fall_idx"], max_batches=args.smoke_batches)
        vb = tsg.compute_validation_bundle(s1, F["model"], F["val_loader"], F["atk_criterion"], F["device"])
        for k in ("train_loss", "mean_base", "mean_src_motion", "mean_fall_margin", "mean_targeted", "mean_fallconsist"):
            assert np.isfinite(tr[k]), f"{k} not finite at epoch {epoch}"
        row = {"epoch": epoch, **{k: tr[k] for k in tr if k != "batches"},
               "val_clean_accuracy": vb["val_clean_accuracy"], "val_clean_macro_f1": vb["val_clean_macro_f1"],
               "val_clean_fall_recall": vb["val_clean_fall_recall"], "val_pgd_fall_recall": vb["val_pgd_fall_recall"],
               "val_pgd_false_fall_alarms": vb["val_pgd_false_fall_alarms"]}
        history.append(row)
        print(f"  epoch {epoch}/{args.epochs} | loss={tr['train_loss']:.3f} base={tr['mean_base']:.3f} "
              f"src={tr['mean_src_motion']:.3f} fall={tr['mean_fall_margin']:.3f} tgt={tr['mean_targeted']:.3f} "
              f"consist={tr['mean_fallconsist']:.4f} (pf_cl={tr['consist_p_f_clean']:.3f}->pf_adv={tr['consist_p_f_adv']:.3f}) "
              f"| acc={vb['val_clean_accuracy']:.3f} cFR={vb['val_clean_fall_recall']:.3f} "
              f"pgd_fr={vb['val_pgd_fall_recall']:.3f} pgd_FP={vb['val_pgd_false_fall_alarms']}")
    elapsed = time.time() - start
    with (base / f"{run}_log.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(history[0].keys())); w.writeheader()
        for r in history:
            w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in history[0]})
    summary = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "stage": "basat_stage1_smoke",
               "method": "Safety-TRADES (G1 + beta*fall-prob consistency)", "beta": args.beta, "seed": args.seed,
               "epochs": args.epochs, "smoke_batches": args.smoke_batches, "elapsed_seconds": elapsed,
               "per_epoch_seconds_estimate": elapsed / max(1, args.epochs),
               "final": {k: history[-1][k] for k in ("train_loss", "mean_fallconsist", "consist_p_f_clean",
                                                     "consist_p_f_adv", "val_clean_fall_recall",
                                                     "val_pgd_fall_recall", "val_pgd_false_fall_alarms")},
               "test_set_used": False, "device": str(F["device"]),
               "python_version": platform.python_version(), "torch_version": torch.__version__,
               "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(F["exp"])),
               "note": "SMOKE ONLY -- code-correctness + runtime estimate; NOT a pilot/convergence result; no .pt persisted."}
    with (base / f"{run}_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  smoke done in {elapsed:.1f}s ({summary['per_epoch_seconds_estimate']:.2f}s/epoch on {args.smoke_batches} batches)")
    print(f"  summary -> {base / (run + '_summary.json')}")
    print("=" * 78)
    return summary


def run_pilot(args, F):
    """Approved seed-42 full pilot. Mirrors G1 run_full selection-v2 EXACTLY; only the per-batch loss
    adds beta*L_fallconsist. Writes to the boundary_aware_selective_at/seed42 namespace (non-overwriting)."""
    assert args.seed == 42, "pilot is seed 42 ONLY"
    tsg, s1 = F["tsg"], F["s1"]; device = F["device"]
    btag = _beta_tag(args.beta)
    run = f"seed{args.seed}_basat_stage1_{btag}"
    base = F["exp"] / "results" / "safety_guided_defense" / "boundary_aware_selective_at" / f"seed{args.seed}" / btag
    ck_dir = F["exp"] / "checkpoints" / "safety_guided_defense" / "boundary_aware_selective_at" / f"seed{args.seed}" / btag
    logs_dir = base / "logs"; ana_dir = base / "analysis"; meta_dir = base / "metadata"
    for d in (ck_dir, logs_dir, ana_dir, meta_dir):
        d.mkdir(parents=True, exist_ok=True)
    ck = {k: ck_dir / f"{run}_{k}_best.pt" for k in ("v2safety", "v2maxrec", "v2lowFA", "v2macroF1")}
    ck_last = ck_dir / f"{run}_last.pt"

    print("=" * 78)
    print(f"Safety-TRADES / BASAT Stage 1 FULL PILOT  beta={args.beta}  run={run}")
    print(f"  G1 base: lam_s={BASE_LAM_S} lam_f={BASE_LAM_F} lam_t={BASE_LAM_T} w_wr={BASE_W_WR} fw={args.fall_weight} | NEW beta={args.beta}")
    print(f"  guard acc>={V2_GUARD_ACC} & mF1>={V2_GUARD_F1} | epochs={args.epochs} patience={args.patience} "
          f"min={args.min_epochs} eps={F['train_epsilons']}")
    print("=" * 78)

    history = []
    best = {"v2safety": (-1e9, -1), "v2maxrec": ((-1e9, 1e9), -1),
            "v2lowFA": ((1e9, -1e9), -1), "v2macroF1": (-1e9, -1)}
    best_rec = {}; no_improve = 0; start = time.time(); consist_ever_nz = False

    for epoch in range(1, args.epochs + 1):
        tr = train_one_epoch_basat(F["model"], F["train_loader"], F["train_criterion"], F["atk_criterion"],
                                   F["optimizer"], device, F["train_epsilons"], args.train_pgd_steps,
                                   F["rng"], tsg, args.beta, F["fall_idx"], max_batches=None)
        for k in ("train_loss", "mean_base", "mean_src_motion", "mean_fall_margin", "mean_targeted", "mean_fallconsist"):
            if not np.isfinite(tr[k]):
                raise SystemExit(f"STOP (numerical): {k} not finite at epoch {epoch}.")
        consist_ever_nz = consist_ever_nz or (tr["mean_fallconsist"] > 0)

        vb = tsg.compute_validation_bundle(s1, F["model"], F["val_loader"], F["atk_criterion"], device)
        sc = tvg.safety_score(vb)
        acc = vb["val_clean_accuracy"]; f1 = vb["val_clean_macro_f1"]
        rec = vb["val_pgd_fall_recall"]; fpv = vb["val_pgd_false_fall_alarms"]
        eligible = (acc >= V2_GUARD_ACC and f1 >= V2_GUARD_F1)

        def save(key):
            torch.save({"epoch": epoch, "model_state_dict": F["model"].state_dict(), "selection_method": key,
                        "val_bundle": vb, "safety_score": sc, "run_name": run, "beta": args.beta,
                        "args": vars(args)}, ck[key])

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
                        "mean_targeted": tr["mean_targeted"], "mean_fallconsist": tr["mean_fallconsist"],
                        "consist_p_f_clean": tr["consist_p_f_clean"], "consist_p_f_adv": tr["consist_p_f_adv"],
                        "val_clean_accuracy": acc, "val_clean_macro_f1": f1,
                        "val_clean_fall_recall": vb["val_clean_fall_recall"], "val_fgsm_fall_recall": vb["val_fgsm_fall_recall"],
                        "val_pgd_fall_recall": rec, "val_fgsm_false_fall_alarms": vb["val_fgsm_false_fall_alarms"],
                        "val_pgd_false_fall_alarms": fpv, "val_normalized_false_alarm_burden": vb["val_normalized_false_alarm_burden"],
                        "safety_score": sc, "v2_eligible": int(eligible),
                        "sel_v2safety": flags["v2safety"], "sel_v2maxrec": flags["v2maxrec"],
                        "sel_v2lowFA": flags["v2lowFA"], "sel_v2macroF1": flags["v2macroF1"]})
        print(f"Epoch {epoch:03d}/{args.epochs} | loss={tr['train_loss']:.3f} base={tr['mean_base']:.3f} "
              f"consist={tr['mean_fallconsist']:.4f} (pf {tr['consist_p_f_clean']:.3f}->{tr['consist_p_f_adv']:.3f}) | "
              f"acc={acc:.3f} f1={f1:.3f} cFR={vb['val_clean_fall_recall']:.3f} pgd_fr={rec:.3f} pgd_FP={fpv} "
              f"score={sc:.3f} v2elig={int(eligible)} "
              f"[{'S' if flags['v2safety'] else '.'}{'R' if flags['v2maxrec'] else '.'}"
              f"{'L' if flags['v2lowFA'] else '.'}{'F' if flags['v2macroF1'] else '.'}]")
        if args.patience > 0 and epoch >= args.min_epochs and no_improve >= args.patience:
            print(f"Early stopping at epoch {epoch} (best v2safety epoch {best['v2safety'][1]})."); break

    if not consist_ever_nz:
        raise SystemExit("STOP: L_fallconsist was always zero despite fall windows (check pairing).")

    elapsed = time.time() - start
    last_epoch = history[-1]["epoch"]
    torch.save({"epoch": last_epoch, "model_state_dict": F["model"].state_dict(),
                "selection_method": "last", "run_name": run, "beta": args.beta, "args": vars(args)}, ck_last)
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
    meta = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "stage": f"basat_stage1_safety_trades_seed{args.seed}_pilot", "method": "Safety-TRADES (G1 + beta*fall-prob consistency)",
            "namespace": "boundary_aware_selective_at", "run_name": run, "beta": args.beta, "seed": args.seed,
            "lam_s": BASE_LAM_S, "lam_f": BASE_LAM_F, "lam_t": BASE_LAM_T, "w_wr": BASE_W_WR, "fall_weight": args.fall_weight,
            "objective": "L_G1 (frozen Variant G G1) + beta*mean_{adv fall}(sg[p_f(x_clean)] - p_f(x_adv))^2",
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
    print("  NEXT: export val/test PGD probabilities for the selected checkpoints and compute val PGD AUROC")
    print("        of P(fall) vs the g1_baseline_val_frontier go/no-go bar (validation only).")
    print("=" * 78)


def main():
    args = parse_args()
    if args.seed != 42:
        raise SystemExit(f"Safety-TRADES / BASAT Stage 1 is seed-42 ONLY for now (got seed {args.seed}).")
    if args.beta not in ALLOWED_BETAS:
        raise SystemExit(f"beta must be one of {ALLOWED_BETAS} (got {args.beta}); run 3.0 first.")
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
