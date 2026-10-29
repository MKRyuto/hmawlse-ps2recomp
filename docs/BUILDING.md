# Building

## Requirements

- Windows x64 for the currently verified host path.
- Python 3.12 and the repository `.venv`.
- CMake 3.20 or newer.
- C++20 compiler and Windows SDK.
- Ninja or Visual Studio Build Tools.
- Ghidra for the preferred retail/stripped ELF function export.
- decompdecomp installed separately according to its upstream documentation.

The repository does not contain the ISO, extracted ELF, generated C++, or decompdecomp database. Supply your own game copy locally.

## Local setup

Clone the single repository normally:

```powershell
git clone https://github.com/MKRyuto/hmawlse-ps2recomp.git
cd hmawlse-ps2recomp
```

Create or reuse the local Python environment, then make sure the installed interpreter can import `decompnet` before running `import-decomp`.

## Extract and inspect

```powershell
.venv\Scripts\python.exe tools\ps2_pipeline.py extract
.venv\Scripts\python.exe tools\ps2_pipeline.py elf-info artifacts\disc\SLUS_211.71 --out artifacts\disc\elf_info.json
```

The default ISO path is the user-owned file named:

```text
Harvest Moon - A Wonderful Life - Special Edition.iso
```

Use `--iso` in the pipeline source when the local filename or location differs. The extractor reads the ISO and writes only local output under `artifacts/`.

## Analyze and import

```powershell
.venv\Scripts\python.exe tools\ps2_pipeline.py build-tools
.venv\Scripts\python.exe tools\ps2_pipeline.py analyze artifacts\disc\SLUS_211.71 --out artifacts\ps2recomp.toml
.venv\Scripts\python.exe tools\ps2_pipeline.py import-decomp --workspace artifacts\decomp
```

For retail/stripped analysis, use the Ghidra workflow in [`games/hmawlse/ghidra/SETUP.md`](../games/hmawlse/ghidra/SETUP.md) and keep exported maps local until they have been reviewed for proprietary data.

## Runtime investigation

The current diagnostic executable and logs are generated locally. The latest documented run used:

```text
build/PS2ClangNinja/ps2xRuntime/ps2EntryRunner_resourcestatus2.exe
artifacts/resourcestatus2.log
artifacts/resourcestatus2.err
```

The run reaches EE/IOP startup and resource loading but remains before the title scene. See [`games/hmawlse/docs/STATUS.md`](../games/hmawlse/docs/STATUS.md) before changing runtime behavior.

## Contribution rules

1. Keep the ISO, ELF, generated game C++, memory dumps, save cards, and full logs local.
2. Put game-specific analysis, scripts, hooks, and tests under `games/hmawlse/`.
3. Keep shared PS2Recomp/runtime changes in the root modules only when they are genuinely reusable.
4. Attach sanitized logs and screenshots to issues; do not attach copyrighted game data.
5. Record a fresh command, source commit, ELF identity, and visible result for runtime claims.
