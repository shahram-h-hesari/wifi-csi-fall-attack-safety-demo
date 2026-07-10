#!/usr/bin/env python
"""Acceptance test for test-split-guard (warn-only). Imports the matcher's detect() and also runs
the hook process end-to-end to confirm it NEVER blocks. Read-only; writes nothing."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_split_guard as g  # noqa: E402

CASES = [
    (".venv/Scripts/python.exe scripts/export_probability_predictions.py --checkpoint X --model lenet --epsilon 0.015 --split test", True,  "R1 --split test"),
    ("python scripts/export_probability_predictions.py --checkpoint X --model lenet",                                                True,  "R3 export without --split"),
    ("python scripts/adaptive_gate_attack.py --config Y",                                                                            True,  "R4 gate without --split"),
    ("python scripts/export_probability_predictions.py --split legacy --checkpoint X",                                               True,  "R2 legacy"),
    (".venv/Scripts/python.exe scripts/adaptive_gate_attack.py --split test",                                                        True,  "R1 gate --split test"),
    ("python scripts/export_probability_predictions.py --checkpoint X --split val",                                                  False, "export --split val"),
    ("python scripts/adaptive_gate_attack.py --split val --config Y",                                                                False, "gate --split val"),
    ("cat results/converged_attacks/converged_seed42_pgd_safety_metrics_test_epsilon_0_03.csv",                                      False, "read existing test CSV"),
    ("python scripts/automation/update_dashboard.py",                                                                                False, "dashboard refresh"),
    ("python scripts/automation/scan_artifacts.py --write --manifest-out automation/artifact_manifest.csv",                          False, "artifact scan"),
    ("git status --short",                                                                                                           False, "git status"),
    ("python scripts/automation/test_split_guard_cases.py",                                                                          False, "run this test file ('test' in name)"),
    ("python -m pytest -q",                                                                                                          False, "pytest"),
    ("grep -r export_probability_predictions scripts/",                                                                              False, "grep script name (not an invocation)"),
]


def run_hook(command):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    return subprocess.run([sys.executable, str(HERE / "test_split_guard.py")],
                          input=payload, capture_output=True, text=True)


def main():
    ok = True
    print("=== detect() classification ===")
    for cmd, expect, label in CASES:
        got = bool(g.detect(cmd))
        p = got == expect
        ok &= p
        print(f"[{'PASS' if p else 'FAIL'}] {'WARN' if got else 'ALLOW':5s} (want {'WARN' if expect else 'ALLOW'}) {label}")

    print("\n=== warn-only never blocks ===")
    r1 = run_hook(".venv/Scripts/python.exe scripts/export_probability_predictions.py --split test")
    nb = (r1.returncode == 0) and ("WARN-ONLY" in r1.stderr)
    ok &= nb
    print(f"[{'PASS' if nb else 'FAIL'}] --split test: exit {r1.returncode} (want 0), warned={'WARN-ONLY' in r1.stderr}")
    r2 = run_hook("python scripts/export_probability_predictions.py --split val")
    quiet = (r2.returncode == 0) and ("WARN-ONLY" not in r2.stderr)
    ok &= quiet
    print(f"[{'PASS' if quiet else 'FAIL'}] --split val: exit {r2.returncode} (want 0), warned={'WARN-ONLY' in r2.stderr} (want no)")
    r3 = run_hook("")  # empty command
    ok &= (r3.returncode == 0)
    print(f"[{'PASS' if r3.returncode == 0 else 'FAIL'}] empty command: exit {r3.returncode} (want 0)")

    print("\n=== static read-only check (matcher writes nothing) ===")
    src = (HERE / "test_split_guard.py").read_text(encoding="utf-8")
    no_write = ("open(" not in src) and (".write_text" not in src) and ("Path(" not in src)
    ok &= no_write
    print(f"[{'PASS' if no_write else 'FAIL'}] no file-write/open()/Path() in matcher (stderr-only)")

    print("\nRESULT:", "ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
