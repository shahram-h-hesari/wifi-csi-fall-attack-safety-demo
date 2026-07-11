#!/usr/bin/env python
"""Shared repository resolver for Research OS automation.

Implements automation/acceptance/external-repo-resolution.yaml. The resolver keeps the
governance repository (the repository this automation runs from) separate from external
experiment/evidence repositories. External repositories are resolved only through the tracked
registry plus the gitignored local override; no sibling-folder inference is permitted.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

HERE = Path(__file__).resolve().parent
DEFAULT_GOVERNANCE_ROOT = HERE.parents[1]
AUT = DEFAULT_GOVERNANCE_ROOT / "automation"
DEFAULT_REGISTRY_PATH = AUT / "registry" / "external_repositories.yaml"
DEFAULT_LOCAL_PATHS_PATH = AUT / "local" / "external_repository_paths.yaml"
LOCAL_PATHS_TEMPLATE_PATH = AUT / "local" / "external_repository_paths.example.yaml"

GOVERNANCE_REPOSITORY_ID = "governance-self"
SUPPORTED_SCHEMA_VERSION = 1
VALID_REPOSITORY_ROLES = {"experiment-and-evidence", "governance-self"}
VALID_DIRTY_POLICIES = {"allowed_read_only", "rejected", "allowed_with_recorded_dirty_state"}
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ABSOLUTE_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]|^\\\\|^/")
MUTATING_GIT_COMMANDS = {"fetch", "clone", "checkout", "pull", "reset", "merge", "push", "commit", "add"}


class RepositoryResolutionError(RuntimeError):
    """Typed, deterministic resolver failure."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


@dataclass(frozen=True)
class RepositoryConfig:
    repository_id: str
    repository_role: str
    expected_remote_url: str
    canonical_branch_or_ref_policy: str
    provenance_commit_policy: str
    required_repository_relative_paths: tuple[str, ...]
    allowed_evidence_roots: tuple[str, ...]
    read_only_to_research_os: bool
    git_identity_verification_required: bool
    dirty_worktree_policy: str
    claim_boundaries: tuple[str, ...]


@dataclass(frozen=True)
class ResolvedRepository:
    repository_id: str
    repository_role: str
    root_path: Path
    expected_remote_url: str
    resolved_remote_url: str
    full_commit_sha: str
    worktree_clean: bool
    dirty_worktree_policy: str
    dirty_paths: tuple[str, ...]
    required_repository_relative_paths: tuple[str, ...]
    allowed_evidence_roots: tuple[str, ...]

    def public_metadata(self) -> dict[str, Any]:
        return {
            "repository_id": self.repository_id,
            "repository_role": self.repository_role,
            "expected_remote_url": self.expected_remote_url,
            "resolved_remote_url": self.resolved_remote_url,
            "full_commit_sha": self.full_commit_sha,
            "worktree_clean": self.worktree_clean,
            "dirty_worktree_policy": self.dirty_worktree_policy,
            "dirty_paths": list(self.dirty_paths),
        }


@dataclass(frozen=True)
class ResolvedEvidencePath:
    repository: ResolvedRepository
    repository_relative_path: str
    absolute_path: Path
    sha256: str | None = None

    def public_metadata(self) -> dict[str, Any]:
        out = {
            "repository_id": self.repository.repository_id,
            "repository_relative_path": self.repository_relative_path,
            "full_commit_sha": self.repository.full_commit_sha,
            "expected_remote_url": self.repository.expected_remote_url,
            "resolved_remote_url": self.repository.resolved_remote_url,
            "worktree_clean": self.repository.worktree_clean,
        }
        if self.sha256:
            out["sha256"] = self.sha256
        return out


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:  # pragma: no cover
        raise RepositoryResolutionError("yaml_unavailable", "PyYAML is required for repository resolution")
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise RepositoryResolutionError("malformed_yaml", f"{path}: {exc}") from exc
    except OSError as exc:
        raise RepositoryResolutionError("unreadable_yaml", f"{path}: {exc}") from exc


