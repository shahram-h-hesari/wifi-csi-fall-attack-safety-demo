#!/usr/bin/env python
"""Acceptance test for test-split-guard (warn-only). Imports the matcher's detect() and also runs
the hook process end-to-end to confirm it warns visibly (exit 1, stderr) but NEVER blocks (only
exit 2 blocks). Read-only; writes nothing."""
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

    print("\n=== warn-only: stderr WARN-ONLY + exit 1 (non-blocking), no stdout, no permissionDecision ===")
    # risky: exit 1 (non-blocking per hook rules; only exit 2 blocks -> tool call continues),
    # WARN-ONLY on stderr, nothing on stdout, no permissionDecision on either stream.
    r1 = run_hook(".venv/Scripts/python.exe scripts/export_probability_predictions.py --split test")
    has_msg = "WARN-ONLY" in r1.stderr
    stdout_empty = r1.stdout.strip() == ""
    no_perm = "permissionDecision" not in (r1.stdout + r1.stderr)
    warned = (r1.returncode == 1) and has_msg and stdout_empty and no_perm
    ok &= warned
    print(f"[{'PASS' if warned else 'FAIL'}] --split test: exit {r1.returncode} (want 1 = "
          f"non-blocking, tool continues), stderr-has-WARN-ONLY={has_msg}, "
          f"stdout-empty={stdout_empty}, no-permissionDecision={no_perm}")
    # safe: exit 0, no output on either stream.
    r2 = run_hook("python scripts/export_probability_predictions.py --split val")
    quiet = (r2.returncode == 0) and (r2.stdout.strip() == "") and (r2.stderr.strip() == "")
    ok &= quiet
    print(f"[{'PASS' if quiet else 'FAIL'}] --split val: exit {r2.returncode} (want 0), "
          f"stdout+stderr empty={r2.stdout.strip() == '' and r2.stderr.strip() == ''} (want empty)")
    r3 = run_hook("")  # empty command
    empty_ok = (r3.returncode == 0) and (r3.stdout.strip() == "") and (r3.stderr.strip() == "")
    ok &= empty_ok
    print(f"[{'PASS' if empty_ok else 'FAIL'}] empty command: exit {r3.returncode} (want 0), "
          f"stdout+stderr empty={r3.stdout.strip() == '' and r3.stderr.strip() == ''}")

    print("\n=== static read-only check (matcher writes no files, returns no permissionDecision) ===")
    src = (HERE / "test_split_guard.py").read_text(encoding="utf-8")
    no_write = ("open(" not in src) and (".write_text" not in src) and ("Path(" not in src)
    ok &= no_write
    print(f"[{'PASS' if no_write else 'FAIL'}] no file-write/open()/Path() in matcher (stderr line only, no stdout)")
    no_perm_src = "permissionDecision" not in src
    ok &= no_perm_src
    print(f"[{'PASS' if no_perm_src else 'FAIL'}] no permissionDecision anywhere in matcher source")

    print("\nRESULT:", "ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
