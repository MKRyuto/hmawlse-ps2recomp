# Harvest Moon: A Wonderful Life – Special Edition (PS2)

> **Status: paused before the title screen.**

A game-specific PS2Recomp research project for the North American release of **Harvest Moon: A Wonderful Life – Special Edition** (`SLUS_211.71` / `SLUS-21171`). The repository follows the game-project layout used by active PS2 recompilation projects such as [MKSM Recomp](https://github.com/OGmidway/mksm-recomp): shared PS2Recomp modules live at the repository root, while game-specific notes and tooling live under `games/hmawlse/`.

This repository contains source, scripts, documentation, and sanitized evidence only. The user-owned ISO, ELF, extracted disc data, generated game translation, runtime dumps, save cards, and full logs remain local and are ignored by Git.

## Start here

- [Build and run](docs/BUILDING.md)
- [Game project notes](games/hmawlse/README.md)
- [Current status and blocker](games/hmawlse/docs/STATUS.md)
- [Ghidra setup](games/hmawlse/ghidra/SETUP.md)
- [Community help request](games/hmawlse/docs/COMMUNITY_HELP.md)
- [Publishing and licensing notes](docs/REPOSITORY_PUBLISHING.md)

## Toolchain

- [PS2Recomp](https://github.com/ran-j/PS2Recomp): root `ps2xAnalyzer`, `ps2xRecomp`, `ps2xRuntime`, `ps2xIOP`, and related modules
- [decompdecomp](https://github.com/n-delic/decompdecomp): installed externally and imported through the local Python environment
- Ghidra: local ELF analysis and PS2 function export
- Python 3.12: local pipeline and investigation scripts
- CMake, Ninja, LLVM/clang-cl, and Visual Studio Build Tools: native build
- Original compiler detected from the ELF: CodeWarrior PS2 / `MWCPS2-3`

## Workflow

```text
User-owned ISO
    ↓
Extract SYSTEM.CNF, boot ELF, and modules
    ↓
Inspect SLUS_211.71 in Ghidra
    ↓
Export function boundaries/maps for PS2Recomp
    ↓
Run PS2Recomp analysis or use the Ghidra export
    ↓
Import the ISO into a local decompdecomp project
    ↓
Generate/build local C++ runtime
    ↓
Run the EE/IOP/CDVD/GS/VU boot path
    ↓
Record reproducible logs and screenshots
```

The local pipeline is:

```powershell
.venv\Scripts\python.exe tools\ps2_pipeline.py extract
.venv\Scripts\python.exe tools\ps2_pipeline.py elf-info artifacts\disc\SLUS_211.71 --out artifacts\disc\elf_info.json
.venv\Scripts\python.exe tools\ps2_pipeline.py build-tools
.venv\Scripts\python.exe tools\ps2_pipeline.py analyze artifacts\disc\SLUS_211.71 --out artifacts\ps2recomp.toml
.venv\Scripts\python.exe tools\ps2_pipeline.py import-decomp --workspace artifacts\decomp
```

`extract` does not copy the complete ISO. Large disc data remains local. decompdecomp's database and generated split output also remain local.

## Verified progress

| Area | Result |
| --- | --- |
| ISO size | `1,277,591,552` bytes |
| ISO SHA-1 | `d477865863cf3d94c8b3cd2683efb4dacfdb9b2d` |
| Boot ELF | `artifacts/full_disc/SLUS_211.71` |
| ELF size | `7,722,908` bytes |
| ELF SHA-1 | `dbb2458314ebcd7bd270627c57d6ab17d9dfac61` |
| decompdecomp database | about `21,351` functions locally |
| PS2Recomp analysis | about `13,189` functions across `7` sections |
| Generated C++ | about `13,211` functions locally |
| EE/IOP runtime startup | verified |
| Title screen | **not reached** |

## Current blocker

The runtime stops in the asynchronous resource loader before the console/title scene is created. Resource object `0x49DA78` remains busy at status `0x2` while the resource loop continues:

```text
[resource-status-get] pc=0x1196f8 object=0x49da78 b1=0x2 ...
[resource-wait] object=0x49da78 status=0x2
[resource-loop] pc=0x17a868 ra=0x17a868 a0=0x49da78 ...
```

DVCI functions `0x400` and `0x422` execute, and the EE callback at `0x1303E0` runs, but the resource object does not transition to completion. The current working hypothesis is an incomplete game-specific resource completion path between the EE resource manager, IOP RPC/DVCI handling, and callback/queue state.

The first VIF activity only uploads VU1 microcode. No later `MSCAL` or `DIRECT` packet reaches the title scene, so GS rasterization is not the first confirmed blocker.

## Repository map

```text
CMakeLists.txt                 Root PS2Recomp build
ps2xAnalyzer/                  ELF/function analyzer
ps2xRecomp/                    MIPS-to-C++ generator and Ghidra exporter
ps2xRuntime/                   EE runtime, GS/VU, syscalls, and debugger
ps2xIOP/                      IOP/RPC services and HLE
ps2xTest/                     Shared runtime tests
ps2xStudio/                   Optional PS2Recomp tooling
android/ vita/                Upstream platform targets
games/hmawlse/                Harvest Moon-specific docs and Ghidra setup
tools/                        Reproducibility and ISO pipeline scripts
docs/                         Repository-level build/publishing notes
```

The game-specific project is under `games/hmawlse/`; generated game data remains local and ignored.

## What is not included

Do not commit or distribute:

```text
Harvest Moon - A Wonderful Life - Special Edition.iso
SLUS_211.71
DATA*.AFS / DATA*.DAT / DATA*.BIN
artifacts/
build/
mc0/ / mc1/
full runtime logs
memory dumps
compiled game executables
```

Use the sanitized excerpts under `games/hmawlse/docs/evidence/` for public issue discussion. Do not attach the ISO or extracted game assets to issues or pull requests.

## License and upstream source

The root runtime modules are based on PS2Recomp and retain the upstream license in [`LICENSE.PS2Recomp`](LICENSE.PS2Recomp). The game project is not affiliated with or endorsed by the copyright holder. External decompdecomp is a local tool dependency, not a vendored game asset or a required copy in this repository.
