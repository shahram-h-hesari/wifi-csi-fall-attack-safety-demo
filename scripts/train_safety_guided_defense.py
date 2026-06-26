"""
Stage 3b: safety-proxy-guided adversarial-training defense (PGD / FGSM+PGD).

Purpose:
    Train a defended UT-HAR LeNet whose checkpoint is selected on a
    SAFETY-CRITICAL validation score rather than on macro-F1 alone, with the
    explicit goal of improving attacked FALL recall (especially under PGD) while
    controlling false-fall alarms and avoiding clean-performance collapse.

    This extends the existing FGSM-only defense (scripts/train_converged_defense.py)
    in three ways:
        1. PGD (and FGSM+PGD, single- or multi-epsilon) adversarial training.
        2. An optional fall-weighted cross-entropy loss (class 1 = fall).
        3. Dual checkpoint selection -- the SAME run saves both:
             * the best checkpoint by a safety-proxy SafetyScore, and
             * the best checkpoint by the standard validation macro-F1,
           so safety-guided vs. standard selection can be compared head to head.

Data / protocol:
    Reuses the Stage 1 module (train_converged_clean_baseline) so the SenseFi
    UT-HAR loader, preprocessing, train/val/test split, and fall-binary metric
    code are byte-for-byte identical. Train=3977 / val=496 / test=500. The TEST
    split is NEVER used here (no test-set selection); SafetyScore and macro-F1
    are computed on VALIDATION only.

SafetyScore (validation only):
    SafetyScore = 0.35 * clean_fall_recall
                + 0.45 * pgd_fall_recall
                + 0.10 * fgsm_fall_recall
                - 0.10 * normalized_false_alarm_burden

    where all recalls are on the validation split, evaluation FGSM/PGD use the
    thesis evaluation epsilon (0.030), and:

      normalized_false_alarm_burden =
          0.5 * (fgsm_false_fall_alarms / n_nonfall_val)
        + 0.5 * (pgd_false_fall_alarms  / n_nonfall_val)

    i.e. the mean, across the two attacks, of the fraction of non-fall
    validation windows that are (falsely) raised as falls. It lies in [0, 1];
    higher = more false alarms = larger penalty. n_nonfall_val is the number of
    non-fall windows in the validation split.

    CLEAN-COLLAPSE GUARD (important): the raw SafetyScore above is maximized by a
    degenerate always-fall predictor (clean acc ~0.09, every non-fall window
    flagged as a fall), because the 0.10 false-alarm penalty cannot offset the
    +0.90 from clean/PGD/FGSM fall recall all = 1.0. Observed empirically for
    fall_weight=3 (variants B/C/D). SafetyScore selection is therefore restricted
    to checkpoints whose CLEAN validation accuracy and macro-F1 clear a guard
    (--min-clean-accuracy / --min-clean-macro-f1), enforcing the thesis
    requirement of no unacceptable clean collapse. The un-guarded best is still
    recorded in metadata for transparency.

Adversarial training mixing (per batch, batch-split -- efficient on CPU):
    * PGD-only variants:     50% clean + 50% PGD windows.
    * FGSM+PGD variants:     50% clean + 25% FGSM + 25% PGD windows.
    The adversarial portion is perturbed with the CURRENT model; the full
    reconstructed batch then takes a single (optionally fall-weighted) loss /
    backward step. Adversarial perturbations are generated with an UNWEIGHTED
    cross-entropy loss (the adversary does not know the defender's class
    weights); the TRAINING loss uses the configured (possibly weighted) loss.

Training PGD vs evaluation PGD:
    To keep CPU runtime manageable, TRAINING PGD uses a small number of steps
    (default 7, alpha = train_epsilon/4) on the adversarial sub-batch only.
    EVALUATION PGD (per-epoch validation diagnostics AND the separate test-set
    evaluation via run_converged_attacks.py) uses the thesis protocol:
    steps=10, alpha=epsilon/6. These are intentionally distinct and documented.

Scope / claim boundary:
    Window-level, software-tensor (processed CSI) digital-domain white-box
    robustness. NOT physical-layer / over-the-air, NOT certified robustness,
    NOT clinical or medical-device validation, NOT deployment safety.

Variants (preset via --variant; individual knobs still overridable):
    A: PGD-AT,            fall_weight=1, mix 50clean/50pgd,            eps=0.030
    B: PGD-AT,            fall_weight=3, mix 50clean/50pgd,            eps=0.030
    C: FGSM+PGD-AT,       fall_weight=3, mix 50clean/25fgsm/25pgd,     eps=0.030
    D: FGSM+PGD multi-eps,fall_weight=3, mix 50clean/25fgsm/25pgd,     eps={0.005,0.015,0.030}

Commands:
    python scripts/train_safety_guided_defense.py --help
    python scripts/train_safety_guided_defense.py --variant A --seed 42 --dry-run
    python scripts/train_safety_guided_defense.py --variant B --seed 42 \
        --epochs 60 --patience 12
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import platform
import sys
import time
from datetime import datetime, timezone

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim


# Thesis evaluation protocol constants (used for per-epoch validation
# diagnostics and to stay consistent with run_converged_attacks.py).
EVAL_EPSILON = 0.030
EVAL_PGD_STEPS = 10
EVAL_PGD_ALPHA_RULE = "epsilon/6"

FALL_CLASS_INDEX = 1
NUM_CLASSES = 7


# ----------------------------------------------------------------------------
# Variant presets. Each maps to a fully-specified config; CLI flags override.
# ----------------------------------------------------------------------------
VARIANT_PRESETS = {
    "A": {
        "attack_mode": "pgd",
        "fall_weight": 1.0,
        "train_epsilons": [0.030],
        "mix": "50clean_50pgd",
        "label": "pgd_at",
    },
    "B": {
        "attack_mode": "pgd",
        "fall_weight": 3.0,
        "train_epsilons": [0.030],
        "mix": "50clean_50pgd",
        "label": "pgd_at",
    },
    "C": {
        "attack_mode": "fgsm_pgd",
        "fall_weight": 3.0,
        "train_epsilons": [0.030],
        "mix": "50clean_25fgsm_25pgd",
        "label": "fgsm_pgd_at",
    },
    "D": {
        "attack_mode": "fgsm_pgd",
        "fall_weight": 3.0,
        "train_epsilons": [0.005, 0.015, 0.030],
        "mix": "50clean_25fgsm_25pgd",
        "label": "fgsm_pgd_multieps_at",
    },
}


def import_stage1():
    """Import the Stage 1 module so loader/preprocessing/metrics are identical."""
    experiment_dir = Path(__file__).resolve().parents[1]
    scripts_dir = experiment_dir / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import train_converged_clean_baseline as s1  # noqa: E402

    return s1


# ----------------------------------------------------------------------------
# Adversarial perturbation generators (no [0,1] clamp: processed CSI tensors).
# These use the UNWEIGHTED criterion passed in by the caller.
# ----------------------------------------------------------------------------
def fgsm_perturb(model, inputs, labels, criterion, epsilon):
    """Single-step FGSM on processed CSI tensors."""
    if epsilon == 0.0 or inputs.numel() == 0:
        return inputs.detach()
    x = inputs.clone().detach()
    x.requires_grad = True
    loss = criterion(model(x).float(), labels)
    model.zero_grad()
    loss.backward()
    adv = x + epsilon * x.grad.detach().sign()
    return adv.detach()


def pgd_perturb(model, inputs, labels, criterion, epsilon, steps, alpha):
    """Untargeted L-infinity PGD on processed CSI tensors (projected each step)."""
    if epsilon == 0.0 or inputs.numel() == 0:
        return inputs.detach()
    original = inputs.detach()
    adv = original.clone().detach()
    for _ in range(steps):
        adv.requires_grad = True
        loss = criterion(model(adv).float(), labels)
        model.zero_grad()
        loss.backward()
        with torch.no_grad():
            adv = adv + alpha * adv.grad.sign()
            perturbation = torch.clamp(adv - original, min=-epsilon, max=epsilon)
            adv = original + perturbation
        adv = adv.detach()
    return adv


# ----------------------------------------------------------------------------
# One adversarial-training epoch (batch-split mixing).
# ----------------------------------------------------------------------------
def train_one_epoch(
    model, loader, train_criterion, atk_criterion, optimizer, device,
    attack_mode, train_epsilons, train_pgd_steps, rng,
):
    """Mixed clean/adversarial training for one epoch using batch-split mixing.

    PGD-only:   first 50% of each batch stays clean, last 50% is PGD-perturbed.
    FGSM+PGD:   50% clean, 25% FGSM, 25% PGD.
    The training epsilon is sampled uniformly from ``train_epsilons`` per batch
    (single-element list => fixed epsilon).
    """
    model.train()
    total_loss = 0.0
    total = 0
    clean_correct = 0
    adv_correct = 0
    adv_total = 0

    for inputs, labels in loader:
        inputs = inputs.to(device).float()
        labels = labels.type(torch.LongTensor).to(device)
        bs = labels.size(0)

        eps = float(rng.choice(train_epsilons))
        pgd_alpha = eps / 4.0  # training PGD step size (smaller-step, documented)

        if attack_mode == "pgd":
            n_clean = bs // 2
            clean_x = inputs[:n_clean]
            pgd_src = inputs[n_clean:]
            pgd_lbl = labels[n_clean:]
            model.eval()
            pgd_adv = pgd_perturb(model, pgd_src, pgd_lbl, atk_criterion, eps,
                                  train_pgd_steps, pgd_alpha)
            model.train()
            batch_x = torch.cat([clean_x, pgd_adv], dim=0)
            batch_y = labels  # order preserved: [clean | pgd]
            adv_count = pgd_src.size(0)
        else:  # fgsm_pgd: 50 clean / 25 fgsm / 25 pgd
            n_clean = bs // 2
            n_fgsm = (bs - n_clean) // 2
            clean_x = inputs[:n_clean]
            fgsm_src = inputs[n_clean:n_clean + n_fgsm]
            fgsm_lbl = labels[n_clean:n_clean + n_fgsm]
            pgd_src = inputs[n_clean + n_fgsm:]
            pgd_lbl = labels[n_clean + n_fgsm:]
            model.eval()
            fgsm_adv = fgsm_perturb(model, fgsm_src, fgsm_lbl, atk_criterion, eps)
            pgd_adv = pgd_perturb(model, pgd_src, pgd_lbl, atk_criterion, eps,
                                  train_pgd_steps, pgd_alpha)
            model.train()
            batch_x = torch.cat([clean_x, fgsm_adv, pgd_adv], dim=0)
            batch_y = labels
            adv_count = fgsm_src.size(0) + pgd_src.size(0)
            n_clean = clean_x.size(0)

        optimizer.zero_grad()
        outputs = model(batch_x).float()
        loss = train_criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()

        preds = torch.argmax(outputs, dim=1)
        total_loss += loss.item() * bs
        total += bs
        clean_correct += (preds[:n_clean] == batch_y[:n_clean]).sum().item()
        adv_correct += (preds[n_clean:] == batch_y[n_clean:]).sum().item()
        adv_total += adv_count

    return {
        "train_loss": total_loss / total,
        "train_clean_accuracy": clean_correct / max(n_clean, 1) if total else 0.0,
        "train_adv_accuracy": adv_correct / adv_total if adv_total else 0.0,
    }


# ----------------------------------------------------------------------------
# Validation diagnostics: clean + FGSM@eval + PGD@eval, plus safety bundle.
# ----------------------------------------------------------------------------
def eval_attacked(model, loader, atk_criterion, device, attack, epsilon, steps, alpha):
    """Return (y_true, y_pred) for an FGSM or PGD attacked pass over a loader."""
    model.eval()
    y_true_all, y_pred_all = [], []
    for inputs, labels in loader:
        inputs = inputs.to(device).float()
        labels = labels.type(torch.LongTensor).to(device)
        if attack == "fgsm":
            adv = fgsm_perturb(model, inputs, labels, atk_criterion, epsilon)
        else:
            adv = pgd_perturb(model, inputs, labels, atk_criterion, epsilon, steps, alpha)
        with torch.no_grad():
            preds = torch.argmax(model(adv).float(), dim=1)
        y_true_all.append(labels.cpu().numpy())
        y_pred_all.append(preds.cpu().numpy())
    return np.concatenate(y_true_all), np.concatenate(y_pred_all)


def compute_validation_bundle(s1, model, val_loader, atk_criterion, device):
    """Compute the full per-epoch validation safety bundle.

    Returns a dict with clean/FGSM/PGD fall recall, false-fall alarms, macro-F1,
    accuracy, normalized false-alarm burden, and the SafetyScore.
    """
    eval_alpha = EVAL_EPSILON / 6.0

    # Clean.
    _, c_true, c_pred, _ = s1.run_inference(model, val_loader, atk_criterion, device)
    c_fb = s1.compute_fall_binary_metrics(c_true, c_pred)
    n_nonfall = c_fb["nonfall_windows"]

    # FGSM@eval.
    f_true, f_pred = eval_attacked(model, val_loader, atk_criterion, device,
                                   "fgsm", EVAL_EPSILON, EVAL_PGD_STEPS, eval_alpha)
    f_fb = s1.compute_fall_binary_metrics(f_true, f_pred)

    # PGD@eval.
    p_true, p_pred = eval_attacked(model, val_loader, atk_criterion, device,
                                   "pgd", EVAL_EPSILON, EVAL_PGD_STEPS, eval_alpha)
    p_fb = s1.compute_fall_binary_metrics(p_true, p_pred)

    fgsm_fp = f_fb["fall_false_positive"]
    pgd_fp = p_fb["fall_false_positive"]
    if n_nonfall > 0:
        nfab = 0.5 * (fgsm_fp / n_nonfall) + 0.5 * (pgd_fp / n_nonfall)
    else:
        nfab = 0.0

    safety_score = (
        0.35 * c_fb["fall_recall"]
        + 0.45 * p_fb["fall_recall"]
        + 0.10 * f_fb["fall_recall"]
        - 0.10 * nfab
    )

    return {
        "val_clean_accuracy": s1.accuracy_of(c_true, c_pred),
        "val_clean_macro_f1": s1.macro_f1_of(c_true, c_pred),
        "val_clean_fall_recall": c_fb["fall_recall"],
        "val_fgsm_fall_recall": f_fb["fall_recall"],
        "val_pgd_fall_recall": p_fb["fall_recall"],
        "val_fgsm_false_fall_alarms": fgsm_fp,
        "val_pgd_false_fall_alarms": pgd_fp,
        "val_clean_missed_fall_count": c_fb["fall_false_negative"],
        "val_fgsm_missed_fall_count": f_fb["fall_false_negative"],
        "val_pgd_missed_fall_count": p_fb["fall_false_negative"],
        "val_nonfall_windows": n_nonfall,
        "val_normalized_false_alarm_burden": nfab,
        "safety_score": safety_score,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 3b: safety-proxy-guided PGD / FGSM+PGD adversarial-training defense.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--variant", choices=list(VARIANT_PRESETS.keys()), required=True,
                        help="Defense variant preset (A/B/C/D). See module docstring.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--epochs", type=int, default=60, help="Maximum training epochs.")
    parser.add_argument("--patience", type=int, default=15,
                        help="Early-stopping patience on the SafetyScore. 0 disables.")
    parser.add_argument("--min-epochs", type=int, default=35,
                        help="Do not early-stop before this epoch. Guards against the "
                        "flat-zero SafetyScore of early training (fall recall starts at 0).")
    parser.add_argument("--lr", type=float, default=1e-3, help="Adam learning rate.")
    parser.add_argument("--batch-size", type=int, default=64, help="Training batch size.")
    parser.add_argument("--train-pgd-steps", type=int, default=7,
                        help="TRAINING PGD steps (smaller-step; eval PGD always uses 10).")
    parser.add_argument("--min-clean-accuracy", type=float, default=0.60,
                        help="Clean-collapse guard: a checkpoint is only eligible for "
                        "SafetyScore selection if its CLEAN validation accuracy is at "
                        "least this. Prevents the degenerate always-fall predictor "
                        "(clean acc ~0.09, all non-fall windows flagged) from winning, "
                        "since the raw SafetyScore's 0.10 false-alarm penalty alone "
                        "does not suppress it.")
    parser.add_argument("--min-clean-macro-f1", type=float, default=0.50,
                        help="Clean-collapse guard companion: minimum CLEAN validation "
                        "macro-F1 for SafetyScore eligibility.")
    # Optional overrides (default: use the variant preset).
    parser.add_argument("--fall-weight", type=float, default=None,
                        help="Override fall-class (class 1) loss weight.")
    parser.add_argument("--train-epsilons", type=str, default=None,
                        help="Override comma-separated training epsilons, e.g. '0.005,0.015,0.030'.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Build loaders/model and print planned paths WITHOUT training.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preset = VARIANT_PRESETS[args.variant]

    fall_weight = args.fall_weight if args.fall_weight is not None else preset["fall_weight"]
    if args.train_epsilons is not None:
        train_epsilons = [float(x) for x in args.train_epsilons.split(",") if x.strip()]
    else:
        train_epsilons = list(preset["train_epsilons"])
    attack_mode = preset["attack_mode"]
    mix = preset["mix"]

    experiment_dir = Path(__file__).resolve().parents[1]
    benchmark_dir = experiment_dir / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    data_dir = benchmark_dir / "Data" / "UT_HAR"

    seed_tag = f"seed{args.seed}"
    checkpoints_dir = experiment_dir / "checkpoints" / "safety_guided_defense" / seed_tag
    logs_dir = experiment_dir / "results" / "safety_guided_defense" / seed_tag / "logs"

    if not benchmark_dir.exists():
        raise FileNotFoundError(f"SenseFi clone not found: {benchmark_dir}")
    if not data_dir.exists():
        raise FileNotFoundError(f"UT-HAR data not found: {data_dir}")

    s1 = import_stage1()
    s1.patch_sensefi_dataset_loader(benchmark_dir)
    if str(benchmark_dir) not in sys.path:
        sys.path.insert(0, str(benchmark_dir))
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from model_factory import build_model

    s1.set_seed(args.seed)

    data = s1.load_raw_ut_har(benchmark_dir)
    train_loader, val_loader, test_loader, split_sizes = s1.build_loaders(data, args.batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model("lenet").to(device)

    # Training loss: optionally fall-weighted CE. Attack loss: always unweighted CE.
    class_weights = torch.ones(NUM_CLASSES, device=device)
    class_weights[FALL_CLASS_INDEX] = fall_weight
    train_criterion = nn.CrossEntropyLoss(weight=class_weights)
    atk_criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    rng = np.random.default_rng(args.seed)

    # Run name encodes seed, variant, fall weight, attack mixture.
    fw_tag = f"fw{int(fall_weight) if float(fall_weight).is_integer() else fall_weight}"
    run_name = f"{seed_tag}_variant{args.variant}_{preset['label']}_{fw_tag}_{mix}"

    # Dual-selection checkpoint paths (same run; selection method in the name).
    ckpt_safety = checkpoints_dir / f"{run_name}_bySafetyScore_best.pt"
    ckpt_f1 = checkpoints_dir / f"{run_name}_byValMacroF1_best.pt"
    ckpt_last = checkpoints_dir / f"{run_name}_last.pt"
    log_path = logs_dir / f"{run_name}_training_log.csv"
    metadata_path = logs_dir / f"{run_name}_metadata.json"

    selection_def = (
        "SafetyScore = 0.35*clean_fall_recall + 0.45*pgd_fall_recall "
        "+ 0.10*fgsm_fall_recall - 0.10*normalized_false_alarm_burden "
        "(validation only; FGSM/PGD at eval epsilon 0.030)"
    )

    print("Stage 3b: safety-proxy-guided adversarial-training defense")
    print("-" * 72)
    print(f"Variant:            {args.variant}  ({preset['label']})")
    print(f"Run name:           {run_name}")
    print(f"Device:             {device}")
    print(f"Seed:               {args.seed}")
    print(f"Attack mode:        {attack_mode}  | mix: {mix}")
    print(f"Fall weight:        {fall_weight}")
    print(f"Train epsilons:     {train_epsilons}")
    print(f"Train PGD steps:    {args.train_pgd_steps} (alpha=eps/4)")
    print(f"Eval  PGD protocol: steps={EVAL_PGD_STEPS}, alpha={EVAL_PGD_ALPHA_RULE}, eps={EVAL_EPSILON}")
    print(f"Max epochs:         {args.epochs}  | patience: {args.patience}")
    print(f"Split sizes:        {split_sizes}")
    print(f"Selection:          {selection_def}")
    print("-" * 72)

    if args.dry_run:
        print("[dry-run] model + loaders built; no training, no files written.")
        for label, p in [("ckpt_bySafetyScore", ckpt_safety), ("ckpt_byValMacroF1", ckpt_f1),
                         ("ckpt_last", ckpt_last), ("training_log", log_path),
                         ("metadata_json", metadata_path)]:
            print(f"    {label}: {p}")
        return

    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_fields = [
        "epoch", "train_loss", "train_clean_accuracy", "train_adv_accuracy",
        "val_clean_accuracy", "val_clean_macro_f1", "val_clean_fall_recall",
        "val_fgsm_fall_recall", "val_pgd_fall_recall",
        "val_fgsm_false_fall_alarms", "val_pgd_false_fall_alarms",
        "val_clean_missed_fall_count", "val_fgsm_missed_fall_count",
        "val_pgd_missed_fall_count", "val_normalized_false_alarm_burden",
        "safety_score", "selected_by_safety_score", "selected_by_val_macro_f1",
    ]

    history = []
    best_safety = -1e9
    best_safety_epoch = -1
    best_safety_record = None
    best_f1 = -1e9
    best_f1_epoch = -1
    best_f1_record = None
    # Raw (un-guarded) SafetyScore tracking: documents what the naive score would
    # have picked (typically the degenerate always-fall predictor); not saved as a
    # checkpoint, recorded in metadata only for transparency.
    best_raw_safety = -1e9
    best_raw_epoch = -1
    best_raw_bundle = None
    no_improve = 0  # patience tracks eligible SafetyScore improvements
    start = time.time()

    for epoch in range(1, args.epochs + 1):
        tr = train_one_epoch(
            model, train_loader, train_criterion, atk_criterion, optimizer, device,
            attack_mode, train_epsilons, args.train_pgd_steps, rng,
        )
        vb = compute_validation_bundle(s1, model, val_loader, atk_criterion, device)

        # Clean-collapse guard: a checkpoint must retain non-degenerate clean
        # performance to be eligible for SafetyScore selection.
        eligible = (vb["val_clean_accuracy"] >= args.min_clean_accuracy
                    and vb["val_clean_macro_f1"] >= args.min_clean_macro_f1)
        improved_safety = eligible and vb["safety_score"] > best_safety
        improved_f1 = vb["val_clean_macro_f1"] > best_f1

        # Track the raw (un-guarded) best for the metadata record only.
        if vb["safety_score"] > best_raw_safety:
            best_raw_safety = vb["safety_score"]
            best_raw_epoch = epoch
            best_raw_bundle = vb

        if improved_safety:
            best_safety = vb["safety_score"]
            best_safety_epoch = epoch
            no_improve = 0
            torch.save({"epoch": epoch, "model_state_dict": model.state_dict(),
                        "selection_method": "safety_score_clean_guarded", "safety_score": vb["safety_score"],
                        "val_bundle": vb, "variant": args.variant, "run_name": run_name,
                        "args": vars(args)}, ckpt_safety)
        elif best_safety_epoch > 0:
            # Only count toward patience once an eligible checkpoint has appeared.
            no_improve += 1

        if improved_f1:
            best_f1 = vb["val_clean_macro_f1"]
            best_f1_epoch = epoch
            torch.save({"epoch": epoch, "model_state_dict": model.state_dict(),
                        "selection_method": "val_macro_f1", "val_macro_f1": vb["val_clean_macro_f1"],
                        "val_bundle": vb, "variant": args.variant, "run_name": run_name,
                        "args": vars(args)}, ckpt_f1)

        record = {"epoch": epoch, "train_loss": tr["train_loss"],
                  "train_clean_accuracy": tr["train_clean_accuracy"],
                  "train_adv_accuracy": tr["train_adv_accuracy"],
                  "selected_by_safety_score": int(improved_safety),
                  "selected_by_val_macro_f1": int(improved_f1)}
        record.update({k: vb[k] for k in (
            "val_clean_accuracy", "val_clean_macro_f1", "val_clean_fall_recall",
            "val_fgsm_fall_recall", "val_pgd_fall_recall",
            "val_fgsm_false_fall_alarms", "val_pgd_false_fall_alarms",
            "val_clean_missed_fall_count", "val_fgsm_missed_fall_count",
            "val_pgd_missed_fall_count", "val_normalized_false_alarm_burden",
            "safety_score")})
        history.append(record)
        if improved_safety:
            best_safety_record = record
        if improved_f1:
            best_f1_record = record

        flags = (("S" if improved_safety else " ") + ("F" if improved_f1 else " ")
                 + ("g" if not eligible else " "))  # 'g' = blocked by clean-collapse guard
        print(
            f"Epoch {epoch:03d}/{args.epochs} | loss={tr['train_loss']:.4f} | "
            f"clean_fr={vb['val_clean_fall_recall']:.3f} pgd_fr={vb['val_pgd_fall_recall']:.3f} "
            f"fgsm_fr={vb['val_fgsm_fall_recall']:.3f} | "
            f"pgd_FP={vb['val_pgd_false_fall_alarms']} fgsm_FP={vb['val_fgsm_false_fall_alarms']} | "
            f"nfab={vb['val_normalized_false_alarm_burden']:.3f} "
            f"score={vb['safety_score']:.4f} f1={vb['val_clean_macro_f1']:.4f} [{flags}]"
        )

        if (args.patience > 0 and epoch >= args.min_epochs
                and no_improve >= args.patience):
            print(f"Early stopping at epoch {epoch}: no SafetyScore improvement for "
                  f"{args.patience} epochs (best safety epoch {best_safety_epoch}).")
            break

    elapsed = time.time() - start
    last_epoch = history[-1]["epoch"]
    torch.save({"epoch": last_epoch, "model_state_dict": model.state_dict(),
                "selection_method": "last", "variant": args.variant,
                "run_name": run_name, "args": vars(args)}, ckpt_last)

    with log_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=log_fields)
        writer.writeheader()
        for r in history:
            writer.writerow({k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in log_fields})

    metadata = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "stage3b_safety_proxy_guided_adversarial_training",
        "variant": args.variant,
        "variant_label": preset["label"],
        "run_name": run_name,
        "seed": args.seed,
        "attack_mode": attack_mode,
        "training_mixture": mix,
        "fall_weight": fall_weight,
        "train_epsilons": train_epsilons,
        "train_pgd_steps": args.train_pgd_steps,
        "train_pgd_alpha_rule": "train_epsilon/4",
        "eval_protocol": {"epsilon": EVAL_EPSILON, "pgd_steps": EVAL_PGD_STEPS,
                          "pgd_alpha_rule": EVAL_PGD_ALPHA_RULE},
        "selection_score_definition": selection_def,
        "clean_collapse_guard": {
            "min_clean_accuracy": args.min_clean_accuracy,
            "min_clean_macro_f1": args.min_clean_macro_f1,
            "rationale": (
                "The raw SafetyScore (0.10 false-alarm penalty) is maximized by a "
                "degenerate always-fall predictor (clean acc ~0.09, every non-fall "
                "window flagged), which violates the 'no unacceptable clean-performance "
                "collapse' requirement. SafetyScore selection is therefore restricted "
                "to checkpoints passing this clean-performance gate."
            ),
        },
        "raw_ungated_safety_best": {
            "note": "What the un-guarded SafetyScore would have selected (NOT saved as a checkpoint).",
            "epoch": best_raw_epoch,
            "safety_score": best_raw_safety,
            "val_clean_accuracy": (best_raw_bundle or {}).get("val_clean_accuracy"),
            "val_clean_macro_f1": (best_raw_bundle or {}).get("val_clean_macro_f1"),
            "val_clean_fall_recall": (best_raw_bundle or {}).get("val_clean_fall_recall"),
            "val_pgd_fall_recall": (best_raw_bundle or {}).get("val_pgd_fall_recall"),
            "val_pgd_false_fall_alarms": (best_raw_bundle or {}).get("val_pgd_false_fall_alarms"),
        },
        "normalized_false_alarm_burden_definition": (
            "0.5*(fgsm_false_fall_alarms/n_nonfall_val) + "
            "0.5*(pgd_false_fall_alarms/n_nonfall_val); range [0,1]; "
            f"n_nonfall_val from validation split"
        ),
        "adversary_loss": "unweighted cross-entropy (defender class weights not used by adversary)",
        "training_loss": f"cross-entropy with class weights (fall class {FALL_CLASS_INDEX} = {fall_weight})",
        "best_safety_epoch": best_safety_epoch,
        "best_safety_score": best_safety,
        "best_safety_record": best_safety_record,
        "best_val_macro_f1_epoch": best_f1_epoch,
        "best_val_macro_f1": best_f1,
        "best_val_macro_f1_record": best_f1_record,
        "epochs_run": last_epoch,
        "max_epochs": args.epochs,
        "patience": args.patience,
        "min_epochs": args.min_epochs,
        "learning_rate": args.lr,
        "batch_size": args.batch_size,
        "split_sizes": split_sizes,
        "checkpoint_bySafetyScore": str(ckpt_safety),
        "checkpoint_byValMacroF1": str(ckpt_f1),
        "checkpoint_last": str(ckpt_last),
        "training_log_csv": str(log_path),
        "claim_boundary": (
            "Digital-domain white-box robustness on processed CSI tensors; "
            "NOT physical/over-the-air, NOT certified, NOT clinical or deployment safety."
        ),
        "device": str(device),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "git_branch": s1.get_command_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(experiment_dir)),
        "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(experiment_dir)),
        "elapsed_seconds": elapsed,
    }
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("-" * 72)
    print(f"Variant {args.variant} done in {elapsed:.1f}s ({last_epoch} epochs).")
    print(f"  best-by-SafetyScore : epoch {best_safety_epoch}  score={best_safety:.4f}")
    if best_safety_record:
        print(f"     val clean_fr={best_safety_record['val_clean_fall_recall']:.3f} "
              f"pgd_fr={best_safety_record['val_pgd_fall_recall']:.3f} "
              f"fgsm_fr={best_safety_record['val_fgsm_fall_recall']:.3f}")
    print(f"  best-by-ValMacroF1  : epoch {best_f1_epoch}  f1={best_f1:.4f}")
    print(f"  checkpoints -> {checkpoints_dir}")
    print(f"  log         -> {log_path}")


if __name__ == "__main__":
    main()
