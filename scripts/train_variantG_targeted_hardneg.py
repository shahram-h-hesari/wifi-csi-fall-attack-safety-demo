"""
Variant G seed-42 pilot: targeted nonfall->fall hard-negative + source-class-weighted motion margin.

Implements VARIANT_G_MATH_TO_CODE_SPEC.md. Reuses the frozen Variant F / Variant E / Variant D
batch-split adversarial-training machinery (50% clean / 25% FGSM / 25% PGD, multi-eps
{0.005,0.015,0.030}, fall-weighted CE) and the selection-v2 checkpoint rule. The committed
Variant D / E / selection-v2 / Variant F scripts are NOT modified; this is a NEW script.

Objective (spec sec.4; term B REPLACES Variant F's motion margin -- no double-count):
    L_G = L_FWCE
        + lambda_s * mean_{i in adv nonfall}  w_{y_i} * max(0, gamma_m + z_fall(x_i^adv)  - z_true(x_i^adv))   [B src-weighted motion]
        + lambda_f * mean_{i in adv true-fall}         max(0, gamma_f + max_{c!=fall} z_c - z_fall(x_i^adv))     [F fall preservation]
        + lambda_t * mean_{i in tgt nonfall}  w_{y_i} * max(0, gamma_t + z_fall(xhat_i)   - z_true(xhat_i))      [A targeted hard-neg]
where xhat = targeted-to-fall PGD (descent on CE-to-fall; spec sec.5), w_walk=w_run=w_wr>=1, w_other=1.
Fixed: lambda_s=1.0, lambda_f=1.0, gamma_m=gamma_f=gamma_t=0.5, fall weight 3.

Pilot settings (ONLY these three; spec sec.9):
    G1 balanced A+B          : lambda_t=1.0, w_wr=2.0
    G2 targeted-heavy (=A)   : lambda_t=2.0, w_wr=1.0
    G3 source-weighted (=B)  : lambda_t=0.0, w_wr=2.0   (ablation anchor)

Scope: seed 42 ONLY, LeNet only, same UT-HAR/SenseFi split. Window-level, digital-domain,
white-box; NOT solved/certified/clinical/over-the-air.

Modes:
    --self-check   class-index assertions + targeted-PGD sign check + one-batch loss decomposition (no training, no .pt)
    --smoke        2-epoch tiny run on seed 42 (one setting), writes to a `_smoke` namespace
    (default)      full single-setting training run  [NOT to be launched during smoke validation]

Commands:
    python scripts/train_variantG_targeted_hardneg.py --setting G1 --self-check
    python scripts/train_variantG_targeted_hardneg.py --setting G1 --smoke --epochs 2 --smoke-batches 5
"""
from __future__ import annotations
from pathlib import Path
import argparse, csv, json, platform, sys, time
from datetime import datetime, timezone
import numpy as np
import torch, torch.nn as nn, torch.optim as optim

WALK, RUN = 2, 4
NONFALL_EXPECTED = {0, 2, 3, 4, 5, 6}
V2_GUARD_ACC, V2_GUARD_F1 = 0.70, 0.65
LOWFA_RECALL_FLOOR = 0.10

# Fixed Variant G hyperparameters (spec sec.9); only (lambda_t, w_wr) vary per setting.
LAM_S, LAM_F = 1.0, 1.0
GAMMA_M = GAMMA_F = GAMMA_T = 0.5
SETTINGS = {
    "G1": {"lam_t": 1.0, "w_wr": 2.0, "desc": "balanced A+B"},
    "G2": {"lam_t": 2.0, "w_wr": 1.0, "desc": "targeted-heavy (isolates A)"},
    "G3": {"lam_t": 0.0, "w_wr": 2.0, "desc": "source-weighted / ablation anchor (isolates B)"},
}


def import_variantF():
    sd = Path(__file__).resolve().parent
    if str(sd) not in sys.path:
        sys.path.insert(0, str(sd))
    import train_variantF_motion_margin as tvf
    return tvf


