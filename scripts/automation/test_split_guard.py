#!/usr/bin/env python
"""test-split-guard (WARN-ONLY phase). PreToolUse hook matcher for the Bash (and PowerShell) tools.

Reads the tool-call JSON on stdin, inspects the command string, and WARNS (never blocks) when the
command would generate/consume held-out TEST-split data. Warn-only contract: ALWAYS exits 0 (allow).
Pure stdlib, read-only: writes NOTHING (the guard log is intentionally disabled in this phase),
creates no authorization tokens, runs no experiments.

Detection (WARN):
  R1  --split test
  R2  --split legacy
  R3  export_probability_predictions.py invoked (python ...) without --split (default is test)
  R4  adaptive_gate_attack.py invoked (python ...) without --split (default is test)
Everything else ALLOWs silently: --split val, reading existing test CSVs, dashboard refresh,
artifact scan, git, pytest, grep, etc.
"""
import json
import re
import sys

# a python invocation token (python, python.exe, .venv/Scripts/python.exe, /usr/bin/python3, ...)
PY = r"(?:[\w./\\-]*python[\w.]*)"

EXPLICIT = [
    ("R1_test",   re.compile(r"--split\s+test(?!\w)", re.I), "explicit --split test (held-out test generation)"),
    ("R2_legacy", re.compile(r"--split\s+legacy\b", re.I),   "explicit --split legacy"),
]
NO_SPLIT_SCRIPTS = [
    ("R3_export", "export_probability_predictions.py"),
    ("R4_gate",   "adaptive_gate_attack.py"),
]


def detect(cmd):
    """Return a de-duplicated list of (rule_id, message) warnings for a command string. Pure."""
    warns = []
    for rid, rx, msg in EXPLICIT:
        if rx.search(cmd):
            warns.append((rid, msg))
    has_split = re.search(r"--split\s+\S+", cmd, re.I)
    invokes_py = re.search(PY, cmd, re.I)
    for rid, script in NO_SPLIT_SCRIPTS:
        if script in cmd and invokes_py and not has_split:
            warns.append((rid, f"{script} invoked without --split (default is test)"))
    seen, out = set(), []
    for rid, msg in warns:
        if rid not in seen:
            seen.add(rid)
            out.append((rid, msg))
    return out


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # malformed / no input -> allow silently
    if not isinstance(data, dict) or data.get("tool_name") not in ("Bash", "PowerShell"):
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "") or ""
    if not cmd.strip():
        return 0
    warns = detect(cmd)
    if warns:
        ids = ",".join(r for r, _ in warns)
        msgs = "; ".join(m for _, m in warns)
        sys.stderr.write(
            f"\n[test-split-guard WARN-ONLY] {ids}: {msgs}\n"
            f"  This command may generate/consume HELD-OUT TEST data. Allowed (warn-only mode).\n"
            f"  If intended, confirm it is an authorized frozen-protocol read; otherwise prefer --split val.\n\n")
    return 0  # WARN-ONLY: never block


if __name__ == "__main__":
    raise SystemExit(main())
