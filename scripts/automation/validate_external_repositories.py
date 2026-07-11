#!/usr/bin/env python
"""Read-only validator for automation/registry/external_repositories.yaml.

The tracked registry may contain only portable repository identity and policy data. Machine-local
checkout paths belong only in automation/local/external_repository_paths.yaml, which is gitignored.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML required: pip install pyyaml")

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import repo_resolver as rr  # noqa: E402

REPO = rr.DEFAULT_GOVERNANCE_ROOT
REGISTRY = REPO / "automation" / "registry" / "external_repositories.yaml"
LOCAL_OVERRIDE = REPO / "automation" / "local" / "external_repository_paths.yaml"
LOCAL_TEMPLATE = REPO / "automation" / "local" / "external_repository_paths.example.yaml"


def validate_paths(registry_path: Path = REGISTRY, template_path: Path = LOCAL_TEMPLATE) -> list[str]:
    errors: list[str] = []
    if not registry_path.exists():
        return [f"registry file not found: {registry_path}"]
    try:
        doc = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return [f"registry YAML is malformed: {exc}"]
    errors.extend(rr.validate_registry_doc(doc))
    if not template_path.exists():
        errors.append(f"local-path example template missing: {template_path}")
    else:
        text = template_path.read_text(encoding="utf-8")
        if "C:\\Users\\Hesar" in text or "/Users/" in text or "\\Users\\" in text:
            errors.append("local-path example contains a machine-specific user path")
        try:
            tmpl = yaml.safe_load(text) or {}
        except yaml.YAMLError as exc:
            errors.append(f"local-path example YAML is malformed: {exc}")
        else:
            if tmpl.get("schema_version") != 1:
                errors.append("local-path example schema_version must be 1")
            if not isinstance(tmpl.get("local_paths"), dict):
                errors.append("local-path example local_paths must be a mapping")
    if LOCAL_OVERRIDE.exists():
        errors.append(f"real machine-local override must not be committed or used by validator: {LOCAL_OVERRIDE}")
    return sorted(errors)


def main(argv: list[str]) -> int:
    kv = dict(a.partition("=")[::2] for a in argv if "=" in a)
    registry_path = Path(kv.get("registry", REGISTRY))
    template_path = Path(kv.get("template", LOCAL_TEMPLATE))
    errors = validate_paths(registry_path, template_path)
    try:
        doc = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    except Exception:
        doc = {}
    repos = doc.get("repositories") or []
    default_legacy = doc.get("default_legacy_repository_id")
    print(f"[validate] external_repositories={len(repos)} default_legacy_repository_id={default_legacy!r}")
    if errors:
        for error in errors:
            print(f"  ERROR: {error}")
        print(f"[validate] FAIL - {len(errors)} error(s)")
        return 1
    print("[validate] PASS - no errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