def safety_score(vb):
    """Identical to the frozen Variant F / selection-v2 SafetyScore (NOT changed)."""
    return (0.35 * vb["val_clean_fall_recall"] + 0.45 * vb["val_pgd_fall_recall"]
            + 0.10 * vb["val_fgsm_fall_recall"] - 0.10 * vb["val_normalized_false_alarm_burden"])


# ----------------------------------------------------------------------------- targeted PGD (spec sec.5)
def targeted_fall_pgd(model, inputs, fall_idx, atk_criterion, epsilon, steps, alpha):
    """Targeted-to-fall L-inf PGD: DESCENT on CE-to-fall (opposite sign of the untargeted
    tsg.pgd_perturb, which ascends CE on the true label). No [0,1] clamp (processed CSI)."""
    if inputs.numel() == 0 or steps == 0:
        return inputs.detach()
    x0 = inputs.detach()
    adv = x0.clone().detach()
    tgt = torch.full((inputs.size(0),), fall_idx, dtype=torch.long, device=inputs.device)
    for _ in range(steps):
        adv.requires_grad_(True)
        loss_to_fall = atk_criterion(model(adv).float(), tgt)
        model.zero_grad()
        loss_to_fall.backward()
        with torch.no_grad():
            adv = adv - alpha * adv.grad.sign()                       # MINUS: descend CE-to-fall
            adv = x0 + torch.clamp(adv - x0, min=-epsilon, max=epsilon)  # project to L-inf ball
        adv = adv.detach()
    return adv


def source_weights(labels, w_wr, device):
    """w_walk = w_run = w_wr (>=1); all other classes weight 1."""
    w = torch.ones(labels.size(0), device=device)
    if float(w_wr) != 1.0:
        w[(labels == WALK) | (labels == RUN)] = float(w_wr)
    return w


# ----------------------------------------------------------- single math-to-code site for the 3 margin terms
def variantG_margin_terms(adv_out, adv_lab, tgt_out, tgt_lab, w_wr, fall_idx, device):
    """Returns (L_src_motion[B], L_fall[F], L_targeted[A]). Each is a finite scalar tensor >= 0."""
    # B: source-weighted motion margin over ADV NONFALL windows (replaces F's walk/run-only motion term)
    nf = adv_lab != fall_idx
    if nf.any():
        zo = adv_out[nf]
        zf = zo[:, fall_idx]
        zt = zo.gather(1, adv_lab[nf].unsqueeze(1)).squeeze(1)
        w = source_weights(adv_lab[nf], w_wr, device)
        L_src = (w * torch.relu(GAMMA_M + zf - zt)).mean()
    else:
        L_src = torch.zeros((), device=device)
    # F: fall-preservation margin over ADV TRUE-FALL windows (unchanged from Variant F)
    f = adv_lab == fall_idx
    if f.any():
        zo = adv_out[f].clone()
        zf2 = zo[:, fall_idx].clone()
        zo[:, fall_idx] = float("-inf")
        L_fall = torch.relu(GAMMA_F + zo.max(dim=1).values - zf2).mean()
    else:
        L_fall = torch.zeros((), device=device)
    # A: targeted nonfall->fall hard-negative (source-weighted) over TARGETED nonfall examples
    if tgt_out is not None and tgt_out.numel() > 0 and tgt_lab.numel() > 0:
        zf_t = tgt_out[:, fall_idx]
        zt_t = tgt_out.gather(1, tgt_lab.unsqueeze(1)).squeeze(1)
        w_t = source_weights(tgt_lab, w_wr, device)
        L_tgt = (w_t * torch.relu(GAMMA_T + zf_t - zt_t)).mean()
    else:
        L_tgt = torch.zeros((), device=device)
    return L_src, L_fall, L_tgt


