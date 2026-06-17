"""
Stage 2: attack the FROZEN Stage 1 converged clean checkpoint (no retraining).

Purpose:
    Apply software-level FGSM and PGD perturbations to processed UT-HAR CSI
    tensors against the converged clean LeNet baseline saved in Stage 1, instead
    of the old `*_short` behavior that retrained a fresh 5-epoch model inside
    every attack script. The model weights are loaded once and never updated.

Splits:
    Primary results are on the held-out TEST split (n=500). A clearly-labeled
    LEGACY combined validation+test pool (n=996) is also exported, for
    comparison to prior 996-window thesis artifacts only. The legacy pool is
    never used for any training or selection (there is no training here at all).

Attacks:
    FGSM (single step) and PGD (L-infinity, projected). Defaults target
    epsilon = 0.030. PGD uses steps=10 and alpha=epsilon/6 (= 0.005 at
    epsilon=0.03, matching the old single-epsilon PGD script which used a fixed
    alpha=0.005, and the 18-epsilon sweep which used alpha=epsilon/6). The full
    epsilon sweep is intentionally NOT run by this script yet.

Important claim boundary:
    These are window-level, software-tensor adversarial perturbations on
    processed CSI features. They are not physical-layer, packet-level,
    preamble-level, SDR, or over-the-air attacks, and not clinical or
    medical-device validation.

Expected run location:
    Repository root (standalone wifi-csi-fall-attack-safety-demo repo).

Commands:
    python scripts/run_converged_attacks.py --help
    python scripts/run_converged_attacks.py --dry-run
    python scripts/run_converged_attacks.py --epsilon 0.03 --attacks both
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import platform
import sys
from datetime import datetime, timezone

import numpy as np
import torch
import torch.nn as nn


DEFAULT_CHECKPOINT = Path("checkpoints/converged_clean_baseline/converged_seed42_best.pt")
REGEN_COMMAND = (
    "python scripts/train_converged_clean_baseline.py "
    "--epochs 200 --patience 20 --seed 42 --run-name converged_seed42"
)

# Canonical 18-epsilon sweep list (epsilon 0.0 = clean / no perturbation).
EPSILON_SWEEP = [
    0.0, 0.0025, 0.005, 0.0075, 0.010, 0.0125, 0.015, 0.0175, 0.020,
    0.025, 0.030, 0.035, 0.040, 0.045, 0.050, 0.055, 0.060, 0.075,
]


def import_stage1():
    """Import the Stage 1 module so loader/preprocessing/metrics are identical."""
    experiment_dir = Path(__file__).resolve().parents[1]
    scripts_dir = experiment_dir / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import train_converged_clean_baseline as s1  # noqa: E402

    return s1


def epsilon_to_token(epsilon: float) -> str:
    """0.03 -> '0_03', 0.0 -> '0' (matches the old filename convention)."""
    text = f"{epsilon:.6f}".rstrip("0").rstrip(".")
    return text.replace(".", "_")


def generate_attacked_batch(model, inputs, labels, criterion, attack, epsilon, alpha, steps):
    """Return adversarial inputs for one batch using the proven FGSM/PGD math.

    No value clamp to [0, 1]: UT-HAR tensors are processed CSI features, not
    image pixels (consistent with the old attack scripts).
    """
    if epsilon == 0.0:
        return inputs.detach()

    if attack == "fgsm":
        x = inputs.clone().detach()
        x.requires_grad = True
        outputs = model(x).float()
        loss = criterion(outputs, labels)
        model.zero_grad()
        loss.backward()
        adv = x + epsilon * x.grad.detach().sign()
        return adv.detach()

    # PGD: untargeted L-infinity, projected after each step.
    original = inputs.detach()
    adv = original.clone().detach()
    for _ in range(steps):
        adv.requires_grad = True
        outputs = model(adv).float()
        loss = criterion(outputs, labels)
        model.zero_grad()
        loss.backward()
        with torch.no_grad():
            adv = adv + alpha * adv.grad.sign()
            perturbation = torch.clamp(adv - original, min=-epsilon, max=epsilon)
            adv = original + perturbation
        adv = adv.detach()
    return adv


def collect_paired_predictions(model, loader, criterion, device, attack, epsilon, alpha, steps, s1):
    """Run one attack over a loader; return (rows, y_true, y_clean, y_attacked).

    rows use a paired clean+attacked schema compatible with the old FGSM/PGD
    prediction CSVs (PGD additionally records alpha and pgd_steps).
    """
    model.eval()
    rows = []
    y_true_all, y_clean_all, y_attacked_all = [], [], []
    sample_id = 0

    for inputs, labels in loader:
        inputs = inputs.to(device).float()
        labels = labels.to(device).long()

        with torch.no_grad():
            clean_out = model(inputs).float()
            clean_probs = torch.softmax(clean_out, dim=1)
            clean_conf, clean_pred = torch.max(clean_probs, dim=1)

        adv = generate_attacked_batch(model, inputs, labels, criterion, attack, epsilon, alpha, steps)

        with torch.no_grad():
            adv_out = model(adv).float()
            adv_probs = torch.softmax(adv_out, dim=1)
            adv_conf, adv_pred = torch.max(adv_probs, dim=1)

        labels_np = labels.cpu().numpy()
        clean_np = clean_pred.cpu().numpy()
        adv_np = adv_pred.cpu().numpy()
        clean_conf_np = clean_conf.cpu().numpy()
        adv_conf_np = adv_conf.cpu().numpy()

        for i in range(len(labels_np)):
            t = int(labels_np[i])
            cp = int(clean_np[i])
            ap = int(adv_np[i])
            row = {
                "sample_id": sample_id,
                "epsilon": f"{epsilon:.6f}",
                "true_label": t,
                "true_class_name": s1.CLASS_NAMES.get(t, f"unknown_{t}"),
                "clean_predicted_label": cp,
                "clean_predicted_class_name": s1.CLASS_NAMES.get(cp, f"unknown_{cp}"),
                "attacked_predicted_label": ap,
                "attacked_predicted_class_name": s1.CLASS_NAMES.get(ap, f"unknown_{ap}"),
                "fall_true_binary": s1.to_fall_binary(t),
                "clean_fall_pred_binary": s1.to_fall_binary(cp),
                "attacked_fall_pred_binary": s1.to_fall_binary(ap),
                "clean_prediction_confidence": f"{float(clean_conf_np[i]):.6f}",
                "attacked_prediction_confidence": f"{float(adv_conf_np[i]):.6f}",
                "clean_correct": int(cp == t),
                "attacked_correct": int(ap == t),
                "prediction_changed": int(cp != ap),
            }
            if attack == "pgd":
                row["alpha"] = f"{alpha:.6f}"
                row["pgd_steps"] = steps
            rows.append(row)
            sample_id += 1

        y_true_all.append(labels_np)
        y_clean_all.append(clean_np)
        y_attacked_all.append(adv_np)

    return (
        rows,
        np.concatenate(y_true_all),
        np.concatenate(y_clean_all),
        np.concatenate(y_attacked_all),
    )


def write_predictions_csv(path: Path, rows: list) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def compute_attack_safety_metrics(y_true, y_clean, y_attacked, attack, epsilon, alpha, steps, split, s1):
    """Compute the full Stage 2 metric set for an attacked split."""
    attacked_fb = s1.compute_fall_binary_metrics(y_true, y_attacked)
    clean_fb = s1.compute_fall_binary_metrics(y_true, y_clean)
    prediction_change_rate = float(np.mean(y_clean != y_attacked)) if len(y_true) else 0.0

    return {
        "attack": attack,
        "split": split,
        "epsilon": f"{epsilon:.6f}",
        "alpha": f"{alpha:.6f}" if attack == "pgd" else "n/a",
        "pgd_steps": steps if attack == "pgd" else "n/a",
        "n_windows": int(len(y_true)),
        # clean reference (under this same loaded checkpoint)
        "clean_accuracy": s1.accuracy_of(y_true, y_clean),
        "clean_macro_f1": s1.macro_f1_of(y_true, y_clean),
        "clean_fall_recall": clean_fb["fall_recall"],
        # attacked multiclass
        "attack_accuracy": s1.accuracy_of(y_true, y_attacked),
        "attack_macro_f1": s1.macro_f1_of(y_true, y_attacked),
        # attacked fall-vs-nonfall safety proxy
        "fall_recall": attacked_fb["fall_recall"],
        "missed_fall_rate": attacked_fb["missed_fall_rate"],
        "fall_precision": attacked_fb["fall_precision"],
        "fall_f1": attacked_fb["fall_f1"],
        "fall_true_positive": attacked_fb["fall_true_positive"],
        "fall_false_negative": attacked_fb["fall_false_negative"],
        "fall_false_positive": attacked_fb["fall_false_positive"],
        "fall_true_negative": attacked_fb["fall_true_negative"],
        "false_fall_alarm_count": attacked_fb["fall_false_positive"],
        "prediction_change_rate": prediction_change_rate,
    }


def read_metric_value_csv(path: Path) -> dict:
    if not path.exists():
        return {}
    out = {}
    with path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["metric"]] = row["value"]
    return out


def stage1_clean_references(results_dir: Path) -> dict:
    """Pull committed Stage 1 clean metrics for cross-reference in metadata."""
    test_sum = read_metric_value_csv(results_dir / "converged_seed42_summary_metrics.csv")
    test_fall = read_metric_value_csv(results_dir / "converged_seed42_fall_binary_metrics.csv")
    legacy_sum = read_metric_value_csv(results_dir / "converged_seed42_legacy_eval_summary_metrics.csv")
    legacy_fall = read_metric_value_csv(results_dir / "converged_seed42_legacy_eval_fall_binary_metrics.csv")
    return {
        "test_accuracy": test_sum.get("test_accuracy"),
        "test_macro_f1": test_sum.get("test_macro_f1"),
        "test_fall_recall": test_fall.get("fall_recall"),
        "legacy_accuracy": legacy_sum.get("legacy_accuracy"),
        "legacy_macro_f1": legacy_sum.get("legacy_macro_f1"),
        "legacy_fall_recall": legacy_fall.get("fall_recall"),
    }


def sweep_summary_row(m: dict) -> dict:
    """Map a metrics dict into an ordered epsilon-sweep summary row."""
    def f(x):
        return f"{x:.6f}" if isinstance(x, float) else x

    return {
        "attack": m["attack"],
        "split": m["split"],
        "epsilon": m["epsilon"],
        "pgd_steps": m["pgd_steps"],
        "pgd_alpha": m["alpha"],
        "attack_accuracy": f(m["attack_accuracy"]),
        "attack_macro_f1": f(m["attack_macro_f1"]),
        "fall_recall": f(m["fall_recall"]),
        "missed_fall_rate": f(m["missed_fall_rate"]),
        "fall_precision": f(m["fall_precision"]),
        "fall_f1": f(m["fall_f1"]),
        "fall_true_positive": m["fall_true_positive"],
        "fall_false_negative": m["fall_false_negative"],
        "fall_false_positive": m["fall_false_positive"],
        "fall_true_negative": m["fall_true_negative"],
        "false_fall_alarm_count": m["false_fall_alarm_count"],
        "prediction_change_rate": f(m["prediction_change_rate"]),
        "fall_recall_drop_vs_clean": f(m["fall_recall_drop_vs_clean"]),
        "accuracy_drop_vs_clean": f(m["accuracy_drop_vs_clean"]),
    }


def write_sweep_summary_csv(path: Path, rows: list) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def find_sweep_thresholds(metric_dicts: list) -> dict:
    """Given per-epsilon metric dicts (ascending epsilon) for one attack/split,
    return the epsilon thresholds of interest. Clean fall recall is taken from
    epsilon 0.0 (the unperturbed row).
    """
    ms = sorted(metric_dicts, key=lambda d: float(d["epsilon"]))
    clean_recall = ms[0]["clean_fall_recall"]

    def first(predicate):
        for d in ms:
            if predicate(d):
                return float(d["epsilon"])
        return None

    return {
        "clean_fall_recall": clean_recall,
        "first_epsilon_drop_ge_0_10": first(
            lambda d: (clean_recall - d["fall_recall"]) >= 0.10
        ),
        "first_epsilon_recall_below_0_50": first(lambda d: d["fall_recall"] < 0.50),
        "first_epsilon_recall_zero": first(lambda d: d["fall_recall"] == 0.0),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 2: FGSM/PGD attacks on the frozen converged clean checkpoint.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--epsilon", type=float, default=0.03, help="Attack epsilon (L-inf).")
    parser.add_argument(
        "--attacks", choices=["fgsm", "pgd", "both"], default="both", help="Which attacks to run."
    )
    parser.add_argument("--pgd-steps", type=int, default=10, help="PGD iterations.")
    parser.add_argument(
        "--pgd-alpha",
        type=float,
        default=None,
        help="PGD step size. Default: epsilon/6 (= old single-epsilon alpha 0.005 at eps=0.03).",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed (loader batching only).")
    parser.add_argument(
        "--run-name", type=str, default="converged_seed42", help="Output filename prefix."
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=str(DEFAULT_CHECKPOINT),
        help="Path to the frozen Stage 1 checkpoint.",
    )
    parser.add_argument(
        "--epsilon-sweep",
        action="store_true",
        help="Run the canonical 18-epsilon FGSM/PGD sweep against the frozen "
        "checkpoint (PGD alpha = epsilon/6 per point) instead of a single epsilon. "
        "Writes sweep summary + aggregated per-window prediction CSVs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load checkpoint, build loaders, confirm clean accuracy and print planned "
        "output paths WITHOUT running attacks or writing any files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    experiment_dir = Path(__file__).resolve().parents[1]
    benchmark_dir = experiment_dir / "third_party" / "WiFi-CSI-Sensing-Benchmark"
    data_dir = benchmark_dir / "Data" / "UT_HAR"
    checkpoint_path = (experiment_dir / args.checkpoint) if not Path(args.checkpoint).is_absolute() else Path(args.checkpoint)

    results_dir = experiment_dir / "results" / "converged_attacks"
    stage1_results_dir = experiment_dir / "results" / "converged_baseline"

    # ---- Fail fast on a missing checkpoint, with the regeneration command. ----
    if not checkpoint_path.exists():
        raise FileNotFoundError(
            "Frozen Stage 1 checkpoint not found:\n"
            f"  {checkpoint_path}\n\n"
            "It is git-ignored and local-only, but fully regenerable from Stage 1.\n"
            "Recreate it with:\n"
            f"  {REGEN_COMMAND}"
        )
    if not benchmark_dir.exists():
        raise FileNotFoundError(f"SenseFi clone not found: {benchmark_dir}")
    if not data_dir.exists():
        raise FileNotFoundError(f"UT-HAR data not found: {data_dir}")

    s1 = import_stage1()
    s1.patch_sensefi_dataset_loader(benchmark_dir)
    if str(benchmark_dir) not in sys.path:
        sys.path.insert(0, str(benchmark_dir))
    from UT_HAR_model import UT_HAR_LeNet

    s1.set_seed(args.seed)

    data = s1.load_raw_ut_har(benchmark_dir)
    _, _, test_loader, split_sizes = s1.build_loaders(data, 64)

    legacy_X = torch.cat((data["X_val"], data["X_test"]), 0)
    legacy_y = torch.cat((data["y_val"], data["y_test"]), 0)
    legacy_loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(legacy_X, legacy_y),
        batch_size=256, shuffle=False, drop_last=False,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    state = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model = UT_HAR_LeNet().to(device)
    model.load_state_dict(state["model_state_dict"], strict=True)
    model.eval()
    criterion = nn.CrossEntropyLoss()

    checkpoint_epoch = state.get("epoch")
    alpha = args.pgd_alpha if args.pgd_alpha is not None else args.epsilon / 6.0
    attacks = ["fgsm", "pgd"] if args.attacks == "both" else [args.attacks]
    eps_token = epsilon_to_token(args.epsilon)
    loaders = {"test": test_loader, "legacy": legacy_loader}
    clean_refs = stage1_clean_references(stage1_results_dir)

    # ------------------------------------------------------------------
    # Epsilon-sweep mode: 18-point FGSM/PGD sweep, PGD alpha = epsilon/6.
    # ------------------------------------------------------------------
    if args.epsilon_sweep:
        sweep_planned = {}
        for attack in attacks:
            for split in ("test", "legacy"):
                sweep_planned[f"{attack}_{split}_summary"] = (
                    results_dir / f"{args.run_name}_{attack}_epsilon_sweep_{split}.csv"
                )
                sweep_planned[f"{attack}_{split}_predictions"] = (
                    results_dir / f"{args.run_name}_{attack}_sweep_predictions_{split}.csv"
                )
        sweep_meta_path = results_dir / f"{args.run_name}_sweep_metadata.json"

        print("Stage 2: converged-checkpoint EPSILON SWEEP")
        print("-" * 70)
        print(f"Checkpoint:        {checkpoint_path}")
        print(f"Checkpoint epoch:  {checkpoint_epoch}")
        print(f"Device:            {device}")
        print(f"Attacks:           {attacks}")
        print(f"Epsilon list ({len(EPSILON_SWEEP)}): {EPSILON_SWEEP}")
        print(f"PGD steps / alpha: {args.pgd_steps} / epsilon/6 per point")
        print(f"Split sizes:       {split_sizes}")
        print("-" * 70)

        if args.dry_run:
            _, yt, yc, _ = s1.run_inference(model, test_loader, criterion, device)
            print(f"[dry-run] clean TEST accuracy from loaded checkpoint: {s1.accuracy_of(yt, yc):.4f} "
                  f"(Stage 1 committed: {clean_refs.get('test_accuracy')})")
            print("[dry-run] no sweep executed, no files written.")
            print("[dry-run] planned sweep output files:")
            for key, path in sweep_planned.items():
                print(f"    {key}: {path}")
            print(f"    sweep_metadata_json: {sweep_meta_path}")
            return

        # ---- Real sweep (only when NOT a dry-run). ----
        results_dir.mkdir(parents=True, exist_ok=True)
        thresholds = {}
        for attack in attacks:
            for split, loader in loaders.items():
                summary_rows = []
                metric_dicts = []
                all_pred_rows = []
                for eps in EPSILON_SWEEP:
                    a = (eps / 6.0) if attack == "pgd" else 0.0
                    rows, y_true, y_clean, y_attacked = collect_paired_predictions(
                        model, loader, criterion, device, attack, eps, a, args.pgd_steps, s1
                    )
                    m = compute_attack_safety_metrics(
                        y_true, y_clean, y_attacked, attack, eps, a, args.pgd_steps, split, s1
                    )
                    m["fall_recall_drop_vs_clean"] = m["clean_fall_recall"] - m["fall_recall"]
                    m["accuracy_drop_vs_clean"] = m["clean_accuracy"] - m["attack_accuracy"]
                    metric_dicts.append(m)
                    summary_rows.append(sweep_summary_row(m))
                    all_pred_rows.extend(rows)
                    print(
                        f"{attack.upper():4s} [{split:6s}] eps={eps:.4f} "
                        f"acc={m['attack_accuracy']:.4f} fall_recall={m['fall_recall']:.4f} "
                        f"missed={m['missed_fall_rate']:.4f} FP={m['false_fall_alarm_count']}"
                    )

                write_sweep_summary_csv(sweep_planned[f"{attack}_{split}_summary"], summary_rows)
                write_predictions_csv(sweep_planned[f"{attack}_{split}_predictions"], all_pred_rows)
                thresholds[f"{attack}_{split}"] = find_sweep_thresholds(metric_dicts)

        sweep_metadata = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "stage": "stage2_converged_attacks_epsilon_sweep",
            "run_name": args.run_name,
            "checkpoint_path": str(checkpoint_path),
            "checkpoint_epoch": checkpoint_epoch,
            "checkpoint_val_macro_f1": state.get("val_macro_f1"),
            "stage1_clean_references": clean_refs,
            "epsilon_list": EPSILON_SWEEP,
            "attack_parameters": {
                "attacks": attacks,
                "pgd_steps": args.pgd_steps,
                "pgd_alpha_rule": "epsilon/6 per point",
                "epsilon_zero_handling": "epsilon=0.0 applies no perturbation (clean baseline row)",
                "value_clamp": "none (processed CSI tensors, not [0,1] pixels)",
                "seed": args.seed,
            },
            "split_sizes": split_sizes,
            "legacy_note": (
                "legacy val+test (996 windows) is a comparison-only pool for prior "
                "thesis artifacts; no training or selection occurs in Stage 2."
            ),
            "fall_recall_thresholds": thresholds,
            "device": str(device),
            "python_version": platform.python_version(),
            "torch_version": torch.__version__,
            "sensefi_commit_sha": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(benchmark_dir)),
            "git_branch": s1.get_command_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(experiment_dir)),
            "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(experiment_dir)),
            "outputs": {k: str(v) for k, v in sweep_planned.items()},
        }
        with sweep_meta_path.open("w", encoding="utf-8") as f:
            json.dump(sweep_metadata, f, indent=2)

        print("-" * 70)
        print("Epsilon sweep completed successfully.")
        print(f"Thresholds: {json.dumps(thresholds, indent=2)}")
        print(f"Sweep metadata: {sweep_meta_path}")
        return

    # Planned output paths.
    planned = {}
    for attack in attacks:
        for split in ("test", "legacy"):
            planned[f"{attack}_{split}_predictions"] = (
                results_dir / f"{args.run_name}_{attack}_predictions_{split}_epsilon_{eps_token}.csv"
            )
            planned[f"{attack}_{split}_safety_metrics"] = (
                results_dir / f"{args.run_name}_{attack}_safety_metrics_{split}_epsilon_{eps_token}.csv"
            )
    metadata_path = results_dir / f"{args.run_name}_attacks_metadata.json"

    print("Stage 2: converged-checkpoint attacks")
    print("-" * 70)
    print(f"Checkpoint:        {checkpoint_path}")
    print(f"Checkpoint epoch:  {checkpoint_epoch}")
    print(f"Device:            {device}")
    print(f"Attacks:           {attacks}")
    print(f"Epsilon:           {args.epsilon}")
    print(f"PGD steps / alpha: {args.pgd_steps} / {alpha:.6f}")
    print(f"Split sizes:       {split_sizes}")
    print(f"Stage 1 clean ref: test_acc={clean_refs.get('test_accuracy')} "
          f"test_fall_recall={clean_refs.get('test_fall_recall')}")
    print("-" * 70)

    if args.dry_run:
        # Integrity check: confirm the loaded checkpoint reproduces clean test acc.
        _, yt, yc, _ = s1.run_inference(model, test_loader, criterion, device)
        print(f"[dry-run] clean TEST accuracy from loaded checkpoint: {s1.accuracy_of(yt, yc):.4f} "
              f"(Stage 1 committed: {clean_refs.get('test_accuracy')})")
        print("[dry-run] no attacks executed, no files written.")
        print("[dry-run] planned output files:")
        for key, path in planned.items():
            print(f"    {key}: {path}")
        print(f"    metadata_json: {metadata_path}")
        return

    # ---- Full attack run (only reached when NOT a dry-run). ----
    results_dir.mkdir(parents=True, exist_ok=True)
    metrics_index = {}

    for attack in attacks:
        for split, loader in loaders.items():
            rows, y_true, y_clean, y_attacked = collect_paired_predictions(
                model, loader, criterion, device, attack, args.epsilon, alpha, args.pgd_steps, s1
            )
            write_predictions_csv(planned[f"{attack}_{split}_predictions"], rows)

            metrics = compute_attack_safety_metrics(
                y_true, y_clean, y_attacked, attack, args.epsilon, alpha, args.pgd_steps, split, s1
            )
            s1.write_metric_value_csv(planned[f"{attack}_{split}_safety_metrics"], metrics)
            metrics_index[f"{attack}_{split}"] = metrics

            print(
                f"{attack.upper():4s} [{split:6s} n={metrics['n_windows']}] "
                f"attack_acc={metrics['attack_accuracy']:.4f} "
                f"fall_recall={metrics['fall_recall']:.4f} "
                f"missed={metrics['missed_fall_rate']:.4f} "
                f"FP={metrics['false_fall_alarm_count']} "
                f"pred_change={metrics['prediction_change_rate']:.4f}"
            )

    metadata = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "stage2_converged_attacks",
        "run_name": args.run_name,
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_epoch": checkpoint_epoch,
        "checkpoint_val_macro_f1": state.get("val_macro_f1"),
        "stage1_clean_references": clean_refs,
        "attack_parameters": {
            "attacks": attacks,
            "epsilon": args.epsilon,
            "pgd_steps": args.pgd_steps,
            "pgd_alpha": alpha,
            "pgd_alpha_rule": "epsilon/6 (=0.005 at eps=0.03; matches old single-eps and 18-eps sweep)",
            "value_clamp": "none (processed CSI tensors, not [0,1] pixels)",
            "seed": args.seed,
        },
        "split_sizes": split_sizes,
        "legacy_note": (
            "legacy val+test (996 windows) is a comparison-only pool for prior "
            "thesis artifacts; it was not used for training or selection (no "
            "training occurs in Stage 2)."
        ),
        "device": str(device),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "sensefi_commit_sha": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(benchmark_dir)),
        "git_branch": s1.get_command_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(experiment_dir)),
        "git_commit": s1.get_command_output(["git", "rev-parse", "HEAD"], cwd=str(experiment_dir)),
        "metrics": metrics_index,
        "outputs": {k: str(v) for k, v in planned.items()},
    }
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("-" * 70)
    print("Stage 2 attack export completed successfully.")
    print(f"Metadata: {metadata_path}")


if __name__ == "__main__":
    main()
