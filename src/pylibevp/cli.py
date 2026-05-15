"""Command line interface for pylibevp."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .api import LibEVP


def _collect_files(base_path: Path, patterns: list[str]) -> list[str]:
    files_to_pack: list[str] = []
    for pattern in patterns:
        if pattern == "*":
            files_to_pack.extend(
                str(file_path.relative_to(base_path))
                for file_path in base_path.rglob("*")
                if file_path.is_file()
            )
            continue

        files_to_pack.extend(
            str(file_path.relative_to(base_path))
            for file_path in base_path.rglob(pattern)
            if file_path.is_file()
        )

    return sorted(set(files_to_pack))


def cmd_list(args: argparse.Namespace) -> int:
    evp = LibEVP(lib_path=args.lib)
    files = evp.get_archive_files(args.archive)

    print(f"Archive: {args.archive}")
    print(f"Files: {len(files)}")
    print(f"{'#':<6} {'Name':<60} {'Size':<12} {'Compressed':<12}")
    print("-" * 96)

    for idx, file_info in enumerate(files, start=1):
        name = file_info["file"]
        if len(name) > 58:
            name = f"{name[:55]}..."

        print(
            f"{idx:<6} {name:<60} "
            f"{file_info['data_size']:<12,d} {file_info['data_compressed_size']:<12,d}"
        )

        if args.limit and idx >= args.limit:
            remaining = len(files) - idx
            if remaining > 0:
                print(f"... {remaining} more files")
            break

    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    evp = LibEVP(lib_path=args.lib)
    result = evp.unpack(args.archive, args.output, create_dir=True)
    print(result["message"] or "Archive extracted successfully")
    return 0 if result["success"] else 1


def cmd_pack(args: argparse.Namespace) -> int:
    base_path = Path(args.base)
    if not base_path.exists():
        raise FileNotFoundError(f"Base directory does not exist: {base_path}")

    files = _collect_files(base_path, args.files)
    if not files:
        raise RuntimeError("No files matched the provided patterns")

    evp = LibEVP(lib_path=args.lib)
    result = evp.pack(str(base_path), files, args.output)
    print(result["message"] or "Archive created successfully")
    return 0 if result["success"] else 1


def cmd_info(args: argparse.Namespace) -> int:
    evp = LibEVP(lib_path=args.lib)
    files = evp.get_archive_files(args.archive)
    archive_size = Path(args.archive).stat().st_size

    total_uncompressed = sum(file_info["data_size"] for file_info in files)
    total_compressed = sum(file_info["data_compressed_size"] for file_info in files)

    print(f"Archive: {args.archive}")
    print(f"Archive size: {archive_size:,d} bytes")
    print(f"Files: {len(files)}")
    print(f"Total uncompressed: {total_uncompressed:,d} bytes")
    print(f"Total compressed: {total_compressed:,d} bytes")
    if total_uncompressed > 0:
        print(f"Compression ratio: {(100 * total_compressed / total_uncompressed):.2f}%")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pylibevp",
        description="Pack and unpack .evp archives",
    )
    parser.add_argument(
        "--lib",
        default=None,
        help="Path to native wrapper library (optional, can use PYLIBEVP_LIB_PATH)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List archive files")
    list_parser.add_argument("archive", help=".evp file path")
    list_parser.add_argument("-l", "--limit", type=int, default=None, help="Limit output rows")
    list_parser.set_defaults(func=cmd_list)

    extract_parser = subparsers.add_parser("extract", help="Extract .evp archive")
    extract_parser.add_argument("archive", help=".evp file path")
    extract_parser.add_argument("-o", "--output", required=True, help="Output directory")
    extract_parser.set_defaults(func=cmd_extract)

    pack_parser = subparsers.add_parser("pack", help="Create .evp archive")
    pack_parser.add_argument("-b", "--base", required=True, help="Base directory")
    pack_parser.add_argument(
        "-f",
        "--files",
        nargs="+",
        default=["*"],
        help="Glob patterns to include, default=*",
    )
    pack_parser.add_argument("-o", "--output", required=True, help="Output .evp file")
    pack_parser.set_defaults(func=cmd_pack)

    info_parser = subparsers.add_parser("info", help="Show archive stats")
    info_parser.add_argument("archive", help=".evp file path")
    info_parser.set_defaults(func=cmd_info)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
