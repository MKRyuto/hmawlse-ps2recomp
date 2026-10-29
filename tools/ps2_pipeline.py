#!/usr/bin/env python3
"""Reproducible PS2 ISO -> ELF -> analysis pipeline for Harvest Moon AWL SE.

The ISO is never modified.  The script extracts only the boot program and small
metadata by default; large game data remains in the user's ISO and is referenced
by the manifest.  PS2Recomp and decompdecomp are invoked when their tools are
available, but the ISO/ELF inspection itself has no third-party dependency.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ISO = ROOT / "Harvest Moon - A Wonderful Life - Special Edition.iso"
ARTIFACTS = ROOT / "artifacts"
SECTOR = 2048


@dataclass(frozen=True)
class IsoEntry:
    path: str
    extent: int
    size: int
    directory: bool


class Iso9660:
    def __init__(self, path: Path):
        self.path = path
        self.file = path.open("rb")
        self.file.seek(16 * SECTOR)
        pvd = self.file.read(SECTOR)
        if len(pvd) != SECTOR or pvd[:7] != b"\x01CD001\x01":
            self.close()
            raise ValueError(f"{path} is not a 2048-byte-sector ISO9660 image")
        record_len = pvd[156]
        root = pvd[156 : 156 + record_len]
        if len(root) < 34:
            self.close()
            raise ValueError("ISO9660 primary volume descriptor has no root record")
        self.root = IsoEntry("", u32le(root, 2), u32le(root, 10), bool(root[25] & 2))

    def close(self) -> None:
        if getattr(self, "file", None) and not self.file.closed:
            self.file.close()

    def __enter__(self) -> "Iso9660":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def read(self, extent: int, size: int) -> bytes:
        self.file.seek(extent * SECTOR)
        return self.file.read(size)

    def entries(self) -> list[IsoEntry]:
        found: list[IsoEntry] = []

        def walk(parent: IsoEntry) -> None:
            data = self.read(parent.extent, parent.size)
            offset = 0
            while offset < len(data):
                length = data[offset]
                if not length:
                    offset = ((offset // SECTOR) + 1) * SECTOR
                    continue
                record = data[offset : offset + length]
                if len(record) < 34:
                    break
                name_len = record[32]
                raw_name = record[33 : 33 + name_len]
                if raw_name not in (b"\x00", b"\x01"):
                    name = raw_name.decode("ascii", "replace")
                    if ";" in name:
                        name = name.split(";", 1)[0]
                    path = f"{parent.path}/{name}" if parent.path else name
                    entry = IsoEntry(path, u32le(record, 2), u32le(record, 10), bool(record[25] & 2))
                    found.append(entry)
                    if entry.directory:
                        walk(entry)
                offset += length

        walk(self.root)
        return found

    def find(self, path: str) -> IsoEntry:
        wanted = path.replace("\\", "/").strip("/").upper()
        for entry in self.entries():
            if entry.path.upper() == wanted:
                return entry
        raise FileNotFoundError(f"ISO entry not found: {path}")

    def read_entry(self, entry: IsoEntry) -> bytes:
        if entry.directory:
            raise IsADirectoryError(entry.path)
        return self.read(entry.extent, entry.size)


def u32le(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def sha1(data: bytes | Path) -> str:
    digest = hashlib.sha1()
    if isinstance(data, Path):
        with data.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    else:
        digest.update(data)
    return digest.hexdigest()


def parse_boot_name(system_cnf: bytes) -> str:
    match = re.search(rb"BOOT2\s*=\s*cdrom0?:?\\*([^\s;]+)", system_cnf, re.I)
    if not match:
        raise ValueError("SYSTEM.CNF has no BOOT2 entry")
    return match.group(1).decode("ascii", "replace").replace("\\", "/").rsplit("/", 1)[-1]


def json_dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def extract(iso_path: Path, out_dir: Path, extract_all: bool = False) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    with Iso9660(iso_path) as iso:
        all_entries = iso.entries()
        system_entry = iso.find("SYSTEM.CNF")
        system = iso.read_entry(system_entry)
        boot_name = parse_boot_name(system)
        boot_entry = iso.find(boot_name)
        boot = iso.read_entry(boot_entry)

        (out_dir / "SYSTEM.CNF").write_bytes(system)
        elf_path = out_dir / boot_name
        elf_path.write_bytes(boot)

        selected = {"SYSTEM.CNF", boot_name.upper()}
        for entry in all_entries:
            if entry.path.upper() in {"MODULES", "MODULES/"} or entry.path.upper().startswith("MODULES/"):
                selected.add(entry.path.upper())
        if extract_all:
            selected = {entry.path.upper() for entry in all_entries if not entry.directory}
        copied: list[str] = []
        for entry in all_entries:
            if entry.directory or entry.path.upper() not in selected:
                continue
            destination = out_dir / Path(entry.path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(iso.read_entry(entry))
            copied.append(entry.path)

        manifest = {
            "iso": {
                "path": str(iso_path),
                "size": iso_path.stat().st_size,
                "sha1": sha1(iso_path),
                "sector_size": SECTOR,
            },
            "system_cnf": system.decode("ascii", "replace"),
            "boot": boot_name,
            "boot_entry": {"path": boot_entry.path, "extent": boot_entry.extent, "size": boot_entry.size},
            "files": [
                {"path": e.path, "extent": e.extent, "size": e.size, "directory": e.directory}
                for e in all_entries
            ],
            "extracted": copied,
        }
    json_dump(out_dir / "disc_manifest.json", manifest)
    print(f"ISO SHA-1: {manifest['iso']['sha1']}")
    print(f"Boot: {boot_name} ({len(boot):,} bytes)")
    print(f"ISO entries: {len(all_entries)}; extracted: {len(copied)}")
    return manifest


def elf_info(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 52 or data[:4] != b"\x7fELF":
        raise ValueError(f"{path} is not an ELF")
    ident = data[:16]
    if ident[4] != 1 or ident[5] != 1:
        raise ValueError("expected ELF32 little-endian")
    header = struct.unpack_from("<16sHHIIIIIHHHHHH", data, 0)
    _, e_type, e_machine, e_version, entry, phoff, shoff, flags, ehsize, phentsize, phnum, shentsize, shnum, shstrndx = header
    if e_machine != 8:
        raise ValueError(f"expected MIPS ELF (machine 8), got {e_machine}")

    segments: list[dict] = []
    for i in range(phnum):
        at = phoff + i * phentsize
        if at + 32 > len(data):
            break
        p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = struct.unpack_from("<IIIIIIII", data, at)
        if p_type == 1:
            segments.append({"offset": p_offset, "vaddr": p_vaddr, "paddr": p_paddr, "filesz": p_filesz,
                             "memsz": p_memsz, "flags": p_flags, "align": p_align})

    sections: list[dict] = []
    raw_sections: list[tuple[int, int, int, int, int, int, int, int, int, int]] = []
    for i in range(shnum):
        at = shoff + i * shentsize
        if at + 40 > len(data):
            break
        section = struct.unpack_from("<IIIIIIIIII", data, at)
        raw_sections.append(section)
    names = b""
    if 0 <= shstrndx < len(raw_sections):
        s = raw_sections[shstrndx]
        names = data[s[4] : s[4] + s[5]]
    for section in raw_sections:
        name_at, kind, flags, addr, offset, size, link, info, align, entsize = section
        end = names.find(b"\x00", name_at)
        name = names[name_at:end if end >= 0 else len(names)].decode("ascii", "replace") if name_at < len(names) else ""
        sections.append({"name": name, "type": kind, "flags": flags, "addr": addr, "offset": offset,
                         "size": size, "link": link, "info": info, "align": align, "entsize": entsize})

    executable = [s for s in segments if s["flags"] & 1]
    code = b"".join(data[s["offset"] : s["offset"] + s["filesz"]] for s in executable)
    words = [u32le(code, i) for i in range(0, len(code) - 3, 4)]
    metrics = {
        "executable_bytes": len(code),
        "mips_words": len(words),
        "jal_like": sum(1 for w in words if (w >> 26) == 3),
        "syscall": sum(1 for w in words if (w & 0x3F) == 0x0C),
        "jr_ra": sum(1 for w in words if w == 0x03E00008),
        "cop2": sum(1 for w in words if (w >> 26) == 0x12),
    }
    comments = []
    for section in sections:
        if section["name"] == ".comment":
            comments.append(data[section["offset"] : section["offset"] + section["size"]].decode("latin1", "replace"))
    result = {
        "path": str(path), "size": len(data), "sha1": sha1(data), "entry": entry,
        "entry_hex": f"0x{entry:08X}", "type": e_type, "machine": e_machine, "flags": flags,
        "program_headers": segments, "sections": sections, "comments": comments,
        "metrics": metrics,
    }
    print(json.dumps({k: result[k] for k in ("path", "size", "sha1", "entry_hex", "metrics", "comments")}, indent=2))
    return result


def locate_tool(name: str) -> Path | None:
    candidates = [
        ROOT / "build" / "PS2Recomp" / name,
        ROOT / "build" / "PS2Recomp" / "Release" / name,
        ROOT / "build" / "PS2Recomp" / "ps2xAnalyzer" / "Release" / name,
        ROOT / "build" / "PS2Recomp" / "ps2xRecomp" / "Release" / name,
        ROOT / "build" / "ps2recomp" / name,
        ROOT / "build" / "ps2recomp" / "Release" / name,
    ]
    suffixes = ["", ".exe"]
    for candidate in candidates:
        for suffix in suffixes:
            path = candidate if not suffix else candidate.with_name(candidate.name + suffix)
            if path.is_file():
                return path
    return None


def run_tool(tool: Path, args: list[str]) -> int:
    print("$", tool, *args)
    return subprocess.run([str(tool), *args], cwd=ROOT, check=False).returncode


def analyze(elf_path: Path, output: Path) -> int:
    analyzer = locate_tool("ps2_analyzer")
    if analyzer is None:
        print("ps2_analyzer belum dibuild; jalankan: python tools/ps2_pipeline.py build-tools", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    return run_tool(analyzer, [str(elf_path), str(output)])


def recompile(config: Path) -> int:
    recompiler = locate_tool("ps2_recomp")
    if recompiler is None:
        print("ps2_recomp belum dibuild; jalankan: python tools/ps2_pipeline.py build-tools", file=sys.stderr)
        return 2
    return run_tool(recompiler, [str(config)])


def import_decomp(iso_path: Path, workspace: Path, toolchain: str) -> int:
    try:
        from decompnet.app.engine import RomNetwork
    except ImportError as error:
        print(f"decompdecomp belum terpasang di interpreter ini: {error}", file=sys.stderr)
        return 2
    workspace.mkdir(parents=True, exist_ok=True)
    network = RomNetwork(workspace / "app.db", workspace)
    slug = network.import_rom(
        iso_path,
        toolchain=toolchain,
        confirmed=True,
        name=iso_path.name,
        log=print,
    )
    print(f"decompdecomp project: {workspace / slug}")
    return 0


def build_tools() -> int:
    build = ROOT / "build" / "PS2Recomp"
    source = ROOT
    build.mkdir(parents=True, exist_ok=True)
    visual_studio = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools")
    if visual_studio.is_dir():
        configure = [
            "cmake", "-S", str(source), "-B", str(build), "-G", "Visual Studio 17 2022", "-A", "x64",
        ]
    else:
        configure = ["cmake", "-S", str(source), "-B", str(build), "-G", "Ninja"]
        llvm = Path(r"C:\Program Files\LLVM\bin")
        if (llvm / "clang.exe").is_file() and (llvm / "clang++.exe").is_file():
            configure.extend([
                f"-DCMAKE_C_COMPILER={llvm / 'clang.exe'}",
                f"-DCMAKE_CXX_COMPILER={llvm / 'clang++.exe'}",
            ])
    configure.extend([
        "-DPS2X_BUILD_RUNTIME=OFF", "-DPS2X_BUILD_TEST=OFF", "-DPS2X_BUILD_STUDIO=OFF",
        "-DPS2X_BUILD_ANALYZER=ON", "-DPS2X_BUILD_RECOMP=ON", "-DCMAKE_BUILD_TYPE=Release",
    ])
    print("$", *configure)
    result = subprocess.run(configure, cwd=ROOT, check=False)
    if result.returncode:
        return result.returncode
    return subprocess.run(
        ["cmake", "--build", str(build), "--config", "Release", "--parallel"],
        cwd=ROOT, check=False,
    ).returncode


def prepare(args: argparse.Namespace) -> int:
    manifest = extract(args.iso, args.out, args.extract_all)
    elf = args.out / manifest["boot"]
    info = elf_info(elf)
    json_dump(args.out / "elf_info.json", info)
    config = args.out / "ps2recomp.toml"
    code = analyze(elf, config)
    if code == 0:
        print(f"PS2Recomp config: {config}")
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", type=Path, default=DEFAULT_ISO)
    sub = parser.add_subparsers(dest="command", required=True)
    p_extract = sub.add_parser("extract", help="extract SYSTEM.CNF, BOOT ELF, and MODULES")
    p_extract.add_argument("--out", type=Path, default=ARTIFACTS / "disc")
    p_extract.add_argument("--all", dest="extract_all", action="store_true")
    p_elf = sub.add_parser("elf-info", help="inspect a PS2 ELF")
    p_elf.add_argument("elf", type=Path)
    p_elf.add_argument("--out", type=Path)
    p_analyze = sub.add_parser("analyze", help="run PS2Recomp's native analyzer")
    p_analyze.add_argument("elf", type=Path)
    p_analyze.add_argument("--out", type=Path, default=ARTIFACTS / "ps2recomp.toml")
    p_recomp = sub.add_parser("recompile", help="run PS2Recomp on a TOML config")
    p_recomp.add_argument("config", type=Path)
    p_import = sub.add_parser("import-decomp", help="import the ISO into decompdecomp")
    p_import.add_argument("--workspace", type=Path, default=ARTIFACTS / "decomp")
    p_import.add_argument("--toolchain", default="mwcps2-3.0.1")
    sub.add_parser("build-tools", help="configure and build PS2Recomp analyzer/recompiler")
    p_prepare = sub.add_parser("prepare", help="extract, inspect, and analyze the game")
    p_prepare.add_argument("--out", type=Path, default=ARTIFACTS / "disc")
    p_prepare.add_argument("--all", dest="extract_all", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "extract":
        extract(args.iso, args.out, args.extract_all)
        return 0
    if args.command == "elf-info":
        info = elf_info(args.elf)
        if args.out:
            json_dump(args.out, info)
        return 0
    if args.command == "analyze":
        return analyze(args.elf, args.out)
    if args.command == "recompile":
        return recompile(args.config)
    if args.command == "import-decomp":
        return import_decomp(args.iso, args.workspace, args.toolchain)
    if args.command == "build-tools":
        return build_tools()
    if args.command == "prepare":
        return prepare(args)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
