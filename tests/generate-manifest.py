#!/usr/bin/env python3
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / os.environ.get("DIST_DIR", "dist")
SUITE_VERSION = os.environ.get("SUITE_VERSION", "2.0.0-dev")
RELEASE_TAG = os.environ.get("RELEASE_TAG", "")
SOURCE_COMMIT = os.environ.get("SOURCE_COMMIT", "")

TOOLS = [
    ("chromacat", "ChromaCat/chromacat"),
    ("cleanx", "Clean/cleanx"),
    ("dockex", "Docker/dockex"),
    ("gitx", "Git/gitx"),
    ("netx", "Network/netx"),
    ("phpx", "PHP/phpx"),
    ("sqlitex", "Sqlite/sqlitex"),
]

VERSION_RE = re.compile(
    r"^(?P<name>[a-z0-9-]+) (?P<version>[0-9]+\.[0-9]+(?:\.[0-9]+)?(?:[.-][0-9A-Za-z][0-9A-Za-z.-]*)?)$"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tool_version(name: str, path: Path) -> str:
    result = subprocess.run(
        ["bash", str(path), "--version"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
        timeout=10,
        env={
            **os.environ,
            "NO_COLOR": "1",
            "PHPX_NO_LOG": "1",
            "NETX_COLOR": "never",
            "TERM": "dumb",
        },
    )
    if result.stderr:
        raise RuntimeError(f"{name} --version wrote to stderr: {result.stderr!r}")

    output = result.stdout.strip()
    match = VERSION_RE.fullmatch(output)
    if not match or match.group("name") != name:
        raise RuntimeError(f"invalid version output for {name}: {output!r}")
    return match.group("version")


def source_commit() -> str:
    if SOURCE_COMMIT:
        return SOURCE_COMMIT
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


entries = []
for name, source_path in TOOLS:
    artifact = DIST / name
    if not artifact.is_file():
        raise FileNotFoundError(f"missing packaged artifact: {artifact}")
    entries.append(
        {
            "name": name,
            "version": tool_version(name, artifact),
            "asset": name,
            "source_path": source_path,
            "sha256": sha256(artifact),
        }
    )

installer = DIST / "install.sh"
if not installer.is_file():
    raise FileNotFoundError(f"missing packaged installer: {installer}")

manifest = {
    "schema_version": 1,
    "suite": {
        "name": "Toolset",
        "version": SUITE_VERSION,
        "release_tag": RELEASE_TAG or None,
        "repository": "infocyph/Toolset",
        "source_commit": source_commit(),
    },
    "installer": {
        "asset": "install.sh",
        "source_path": "install.sh",
        "sha256": sha256(installer),
    },
    "tools": entries,
}

output = DIST / "manifest.json"
output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
print(output)
