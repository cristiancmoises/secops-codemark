#!/usr/bin/env python3
"""Build a deterministic zipapp and source staging. GPL-3.0-or-later."""

import argparse
import hashlib
import io
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from codemark import __version__


def archive_bytes(entries, prefix=b""):
    output = io.BytesIO()
    output.write(prefix)
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name, data in sorted(entries.items()):
            item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.create_system = 3
            mode = 0o755 if name.endswith((".sh", ".pyz")) else 0o644
            item.external_attr = (0o100000 | mode) << 16
            archive.writestr(item, data)
    return output.getvalue()


def checksum_entries(entries):
    return "".join(
        hashlib.sha256(data).hexdigest() + "  " + name + "\n"
        for name, data in sorted(entries.items())
    ).encode("utf-8")


def public_source(path):
    relative = path.relative_to(ROOT)
    excluded = {"__pycache__", ".git", ".superpowers", "superpowers", "node_modules"}
    if any(part in excluded for part in relative.parts):
        return False
    if relative.parts[:2] == ("website", "public"):
        return False
    return (
        path.name not in {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}
        and not path.name.upper().startswith(("PROMPT", "EXECUTION-PROMPT"))
        and path.suffix != ".pyc"
    )


def build(output, *, archive=False):
    output.mkdir(parents=True, exist_ok=True)
    name = f"secops-codemark-{__version__}"
    destination = output / name
    if destination.exists() or destination.is_symlink():
        raise RuntimeError(
            "Source staging already exists; choose a fresh --output directory."
        )
    sources = {}
    for directory in (
        "codemark",
        "docs",
        "tests",
        "scripts",
        "examples",
        ".github",
        "website",
    ):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_symlink():
                raise RuntimeError("Do not ship symlinks: " + str(path))
            if path.is_file() and public_source(path):
                sources[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for filename in (
        "README.md",
        "README.pt-BR.md",
        "COPYING",
        "codemark.py",
        "iniciar.sh",
        "Iniciar.bat",
        ".gitignore",
        ".gitattributes",
        "CHANGELOG.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "pyproject.toml",
    ):
        path = ROOT / filename
        if path.is_symlink():
            raise RuntimeError("Do not ship symlinks: " + str(path))
        if path.is_file():
            sources[filename] = path.read_bytes()
    package = {
        filename: data
        for filename, data in sources.items()
        if Path(filename).parent.as_posix() == "codemark" and filename.endswith(".py")
    }
    package["__main__.py"] = (
        b"from codemark.cli import main\nraise SystemExit(main())\n"
    )
    package["COPYING"] = sources["COPYING"]
    portable = archive_bytes(package, b"#!/usr/bin/env python3\n")
    (output / "codemark.pyz").write_bytes(portable)
    (output / "codemark.pyz").chmod(0o755)
    sources["codemark.pyz"] = portable
    sources["SHA256SUMS"] = checksum_entries(sources)
    with tempfile.TemporaryDirectory(
        prefix=".codemark-build-", dir=output
    ) as directory:
        stage = Path(directory) / destination.name
        stage.mkdir()
        for filename, data in sources.items():
            target = stage / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(0o755 if target.suffix in (".sh", ".pyz") else 0o644)
        stage.rename(destination)
    release_files = {"codemark.pyz": portable}
    result = destination
    if archive:
        zupt = shutil.which("zupt")
        if not zupt:
            raise RuntimeError(
                "ZUPT is required for --archive; no source archive was created."
            )
        result = output / (destination.name + ".zupt")
        subprocess.run(
            [zupt, "compress", "-t", "2", result.name, destination.name],
            cwd=output,
            check=True,
            timeout=120,
        )
        subprocess.run([zupt, "test", str(result)], check=True, timeout=120)
        release_files[result.name] = result.read_bytes()
    (output / "SHA256SUMS").write_bytes(checksum_entries(release_files))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument(
        "--archive",
        action="store_true",
        help="also create and test a genuine ZUPT source archive",
    )
    args = parser.parse_args()
    print(build(args.output.resolve(), archive=args.archive))