def train_one_epoch_variantG(model, loader, train_criterion, atk_criterion, optimizer, device,
                             train_epsilons, train_pgd_steps, rng, tsg, lam_t, w_wr, fall_idx,
                             max_batches=None):
    """Variant F batch-split FGSM+PGD adversarial training + Variant G targeted/source-weighted terms."""
    model.train()
    tot_loss = tot = 0.0
    s = {"base": 0.0, "src": 0.0, "fall": 0.0, "tgt": 0.0}
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
        # term A: targeted-to-fall examples from the batch's NONFALL windows (only if lam_t > 0)
        nf_mask = labels != fall_idx
        if lam_t > 0 and nf_mask.any():
            tgt_adv = targeted_fall_pgd(model, inputs[nf_mask], fall_idx, atk_criterion, eps, train_pgd_steps, pgd_alpha)
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

        L_src, L_fall, L_tgt = variantG_margin_terms(adv_out, adv_lab, tgt_out, tgt_lab, w_wr, fall_idx, device)
        loss = base + LAM_S * L_src + LAM_F * L_fall + lam_t * L_tgt
        loss.backward(); optimizer.step()

        tot_loss += loss.item() * bs; tot += bs; nb += 1
        s["base"] += float(base.item()); s["src"] += float(L_src.item())
        s["fall"] += float(L_fall.item()); s["tgt"] += float(L_tgt.item())
    d = max(1, nb)
    return {"train_loss": tot_loss / max(1, tot), "mean_base": s["base"] / d,
            "mean_src_motion": s["src"] / d, "mean_fall_margin": s["fall"] / d,
            "mean_targeted": s["tgt"] / d, "batches": nb}


# ------------------------------------------------------------------ mandatory targeted-PGD sign check (spec sec.5/8.3/14.2)
def targeted_sign_check(model, loader, atk_criterion, fall_idx, device, epsilon=0.030, steps=7):
    model.eval()
    inputs, labels = next(iter(loader))
    inputs = inputs.to(device).float(); labels = labels.type(torch.LongTensor).to(device)
    x_nf = inputs[labels != fall_idx]
    with torch.no_grad():
        cl = model(x_nf).float()
        clean_fall_logit = float(cl[:, fall_idx].median())
        clean_pfall = float(cl.softmax(1)[:, fall_idx].median())
    x_tgt = targeted_fall_pgd(model, x_nf, fall_idx, atk_criterion, epsilon, steps, epsilon / 4.0)
    with torch.no_grad():
        tl = model(x_tgt).float()
        tgt_fall_logit = float(tl[:, fall_idx].median())
        tgt_pfall = float(tl.softmax(1)[:, fall_idx].median())
    increased = (tgt_fall_logit > clean_fall_logit) or (tgt_pfall > clean_pfall)
    return {"n_nonfall": int(x_nf.size(0)), "clean_median_fall_logit": clean_fall_logit,
            "targeted_median_fall_logit": tgt_fall_logit, "clean_median_p_fall": clean_pfall,
            "targeted_median_p_fall": tgt_pfall, "increased": bool(increased)}, increased


def parse_args():
    p = argparse.ArgumentParser(description="Variant G targeted hard-negative defense (seed-42 pilot).")
    p.add_argument("--setting", choices=sorted(SETTINGS.keys()), required=True,
                   help="G1 balanced A+B | G2 targeted-heavy | G3 source-weighted/ablation anchor")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=70)
    p.add_argument("--patience", type=int, default=15)
    p.add_argument("--min-epochs", type=int, default=35)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--train-pgd-steps", type=int, default=7)
    p.add_argument("--fall-weight", type=float, default=3.0)
    p.add_argument("--self-check", action="store_true",
                   help="assertions + targeted sign check + one-batch loss decomposition; no training, no .pt")
    p.add_argument("--smoke", action="store_true", help="2-epoch tiny run to a `_smoke` namespace")
    p.add_argument("--smoke-batches", type=int, default=5, help="train batches/epoch in smoke mode")
    return p.parse_args()


