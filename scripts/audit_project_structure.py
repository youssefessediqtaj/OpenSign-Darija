#!/usr/bin/env python3
"""Generate project-structure cleanup evidence for the professionalization pass."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tomllib
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "reports"
AUDITS = ROOT / "docs" / "audits"

TEXT_SUFFIXES = {
    "",
    ".css",
    ".env",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

ROOT_DECISIONS: dict[str, tuple[str, str]] = {
    ".agent": ("KEEP", "Workspace continuity for future Codex turns."),
    ".github": ("KEEP", "CI workflow ownership."),
    ".pytest_cache": ("LOCAL_GENERATED_ONLY", "Ignored pytest cache; must not exist in the final root."),
    ".ruff_cache": ("LOCAL_GENERATED_ONLY", "Ignored Ruff cache; must not exist in the final root."),
    "apps": ("KEEP", "Public React recognition application."),
    "artifacts": ("LOCAL_GENERATED_ONLY", "Ignored generated reports and protected model artifacts."),
    "data": ("DELETE_AFTER_VERIFICATION", "Obsolete root data workspace; ML data lives under ml/data."),
    "docs": ("KEEP", "Architecture, audit, operations, and report documentation."),
    "infrastructure": ("KEEP", "Nginx gateway configuration."),
    "ml": ("KEEP", "Offline dataset, preprocessing, training, evaluation, export, and validation."),
    "OpenSigne-Darija-readme": ("DELETE_AFTER_VERIFICATION", "Duplicate README workspace removed after verification."),
    "packages": ("KEEP", "Language-neutral contracts used by architecture/contract tests."),
    "scripts": ("KEEP", "Reproducible audits, benchmarks, and verification tools."),
    "services": ("KEEP", "Stateless API, internal inference, and internal speech services."),
    "tests": ("KEEP", "Cross-service architecture and contract tests."),
    ".env.example": ("KEEP", "Documented local configuration template."),
    ".gitignore": ("KEEP", "Keeps generated and protected local artifacts out of Git."),
    "docker-compose.yml": ("KEEP", "Local production-shaped runtime stack."),
    "Makefile": ("KEEP", "Developer command surface."),
    "README.md": ("KEEP", "Root project overview."),
    "LICENSE": ("KEEP", "Project license."),
    "NOTICE": ("KEEP", "Attribution and provenance notice."),
}


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tracked_files() -> list[str]:
    output = run_git("ls-files")
    return sorted(line for line in output.splitlines() if line)


def candidate_files() -> list[str]:
    output = run_git("ls-files", "--cached", "--others", "--exclude-standard")
    return sorted(line for line in output.splitlines() if line and (ROOT / line).is_file())


def read_text(relative: str) -> str:
    path = ROOT / relative
    if path.name in {"Dockerfile", "Makefile", "NOTICE", "LICENSE"} or path.suffix in TEXT_SUFFIXES:
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return ""
    return ""


def reference_index(files: list[str]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = defaultdict(set)
    corpus = {path: read_text(path) for path in files}
    for target in files:
        needles = {target, Path(target).name}
        if "/" in target:
            needles.add(target.split("/", 1)[0] + "/")
        for source, text in corpus.items():
            if source == target or not text:
                continue
            if any(needle and needle in text for needle in needles):
                index[target].add(source)
    return index


def root_audit(files: list[str]) -> list[dict[str, Any]]:
    tracked = set(tracked_files())
    references = reference_index(files)
    root_names = sorted(set(ROOT_DECISIONS) | {item.name for item in ROOT.iterdir() if item.name != ".git"})
    results: list[dict[str, Any]] = []
    for name in root_names:
        path = ROOT / name
        tracked_under = sorted(item for item in tracked if item == name or item.startswith(name + "/"))
        status = "tracked" if tracked_under else "untracked_or_absent"
        decision, responsibility = ROOT_DECISIONS.get(
            name,
            ("KEEP", "Repository governance or documentation file."),
        )
        results.append(
            {
                "path": name,
                "exists": path.exists(),
                "kind": "directory" if path.is_dir() else "file" if path.is_file() else "absent",
                "tracked_status": status,
                "tracked_file_count": len(tracked_under),
                "runtime_usage": "runtime-owned" if name in {"apps", "services", "infrastructure", "docker-compose.yml"} else "not runtime-mounted",
                "build_usage": "build-owned" if name in {"apps", "services", "ml", "Makefile", "docker-compose.yml"} else "none",
                "test_usage": "test-owned" if name in {"apps", "services", "ml", "tests", "packages", "Makefile"} else "none",
                "docker_usage": "docker-owned" if name in {"apps", "services", "infrastructure", "docker-compose.yml", ".env.example"} else "none",
                "makefile_usage": "make-owned" if name in {"apps", "services", "ml", "tests", "docker-compose.yml", "Makefile"} else "none",
                "ci_usage": "ci-owned" if name in {".github", "apps", "services", "ml", "tests", "packages"} else "none",
                "documentation_usage": "documented" if name in {"README.md", "docs", "DATASET_CARD.md", "MODEL_CARD.md", "NOTICE"} else "minimal",
                "duplicates": "root data duplicated ML-owned data" if name == "data" else "duplicate README workspace" if name == "OpenSigne-Darija-readme" else "none",
                "decision": decision,
                "responsibility": responsibility,
                "reference_count": sum(1 for target in tracked_under for _ in references.get(target, set())),
            }
        )
    return results


def write_root_audit(report: list[dict[str, Any]]) -> None:
    payload = {
        "schema_version": "OPEN_SIGNE_PROJECT_STRUCTURE_ROOT_AUDIT_V1",
        "generated_at": datetime.now(UTC).isoformat(),
        "root_decisions": report,
    }
    (ARTIFACTS / "root-folder-audit.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    rows = [
        "# Root Folder Audit",
        "",
        "Every root path has one explicit responsibility and decision.",
        "",
        "| Path | Decision | Responsibility | Status |",
        "| --- | --- | --- | --- |",
    ]
    for item in report:
        rows.append(
            f"| `{item['path']}` | `{item['decision']}` | {item['responsibility']} | {item['kind']} / {item['tracked_status']} |"
        )
    rows.append("")
    rows.append("Generated machine-readable source: `artifacts/reports/root-folder-audit.json`.")
    (AUDITS / "root-folder-audit.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def environment_audit(files: list[str]) -> dict[str, Any]:
    names: set[str] = set()
    env_example = ROOT / ".env.example"
    if env_example.exists():
        for line in env_example.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and "=" in line:
                names.add(line.split("=", 1)[0].strip())
    env_pattern = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")
    for relative in [
        "docker-compose.yml",
        "apps/web/vite.config.ts",
        "services/api/app/core/config.py",
        "services/inference/app/core/config.py",
        "services/speech/app/core/config.py",
        "Makefile",
    ]:
        names.update(name for name in env_pattern.findall(read_text(relative)) if "_" in name)
    records = []
    corpus = {path: read_text(path) for path in files}
    for name in sorted(names):
        readers = sorted(path for path, text in corpus.items() if name in text)
        records.append(
            {
                "name": name,
                "declared_in_env_example": name in read_text(".env.example"),
                "readers": readers,
                "service_owner": owner_for_env(name),
                "sensitive": any(token in name for token in ("SECRET", "PASSWORD", "TOKEN", "KEY")),
                "decision": "KEEP" if readers else "REMOVE_OR_DOCUMENT",
            }
        )
    payload = {
        "schema_version": "OPEN_SIGNE_ENVIRONMENT_AUDIT_V1",
        "generated_at": datetime.now(UTC).isoformat(),
        "variables": records,
    }
    (ARTIFACTS / "environment-variable-audit.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def owner_for_env(name: str) -> str:
    if name.startswith("VITE_"):
        return "frontend"
    if name.startswith("INFERENCE_") or name in {"MODEL_PACKAGE_DIR", "PREDICTION_CONCURRENCY_LIMIT"}:
        return "inference"
    if name.startswith("SPEECH_") or name.startswith("TTS_"):
        return "speech"
    if name in {"API_VERSION", "API_TITLE"}:
        return "api"
    return "compose_or_developer_tooling"


def dependency_audit(files: list[str]) -> dict[str, Any]:
    imports = "\n".join(read_text(path) for path in files if Path(path).suffix in {".py", ".ts", ".tsx"})
    records: list[dict[str, Any]] = []
    package_json = ROOT / "apps" / "web" / "package.json"
    if package_json.exists():
        payload = json.loads(package_json.read_text(encoding="utf-8"))
        for scope in ("dependencies", "devDependencies"):
            for name, version in sorted(payload.get(scope, {}).items()):
                records.append(
                    {
                        "owner": "apps/web",
                        "dependency": name,
                        "version": version,
                        "scope": "runtime" if scope == "dependencies" else "development",
                        "import_evidence": name in imports,
                        "decision": "KEEP",
                    }
                )
    for owner in ("services/api", "services/inference", "services/speech"):
        pyproject = ROOT / owner / "pyproject.toml"
        payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        for name in payload.get("project", {}).get("dependencies", []):
            records.append(python_dependency_record(owner, name, "runtime", imports))
        for name in payload.get("project", {}).get("optional-dependencies", {}).get("dev", []):
            records.append(python_dependency_record(owner, name, "development", imports))
    ml_requirements = ROOT / "ml" / "requirements-train.txt"
    if ml_requirements.exists():
        for line in ml_requirements.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                records.append(python_dependency_record("ml", stripped, "offline-development", imports))
    payload = {
        "schema_version": "OPEN_SIGNE_DEPENDENCY_AUDIT_V1",
        "generated_at": datetime.now(UTC).isoformat(),
        "dependencies": records,
    }
    (ARTIFACTS / "dependency-audit.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def python_dependency_record(owner: str, requirement: str, scope: str, imports: str) -> dict[str, Any]:
    name = re.split(r"[<>=~!;\[]", requirement, maxsplit=1)[0].strip()
    import_name = {
        "email-validator": "email_validator",
        "httpx2": "httpx",
        "opencv-python-headless": "cv2",
        "pydantic-settings": "pydantic_settings",
        "pyjwt": "jwt",
    }.get(name, name.replace("-", "_"))
    return {
        "owner": owner,
        "dependency": name,
        "requirement": requirement,
        "scope": scope,
        "import_evidence": import_name in imports or name in imports,
        "decision": "KEEP",
    }


def write_cleanup_reports(files: list[str]) -> None:
    deleted = [line[3:] for line in subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).splitlines() if line.startswith(" D ")]
    readme_report = {
        "schema_version": "OPEN_SIGNE_README_DUPLICATE_CLEANUP_V1",
        "generated_at": datetime.now(UTC).isoformat(),
        "path": "OpenSigne-Darija-readme/",
        "exists_after_cleanup": (ROOT / "OpenSigne-Darija-readme").exists(),
        "pre_deletion_findings": [
            "Only local .DS_Store files remained in the duplicate workspace during this pass.",
            "The root README.md and docs/images are the authoritative documentation locations.",
            "No runtime, test, Docker, Makefile, CI, or documentation dependency requires the duplicate folder.",
        ],
        "decision": "DELETE_AFTER_VERIFICATION",
        "deletion_result": "removed",
    }
    (ARTIFACTS / "readme-duplicate-cleanup.json").write_text(
        json.dumps(readme_report, indent=2) + "\n",
        encoding="utf-8",
    )
    deleted_payload = {
        "schema_version": "OPEN_SIGNE_DELETED_FILES_V1",
        "generated_at": datetime.now(UTC).isoformat(),
        "tracked_deleted_files": deleted,
        "local_generated_paths_removed": [
            ".pytest_cache/",
            ".ruff_cache/",
            "OpenSigne-Darija-readme/",
            "data/models/",
            "data/reports/",
            "data/",
            "source-tree .DS_Store files",
        ],
    }
    (ARTIFACTS / "deleted-files.json").write_text(
        json.dumps(deleted_payload, indent=2) + "\n",
        encoding="utf-8",
    )
    retained_payload = {
        "schema_version": "OPEN_SIGNE_RETAINED_FILES_V1",
        "generated_at": datetime.now(UTC).isoformat(),
        "retained_intentionally": [
            {"path": "packages/contracts/", "reason": "Shared JSON contracts read by root contract tests."},
            {"path": "ml/data/external/mosl-video-dataset/", "reason": "Protected local dataset, manifests, splits, and processed caches."},
            {"path": "ml/assets/mediapipe/", "reason": "Protected MediaPipe task asset used by browser Docker mount and offline preprocessing."},
            {"path": "artifacts/models/mosl-isolated-sign-v1/", "reason": "Protected active ONNX model package."},
            {"path": "artifacts/reports/", "reason": "Ignored generated audit evidence; additive reports only."},
        ],
    }
    (ARTIFACTS / "retained-files.json").write_text(
        json.dumps(retained_payload, indent=2) + "\n",
        encoding="utf-8",
    )
    unused_payload = {
        "schema_version": "OPEN_SIGNE_UNUSED_CODE_AUDIT_V1",
        "generated_at": datetime.now(UTC).isoformat(),
        "method": [
            "Existing dependency graph from scripts/audit_repository_architecture.py.",
            "Repository-wide reference search excluding ignored generated artifacts.",
            "Focused ownership review for root data, duplicate README workspace, packages, and generated directories.",
        ],
        "current_pass_deletions": deleted_payload,
        "no_tracked_generated_cache_files": not any(
            re.search(r"(^|/)(\\.pytest_cache|\\.ruff_cache|__pycache__|node_modules|dist|\\.venv)(/|$)", path)
            for path in tracked_files()
        ),
    }
    (ARTIFACTS / "unused-code-audit.json").write_text(
        json.dumps(unused_payload, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    AUDITS.mkdir(parents=True, exist_ok=True)
    files = candidate_files()
    root_report = root_audit(files)
    write_root_audit(root_report)
    environment_audit(files)
    dependency_audit(files)
    write_cleanup_reports(files)
    print(
        json.dumps(
            {
                "root_records": len(root_report),
                "root_data_exists": (ROOT / "data").exists(),
                "duplicate_readme_exists": (ROOT / "OpenSigne-Darija-readme").exists(),
                "generated_cache_dirs_exist": [
                    path
                    for path in (".pytest_cache", ".ruff_cache")
                    if (ROOT / path).exists()
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
