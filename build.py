from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path


def list_files_to_package(root: Path, excluded_relative_paths: set[str]) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Failed to list files with Git. Make sure Git is installed and this folder is a Git repository."
        )

    files: list[Path] = []
    for line in result.stdout.splitlines():
        if not line:
            continue

        relative = line.replace("\\", "/")
        if relative in excluded_relative_paths:
            continue

        if Path(relative).name.startswith("."):
            continue

        file_path = root / line
        if file_path.is_file():
            files.append(file_path)

    return files


def build_zip(root: Path, output_zip: Path) -> None:
    excluded = {Path(__file__).name.replace("\\", "/")}

    try:
        output_rel = output_zip.resolve().relative_to(root.resolve())
        excluded.add(output_rel.as_posix())
    except ValueError:
        pass

    files = list_files_to_package(root, excluded)
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in files:
            archive.write(file_path, arcname=file_path.relative_to(root).as_posix())

    print(f"Created {output_zip} with {len(files)} files.")


def read_manifest_value(manifest_path: Path, key: str) -> str:
    pattern = re.compile(rf"^{re.escape(key)}\s*=\s*\"([^\"]+)\"\s*$")

    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            return match.group(1)

    raise ValueError(f"Could not find '{key}' in {manifest_path.name}.")


def main() -> int:
    root = Path(__file__).resolve().parent
    manifest_path = root / "blender_manifest.toml"
    addon_id = read_manifest_value(manifest_path, "id")
    version = read_manifest_value(manifest_path, "version")
    default_output = root / f"{addon_id}-v{version}.zip"

    parser = argparse.ArgumentParser(
        description="Create a zip archive of this repository excluding .gitignore matches and this build script."
    )
    parser.add_argument(
        "--output",
        "-o",
        default=str(default_output),
        help="Output zip file path (default: <id>-v<version>.zip in the repository root).",
    )
    args = parser.parse_args()

    output_zip = Path(args.output).resolve()

    try:
        build_zip(root, output_zip)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