def load_foundation(args):
    """Build the exact same data/model/training foundation as Variant F; assert class constants."""
    tvf = import_variantF()
    tve = tvf.import_variantE()
    tsg = tve.import_variantD()
    s1 = tsg.import_stage1()
    fall_idx, num_classes = tsg.FALL_CLASS_INDEX, tsg.NUM_CLASSES
    # spec sec.14.1: verify class constants from source, do not trust memory
    assert fall_idx == 1, f"FALL_CLASS_INDEX expected 1, got {fall_idx}"
    assert num_classes == 7, f"NUM_CLASSES expected 7, got {num_classes}"
    assert (WALK, RUN) == (2, 4), f"WALK/RUN expected (2,4), got {(WALK, RUN)}"
    assert {c for c in range(num_classes) if c != fall_idx} == NONFALL_EXPECTED, "nonfall set mismatch"

    exp = Path(__file__).resolve().parents[1]
    benchmark = exp / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    s1.patch_sensefi_dataset_loader(benchmark)
    if str(benchmark) not in sys.path:
        sys.path.insert(0, str(benchmark))
    from model_factory import build_model
    s1.set_seed(args.seed)
    data = s1.load_raw_ut_har(benchmark)
    train_loader, val_loader, test_loader, split_sizes = s1.build_loaders(data, args.batch_size)
    # NOTE: test_loader is intentionally NOT used anywhere in training/selection/smoke (spec sec.14.3).
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model("lenet").to(device)
    class_weights = torch.ones(num_classes, device=device); class_weights[fall_idx] = args.fall_weight
    train_criterion = nn.CrossEntropyLoss(weight=class_weights)
    atk_criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    rng = np.random.default_rng(args.seed)
    preset = tsg.VARIANT_PRESETS["D"]; train_epsilons = list(preset["train_epsilons"])
    return dict(exp=exp, tsg=tsg, s1=s1, model=model, device=device, fall_idx=fall_idx,
                num_classes=num_classes, train_criterion=train_criterion, atk_criterion=atk_criterion,
                optimizer=optimizer, rng=rng, train_epsilons=train_epsilons, split_sizes=split_sizes,
                train_loader=train_loader, val_loader=val_loader, _test_loader=test_loader)


def run_self_check(args, F):
    cfg = SETTINGS[args.setting]
    print("=" * 72); print(f"Variant G --self-check  setting={args.setting} ({cfg['desc']})")
    print(f"  class-index assertions PASSED: FALL={F['fall_idx']} NUM={F['num_classes']} "
          f"WALK={WALK} RUN={RUN} nonfall={sorted(NONFALL_EXPECTED)}")
    # targeted-PGD sign check
    sc, ok = targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
    print("  targeted-PGD sign check (nonfall windows):")
    print(f"    clean   median fall_logit={sc['clean_median_fall_logit']:.4f}  median P(fall)={sc['clean_median_p_fall']:.4f}")
    print(f"    targeted median fall_logit={sc['targeted_median_fall_logit']:.4f}  median P(fall)={sc['targeted_median_p_fall']:.4f}")
    print(f"    increased={sc['increased']}  (n_nonfall={sc['n_nonfall']})")
    if not ok:
        raise SystemExit("SIGN CHECK FAILED: targeted PGD did not increase fall logit / P(fall) on "
                         "nonfall windows -> targeted attack sign is wrong (halt; spec sec.14.2).")
    # one-batch loss decomposition (no optimizer step)
    F["model"].train()
    inputs, labels = next(iter(F["train_loader"]))
    inputs = inputs.to(F["device"]).float(); labels = labels.type(torch.LongTensor).to(F["device"])
    bs = labels.size(0); eps = float(F["rng"].choice(F["train_epsilons"])); a = eps / 4.0
    n_clean = bs // 2; n_fgsm = (bs - n_clean) // 2
    clean_x = inputs[:n_clean]
    fgsm = F["tsg"].fgsm_perturb(F["model"], inputs[n_clean:n_clean + n_fgsm], labels[n_clean:n_clean + n_fgsm], F["atk_criterion"], eps)
    pgd = F["tsg"].pgd_perturb(F["model"], inputs[n_clean + n_fgsm:], labels[n_clean + n_fgsm:], F["atk_criterion"], eps, args.train_pgd_steps, a)
    nf_mask = labels != F["fall_idx"]
    tgt_adv = targeted_fall_pgd(F["model"], inputs[nf_mask], F["fall_idx"], F["atk_criterion"], eps, args.train_pgd_steps, a)
    tgt_lab = labels[nf_mask]
    outputs = F["model"](torch.cat([clean_x, fgsm, pgd], 0)).float()
    base = F["train_criterion"](outputs, labels)
    tgt_out = F["model"](tgt_adv).float()
    L_src, L_fall, L_tgt = variantG_margin_terms(outputs[n_clean:], labels[n_clean:], tgt_out, tgt_lab, cfg["w_wr"], F["fall_idx"], F["device"])
    total = base + LAM_S * L_src + LAM_F * L_fall + cfg["lam_t"] * L_tgt
    comp = {"FWCE_base": base.item(), "L_src_motion": L_src.item(), "L_fall_preservation": L_fall.item(),
            "L_targeted": L_tgt.item(), "total_loss": total.item(),
            "n_adv_fall": int((labels[n_clean:] == F["fall_idx"]).sum()), "n_targeted_nonfall": int(tgt_lab.numel())}
    print("  one-batch loss components:")
    for k in ("FWCE_base", "L_src_motion", "L_fall_preservation", "L_targeted", "total_loss"):
        print(f"    {k:22s} = {comp[k]:.5f}")
    for k in ("FWCE_base", "L_src_motion", "L_fall_preservation", "L_targeted", "total_loss"):
        assert np.isfinite(comp[k]), f"{k} not finite"
    assert comp["L_targeted"] > 0, "L_targeted must be > 0 on targeted nonfall examples"
    if comp["n_adv_fall"] > 0:
        assert comp["L_fall_preservation"] >= 0
    print("  PASS: all components finite; L_targeted > 0; fall-preservation valid.")
    print("=" * 72)
    return {"sign_check": sc, "components": comp}