def _run_git_read_only(root: Path, args: list[str]) -> str:
    if not args:
        raise RepositoryResolutionError("git_command_refused", "empty git command")
    if args[0] in MUTATING_GIT_COMMANDS or any(a in MUTATING_GIT_COMMANDS for a in args[1:]):
        raise RepositoryResolutionError("git_command_refused", f"mutating git command refused: {' '.join(args)}")
    allowed = (
        args[:2] == ["rev-parse", "--show-toplevel"]
        or args[:2] == ["rev-parse", "HEAD"]
        or args[:2] == ["remote", "get-url"]
        or args[:2] == ["status", "--porcelain"]
    )
    if not allowed:
        raise RepositoryResolutionError("git_command_refused", f"unsupported read-only git query: {' '.join(args)}")
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RepositoryResolutionError("git_unavailable", f"git query failed in {root}: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RepositoryResolutionError("git_query_failed", f"git {' '.join(args)} failed in {root}: {detail}")
    return result.stdout.strip()


def _git_toplevel(path: Path) -> Path:
    top = _run_git_read_only(path, ["rev-parse", "--show-toplevel"])
    return Path(top).resolve()


def _git_head_full(path: Path) -> str:
    head = _run_git_read_only(path, ["rev-parse", "HEAD"])
    if not FULL_SHA_RE.match(head):
        raise RepositoryResolutionError("invalid_commit_sha", f"git HEAD is not a full 40-character SHA: {head!r}")
    return head


def _git_remote_url(path: Path, remote_name: str = "origin") -> str:
    return _run_git_read_only(path, ["remote", "get-url", remote_name])


def _git_dirty_paths(path: Path) -> tuple[str, ...]:
    out = _run_git_read_only(path, ["status", "--porcelain"])
    paths: list[str] = []
    for line in out.splitlines():
        if not line:
            continue
        raw = line[3:] if len(line) > 2 and line[2] == " " else line[2:]
        raw = raw.strip().strip('"')
        paths.append(raw.replace("\\", "/"))
    return tuple(sorted(paths))


def _normalize_relative_path(value: str, *, label: str = "repository_relative_path") -> str:
    raw = str(value or "").strip().replace("\\", "/")
    if not raw:
        raise RepositoryResolutionError("empty_relative_path", f"{label} is empty")
    if ABSOLUTE_PATH_RE.search(raw):
        raise RepositoryResolutionError("absolute_path_rejected", f"{label} must be repository-relative: {value!r}")
    parts = PurePosixPath(raw).parts
    if any(part == ".." for part in parts):
        raise RepositoryResolutionError("path_traversal_rejected", f"{label} contains '..': {value!r}")
    if any(part == "" for part in parts):
        raise RepositoryResolutionError("invalid_relative_path", f"{label} is malformed: {value!r}")
    normalized = PurePosixPath(raw).as_posix()
    return "" if normalized == "." else normalized


def _normalize_roots(roots: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    out = []
    for root in roots or []:
        norm = _normalize_relative_path(str(root), label="allowed_evidence_roots").rstrip("/")
        if norm:
            out.append(norm)
    return tuple(sorted(set(out)))


def _is_under_rel(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")


def _case_norm(path: Path) -> str:
    return os.path.normcase(os.path.realpath(path))


def _is_under_abs(path: Path, root: Path) -> bool:
    p = _case_norm(path)
    r = _case_norm(root)
    return p == r or p.startswith(r.rstrip("\\/") + os.sep)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_registry(registry_path: Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    if not registry_path.exists():
        raise RepositoryResolutionError("registry_missing", f"tracked registry not found: {registry_path}")
    doc = _load_yaml(registry_path)
    if doc.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise RepositoryResolutionError("unsupported_registry_schema", f"schema_version must be {SUPPORTED_SCHEMA_VERSION}")
    repos = doc.get("repositories")
    if not isinstance(repos, list):
        raise RepositoryResolutionError("malformed_registry", "repositories must be a list")
    return doc


def _config_from_entry(entry: dict[str, Any]) -> RepositoryConfig:
    try:
        return RepositoryConfig(
            repository_id=str(entry["repository_id"]),
            repository_role=str(entry["repository_role"]),
            expected_remote_url=str(entry["expected_remote_url"]),
            canonical_branch_or_ref_policy=str(entry["canonical_branch_or_ref_policy"]),
            provenance_commit_policy=str(entry["provenance_commit_policy"]),
            required_repository_relative_paths=tuple(
                _normalize_relative_path(str(p), label="required_repository_relative_paths")
                for p in (entry.get("required_repository_relative_paths") or [])
            ),
            allowed_evidence_roots=_normalize_roots(tuple(entry.get("allowed_evidence_roots") or [])),
            read_only_to_research_os=bool(entry["read_only_to_research_os"]),
            git_identity_verification_required=bool(entry["git_identity_verification_required"]),
            dirty_worktree_policy=str(entry["dirty_worktree_policy"]),
            claim_boundaries=tuple(str(x) for x in (entry.get("claim_boundaries") or [])),
        )
    except KeyError as exc:
        raise RepositoryResolutionError("malformed_registry", f"repository entry missing required field {exc.args[0]!r}") from exc


def _registry_configs(registry_path: Path = DEFAULT_REGISTRY_PATH) -> dict[str, RepositoryConfig]:
    doc = load_registry(registry_path)
    configs: dict[str, RepositoryConfig] = {}
    for entry in doc.get("repositories") or []:
        config = _config_from_entry(entry)
        configs[config.repository_id] = config
    return configs


def _load_local_paths(local_paths_path: Path = DEFAULT_LOCAL_PATHS_PATH) -> dict[str, str]:
    if not local_paths_path.exists():
        raise RepositoryResolutionError(
            "local_override_missing",
            f"local override not found: {local_paths_path}; create it from {LOCAL_PATHS_TEMPLATE_PATH}",
        )
    doc = _load_yaml(local_paths_path)
    if doc.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise RepositoryResolutionError("unsupported_local_override_schema", f"schema_version must be {SUPPORTED_SCHEMA_VERSION}")
    paths = doc.get("local_paths")
    if not isinstance(paths, dict):
        raise RepositoryResolutionError("malformed_local_override", "local_paths must be a mapping of repository_id to absolute path")
    return {str(k): str(v) for k, v in paths.items()}


def resolve_governance_repository(start: Path | None = None) -> ResolvedRepository:
    root = _git_toplevel((start or DEFAULT_GOVERNANCE_ROOT).resolve())
    head = _git_head_full(root)
    dirty = _git_dirty_paths(root)
    remote = ""
    try:
        remote = _git_remote_url(root)
    except RepositoryResolutionError:
        remote = ""
    return ResolvedRepository(
        repository_id=GOVERNANCE_REPOSITORY_ID,
        repository_role="governance-self",
        root_path=root,
        expected_remote_url=remote,
        resolved_remote_url=remote,
        full_commit_sha=head,
        worktree_clean=not dirty,
        dirty_worktree_policy="allowed_read_only",
        dirty_paths=dirty,
        required_repository_relative_paths=(),
        allowed_evidence_roots=(),
    )


def governance_repo_root(start: Path | None = None) -> Path:
    return resolve_governance_repository(start).root_path


def resolve_external_repository(
    repository_id: str,
    *,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    local_paths_path: Path = DEFAULT_LOCAL_PATHS_PATH,
) -> ResolvedRepository:
    configs = _registry_configs(registry_path)
    if repository_id not in configs:
        known = ", ".join(sorted(configs)) or "(none)"
        raise RepositoryResolutionError("unknown_repository_id", f"{repository_id!r} not present in {registry_path}; known: {known}")
    config = configs[repository_id]
    paths = _load_local_paths(local_paths_path)
    if repository_id not in paths:
        raise RepositoryResolutionError(
            "local_override_missing_entry",
            f"{repository_id!r} missing from {local_paths_path}; create an entry from {LOCAL_PATHS_TEMPLATE_PATH}",
        )
    root = Path(paths[repository_id]).expanduser()
    if not root.is_absolute():
        raise RepositoryResolutionError("invalid_local_path", f"local path for {repository_id!r} must be absolute")
    if not root.exists():
        raise RepositoryResolutionError("invalid_local_path", f"local path for {repository_id!r} does not exist: {root}")
    try:
        toplevel = _git_toplevel(root)
    except RepositoryResolutionError as exc:
        raise RepositoryResolutionError("not_git_worktree", f"{repository_id!r} is not a valid Git worktree: {root}") from exc
    remote = _git_remote_url(toplevel)
    if remote != config.expected_remote_url:
        raise RepositoryResolutionError(
            "remote_url_mismatch",
            f"{repository_id!r} origin remote {remote!r} != expected {config.expected_remote_url!r}",
        )
    missing_required = [
        rel for rel in config.required_repository_relative_paths
        if not (toplevel / rel).exists()
    ]
    if missing_required:
        raise RepositoryResolutionError(
            "required_path_missing",
            f"{repository_id!r} missing required path(s): {', '.join(sorted(missing_required))}",
        )
    head = _git_head_full(toplevel)
    dirty_paths = _git_dirty_paths(toplevel)
    if dirty_paths and config.dirty_worktree_policy == "rejected":
        raise RepositoryResolutionError(
            "dirty_worktree_rejected",
            f"{repository_id!r} worktree dirty under policy 'rejected': {', '.join(dirty_paths)}",
        )
    return ResolvedRepository(
        repository_id=repository_id,
        repository_role=config.repository_role,
        root_path=toplevel,
        expected_remote_url=config.expected_remote_url,
        resolved_remote_url=remote,
        full_commit_sha=head,
        worktree_clean=not dirty_paths,
        dirty_worktree_policy=config.dirty_worktree_policy,
        dirty_paths=dirty_paths,
        required_repository_relative_paths=config.required_repository_relative_paths,
        allowed_evidence_roots=config.allowed_evidence_roots,
    )


def _check_evidence_path(repository: ResolvedRepository, repository_relative_path: str, *, must_exist: bool) -> Path:
    rel = _normalize_relative_path(repository_relative_path)
    if repository.allowed_evidence_roots:
        if not any(_is_under_rel(rel, root) for root in repository.allowed_evidence_roots):
            raise RepositoryResolutionError(
                "outside_allowed_evidence_roots",
                f"{repository.repository_id}:{rel} is outside allowed evidence roots {list(repository.allowed_evidence_roots)}",
            )
    path = repository.root_path / rel
    if must_exist and not path.exists():
        raise RepositoryResolutionError("evidence_path_missing", f"{repository.repository_id}:{rel} does not exist")
    if path.exists():
        real_path = Path(os.path.realpath(path))
        if not _is_under_abs(real_path, repository.root_path):
            raise RepositoryResolutionError("symlink_escape_rejected", f"{repository.repository_id}:{rel} resolves outside repository root")
        if repository.allowed_evidence_roots:
            allowed = [repository.root_path / root for root in repository.allowed_evidence_roots]
            if not any(_is_under_abs(real_path, root) for root in allowed):
                raise RepositoryResolutionError("symlink_escape_rejected", f"{repository.repository_id}:{rel} resolves outside allowed evidence roots")
    return path


def resolve_external_evidence_path(
    repository_id: str,
    repository_relative_path: str,
    *,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    local_paths_path: Path = DEFAULT_LOCAL_PATHS_PATH,
    must_exist: bool = True,
    compute_sha256: bool = True,
) -> ResolvedEvidencePath:
    repository = resolve_external_repository(
        repository_id,
        registry_path=registry_path,
        local_paths_path=local_paths_path,
    )
    path = _check_evidence_path(repository, repository_relative_path, must_exist=must_exist)
    rel = _normalize_relative_path(repository_relative_path)
    sha = _sha256_file(path) if compute_sha256 and path.is_file() else None
    return ResolvedEvidencePath(repository=repository, repository_relative_path=rel, absolute_path=path, sha256=sha)


def resolve_governance_evidence_path(
    repository_relative_path: str,
    *,
    base: Path | None = None,
    must_exist: bool = True,
    compute_sha256: bool = True,
) -> ResolvedEvidencePath:
    repository = resolve_governance_repository(base)
    rel = _normalize_relative_path(repository_relative_path)
    path = repository.root_path / rel
    if must_exist and not path.exists():
        raise RepositoryResolutionError("evidence_path_missing", f"{GOVERNANCE_REPOSITORY_ID}:{rel} does not exist")
    if path.exists() and not _is_under_abs(Path(os.path.realpath(path)), repository.root_path):
        raise RepositoryResolutionError("symlink_escape_rejected", f"{GOVERNANCE_REPOSITORY_ID}:{rel} resolves outside repository root")
    sha = _sha256_file(path) if compute_sha256 and path.is_file() else None
    return ResolvedEvidencePath(repository=repository, repository_relative_path=rel, absolute_path=path, sha256=sha)


def resolve_legacy_evidence_path(
    repository_relative_path: str,
    *,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    local_paths_path: Path = DEFAULT_LOCAL_PATHS_PATH,
    base: Path | None = None,
    must_exist: bool = True,
    compute_sha256: bool = True,
) -> ResolvedEvidencePath:
    rel = _normalize_relative_path(repository_relative_path)
    if not registry_path.exists():
        return resolve_governance_evidence_path(rel, base=base, must_exist=must_exist, compute_sha256=compute_sha256)
    doc = load_registry(registry_path)
    repos = [str(r.get("repository_id")) for r in (doc.get("repositories") or [])]
    if not repos:
        return resolve_governance_evidence_path(rel, base=base, must_exist=must_exist, compute_sha256=compute_sha256)
    default_id = doc.get("default_legacy_repository_id")
    if default_id:
        if default_id not in repos:
            raise RepositoryResolutionError("legacy_repository_unresolved", f"default_legacy_repository_id {default_id!r} is not in the registry")
        return resolve_external_evidence_path(
            str(default_id), rel, registry_path=registry_path, local_paths_path=local_paths_path,
            must_exist=must_exist, compute_sha256=compute_sha256,
        )
    if len(repos) == 1:
        return resolve_external_evidence_path(
            repos[0], rel, registry_path=registry_path, local_paths_path=local_paths_path,
            must_exist=must_exist, compute_sha256=compute_sha256,
        )
    raise RepositoryResolutionError(
        "legacy_path_ambiguous",
        f"legacy path {rel!r} has no repository_id and {len(repos)} repositories are configured: {', '.join(sorted(repos))}",
    )


def resolve_evidence_path(
    repository_id: str | None,
    repository_relative_path: str,
    *,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    local_paths_path: Path = DEFAULT_LOCAL_PATHS_PATH,
    base: Path | None = None,
    must_exist: bool = True,
    compute_sha256: bool = True,
) -> ResolvedEvidencePath:
    if repository_id in (None, ""):
        return resolve_legacy_evidence_path(
            repository_relative_path,
            registry_path=registry_path,
            local_paths_path=local_paths_path,
            base=base,
            must_exist=must_exist,
            compute_sha256=compute_sha256,
        )
    if repository_id == GOVERNANCE_REPOSITORY_ID:
        return resolve_governance_evidence_path(
            repository_relative_path, base=base, must_exist=must_exist, compute_sha256=compute_sha256
        )
    return resolve_external_evidence_path(
        repository_id,
        repository_relative_path,
        registry_path=registry_path,
        local_paths_path=local_paths_path,
        must_exist=must_exist,
        compute_sha256=compute_sha256,
    )


def dump_public_metadata(obj: ResolvedRepository | ResolvedEvidencePath) -> str:
    payload = obj.public_metadata() if hasattr(obj, "public_metadata") else asdict(obj)
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"


def validate_registry_doc(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(doc, dict):
        return ["registry root is not a mapping"]
    if doc.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        errors.append(f"schema_version must be {SUPPORTED_SCHEMA_VERSION}")
    repos = doc.get("repositories")
    if not isinstance(repos, list):
        errors.append("repositories must be a list")
        repos = []
    seen: set[str] = set()
    for idx, entry in enumerate(repos):
        where = f"repositories[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{where} is not a mapping")
            continue
        required = {
            "repository_id", "repository_role", "expected_remote_url", "canonical_branch_or_ref_policy",
            "provenance_commit_policy", "required_repository_relative_paths", "allowed_evidence_roots",
            "read_only_to_research_os", "git_identity_verification_required", "dirty_worktree_policy",
            "claim_boundaries",
        }
        missing = sorted(required - set(entry))
        if missing:
            errors.append(f"{where} missing required fields {missing}")
            continue
        rid = str(entry.get("repository_id"))
        if rid in seen:
            errors.append(f"{where} duplicate repository_id {rid!r}")
        seen.add(rid)
        if not re.match(r"^[a-z0-9][a-z0-9._-]*$", rid):
            errors.append(f"{where}.repository_id is not a stable slug: {rid!r}")
        if entry.get("repository_role") not in VALID_REPOSITORY_ROLES:
            errors.append(f"{where}.repository_role invalid: {entry.get('repository_role')!r}")
        remote = str(entry.get("expected_remote_url") or "")
        if not remote.startswith("https://") or "@" in remote:
            errors.append(f"{where}.expected_remote_url must be credential-free https URL")
        if entry.get("read_only_to_research_os") is not True:
            errors.append(f"{where}.read_only_to_research_os must be true")
        if entry.get("git_identity_verification_required") is not True:
            errors.append(f"{where}.git_identity_verification_required must be true")
        if entry.get("dirty_worktree_policy") not in VALID_DIRTY_POLICIES:
            errors.append(f"{where}.dirty_worktree_policy invalid: {entry.get('dirty_worktree_policy')!r}")
        for field in ("required_repository_relative_paths", "allowed_evidence_roots", "claim_boundaries"):
            if not isinstance(entry.get(field), list):
                errors.append(f"{where}.{field} must be a list")
        for field in ("required_repository_relative_paths", "allowed_evidence_roots"):
            for value in entry.get(field) or []:
                text = str(value)
                if ABSOLUTE_PATH_RE.search(text):
                    errors.append(f"{where}.{field} contains absolute path {text!r}")
                if ".." in PurePosixPath(text.replace("\\", "/")).parts:
                    errors.append(f"{where}.{field} contains traversal {text!r}")
        for path, value in _walk_strings(entry):
            text = str(value)
            if "token" in path.lower() or "credential" in path.lower():
                errors.append(f"{where}.{path} must not store credentials")
            if ABSOLUTE_PATH_RE.search(text) and path not in {"expected_remote_url"}:
                errors.append(f"{where}.{path} contains an absolute local path")
    default_id = doc.get("default_legacy_repository_id")
    if default_id is not None and default_id not in seen:
        errors.append(f"default_legacy_repository_id {default_id!r} is not registered")
    return sorted(errors)


def _walk_strings(node: Any, path: str = ""):
    if isinstance(node, dict):
        for k, v in sorted(node.items(), key=lambda kv: str(kv[0])):
            yield from _walk_strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node
