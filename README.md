# Harvest Moon: A Wonderful Life – Special Edition (PS2)

> **Status: paused before the title screen.**
>
> This repository contains the local analysis/recompilation workflow, scripts, dependency snapshots, and documented runtime evidence. The game ISO, extracted disc data, generated build output, save cards, and other local artifacts are intentionally excluded from Git.

## Scope and distribution boundary

This is a technical research/recompilation project based on a user-owned copy of the game. Do not commit or distribute the ISO, boot ELF, extracted game assets, generated disc contents, or other copyrighted game data. Keep those files local and use the ignore rules in this repository.

## Toolchain

- Target: PS2 North American build, boot ELF `SLUS_211.71`, serial `SLUS-21171`
- Recompiler: `vendor/PS2Recomp`
- Decompiler/database tool: `vendor/decompdecomp`
- Python: 3.12 in `.venv`
- Ghidra: installed by the pinned decompdecomp toolchain
- Detected original compiler: CodeWarrior PS2 / `MWCPS2-3`
- Native build tools: CMake, Ninja, LLVM/clang-cl, and Visual Studio Build Tools where available

## Current workflow

The local workflow is:

1. Read the user-owned ISO and extract `SYSTEM.CNF`, the boot ELF, and required modules.
2. Inspect the ELF metadata and identify its sections, entry point, compiler, and symbols.
3. Build the PS2Recomp analyzer/recompiler tools.
4. Run PS2Recomp analysis and generate the TOML configuration.
5. Import the ISO into a local decompdecomp database.
6. Build the generated runtime and run the real boot path with local CDVD/IOP/GS/VU support.
7. Use runtime traces and screenshots to locate the first game-specific incompatibility.

The main pipeline commands are:

```powershell
.venv\Scripts\python.exe tools\ps2_pipeline.py extract
.venv\Scripts\python.exe tools\ps2_pipeline.py elf-info artifacts\disc\SLUS_211.71 --out artifacts\disc\elf_info.json
.venv\Scripts\python.exe tools\ps2_pipeline.py build-tools
.venv\Scripts\python.exe tools\ps2_pipeline.py analyze artifacts\disc\SLUS_211.71 --out artifacts\ps2recomp.toml
.venv\Scripts\python.exe tools\ps2_pipeline.py import-decomp --workspace artifacts\decomp
```

`extract` does not copy the full 1.2 GB ISO. Large disc data remains local and is accessed by the local tooling. The decompdecomp database and split output are also local generated state.

## Verified progress

The latest verified local state is:

| Area | Result |
| --- | --- |
| ISO size | `1,277,591,552` bytes |
| ISO SHA-1 | `d477865863cf3d94c8b3cd2683efb4dacfdb9b2d` |
| Boot ELF | `artifacts/full_disc/SLUS_211.71` |
| ELF size | `7,722,908` bytes |
| ELF SHA-1 | `dbb2458314ebcd7bd270627c57d6ab17d9dfac61` |
| decompdecomp database | about `21,351` functions in `artifacts/decomp/app.db` |
| PS2Recomp analysis | about `13,189` functions across `7` sections |
| Generated C++ | about `13,211` functions |
| Runtime | starts the EE/IOP/GS/VU1 boot path |
| Title screen | **not reached** |

The title assets have been identified in local `DATA0000.AFS` data, including `title.tex`, `title-scee.tex`, `title.ani`, `title-scee.ani`, `title_logo.pig`, `title_logo2.pig`, and `SNGTITLE.adx`. Those files remain ignored and local.

## Current blocker

The runtime stops in the asynchronous resource loader before the console/title scene is created. The resource object at guest address `0x49DA78` repeatedly reports status byte `0x2` (busy):

```text
[resource-status-get] pc=0x1196f8 object=0x49da78 b1=0x2 ...
[resource-wait] object=0x49da78 status=0x2
[resource-loop] pc=0x17a868 ra=0x17a868 a0=0x49da78 ...
```

The IOP side is active: DVCI functions `0x400` and `0x422` execute, and the EE callback at `0x1303E0` is invoked. The observed callback result does not cause the resource object to transition to a completed state. The current working hypothesis is an incomplete game-specific resource completion path between the EE resource manager, IOP RPC/DVCI, and the callback/queue state.

The first VIF activity only uploads VU1 microcode. No later `MSCAL`/`DIRECT` render packet reaches the title scene, so GS rasterization is not the first confirmed blocker.

## Runtime evidence

- Latest diagnostic executable: `build/PS2ClangNinja/ps2xRuntime/ps2EntryRunner_resourcestatus2.exe`
- Resource trace: `artifacts/resourcestatus2.log`
- IOP/callback trace: `artifacts/resourcestatus2.err`
- Host-window screenshot: `artifacts/runtime_surface_45s.png`
- Public, sanitized excerpts: `docs/evidence/`
- Community issue draft and evidence checklist: [`docs/COMMUNITY_HELP.md`](docs/COMMUNITY_HELP.md)

The screenshot proves that the runner window opens, but its render area is black. It is not evidence of a working title screen.

## Repository layout

```text
README.md
.recomp.json
tools/                  Reproducibility scripts only
docs/                   Public status and community issue material
vendor/                 PS2Recomp and decompdecomp source snapshots
artifacts/              Local ISO/decomp/runtime output; ignored
build/                  Local native build output; ignored
```

## Resuming the investigation

The next investigation should focus on the resource completion callback and queue semantics. Do not treat a status bypass as a solution: previous bypass experiments only moved execution to another resource loop and did not produce the title screen.

A local diagnostic run can be resumed with:

```powershell
powershell.exe -NoProfile -Command "$p=Start-Process -FilePath 'build\PS2ClangNinja\ps2xRuntime\ps2EntryRunner_resourcestatus2.exe' -ArgumentList 'artifacts\full_disc\SLUS_211.71' -WorkingDirectory 'artifacts\full_disc' -PassThru; $p.WaitForExit()"
```

Do not claim title-screen progress without a new screenshot that visibly shows the game title.

## Build notes

PS2Recomp requires C++20 and the Windows SDK. The helper script prefers Visual Studio Build Tools and falls back to LLVM/Ninja. PS2Recomp and decompdecomp are still beta for PS2 projects; generated C/C++ is not automatically a native, bootable port.