def run_smoke(args, F):
    cfg = SETTINGS[args.setting]
    tsg, s1 = F["tsg"], F["s1"]
    run = f"seed{args.seed}_variantG_{args.setting}_smoke"
    base = F["exp"] / "results" / "safety_guided_defense" / "variantG_targeted_hardneg" / "_smoke" / f"seed{args.seed}"
    ck_dir = F["exp"] / "checkpoints" / "safety_guided_defense" / "variantG_targeted_hardneg" / "_smoke" / f"seed{args.seed}"
    for d in (base, ck_dir):
        d.mkdir(parents=True, exist_ok=True)
    print("=" * 72); print(f"Variant G --smoke  setting={args.setting} ({cfg['desc']})  run={run}")
    print(f"  lam_s={LAM_S} lam_f={LAM_F} lam_t={cfg['lam_t']} w_wr={cfg['w_wr']} "
          f"gamma_m=gamma_f=gamma_t={GAMMA_M}  epochs={args.epochs} smoke_batches={args.smoke_batches}")
    history = []; start = time.time()
    best = {"v2safety": (-1e9, -1)}
    for epoch in range(1, args.epochs + 1):
        tr = train_one_epoch_variantG(F["model"], F["train_loader"], F["train_criterion"], F["atk_criterion"],
                                      F["optimizer"], F["device"], F["train_epsilons"], args.train_pgd_steps,
                                      F["rng"], tsg, cfg["lam_t"], cfg["w_wr"], F["fall_idx"],
                                      max_batches=args.smoke_batches)
        vb = tsg.compute_validation_bundle(s1, F["model"], F["val_loader"], F["atk_criterion"], F["device"])
        acc, f1 = vb["val_clean_accuracy"], vb["val_clean_macro_f1"]
        rec, fpv = vb["val_pgd_fall_recall"], vb["val_pgd_false_fall_alarms"]
        sc = (0.35 * vb["val_clean_fall_recall"] + 0.45 * rec + 0.10 * vb["val_fgsm_fall_recall"]
              - 0.10 * vb["val_normalized_false_alarm_burden"])
        eligible = (acc >= V2_GUARD_ACC and f1 >= V2_GUARD_F1)
        # checkpoint selection on VALIDATION ONLY (spec sec.14.3) -- save to smoke dir
        if eligible and sc > best["v2safety"][0]:
            best["v2safety"] = (sc, epoch)
            torch.save({"epoch": epoch, "model_state_dict": F["model"].state_dict(),
                        "selection_method": "v2safety", "val_bundle": vb, "run_name": run,
                        "smoke": True}, ck_dir / f"{run}_v2safety_best.pt")
        for k, v in (("epoch", epoch), ("train_loss", tr["train_loss"]), ("mean_base", tr["mean_base"]),
                     ("mean_src_motion", tr["mean_src_motion"]), ("mean_fall_margin", tr["mean_fall_margin"]),
                     ("mean_targeted", tr["mean_targeted"]), ("val_clean_accuracy", acc),
                     ("val_clean_macro_f1", f1), ("val_pgd_fall_recall", rec),
                     ("val_pgd_false_fall_alarms", fpv), ("v2_eligible", int(eligible))):
            pass
        history.append({"epoch": epoch, "train_loss": tr["train_loss"], "mean_base": tr["mean_base"],
                        "mean_src_motion": tr["mean_src_motion"], "mean_fall_margin": tr["mean_fall_margin"],
                        "mean_targeted": tr["mean_targeted"], "val_clean_accuracy": acc,
                        "val_clean_macro_f1": f1, "val_pgd_fall_recall": rec,
                        "val_pgd_false_fall_alarms": fpv, "v2_eligible": int(eligible)})
        print(f"  epoch {epoch}/{args.epochs} | loss={tr['train_loss']:.3f} base={tr['mean_base']:.3f} "
              f"src={tr['mean_src_motion']:.3f} fall={tr['mean_fall_margin']:.3f} tgt={tr['mean_targeted']:.3f} "
              f"| val_acc={acc:.3f} f1={f1:.3f} pgd_fr={rec:.3f} pgd_FP={fpv} elig={int(eligible)}")
        for k in ("train_loss", "mean_base", "mean_src_motion", "mean_fall_margin", "mean_targeted"):
            assert np.isfinite(history[-1][k]), f"{k} not finite at epoch {epoch}"
    elapsed = time.time() - start
    # write tiny summaries (kept); the model .pt is a smoke artifact to be removed by the operator
    with (base / f"{run}_log.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(history[0].keys())); w.writeheader()
        for r in history:
            w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in history[0]})
    summary = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "stage": "variantG_smoke",
               "setting": args.setting, "setting_desc": cfg["desc"], "seed": args.seed,
               "lam_s": LAM_S, "lam_f": LAM_F, "lam_t": cfg["lam_t"], "w_wr": cfg["w_wr"],
               "gamma_m": GAMMA_M, "gamma_f": GAMMA_F, "gamma_t": GAMMA_T, "epochs": args.epochs,
               "smoke_batches": args.smoke_batches, "elapsed_seconds": elapsed,
               "final_components": {k: history[-1][k] for k in
                                    ("mean_base", "mean_src_motion", "mean_fall_margin", "mean_targeted", "train_loss")},
               "test_set_used": False, "device": str(F["device"]),
               "python_version": platform.python_version(), "torch_version": torch.__version__,
               "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(F["exp"])),
               "note": "SMOKE ONLY -- not a pilot result; .pt checkpoints are disposable."}
    with (base / f"{run}_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  smoke done in {elapsed:.1f}s | summary -> {base / (run + '_summary.json')}")
    print("=" * 72)
    return summary


