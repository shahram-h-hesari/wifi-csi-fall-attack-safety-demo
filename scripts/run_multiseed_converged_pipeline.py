"""
Priority 1 orchestrator: run the converged UT-HAR/SenseFi pipeline across seeds.

Purpose:
    Drive multi-seed reliability experiments by calling the EXISTING Stage 1 /
    Stage 2 / Stage 3 scripts with seed-specific run names. This script does NOT
    reimplement training, attacks, or defenses; it only sequences the existing
    entry points so a full multi-seed sweep is one reproducible command.

    Reused entry points (unchanged):
        Stage 1 clean baseline : scripts/train_converged_clean_baseline.py
        Stage 2 attacks / sweep: scripts/run_converged_attacks.py
        Stage 3 FGSM-AT defense: scripts/train_converged_defense.py

Run-name / path conventions (match the committed seed-42 artifacts):
    clean + undefended attacks : run-name  converged_seed{SEED}
        checkpoint             : checkpoints/converged_clean_baseline/converged_seed{SEED}_best.pt
    FGSM-AT defense            : run-name  defended_fgsm_at_seed{SEED}
        checkpoint             : checkpoints/converged_defense/defended_fgsm_at_seed{SEED}_best.pt

Scope / claim boundary:
    Window-level, software-tensor evaluation on processed CSI features. Not
    physical-layer / over-the-air, not clinical, not certified robustness.

Commands:
    python scripts/run_multiseed_converged_pipeline.py --help
    python scripts/run_multiseed_converged_pipeline.py --dry-run \
        --seeds 42 43 --stages clean attacks defense --epsilon-sweep
    python scripts/run_multiseed_converged_pipeline.py \
        --seeds 42 43 44 45 46 --stages clean attacks --epsilon-sweep
"""

from __future__ import annotations

from pathlib import Path
import argparse
import subprocess
import sys
import time

# Repository root (this file lives in <root>/scripts/).
REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

DEFAULT_SEEDS = [42, 43, 44, 45, 46]
ALL_STAGES = ["clean", "attacks", "defense"]

# Training hyper-parameters mirror the planning document's recommended command.
CLEAN_EPOCHS = 200
CLEAN_PATIENCE = 20
DEFENSE_EPOCHS = 200
DEFENSE_PATIENCE = 20
MATCHED_EPSILON = 0.03
TRAIN_EPSILON = 0.03

# Stage-1 / stage-3 checkpoint locations created by the existing scripts.
CLEAN_CKPT_DIR = REPO_ROOT / "checkpoints" / "converged_clean_baseline"
DEFENSE_CKPT_DIR = REPO_ROOT / "checkpoints" / "converged_defense"

# Representative output markers used by --skip-existing.
ATTACKS_RESULTS_DIR = REPO_ROOT / "results" / "converged_attacks"
BASELINE_RESULTS_DIR = REPO_ROOT / "results" / "converged_baseline"
DEFENSE_RESULTS_DIR = REPO_ROOT / "results" / "converged_defense"


def clean_run_name(seed: int) -> str:
    return f"converged_seed{seed}"


def defense_run_name(seed: int) -> str:
    return f"defended_fgsm_at_seed{seed}"


def clean_checkpoint(seed: int) -> Path:
    return CLEAN_CKPT_DIR / f"{clean_run_name(seed)}_best.pt"


def defense_checkpoint(seed: int) -> Path:
    return DEFENSE_CKPT_DIR / f"{defense_run_name(seed)}_best.pt"


