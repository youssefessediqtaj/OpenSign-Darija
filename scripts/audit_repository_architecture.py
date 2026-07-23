#!/usr/bin/env python3
"""Generate the evidence-led repository inventory and dependency graph.

The audit intentionally uses only the Python standard library. It combines Git's
tracked-file view with AST/import parsing and repository-wide text references.
Static results remain heuristics: proposed deletions still require runtime and
manual-reference verification.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import re
import subprocess
import tomllib
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "artifacts" / "reports"
GRAPH_DOC = ROOT / "docs" / "architecture" / "dependency-graph.md"

TEXT_SUFFIXES = {
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
PYTHON_SERVICE_ROOTS = {
    "services/api": ROOT / "services" / "api",
    "services/inference": ROOT / "services" / "inference",
    "services/speech": ROOT / "services" / "speech",
}
RUNTIME_ENTRYPOINTS = {
    "apps/web/src/main.tsx",
    "services/api/app/main.py",
    "services/inference/app/main.py",
    "services/speech/app/main.py",
}
ACTIVE_API_FILES = {
    "services/api/app/__init__.py",
    "services/api/app/main.py",
    "services/api/app/api/__init__.py",
    "services/api/app/api/v1/__init__.py",
    "services/api/app/api/v1/router.py",
    "services/api/app/api/v1/recognitions.py",
    "services/api/app/api/v1/speech.py",
    "services/api/app/api/v1/system.py",
    "services/api/app/core/config.py",
    "services/api/app/core/errors.py",
    "services/api/app/schemas/recognition.py",
    "services/api/app/schemas/speech.py",
    "services/api/app/schemas/system.py",
    "services/api/app/services/inference_client.py",
    "services/api/app/services/speech/__init__.py",
    "services/api/app/services/speech/client.py",
    "services/api/app/services/supported_signs.py",
}
HISTORICAL_API_PREFIXES = (
    "services/api/migrations/",
    "services/api/app/db/",
    "services/api/app/jobs/",
    "services/api/app/models/",
    "services/api/app/security/",
    "services/api/app/tools/",
    "services/api/app/services/linguistics/",
)
HISTORICAL_API_FILES = {
    "services/api/alembic.ini",
    "services/api/app/api/deps.py",
    "services/api/app/api/v1/admin_datasets.py",
    "services/api/app/api/v1/admin_models.py",
    "services/api/app/api/v1/auth.py",
    "services/api/app/api/v1/consents.py",
    "services/api/app/api/v1/contribution_campaigns.py",
    "services/api/app/api/v1/contributions.py",
    "services/api/app/api/v1/contributors.py",
    "services/api/app/api/v1/linguistics.py",
    "services/api/app/api/v1/messages.py",
    "services/api/app/api/v1/reviews.py",
    "services/api/app/api/v1/signs.py",
    "services/api/app/schemas/auth.py",
    "services/api/app/schemas/dataset.py",
    "services/api/app/schemas/messages.py",
    "services/api/app/schemas/signs.py",
    "services/api/app/services/auth_service.py",
    "services/api/app/services/object_storage.py",
}
HISTORICAL_DOC_NAMES = {
    "consent-management.md",
    "contribution-workflow.md",
    "dataset-collection.md",
    "dataset-export.md",
    "dataset-versioning.md",
    "linguistic-engine.md",
    "manual-message-testing.md",
    "message-backend-log-checklist.md",
    "message-builder.md",
    "message-history.md",
    "message-privacy.md",
    "model-activation.md",
    "model-registry.md",
    "object-storage.md",
    "review-workflow.md",
    "semantic-concepts.md",
}
DIST_IMPORT_ALIASES = {
    "alembic": {"alembic"},
    "argon2-cffi": {"argon2"},
    "email-validator": {"email_validator"},
    "fastapi": {"fastapi"},
    "httpx": {"httpx"},
    "httpx2": {"httpx2"},
    "mediapipe": {"mediapipe"},
    "minio": {"minio"},
    "numpy": {"numpy"},
    "onnxruntime": {"onnxruntime"},
    "opencv-python-headless": {"cv2"},
    "psycopg": {"psycopg"},
    "pydantic": {"pydantic"},
    "pydantic-settings": {"pydantic_settings"},
    "pyjwt": {"jwt"},
    "redis": {"redis"},
    "sqlalchemy": {"sqlalchemy"},
    "uvicorn": {"uvicorn"},
}


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read_text(relative: str) -> str:
    path = ROOT / relative
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {
        "Dockerfile",
        "Makefile",
        "NOTICE",
        "LICENSE",
    }:
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def tracked_files() -> list[str]:
    candidates = run_git(
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
    ).splitlines()
    return sorted(
        item for item in candidates if item and (ROOT / item).is_file()
    )


def language_for(path: str) -> str:
    name = Path(path).name
    suffix = Path(path).suffix.lower()
    if name == "Dockerfile":
        return "Dockerfile"
    if name == "Makefile":
        return "Make"
    return {
        ".css": "CSS",
        ".csv": "CSV",
        ".html": "HTML",
        ".ini": "INI",
        ".js": "JavaScript",
        ".json": "JSON",
        ".md": "Markdown",
        ".mjs": "JavaScript",
        ".png": "PNG",
        ".py": "Python",
        ".toml": "TOML",
        ".ts": "TypeScript",
        ".tsx": "TypeScript/React",
        ".txt": "Text",
        ".yaml": "YAML",
        ".yml": "YAML",
    }.get(suffix, "Other")


def layer_for(path: str) -> str:
    if path.startswith("apps/web/"):
        return "frontend"
    if path.startswith("services/api/"):
        return "public-api"
    if path.startswith("services/inference/"):
        return "inference-runtime"
    if path.startswith("services/speech/"):
        return "speech-runtime"
    if path.startswith("ml/"):
        return "offline-ml"
    if path.startswith("packages/contracts/"):
        return "language-neutral-contracts"
    if path.startswith("packages/"):
        return "shared-package"
    if path.startswith("infrastructure/") or path == "docker-compose.yml":
        return "infrastructure"
    if path.startswith(".github/"):
        return "ci"
    if path.startswith("docs/") or path.endswith(".md"):
        return "documentation"
    if path.startswith("scripts/") or path == "Makefile":
        return "developer-tooling"
    if path.startswith("tests/"):
        return "shared-test-fixtures"
    if path.startswith(".agent/"):
        return "agent-continuity"
    return "repository-governance"


def purpose_for(path: str) -> str:
    name = Path(path).name
    if path.endswith((".test.ts", ".test.tsx")) or "/tests/" in path or name.startswith("test_"):
        return "Automated verification or deterministic test fixture."
    if name == "Dockerfile" or path == "docker-compose.yml":
        return "Container build or runtime service definition."
    if path.startswith(".github/workflows/"):
        return "Continuous-integration workflow."
    if path.startswith("docs/") or path.endswith(".md"):
        return "Architecture, operation, provenance, or historical documentation."
    if "/schemas/" in path or "schema" in name:
        return "Data contract or schema definition."
    if "/api/" in path:
        return "HTTP routing and public/internal request handling."
    if "/services/" in path:
        return "Application orchestration or external service boundary."
    if "/models/" in path:
        return "Domain, persistence, or model-runtime representation."
    if path.startswith("ml/"):
        return "Offline dataset, preprocessing, training, evaluation, export, or validation logic."
    if path.startswith("scripts/"):
        return "Reproducible audit or benchmark command."
    if path.endswith(".json") or path.endswith(".csv"):
        return "Configuration, manifest, fixture, or generated evidence."
    return "Repository source, configuration, or governance asset."


def parse_python_imports(text: str) -> tuple[list[str], list[str]]:
    imports: set[str] = set()
    classes: set[str] = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = ("." * node.level) + node.module
                imports.add(module)
                imports.update(
                    f"{module}.{alias.name}"
                    for alias in node.names
                    if alias.name != "*"
                )
        elif isinstance(node, ast.ClassDef):
            classes.add(node.name)
    return sorted(imports), sorted(classes)


TS_IMPORT_PATTERN = re.compile(
    r"""(?:from\s+|import\s*\(\s*|require\(\s*)["']([^"']+)["']"""
)
TS_EXPORT_PATTERN = re.compile(
    r"\bexport\s+(?:default\s+)?(?:async\s+)?(?:class|const|function|interface|type|enum)\s+([A-Za-z_$][\w$]*)"
)


def parse_ts_imports(text: str) -> tuple[list[str], list[str]]:
    return sorted(set(TS_IMPORT_PATTERN.findall(text))), sorted(set(TS_EXPORT_PATTERN.findall(text)))


def resolve_python_import(source: str, imported: str, candidates: set[str]) -> str | None:
    if imported.startswith("."):
        return None
    source_root: Path | None = None
    source_prefix = ""
    for prefix, root in PYTHON_SERVICE_ROOTS.items():
        if source.startswith(prefix + "/"):
            source_root = root
            source_prefix = prefix + "/"
            break
    if source.startswith("ml/"):
        source_root = ROOT
    if source_root is None:
        return None
    if imported.startswith("app.") and source_prefix:
        relative = imported.replace(".", "/")
        options = [
            source_prefix + relative + ".py",
            source_prefix + relative + "/__init__.py",
        ]
    elif imported == "app" and source_prefix:
        options = [source_prefix + "app/__init__.py"]
    elif imported.startswith("ml."):
        relative = imported.replace(".", "/")
        options = [relative + ".py", relative + "/__init__.py"]
    else:
        return None
    return next((option for option in options if option in candidates), None)


def resolve_ts_import(source: str, imported: str, candidates: set[str]) -> str | None:
    if not imported.startswith("."):
        return None
    base = (ROOT / source).parent / imported
    options = [
        base,
        Path(str(base) + ".ts"),
        Path(str(base) + ".tsx"),
        base / "index.ts",
        base / "index.tsx",
    ]
    for option in options:
        try:
            relative = option.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            continue
        if relative in candidates:
            return relative
    return None


def references_in_corpus(path: str, corpora: dict[str, str]) -> dict[str, bool]:
    basename = Path(path).name
    needles = {path, path.removesuffix(Path(path).suffix), basename}
    return {
        name: any(needle and needle in text for needle in needles)
        for name, text in corpora.items()
    }


def proposed_action(path: str) -> tuple[str, str, float]:
    if path in HISTORICAL_API_FILES or path.startswith(HISTORICAL_API_PREFIXES):
        return (
            "DELETE_AFTER_TESTS",
            "Unreachable from the mounted stateless API and retained from removed stateful product phases.",
            0.96,
        )
    if path.startswith("services/api/opensign_api.egg-info/") or path.endswith(
        "tsconfig.tsbuildinfo"
    ):
        return (
            "DELETE_AFTER_TESTS",
            "Tracked build/install output; source configuration can reproduce it.",
            0.99,
        )
    if path.startswith("OpenSigne-Darija-readme/"):
        return (
            "DELETE_AFTER_TESTS",
            "Duplicate README/image copy outside the authoritative root documentation tree.",
            0.99,
        )
    if path.startswith(("packages/config/", "packages/linguistics/")):
        return (
            "DELETE_AFTER_TESTS",
            "Unreferenced placeholder or superseded configuration package.",
            0.95,
        )
    if Path(path).name in HISTORICAL_DOC_NAMES:
        return (
            "HISTORICAL_DOCUMENTATION",
            "Describes a removed database/auth/dataset/message workflow rather than the active product.",
            0.93,
        )
    if path.startswith("docs/integrations/") or path in {
        "DATASET_CARD_KAGGLE_ALPHABET.md",
        "DATASET_CARD_MENDELEY_MOSL.md",
        "MODEL_CARD_ALPHABET.md",
        "THIRD_PARTY_DATASETS.md",
    }:
        return (
            "HISTORICAL_DOCUMENTATION",
            "Retained provenance or completed migration history; not an active runtime instruction.",
            0.85,
        )
    if Path(path).name == ".gitkeep":
        return (
            "GENERATED_ARTIFACT",
            "Directory placeholder; remove when the directory contains real owned code or is obsolete.",
            0.9,
        )
    if path in {
        "ml/training/train_mosl_word.py",
        "ml/export/validate_mosl_word_smoke.py",
    }:
        return (
            "REQUIRES_MANUAL_REVIEW",
            "Earlier smoke-model path that may be retained only for historical reproducibility.",
            0.7,
        )
    if path.startswith("apps/web/src/") and any(
        token in path for token in ("/utils/", "/types/", "/pages/", "/routes/", "/lib/")
    ):
        return (
            "MOVE",
            "Move under the owning recognition feature, app shell, or shared API boundary.",
            0.9,
        )
    if path in ACTIVE_API_FILES:
        return ("SIMPLIFY", "Active API core; retain while tightening responsibility boundaries.", 1.0)
    return ("KEEP", "Active source, test, configuration, evidence, or protected provenance.", 1.0)


def is_generated(path: str) -> bool:
    return (
        ".egg-info/" in path
        or path.endswith((".tsbuildinfo", ".png"))
        or Path(path).name == ".gitkeep"
        or "/manifests/" in path
        or "/reports/" in path
        or "/splits/" in path
        or path.endswith("package-lock.json")
    )


def owner_for(path: str) -> str:
    layer = layer_for(path)
    return {
        "frontend": "Web recognition feature",
        "public-api": "Public API service",
        "inference-runtime": "ONNX inference service",
        "speech-runtime": "Local speech service",
        "offline-ml": "Offline ML pipeline",
        "language-neutral-contracts": "Cross-service contracts",
        "infrastructure": "Runtime infrastructure",
        "ci": "Quality/CI",
        "documentation": "Architecture/documentation",
        "developer-tooling": "Developer tooling",
        "shared-test-fixtures": "Cross-language contract tests",
    }.get(layer, "Repository maintainers")


def compute_reachable(edges: list[dict[str, str]]) -> set[str]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        if edge["type"] == "imports":
            adjacency[edge["from"]].add(edge["to"])
    reachable = set(RUNTIME_ENTRYPOINTS)
    stack = list(RUNTIME_ENTRYPOINTS)
    while stack:
        current = stack.pop()
        for target in adjacency.get(current, set()):
            if target not in reachable:
                reachable.add(target)
                stack.append(target)
    return reachable


def strongly_connected_components(edges: list[dict[str, str]]) -> list[list[str]]:
    adjacency: dict[str, list[str]] = defaultdict(list)
    nodes: set[str] = set()
    for edge in edges:
        if edge["type"] == "imports":
            adjacency[edge["from"]].append(edge["to"])
            nodes.update((edge["from"], edge["to"]))
    index = 0
    indexes: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indexes[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in adjacency.get(node, []):
            if target not in indexes:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indexes[target])
        if lowlinks[node] == indexes[node]:
            component: list[str] = []
            while stack:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            if len(component) > 1:
                components.append(sorted(component))

    for node in sorted(nodes):
        if node not in indexes:
            visit(node)
    return sorted(components)


def directory_summary(relative: str, role: str, protected: bool) -> dict[str, Any]:
    root = ROOT / relative
    count = 0
    size = 0
    if root.exists():
        for directory, _, files in os.walk(root):
            for filename in files:
                file_path = Path(directory) / filename
                try:
                    size += file_path.stat().st_size
                    count += 1
                except OSError:
                    continue
    return {
        "path": relative,
        "exists": root.exists(),
        "file_count": count,
        "size_bytes": size,
        "protected": protected,
        "role": role,
    }


def ignored_runtime_inventory() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    directories = [
        directory_summary(
            "ml/data/external/mosl-video-dataset/raw",
            "Protected source video records; offline ML only.",
            True,
        ),
        directory_summary(
            "ml/data/external/mosl-video-dataset/processed",
            "Protected deterministic 60×75×3 landmark cache.",
            True,
        ),
        directory_summary(
            "ml/assets/mediapipe",
            "Protected browser/offline MediaPipe task asset.",
            True,
        ),
        directory_summary(
            "artifacts/models",
            "Protected model packages consumed read-only by runtime services.",
            True,
        ),
        directory_summary(
            "artifacts/reports",
            "Protected generated evidence and audit reports.",
            True,
        ),
        directory_summary("apps/web/node_modules", "Local frontend dependency cache.", False),
        directory_summary("services/api/.venv", "Local API development environment.", False),
        directory_summary(
            "services/inference/.venv", "Local inference development environment.", False
        ),
        directory_summary("services/speech/.venv", "Local speech development environment.", False),
        directory_summary("ml/.venv", "Local offline-ML development environment.", False),
    ]
    important_files: list[dict[str, Any]] = []
    for relative_root in (
        "artifacts/models/mosl-isolated-sign-v1",
        "ml/assets/mediapipe",
    ):
        root = ROOT / relative_root
        if not root.exists():
            continue
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            payload = path.read_bytes()
            important_files.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "size_bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "runtime_usage": "read-only protected runtime asset",
                }
            )
    return directories, important_files


def parse_declared_dependencies(
    files: list[str], raw_imports: dict[str, list[str]], reachable: set[str]
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for service in ("api", "inference", "speech"):
        relative = f"services/{service}/pyproject.toml"
        payload = tomllib.loads((ROOT / relative).read_text(encoding="utf-8"))
        runtime = payload.get("project", {}).get("dependencies", [])
        dev = payload.get("project", {}).get("optional-dependencies", {}).get("dev", [])
        service_files = [item for item in files if item.startswith(f"services/{service}/")]
        imported_all = {
            name.split(".", 1)[0].lstrip(".")
            for item in service_files
            for name in raw_imports.get(item, [])
        }
        imported_runtime = {
            name.split(".", 1)[0].lstrip(".")
            for item in service_files
            if item in reachable
            for name in raw_imports.get(item, [])
        }
        for scope, dependencies in (("runtime", runtime), ("dev", dev)):
            for declaration in dependencies:
                distribution = re.split(r"[<>=!~;\[]", declaration, maxsplit=1)[0].strip().lower()
                aliases = DIST_IMPORT_ALIASES.get(
                    distribution, {distribution.replace("-", "_")}
                )
                indirectly_used = (
                    scope == "dev"
                    and distribution in {"httpx", "httpx2"}
                    and service in {"api", "inference", "speech"}
                )
                results.append(
                    {
                        "service": service,
                        "scope": scope,
                        "declaration": declaration,
                        "distribution": distribution,
                        "imported_anywhere": bool(aliases & imported_all),
                        "imported_by_runtime_graph": bool(aliases & imported_runtime),
                        "used_indirectly": indirectly_used,
                        "name_review": (
                            "reviewed_intentional_fastapi_testclient_dependency"
                            if distribution == "httpx2"
                            else None
                        ),
                    }
                )
    return results


def parse_make_targets(text: str) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line or line[0].isspace() or line.startswith("."):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)\s*:(.*)$", line)
        if match:
            targets.append(
                {
                    "target": match.group(1),
                    "dependencies": match.group(2).strip().split(),
                }
            )
    return targets


def build_audit() -> tuple[dict[str, Any], dict[str, Any]]:
    files = tracked_files()
    candidates = set(files)
    texts = {path: read_text(path) for path in files}
    raw_imports: dict[str, list[str]] = {}
    declarations: dict[str, list[str]] = {}
    edges: list[dict[str, str]] = []

    for path, source in texts.items():
        if path.endswith(".py"):
            imports, declared = parse_python_imports(source)
            raw_imports[path] = imports
            declarations[path] = declared
            for imported in imports:
                target = resolve_python_import(path, imported, candidates)
                if target:
                    edges.append({"from": path, "to": target, "type": "imports"})
        elif path.endswith((".ts", ".tsx", ".js", ".mjs")):
            imports, declared = parse_ts_imports(source)
            raw_imports[path] = imports
            declarations[path] = declared
            for imported in imports:
                target = resolve_ts_import(path, imported, candidates)
                if target:
                    edges.append({"from": path, "to": target, "type": "imports"})
        else:
            raw_imports[path] = []
            declarations[path] = []

    imported_by: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        imported_by[edge["to"]].append(edge["from"])
    reachable = compute_reachable(edges)

    corpora = {
        "Docker": "\n".join(
            texts[path]
            for path in files
            if Path(path).name == "Dockerfile" or path == "docker-compose.yml"
        ),
        "Makefile": texts.get("Makefile", ""),
        "CI": "\n".join(texts[path] for path in files if path.startswith(".github/")),
        "documentation": "\n".join(
            texts[path] for path in files if path.startswith("docs/") or path == "README.md"
        ),
    }
    records: list[dict[str, Any]] = []
    for path in files:
        references = references_in_corpus(path, corpora)
        action, reason, confidence = proposed_action(path)
        dynamic = bool(
            re.search(
                r"\b(importlib|__import__|import\.meta\.glob|import\s*\(|require\s*\(|entry_points)\b",
                texts[path],
            )
        )
        test_references = sorted(
            source
            for source in imported_by.get(path, [])
            if "/tests/" in source or Path(source).name.startswith("test_")
        )
        records.append(
            {
                "path": path,
                "layer": layer_for(path),
                "language": language_for(path),
                "purpose": purpose_for(path),
                "imports": raw_imports[path],
                "resolved_imports": sorted(
                    edge["to"] for edge in edges if edge["from"] == path
                ),
                "imported_by_references": sorted(imported_by.get(path, [])),
                "runtime_usage": path in reachable,
                "test_usage": bool(test_references)
                or "/tests/" in path
                or Path(path).name.startswith("test_"),
                "docker_usage": references["Docker"],
                "makefile_usage": references["Makefile"],
                "ci_usage": references["CI"],
                "documentation_usage": references["documentation"],
                "dynamic_loading_risk": dynamic,
                "generated_or_handwritten": "generated" if is_generated(path) else "handwritten",
                "current_owner_responsibility": owner_for(path),
                "proposed_action": action,
                "reason": reason,
                "deletion_confidence": confidence,
            }
        )

    ignored_directories, ignored_files = ignored_runtime_inventory()
    action_counts = Counter(record["proposed_action"] for record in records)

    all_import_names = Counter(
        declaration
        for names in raw_imports.values()
        for declaration in names
        if declaration and not declaration.startswith(".")
    )
    duplicate_classes = {
        name: sorted(path for path, names in declarations.items() if name in names)
        for name, count in Counter(name for names in declarations.values() for name in names).items()
        if count > 1
    }
    duplicate_basenames = {
        basename: sorted(path for path in files if Path(path).name == basename)
        for basename, count in Counter(Path(path).name for path in files).items()
        if count > 1 and basename not in {"__init__.py", "README.md", ".gitkeep", "Dockerfile"}
    }

    forbidden_findings: list[dict[str, str]] = []
    for path, source in texts.items():
        if path.startswith("apps/web/src/"):
            for pattern, reason in (
                (r"https?://(?:inference|speech)(?::\d+)?", "frontend internal-service URL"),
                (
                    r"(?:from|import).*services/(?:api|inference|speech)/app",
                    "frontend backend source reference",
                ),
                (r"\b(?:video|image|audio)_base64\b", "frontend raw-media field"),
            ):
                if re.search(pattern, source, re.IGNORECASE):
                    forbidden_findings.append({"path": path, "reason": reason})
        if path.startswith("services/inference/app/") and re.search(
            r"from app\.(?:speech|api\.v1)|http://speech", source
        ):
            forbidden_findings.append({"path": path, "reason": "inference cross-service dependency"})
        if path.startswith("services/speech/app/") and re.search(
            r"from app\.(?:inference|api\.v1)|http://inference", source
        ):
            forbidden_findings.append({"path": path, "reason": "speech cross-service dependency"})

    route_pattern = re.compile(r"""["']((?:https?://[^"']+)|(?:/api/[^"']+)|(?:/predict/[^"']+)|(?:/synthesize))["']""")
    http_calls: list[dict[str, str]] = []
    for path, source in texts.items():
        for endpoint in sorted(set(route_pattern.findall(source))):
            http_calls.append({"source": path, "endpoint": endpoint})

    env_declarations = sorted(
        set(re.findall(r"\$\{([A-Z][A-Z0-9_]+)", texts.get("docker-compose.yml", "")))
        | set(re.findall(r"^([A-Z][A-Z0-9_]+)=", texts.get(".env.example", ""), re.MULTILINE))
    )
    env_readers: dict[str, list[str]] = defaultdict(list)
    for path, source in texts.items():
        for env_name in env_declarations:
            field_name = env_name.lower()
            if (
                env_name in source
                or f"settings.{field_name}" in source
                or f".{field_name}" in source
                or f"import.meta.env.{env_name}" in source
            ):
                env_readers[env_name].append(path)

    declared_dependencies = parse_declared_dependencies(files, raw_imports, reachable)
    orphan_modules = sorted(
        path
        for path in files
        if path.endswith((".py", ".ts", ".tsx"))
        and path not in RUNTIME_ENTRYPOINTS
        and not imported_by.get(path)
        and "/tests/" not in path
        and not path.startswith("scripts/")
        and Path(path).name not in {"setup.ts", "vite-env.d.ts", "tailwind.config.ts"}
        and path not in corpora["Makefile"]
        and path.removesuffix(".py").replace("/", ".") not in corpora["Makefile"]
        and not Path(path).name.startswith(("test_", "vite.config", "playwright.config"))
        and Path(path).name != "__init__.py"
    )
    unreferenced_exports = sorted(
        {
            f"{path}:{name}"
            for path, names in declarations.items()
            if path.endswith((".ts", ".tsx"))
            for name in names
            if all(name not in texts[other] for other in files if other != path)
        }
    )

    inventory = {
        "schema_version": "OPEN_SIGNE_REPOSITORY_INVENTORY_V1",
        "generated_at": datetime.now(UTC).isoformat(),
        "branch": run_git("branch", "--show-current"),
        "commit": run_git("rev-parse", "HEAD"),
        "methodology": [
            "Git ls-files is authoritative for tracked files.",
            "Python AST and TypeScript import regexes build local import edges.",
            "Docker, Make, CI, docs, runtime entrypoint reachability, and manual action rules are cross-checked.",
            "Ignored protected/runtime directories are recorded as bounded directory summaries; active model and MediaPipe files are individually hashed.",
            "DELETE_AFTER_TESTS remains a proposal until manual search and full runtime verification pass.",
        ],
        "tracked_file_count": len(records),
        "classification_counts": dict(sorted(action_counts.items())),
        "files": records,
        "important_ignored_runtime_directories": ignored_directories,
        "important_ignored_runtime_files": ignored_files,
    }
    graph = {
        "schema_version": "OPEN_SIGNE_MODULE_DEPENDENCY_GRAPH_V1",
        "generated_at": datetime.now(UTC).isoformat(),
        "branch": run_git("branch", "--show-current"),
        "commit": run_git("rev-parse", "HEAD"),
        "nodes": [
            {"id": path, "kind": "file", "layer": layer_for(path)} for path in files
        ],
        "edges": edges,
        "runtime_entrypoints": sorted(RUNTIME_ENTRYPOINTS),
        "runtime_reachable_files": sorted(reachable),
        "cycles": strongly_connected_components(edges),
        "cross_layer_violations": forbidden_findings,
        "orphan_module_candidates": orphan_modules,
        "unreferenced_export_candidates": unreferenced_exports,
        "duplicate_class_or_schema_names": duplicate_classes,
        "duplicate_basenames": duplicate_basenames,
        "declared_dependencies": declared_dependencies,
        "unused_declared_dependency_candidates": [
            item
            for item in declared_dependencies
            if not item["imported_anywhere"]
            and not item["used_indirectly"]
            and item["distribution"] not in {"uvicorn", "pytest", "pytest-cov", "ruff", "mypy"}
        ],
        "dependency_name_reviews": [
            item for item in declared_dependencies if item["name_review"]
        ],
        "environment": {
            "declared": env_declarations,
            "readers": dict(sorted(env_readers.items())),
            "without_repository_reader": sorted(
                env_name for env_name in env_declarations if not env_readers[env_name]
            ),
        },
        "make_targets": parse_make_targets(texts.get("Makefile", "")),
        "http_calls_and_route_literals": http_calls,
        "import_frequency": dict(all_import_names.most_common()),
        "dynamic_import_files": sorted(
            record["path"] for record in records if record["dynamic_loading_risk"]
        ),
        "important_artifact_edges": [
            {
                "from": "docker-compose.yml",
                "to": "artifacts/models/mosl-isolated-sign-v1",
                "type": "read-only-model-mount",
            },
            {
                "from": "docker-compose.yml",
                "to": "ml/assets/mediapipe/holistic_landmarker.task",
                "type": "read-only-browser-model-mount",
            },
            {
                "from": "ml",
                "to": "artifacts/models/mosl-isolated-sign-v1",
                "type": "offline-produces-runtime-consumes",
            },
        ],
    }
    return inventory, graph


def write_inventory(inventory: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORT_DIR / "repository-file-inventory.json"
    csv_path = REPORT_DIR / "repository-file-inventory.csv"
    json_path.write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    fields = [
        "path",
        "layer",
        "language",
        "purpose",
        "imports",
        "imported_by_references",
        "runtime_usage",
        "test_usage",
        "docker_usage",
        "makefile_usage",
        "ci_usage",
        "documentation_usage",
        "dynamic_loading_risk",
        "generated_or_handwritten",
        "current_owner_responsibility",
        "proposed_action",
        "reason",
        "deletion_confidence",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in inventory["files"]:
            row = {field: record[field] for field in fields}
            row["imports"] = json.dumps(row["imports"], ensure_ascii=False)
            row["imported_by_references"] = json.dumps(
                row["imported_by_references"], ensure_ascii=False
            )
            writer.writerow(row)


def write_graph(graph: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    GRAPH_DOC.parent.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "module-dependency-graph.json").write_text(
        json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    dependencies = graph["declared_dependencies"]
    unused = graph["unused_declared_dependency_candidates"]
    violations = graph["cross_layer_violations"]
    doc = f"""# Repository dependency graph

Generated by `scripts/audit_repository_architecture.py` from commit
`{graph["commit"]}` on branch `{graph["branch"]}`.

## Runtime flow

```text
Browser camera
  → browser MediaPipe + automatic segmentation
  → POST /api/v1/recognitions/word
  → API typed inference client
  → POST inference:8001/predict/word
  → protected ONNX model package
  → compact supported-sign or UNKNOWN response
  → POST /api/v1/speech/sign for supported signs only
  → API typed speech client
  → POST speech:8010/synthesize
  → browser audio playback
```

Nginx is the only public gateway. Inference and speech have no host ports and are
reachable only on the Compose network. Raw media never crosses the browser boundary.

## Static graph summary

- Current source/config nodes: {len(graph["nodes"])}
- Resolved local import edges: {len(graph["edges"])}
- Runtime-reachable source files: {len(graph["runtime_reachable_files"])}
- Circular import components: {len(graph["cycles"])}
- Forbidden cross-layer findings: {len(violations)}
- Orphan module candidates requiring review: {len(graph["orphan_module_candidates"])}
- Declared dependency records: {len(dependencies)}
- Unused declared dependency candidates: {len(unused)}

## Audit interpretation

Static candidates are not deletion proof. The inventory combines these edges with
route tests, startup import tracing, Docker/Make/CI references, repository search,
and the complete regression suite. Dynamic import files are listed explicitly in
the JSON report. Historical documentation alone is not evidence that a module is
part of the current runtime.

## Findings

The machine-readable source of truth is
`artifacts/reports/module-dependency-graph.json`. It includes cycles, forbidden
dependencies and URLs, orphan candidates, duplicate names, environment readers,
Make target dependencies, HTTP literals, dependency-use evidence, dynamic imports,
and model/data artifact edges.
"""
    GRAPH_DOC.write_text(doc, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-inventory",
        action="store_true",
        help="Refresh only the dependency graph after refactoring.",
    )
    args = parser.parse_args()
    inventory, graph = build_audit()
    if not args.skip_inventory:
        write_inventory(inventory)
    write_graph(graph)
    print(
        json.dumps(
            {
                "tracked_files": inventory["tracked_file_count"],
                "import_edges": len(graph["edges"]),
                "cycles": len(graph["cycles"]),
                "cross_layer_violations": len(graph["cross_layer_violations"]),
                "orphan_candidates": len(graph["orphan_module_candidates"]),
                "inventory_written": not args.skip_inventory,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
