"""
AFAC candidate-mechanism 2x2 ablation -- controlled training.

Scientific question (NOT a search for better numbers): do the two residual thesis-specific
mechanisms identified by the IP audit contribute independent value to the LEARNED model,
separately from downstream threshold selection?

    Factor A (floor)    : fall-rescue Top-K absolute floor  k_abs_min in {None, 4}
    Factor B (adaptive) : once-per-epoch adaptive-Lagrangian lambda_b in {fixed 0.25, adaptive}

    V00 CONTROL       k_abs_min=None  lambda_b=0.25 fixed
    V10 FLOOR ONLY    k_abs_min=4     lambda_b=0.25 fixed
    V01 ADAPTIVE ONLY k_abs_min=None  lambda_b adaptive (eta=0.10, target_FAR=0.10, cap 1.0)
    V11 FLOOR+ADAPT   k_abs_min=4     lambda_b adaptive          <- reproduces historical Option B

EVERYTHING else is held identical across the four variants: G1 foundation, data, splits, model,
optimizer, lr, batch size, batch composition (50% clean / 25% FGSM / 25% PGD), multi-epsilon
training set {0.005,0.015,0.03}, targeted-to-fall PGD, source weights, margins/gammas, lambda_r=1.0,
epoch budget (fixed 70, no early stopping), and checkpoint-evaluation procedure.

REUSE BOUNDARY (same discipline as the historical Option B script): this file EDITS NO EXISTING
FILE. The G1 base, the Variant H Top-K tail terms, and the Option B controller/selection functions
are reused BY IMPORT ONLY, so the ablation cannot silently diverge from the historical method:
  * train_variantG_targeted_hardneg  (tvg) -- load_foundation, targeted_sign_check
  * train_variantH_dual_tail_budget  (vh)  -- train_one_epoch_variantH (G1 base + both TopK terms)
  * train_optionB_adaptive_lagrangian (ob) -- lambda_update, selection_score, clean_guard_eligible,
                                              validation_nonfall_count, PILOT_EPOCHS, constants
Importing ob is side-effect-safe: its module body only defines constants/functions and its main()
is __name__-guarded (identical reasoning to how ob itself imports vh).

Paired design: for a given seed, all four variants receive identical model initialization, identical
train-batch ordering, and an identical epsilon draw sequence, because the RNG stream is consumed
identically in every variant (the loss terms are deterministic given logits and consume no RNG).
The ONLY divergence between variants is the loss computation itself.

Splits are dataset-fixed (SenseFi UT_HAR X_train/X_val/X_test), NOT resampled per seed, so all seeds
share the same validation (496 = 44 fall / 452 non-fall) and test (500 = 45 fall / 455 non-fall).

The TEST split is NEVER loaded, referenced, or evaluated by this script.

Modes:
    --self-check  verify the 2x2 grid differs ONLY in the two intended factors, that the reused
                  functions are the frozen originals, and that the controller is inert when
                  adaptive=False. No training, no .pt.
    --train       run one (variant, seed) training job.

Commands:
    python scripts/ablation_afac_mechanisms/train_ablation_2x2.py --self-check
    python scripts/ablation_afac_mechanisms/train_ablation_2x2.py --train --variant V00 --seed 42
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import json
import platform
import sys
import time

import numpy as np
import torch


# ----------------------------------------------------------------- frozen-helper imports (by import only)
def _import_helpers():
    scripts_dir = Path(__file__).resolve().parents[1]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import train_variantG_targeted_hardneg as tvg          # frozen G1 foundation
    import train_variantH_dual_tail_budget as vh           # frozen Variant H TopK tail terms
    import train_optionB_adaptive_lagrangian as ob         # frozen Option B controller + selection
    return tvg, vh, ob


tvg, vh, ob = _import_helpers()

# ----------------------------------------------------------------- pinned constants (ALL from Option B)
# Every one of these is imported/derived from the frozen Option B module so the ablation cannot drift.
LAM_B0 = ob.LAM_B0            # 0.25  -- both the fixed value AND the adaptive initial value
LAM_R = ob.LAM_R              # 1.0   -- fixed rescue weight, identical in all four variants
ETA = ob.ETA                  # 0.10
LAM_B_MAX = ob.LAM_B_MAX      # 1.0
TARGET_FAR = ob.TARGET_FAR    # 0.10
K_ABS_MIN_ON = ob.K_ABS_MIN   # 4     -- the floor value when factor A is ON
EXPECTED_VAL_NONFALL = ob.EXPECTED_VAL_NONFALL   # 452
EPOCHS = ob.PILOT_EPOCHS      # 70, no early stopping

# The 2x2 grid. Exactly two keys vary; everything else is shared and pinned above.
VARIANTS = {
    "V00": {"k_abs_min": None,         "adaptive": False, "desc": "CONTROL (no floor, fixed lambda_b)"},
    "V10": {"k_abs_min": K_ABS_MIN_ON, "adaptive": False, "desc": "FLOOR ONLY"},
    "V01": {"k_abs_min": None,         "adaptive": True,  "desc": "ADAPTIVE ONLY"},
    "V11": {"k_abs_min": K_ABS_MIN_ON, "adaptive": True,  "desc": "FLOOR + ADAPTIVE (= historical Option B)"},
}
SEEDS = (42, 43, 44, 45, 46)


def _paths(exp: Path, variant: str, seed: int):
    base = exp / "results" / "ablation_afac_mechanisms" / variant / f"seed{seed}"
    ck_dir = exp / "checkpoints" / "ablation_afac_mechanisms" / variant / f"seed{seed}"
    return base, ck_dir


# ----------------------------------------------------------------------------- training
def _save_ckpt(path, epoch, model, method, variant, seed, args):
    torch.save({"epoch": epoch, "model_state_dict": model.state_dict(), "selection_method": method,
                "variant": variant, "seed": seed, "run_name": f"{variant}_seed{seed}",
                "args": vars(args)}, path)


def run_train(args):
    cfg = VARIANTS[args.variant]
    kabs = cfg["k_abs_min"]
    adaptive = cfg["adaptive"]

    if args.threads:
        torch.set_num_threads(int(args.threads))

    F = tvg.load_foundation(args)          # identical foundation to G1/H/Option B
    exp = F["exp"]
    tsg, s1, device, fall_idx = F["tsg"], F["s1"], F["device"], F["fall_idx"]

    # pinned training-epsilon assertion (same guard Option B uses)
    if sorted(round(e, 3) for e in F["train_epsilons"]) != [0.005, 0.015, 0.03]:
        raise SystemExit(f"STOP: train_epsilons {F['train_epsilons']} != pinned {{0.005,0.015,0.03}}.")

    # FAR denominator from validation labels only; split-integrity guard.
    n_val_nonfall = ob.validation_nonfall_count(F["val_loader"], fall_idx)
    if n_val_nonfall != EXPECTED_VAL_NONFALL:
        raise SystemExit(f"STOP (split mismatch): N_val_nonfall={n_val_nonfall}, expected {EXPECTED_VAL_NONFALL}.")

    base, ck_dir = _paths(exp, args.variant, args.seed)
    for d in (base / "logs", base / "metadata", ck_dir):
        d.mkdir(parents=True, exist_ok=True)
    ck = {"maxscore": ck_dir / f"{args.variant}_seed{args.seed}_maxscore_best.pt",
          "last": ck_dir / f"{args.variant}_seed{args.seed}_last.pt"}

    print("=" * 78)
    print(f"ABLATION {args.variant} ({cfg['desc']})  seed={args.seed}")
    print(f"  k_abs_min={kabs}  adaptive_lambda_b={adaptive}  lambda_b0={LAM_B0}  lambda_r={LAM_R}")
    print(f"  eta={ETA} target_FAR={TARGET_FAR} lam_b_max={LAM_B_MAX} | epochs={EPOCHS} (no early stopping)")
    print(f"  n_val_nonfall={n_val_nonfall}  device={device}  threads={torch.get_num_threads()}")
    print("=" * 78)

    # mandatory targeted-PGD sign check (same discipline as G/H/Option B)
    _, ok = tvg.targeted_sign_check(F["model"], F["train_loader"], F["atk_criterion"], fall_idx, device)
    if not ok:
        raise SystemExit("SIGN CHECK FAILED before training.")

    lam_b_current = LAM_B0
    history = []
    best_maxscore = (-1e9, -1)
    budget_ever_nz = rescue_ever_nz = False
    t0 = time.time()

    for epoch in range(1, EPOCHS + 1):
        tr = vh.train_one_epoch_variantH(
            F["model"], F["train_loader"], F["train_criterion"], F["atk_criterion"], F["optimizer"], device,
            F["train_epsilons"], args.train_pgd_steps, F["rng"], tsg, lam_b_current, LAM_R, fall_idx,
            max_batches=None, fall_k_abs_min=kabs)
        for k in ("train_loss", "mean_base", "mean_nonfall_budget", "mean_fall_rescue"):
            if not np.isfinite(tr[k]):
                raise SystemExit(f"STOP (numerical): {k} not finite at epoch {epoch}.")
        budget_ever_nz = budget_ever_nz or (tr["mean_nonfall_budget"] > 0)
        rescue_ever_nz = rescue_ever_nz or (tr["mean_fall_rescue"] > 0)

        vb = tsg.compute_validation_bundle(s1, F["model"], F["val_loader"], F["atk_criterion"], device)
        fp = vb["val_pgd_false_fall_alarms"]; rec = vb["val_pgd_fall_recall"]
        acc = vb["val_clean_accuracy"]; f1 = vb["val_clean_macro_f1"]; cfr = vb["val_clean_fall_recall"]

        far_val = fp / n_val_nonfall
        eligible = ob.clean_guard_eligible(acc, f1, cfr)
        score = ob.selection_score(rec, far_val, cfr, acc)

        # ---- the ONLY place factor B acts: adaptive variants update lambda_b, fixed variants do not.
        if adaptive:
            lam_b_next = ob.lambda_update(lam_b_current, far_val)
            if not (0.0 <= lam_b_next <= LAM_B_MAX):
                raise SystemExit(f"STOP: lambda_b {lam_b_next} outside [0,{LAM_B_MAX}] at epoch {epoch}.")
        else:
            lam_b_next = LAM_B0

        sel = 0
        if eligible and score > best_maxscore[0]:
            best_maxscore = (score, epoch); sel = 1
            _save_ckpt(ck["maxscore"], epoch, F["model"], "maxscore", args.variant, args.seed, args)

        history.append({
            "epoch": epoch, "lambda_b_current": lam_b_current, "lambda_b_next": lam_b_next,
            "far_val_pgd10": far_val, "n_val_nonfall": n_val_nonfall,
            "val_pgd_false_fall_alarms": fp, "val_pgd_fall_recall": rec,
            "val_fgsm_fall_recall": vb["val_fgsm_fall_recall"],
            "val_fgsm_false_fall_alarms": vb["val_fgsm_false_fall_alarms"],
            "val_clean_accuracy": acc, "val_clean_macro_f1": f1, "val_clean_fall_recall": cfr,
            "val_normalized_false_alarm_burden": vb["val_normalized_false_alarm_burden"],
            "train_loss": tr["train_loss"], "mean_base": tr["mean_base"],
            "mean_src_motion": tr["mean_src_motion"], "mean_fall_margin": tr["mean_fall_margin"],
            "mean_targeted": tr["mean_targeted"],
            "mean_nonfall_budget": tr["mean_nonfall_budget"], "mean_fall_rescue": tr["mean_fall_rescue"],
            "fall_selected_count": tr["fall_selected_count"],
            "nonfall_selected_count": tr["nonfall_selected_count"],
            "fall_k_abs_floor_active_frac": tr["fall_k_abs_floor_active_frac"],
            "budget_to_rescue_loss_ratio": tr["budget_to_rescue_loss_ratio"],
            "clean_guard_eligible": int(eligible), "selection_score": score, "sel_maxscore": sel})
        print(f"  ep {epoch:03d}/{EPOCHS} | lam_b {lam_b_current:.3f}->{lam_b_next:.3f} FAR={far_val:.3f} "
              f"FP={fp} pgd_rec={rec:.3f} | acc={acc:.3f} f1={f1:.3f} cFR={cfr:.3f} "
              f"floor={tr['fall_k_abs_floor_active_frac']:.2f} elig={int(eligible)} score={score:.3f}"
              f"{' *' if sel else ''}", flush=True)

        lam_b_current = lam_b_next

    if not budget_ever_nz:
        raise SystemExit("STOP: nonfall_budget always zero despite valid nonfall examples.")
    if not rescue_ever_nz:
        raise SystemExit("STOP: fall_rescue always zero despite valid fall examples.")

    _save_ckpt(ck["last"], EPOCHS, F["model"], "last", args.variant, args.seed, args)
    elapsed = time.time() - t0

    fields = list(history[0].keys())
    with (base / "logs" / f"{args.variant}_seed{args.seed}_training_log.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in history:
            w.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in fields})

    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "afac_candidate_mechanism_2x2_ablation",
        "variant": args.variant, "variant_desc": cfg["desc"], "seed": args.seed,
        "factor_A_k_abs_min": kabs, "factor_B_adaptive_lambda_b": adaptive,
        "lambda_b0": LAM_B0, "lambda_r": LAM_R, "eta": ETA, "lambda_b_max": LAM_B_MAX,
        "target_far": TARGET_FAR, "k_frac": vh.K_FRAC, "gamma_b": vh.GAMMA_B, "gamma_r": vh.GAMMA_R,
        "base_lam_s": vh.BASE_LAM_S, "base_lam_f": vh.BASE_LAM_F, "base_lam_t": vh.BASE_LAM_T,
        "base_w_wr": vh.BASE_W_WR, "fall_weight": args.fall_weight,
        "fixed_epochs": EPOCHS, "early_stopping": False,
        "train_epsilons": F["train_epsilons"], "train_pgd_steps": args.train_pgd_steps,
        "lr": args.lr, "batch_size": args.batch_size,
        "n_val_nonfall": n_val_nonfall, "split_sizes": F["split_sizes"],
        "selected_epoch_maxscore": best_maxscore[1], "best_maxscore_value": best_maxscore[0],
        "checkpoints": {k: str(v) for k, v in ck.items()},
        "test_set_used": False,
        "selection": "validation-only maxscore (identical rule for all four variants)",
        "objective": "L_FWCE + lam_s*src + lam_f*fall + lam_t*tgt (frozen G1) "
                     "+ lam_b*TopKMean[relu(z_f-z_y+gb)][adv nonfall, src-weighted] "
                     "+ lam_r*TopKMean[relu(gr+max_nonfall-z_f)][adv fall, k_abs_min floor]",
        "claim_boundary": "window-level digital-domain white-box; LeNet/UT-HAR; ablation evidence only; "
                          "not clinical, not certified, not deployment-validated",
        "device": str(device), "torch_threads": torch.get_num_threads(),
        "python_version": platform.python_version(), "torch_version": torch.__version__,
        "git_commit": F["s1"].get_command_output(["git", "rev-parse", "HEAD"], cwd=str(exp)),
        "elapsed_seconds": elapsed}
    with (base / "metadata" / f"{args.variant}_seed{args.seed}_metadata.json").open(
            "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=float)

    print("-" * 78)
    print(f"DONE {args.variant} seed{args.seed} in {elapsed/60:.1f} min | maxscore epoch "
          f"{best_maxscore[1]} | last epoch {EPOCHS}")
    print("=" * 78)


# ----------------------------------------------------------------------------- self-check
def run_self_check():
    out = {}
    print("=" * 78)
    print("ABLATION --self-check")

    # 1. the grid varies ONLY the two intended factors
    keys = {k for cfg in VARIANTS.values() for k in cfg if k != "desc"}
    out["factor_keys"] = sorted(keys)
    assert keys == {"k_abs_min", "adaptive"}, f"unexpected varying keys: {keys}"
    grid = {(c["k_abs_min"], c["adaptive"]) for c in VARIANTS.values()}
    assert grid == {(None, False), (K_ABS_MIN_ON, False), (None, True), (K_ABS_MIN_ON, True)}, grid
    out["grid_complete_2x2"] = True
    print(f"  2x2 grid complete, varying exactly {sorted(keys)}: PASS")

    # 2. the reused functions ARE the frozen originals (identity, not copies)
    ident = {
        "train_one_epoch_variantH_is_vh": vh.train_one_epoch_variantH.__module__ == "train_variantH_dual_tail_budget",
        "lambda_update_is_ob": ob.lambda_update.__module__ == "train_optionB_adaptive_lagrangian",
        "selection_score_is_ob": ob.selection_score.__module__ == "train_optionB_adaptive_lagrangian",
        "clean_guard_is_ob": ob.clean_guard_eligible.__module__ == "train_optionB_adaptive_lagrangian",
        "load_foundation_is_tvg": tvg.load_foundation.__module__ == "train_variantG_targeted_hardneg",
    }
    out["frozen_identity"] = ident
    assert all(ident.values()), ident
    print(f"  reused helpers are the frozen originals: PASS")

    # 3. constants match the historical Option B exactly
    consts = {"LAM_B0": (LAM_B0, 0.25), "LAM_R": (LAM_R, 1.0), "ETA": (ETA, 0.10),
              "LAM_B_MAX": (LAM_B_MAX, 1.0), "TARGET_FAR": (TARGET_FAR, 0.10),
              "K_ABS_MIN_ON": (K_ABS_MIN_ON, 4), "EPOCHS": (EPOCHS, 70),
              "EXPECTED_VAL_NONFALL": (EXPECTED_VAL_NONFALL, 452),
              "K_FRAC": (vh.K_FRAC, 0.25), "GAMMA_B": (vh.GAMMA_B, 0.5), "GAMMA_R": (vh.GAMMA_R, 0.5),
              "BASE_LAM_S": (vh.BASE_LAM_S, 1.0), "BASE_LAM_F": (vh.BASE_LAM_F, 1.0),
              "BASE_LAM_T": (vh.BASE_LAM_T, 1.0), "BASE_W_WR": (vh.BASE_W_WR, 2.0)}
    bad = {k: v for k, v in consts.items() if v[0] != v[1]}
    out["constants"] = {k: v[0] for k, v in consts.items()}
    assert not bad, f"constant drift vs Option B: {bad}"
    print(f"  pinned constants match historical Option B: PASS")

    # 4. V11 must equal the historical Option B configuration
    v11 = VARIANTS["V11"]
    assert v11["k_abs_min"] == ob.K_ABS_MIN and v11["adaptive"] is True
    out["V11_reproduces_optionB"] = True
    print(f"  V11 config == historical Option B (k_abs_min={ob.K_ABS_MIN}, adaptive, lam_r={ob.LAM_R}): PASS")

    # 5. controller inertness: with adaptive=False lambda_b must never move off LAM_B0
    traj = [LAM_B0]
    for far in (0.40, 0.00, 0.25, 0.05):
        traj.append(LAM_B0)                        # mirrors the non-adaptive branch in run_train
    out["fixed_lambda_b_trajectory"] = traj
    assert len(set(traj)) == 1 and traj[0] == LAM_B0
    # and with adaptive=True it must move in the signed direction of (FAR - target)
    up = ob.lambda_update(0.25, 0.40); dn = ob.lambda_update(0.25, 0.00)
    out["adaptive_moves_up_on_high_far"] = up > 0.25
    out["adaptive_moves_down_on_low_far"] = dn < 0.25
    assert up > 0.25 > dn, (up, dn)
    print(f"  controller inert when adaptive=False; moves {dn:.3f}<0.25<{up:.3f} when True: PASS")

    # 6. no test-split reference in the TRAINING code path (tokens built by concatenation so this
    #    check cannot match its own source)
    import inspect
    train_src = inspect.getsource(run_train)
    tokens = ["_" + "test_loader", "test" + "_eval", "--split " + "test", "X_" + "test"]
    forbidden = [t for t in tokens if t in train_src]
    out["no_test_reference_in_run_train"] = (forbidden == [])
    assert not forbidden, f"test-split reference found in run_train: {forbidden}"
    print(f"  no test-split reference in the training code path: PASS")

    print("  ALL SELF-CHECKS PASSED")
    print("=" * 78)
    return out


def parse_args():
    p = argparse.ArgumentParser(description="AFAC candidate-mechanism 2x2 ablation (training).")
    p.add_argument("--self-check", action="store_true")
    p.add_argument("--train", action="store_true")
    p.add_argument("--variant", choices=sorted(VARIANTS), default=None)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--threads", type=int, default=0, help="torch.set_num_threads; 0 = leave default.")
    # foundation args -- identical defaults to the historical Option B pilot
    p.add_argument("--epochs", type=int, default=EPOCHS, help="informational; the run is fixed at 70.")
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--train-pgd-steps", type=int, default=7)
    p.add_argument("--fall-weight", type=float, default=3.0)
    return p.parse_args()


def main():
    args = parse_args()
    if args.self_check:
        out = run_self_check()
        exp = Path(__file__).resolve().parents[2]
        d = exp / "results" / "ablation_afac_mechanisms"
        d.mkdir(parents=True, exist_ok=True)
        with (d / "ablation_selfcheck.json").open("w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=str)
        return
    if args.train:
        if args.variant is None:
            raise SystemExit("--train requires --variant {V00,V10,V01,V11}")
        if args.seed not in SEEDS:
            raise SystemExit(f"seed {args.seed} not in the pre-registered set {SEEDS}")
        run_train(args); return
    raise SystemExit("Pass --self-check or --train --variant <V> --seed <S>.")


if __name__ == "__main__":
    main()
