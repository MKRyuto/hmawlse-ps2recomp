# Ghidra Setup

Ghidra is used to inspect the retail PS2 ELF, recover function boundaries, and export maps for PS2Recomp. It is an analysis tool; it does not by itself produce a complete native port.

## Input

Use the locally extracted boot ELF:

```text
artifacts/full_disc/SLUS_211.71
```

Do not commit the ELF or a Ghidra project database.

## Export workflow

1. Create or open a local Ghidra project.
2. Import `SLUS_211.71` as the PS2 MIPS/Emotion Engine ELF.
3. Apply the PS2/Emotion Engine processor and review the image base and entry point.
4. Run PS2Recomp's exporter:

```text
ps2xRecomp/tools/ghidra/ExportPS2Functions.java
```

5. Keep the generated CSV/TOML maps under `artifacts/` unless a reviewed, game-specific metadata file is intentionally added here.
6. Feed the reviewed local export to PS2Recomp and compare the generated runtime from a clean boot.

## Current investigation addresses

These guest addresses are used in the current resource-loader trace:

```text
0x1196F8  resource status getter
0x17A750  resource loop entry
0x17A868  resource wait/poll loop
0x1303E0  EE callback
```

Addresses are specific to this exact ELF build and are not portable to another region or revision.

## Public evidence

If a Ghidra screenshot is shared in an issue, show only the relevant disassembly/decompiler view. Remove local usernames and paths. Do not share the ISO, ELF, project database, or extracted game assets.