def rel(path: Path) -> str:
    """Repo-relative string for compact, copy-pasteable command logging."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


class PlannedStep:
    """One stage invocation: a labelled command plus a skip predicate."""

    def __init__(self, label: str, argv: list[str], skip_if_exists: Path | None):
        self.label = label
        self.argv = argv
        self.skip_if_exists = skip_if_exists

    def already_done(self) -> bool:
        return self.skip_if_exists is not None and self.skip_if_exists.exists()


def build_steps(seed: int, stages: list[str], python_exe: str, epsilon_sweep: bool) -> list[PlannedStep]:
    """Build the ordered list of stage commands for a single seed."""
    steps: list[PlannedStep] = []

    s1 = str(SCRIPTS_DIR / "train_converged_clean_baseline.py")
    s2 = str(SCRIPTS_DIR / "run_converged_attacks.py")
    s3 = str(SCRIPTS_DIR / "train_converged_defense.py")

    clean_name = clean_run_name(seed)
    def_name = defense_run_name(seed)
    clean_ckpt = clean_checkpoint(seed)
    def_ckpt = defense_checkpoint(seed)

    # ---- Stage 1: clean baseline (saves the frozen checkpoint). ----
    if "clean" in stages:
        steps.append(
            PlannedStep(
                label=f"[seed {seed}] Stage 1 clean baseline ({clean_name})",
                argv=[
                    python_exe, s1,
                    "--epochs", str(CLEAN_EPOCHS),
                    "--patience", str(CLEAN_PATIENCE),
                    "--seed", str(seed),
                    "--run-name", clean_name,
                ],
                skip_if_exists=clean_ckpt,
            )
        )

    # ---- Stage 2: undefended attacks on the frozen clean checkpoint. ----
    if "attacks" in stages:
        steps.append(
            PlannedStep(
                label=f"[seed {seed}] Stage 2 matched attacks eps={MATCHED_EPSILON} ({clean_name})",
                argv=[
                    python_exe, s2,
                    "--epsilon", str(MATCHED_EPSILON),
                    "--attacks", "both",
                    "--seed", str(seed),
                    "--run-name", clean_name,
                    "--checkpoint", rel(clean_ckpt),
                ],
                skip_if_exists=ATTACKS_RESULTS_DIR
                / f"{clean_name}_fgsm_safety_metrics_test_epsilon_0_03.csv",
            )
        )
        if epsilon_sweep:
            steps.append(
                PlannedStep(
                    label=f"[seed {seed}] Stage 2 epsilon sweep ({clean_name})",
                    argv=[
                        python_exe, s2,
                        "--epsilon-sweep",
                        "--attacks", "both",
                        "--seed", str(seed),
                        "--run-name", clean_name,
                        "--checkpoint", rel(clean_ckpt),
                    ],
                    skip_if_exists=ATTACKS_RESULTS_DIR
                    / f"{clean_name}_fgsm_epsilon_sweep_test.csv",
                )
            )

    # ---- Stage 3: FGSM-AT defense, then attacks on the defended checkpoint. ----
    if "defense" in stages:
        steps.append(
            PlannedStep(
                label=f"[seed {seed}] Stage 3 FGSM-AT defense train ({def_name})",
                argv=[
                    python_exe, s3,
                    "--epochs", str(DEFENSE_EPOCHS),
                    "--patience", str(DEFENSE_PATIENCE),
                    "--seed", str(seed),
                    "--train-epsilon", str(TRAIN_EPSILON),
                    "--run-name", def_name,
                ],
                skip_if_exists=def_ckpt,
            )
        )
        steps.append(
            PlannedStep(
                label=f"[seed {seed}] Stage 3 defended matched attacks eps={MATCHED_EPSILON} ({def_name})",
                argv=[
                    python_exe, s2,
                    "--epsilon", str(MATCHED_EPSILON),
                    "--attacks", "both",
                    "--seed", str(seed),
                    "--run-name", def_name,
                    "--checkpoint", rel(def_ckpt),
                ],
                skip_if_exists=ATTACKS_RESULTS_DIR
                / f"{def_name}_fgsm_safety_metrics_test_epsilon_0_03.csv",
            )
        )
        if epsilon_sweep:
            steps.append(
                PlannedStep(
                    label=f"[seed {seed}] Stage 3 defended epsilon sweep ({def_name})",
                    argv=[
                        python_exe, s2,
                        "--epsilon-sweep",
                        "--attacks", "both",
                        "--seed", str(seed),
                        "--run-name", def_name,
                        "--checkpoint", rel(def_ckpt),
                    ],
                    skip_if_exists=ATTACKS_RESULTS_DIR
                    / f"{def_name}_fgsm_epsilon_sweep_test.csv",
                )
            )

    return steps


def format_argv(argv: list[str]) -> str:
    """Compact, repo-relative rendering of a command for logging."""
    rendered = []
    for tok in argv:
        if tok == sys.executable:
            rendered.append("python")
        elif tok.startswith(str(SCRIPTS_DIR)):
            rendered.append(rel(Path(tok)))
        else:
            rendered.append(tok)
    return " ".join(rendered)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Orchestrate the converged UT-HAR pipeline across seeds "
        "(Priority 1 multi-seed reliability). Reuses existing stage scripts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--seeds", type=int, nargs="+", default=DEFAULT_SEEDS,
        help="One or more integer seeds to run.",
    )
    p.add_argument(
        "--stages", nargs="+", choices=ALL_STAGES, default=ALL_STAGES,
        help="Subset of stages to run, in fixed order clean -> attacks -> defense.",
    )
    p.add_argument(
        "--epsilon-sweep", action="store_true",
        help="Also run the 18-point FGSM/PGD epsilon sweep in the attacks/defense "
        "stages (forwarded to run_converged_attacks.py --epsilon-sweep).",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Print the planned commands and exit WITHOUT executing anything.",
    )
    p.add_argument(
        "--skip-existing", action="store_true",
        help="Skip a stage whose representative output already exists.",
    )
    p.add_argument(
        "--python-exe", type=str, default=sys.executable,
        help="Python interpreter used to launch the stage scripts.",
    )
    p.add_argument(
        "--continue-on-error", action="store_true",
        help="Keep going to the next step if a stage exits non-zero "
        "(default: stop on first failure).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    # Preserve the canonical clean -> attacks -> defense order regardless of input order.
    stages = [s for s in ALL_STAGES if s in set(args.stages)]

    all_steps: list[PlannedStep] = []
    for seed in args.seeds:
        all_steps.extend(build_steps(seed, stages, args.python_exe, args.epsilon_sweep))

    print("=" * 78)
    print("Multi-seed converged pipeline orchestrator (Priority 1)")
    print("-" * 78)
    print(f"Repo root:      {REPO_ROOT}")
    print(f"Python exe:     {args.python_exe}")
    print(f"Seeds:          {args.seeds}")
    print(f"Stages:         {stages}")
    print(f"Epsilon sweep:  {args.epsilon_sweep}")
    print(f"Dry run:        {args.dry_run}")
    print(f"Skip existing:  {args.skip_existing}")
    print(f"Planned steps:  {len(all_steps)}")
    print("=" * 78)

    # ---- Always print the full plan first. ----
    for i, step in enumerate(all_steps, 1):
        marker = ""
        if args.skip_existing and step.already_done():
            marker = "  [WOULD SKIP: output exists]"
        elif step.skip_if_exists is not None and step.skip_if_exists.exists():
            marker = "  [note: output already present]"
        print(f"{i:3d}. {step.label}{marker}")
        print(f"     $ {format_argv(step.argv)}")

    if args.dry_run:
        print("-" * 78)
        print("[dry-run] No commands executed. No training, attacks, or files written.")
        return 0

    # ---- Real execution. ----
    print("-" * 78)
    print("Executing planned steps...")
    n_run = n_skipped = n_failed = 0
    for i, step in enumerate(all_steps, 1):
        if args.skip_existing and step.already_done():
            n_skipped += 1
            print(f"[{i}/{len(all_steps)}] SKIP (exists): {step.label}")
            continue

        print(f"[{i}/{len(all_steps)}] RUN: {step.label}")
        print(f"     $ {format_argv(step.argv)}")
        start = time.time()
        result = subprocess.run(step.argv, cwd=str(REPO_ROOT))
        elapsed = time.time() - start

        if result.returncode == 0:
            n_run += 1
            print(f"     done in {elapsed:.1f}s")
        else:
            n_failed += 1
            print(f"     FAILED (exit {result.returncode}) after {elapsed:.1f}s")
            if not args.continue_on_error:
                print("Stopping (use --continue-on-error to keep going).")
                break

    print("-" * 78)
    print(f"Summary: ran={n_run}, skipped={n_skipped}, failed={n_failed}")
    return 1 if n_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