def run_full(args, F):
    """Full single-setting Variant G training with the frozen selection-v2 checkpoint rule
    (clean guard 0.70/0.65; candidates v2safety/v2maxrec/v2lowFA/v2macroF1). Mirrors the
    Variant F training/selection loop exactly; only the per-batch loss differs (Variant G terms).
    Writes to the REAL seed-42 namespace."""
    cfg = SETTINGS[args.setting]; tsg, s1 = F["tsg"], F["s1"]; device = F["device"]
    run = f"seed{args.seed}_variantG_{args.setting}"
    base = F["exp"] / "results" / "safety_guided_defense" / "variantG_targeted_hardneg" / f"seed{args.seed}"
    ck_dir = F["exp"] / "checkpoints" / "safety_guided_defense" / "variantG_targeted_hardneg" / f"seed{args.seed}"
    logs_dir = base / "logs"; ana_dir = base / "analysis"; meta_dir = base / "metadata"
    for d in (ck_dir, logs_dir, ana_dir, meta_dir):
        d.mkdir(parents=True, exist_ok=True)
    ck = {k: ck_dir / f"{run}_{k}_best.pt" for k in ("v2safety", "v2maxrec", "v2lowFA", "v2macroF1")}
    ck_last = ck_dir / f"{run}_last.pt"

    print("=" * 72)
    print(f"Variant G FULL training  setting={args.setting} ({cfg['desc']})  run={run}")
    print(f"  lam_s={LAM_S} lam_f={LAM_F} lam_t={cfg['lam_t']} w_wr={cfg['w_wr']} "
          f"gamma_m=gamma_f=gamma_t={GAMMA_M} fall_weight={args.fall_weight}")
    print(f"  guard clean_acc>={V2_GUARD_ACC} & macro_f1>={V2_GUARD_F1} | "
          f"epochs={args.epochs} patience={args.patience} min={args.min_epochs} eps={F['train_epsilons']}")
    print("=" * 72)

    history = []
    best = {"v2safety": (-1e9, -1), "v2maxrec": ((-1e9, 1e9), -1),
            "v2lowFA": ((1e9, -1e9), -1), "v2macroF1": (-1e9, -1)}
    best_rec = {}; no_improve = 0; start = time.time()

    for epoch in range(1, args.epochs + 1):
        tr = train_one_epoch_variantG(F["model"], F["train_loader"], F["train_criterion"], F["atk_criterion"],
                                      F["optimizer"], device, F["train_epsilons"], args.train_pgd_steps,
                                      F["rng"], tsg, cfg["lam_t"], cfg["w_wr"], F["fall_idx"], max_batches=None)
        vb = tsg.compute_validation_bundle(s1, F["model"], F["val_loader"], F["atk_criterion"], device)
        sc = safety_score(vb)
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
            if rec >= LOWFA_RECALL_FLOOR and (fpv, -rec) < best["v2lowFA"][0]:
                best["v2lowFA"] = ((fpv, -rec), epoch); best_rec["v2lowFA"] = vb; save("v2lowFA"); flags["v2lowFA"] = 1
        if not flags["v2safety"] and best["v2safety"][1] > 0:
            no_improve += 1
        if f1 > best["v2macroF1"][0]:
            best["v2macroF1"] = (f1, epoch); best_rec["v2macroF1"] = vb; save("v2macroF1"); flags["v2macroF1"] = 1

        history.append({"epoch": epoch, "train_loss": tr["train_loss"], "mean_base": tr["mean_base"],
                        "mean_src_motion": tr["mean_src_motion"], "mean_fall_margin": tr["mean_fall_margin"],
                        "mean_targeted": tr["mean_targeted"], "val_clean_accuracy": acc, "val_clean_macro_f1": f1,
                        "val_clean_fall_recall": vb["val_clean_fall_recall"], "val_fgsm_fall_recall": vb["val_fgsm_fall_recall"],
                        "val_pgd_fall_recall": rec, "val_fgsm_false_fall_alarms": vb["val_fgsm_false_fall_alarms"],
                        "val_pgd_false_fall_alarms": fpv, "val_normalized_false_alarm_burden": vb["val_normalized_false_alarm_burden"],
                        "safety_score": sc, "v2_eligible": int(eligible),
                        "sel_v2safety": flags["v2safety"], "sel_v2maxrec": flags["v2maxrec"],
                        "sel_v2lowFA": flags["v2lowFA"], "sel_v2macroF1": flags["v2macroF1"]})
        print(f"Epoch {epoch:03d}/{args.epochs} | loss={tr['train_loss']:.3f} base={tr['mean_base']:.3f} "
              f"src={tr['mean_src_motion']:.3f} fall={tr['mean_fall_margin']:.3f} tgt={tr['mean_targeted']:.3f} | "
              f"acc={acc:.3f} f1={f1:.3f} pgd_fr={rec:.3f} pgd_FP={fpv} score={sc:.3f} v2elig={int(eligible)} "
              f"[{'S' if flags['v2safety'] else '.'}{'R' if flags['v2maxrec'] else '.'}"
              f"{'L' if flags['v2lowFA'] else '.'}{'F' if flags['v2macroF1'] else '.'}]")
        if args.patience > 0 and epoch >= args.min_epochs and no_improve >= args.patience:
            print(f"Early stopping at epoch {epoch} (best v2safety epoch {best['v2safety'][1]})."); break

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
            ep = best[k][1]; vb = best_rec.get(k, {})
            w.writerow([k, ep, f"{vb.get('val_clean_accuracy', float('nan')):.4f}",
                        f"{vb.get('val_clean_macro_f1', float('nan')):.4f}",
                        f"{vb.get('val_pgd_fall_recall', float('nan')):.4f}",
                        vb.get('val_pgd_false_fall_alarms', ''), f"{safety_score(vb):.4f}" if vb else ""])
    meta = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "stage": "variantG_seed42_pilot",
            "run_name": run, "setting": args.setting, "setting_desc": cfg["desc"], "seed": args.seed,
            "lam_s": LAM_S, "lam_f": LAM_F, "lam_t": cfg["lam_t"], "w_wr": cfg["w_wr"],
            "gamma_m": GAMMA_M, "gamma_f": GAMMA_F, "gamma_t": GAMMA_T, "fall_weight": args.fall_weight,
            "objective": "L_FWCE + lam_s*w*relu(gm+z_fall-z_true)[adv nonfall] + lam_f*relu(gf+max_nonfall-z_fall)[adv fall] "
                         "+ lam_t*w*relu(gt+z_fall-z_true)[targeted nonfall]",
            "targeted_pgd": "descent on CE-to-fall (sign-flipped vs untargeted)",
            "v2_guard": {"min_clean_accuracy": V2_GUARD_ACC, "min_clean_macro_f1": V2_GUARD_F1},
            "train_epsilons": F["train_epsilons"], "train_pgd_steps": args.train_pgd_steps,
            "epochs_run": last_epoch, "split_sizes": F["split_sizes"], "test_set_used": False,
            "selected_epochs": {k: best[k][1] for k in ck}, "checkpoints": {k: str(v) for k, v in ck.items()},
            "claim_boundary": "window-level digital-domain white-box; seed42/LeNet only; not solved/certified/clinical/OTA",
            "device": str(device), "python_version": platform.python_version(), "torch_version": torch.__version__,
            "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(F["exp"])), "elapsed_seconds": elapsed}
    with (meta_dir / f"{run}_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("-" * 72)
    print(f"Done in {elapsed:.1f}s ({last_epoch} epochs). selected epochs: " +
          ", ".join(f"{k}={best[k][1]}" for k in ck))
    print("=" * 72)


def main():
    args = parse_args()
    if args.seed not in (42, 44):
        raise SystemExit(f"Variant G is seed-42 (pilot) or seed-44 (pre-registered G1 validation) ONLY "
                         f"(got seed {args.seed}); seeds 43/45/46 are blocked for this script. The seed-44 "
                         "eligibility is the pre-registration's permitted gate relaxation; loss / class "
                         "indices / targeted-PGD sign / source weighting / selection-v2 are unchanged.")
    if args.setting not in SETTINGS:
        raise SystemExit(f"Disallowed setting {args.setting!r}; permitted: {sorted(SETTINGS)}.")
    F = load_foundation(args)
    if args.self_check:
        run_self_check(args, F); return
    if args.smoke:
        # mandatory sign check first, then the 2-epoch smoke
        _, ok = targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
        if not ok:
            raise SystemExit("SIGN CHECK FAILED before smoke (spec sec.14.2).")
        run_smoke(args, F); return
    # ----- full single-setting training: gate OPENED for the pre-registered seed-42 G1/G2/G3 pilot -----
    _, ok = targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], F["fall_idx"], F["device"])
    if not ok:
        raise SystemExit("SIGN CHECK FAILED before full training (spec sec.14.2).")
    run_full(args, F)


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
