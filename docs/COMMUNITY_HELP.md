# Community Help Request

## Project

This is a PS2Recomp/decompdecomp investigation for the North American PS2 release of **Harvest Moon: A Wonderful Life – Special Edition**.

- Boot ELF: `SLUS_211.71`
- Serial: `SLUS-21171`
- PS2Recomp source: `vendor/PS2Recomp`
- decompdecomp source: `vendor/decompdecomp`
- Host: Windows x64
- Runtime: PS2Recomp-generated C++ runner with local HLE/runtime instrumentation

The ISO and all extracted game data are user-owned and must remain private. No ISO, ELF, AFS, TEX, PIG, ANI, ADX, or generated disc data is attached to this request.

## Current workflow

1. Extract `SYSTEM.CNF`, the boot ELF, and local modules from the user-owned ISO.
2. Inspect and analyze `SLUS_211.71` with PS2Recomp.
3. Import the ISO into a local decompdecomp database.
4. Build the generated runtime and start the actual EE/IOP boot path.
5. Trace CDVD, DVCI/RPC, resource queues, callbacks, VIF, and GS until the first game-specific stall.

The ELF analyzes and builds far enough to start the runtime. The runner initializes EE/IOP threads, memory-card setup, CDVD search, RPC/DVCI, GS, and initial VU1 upload.

## Verified failure

The title scene is not reached. The resource object at guest address `0x49DA78` remains busy:

```text
[resource-status-get] pc=0x1196f8 object=0x49da78 b1=0x2 w4=0x4ac0c8 ...
[resource-wait] object=0x49da78 status=0x2
[resource-status-get] pc=0x1196f8 object=0x49da78 b1=0x2 w0c=0x2fc62 ...
[resource-loop] pc=0x17a868 ra=0x17a868 a0=0x49da78 ...
```

The same object is polled repeatedly and does not transition to a completed state. The full sanitized excerpt is in [`evidence/resource_status_excerpt.log`](evidence/resource_status_excerpt.log).

The IOP trace shows repeated DVCI calls and EE callbacks:

```text
[ps2xIOP] [IOP DVCI] fn=0x400 ...
[ps2xIOP] [IOP DVCI] fn=0x422 ...
[ps2xIOP] [IOP direct-callback] fn=0x1246176
[ps2xIOP] [EE callback] address=0x1303e0 ...
[ps2xIOP] [EE callback-result] pc=0x0 steps=7 v0=0x5dc770 gp=0x0
```

The full sanitized callback excerpt is in [`evidence/iop_callback_excerpt.err`](evidence/iop_callback_excerpt.err).

The first VIF packet only uploads VU1 microcode. No later `MSCAL` or `DIRECT` packet reaches the title scene. The host window opens, but the render surface remains black; the screenshot is evidence of the stall, not a title-screen success:

`artifacts/runtime_surface_45s.png` (local only)

## Questions for PS2Recomp / PS2Dev maintainers

1. Does PS2Recomp currently model this kind of asynchronous EE/IOP resource completion, or does this game require a game-specific HLE implementation?
2. For DVCI functions `0x400` and `0x422`, what callback, semaphore, interrupt, or queue transition is expected to mark the EE resource object complete?
3. Is a callback that executes successfully with `gp=0` expected to preserve or restore a game-specific GP/context before it updates the resource object?
4. Are there known PS2 games using the same resource-manager pattern, with a working PS2Recomp or HLE implementation we can compare against?
5. What is the recommended trace point for proving the original IOP completion message and its destination object?

## Evidence request

If you have reproduced this resource path, please provide evidence rather than only a general diagnosis:

- A screenshot showing the corresponding boot/title stage in a working run.
- A short runtime log around the resource allocation, DVCI request, completion callback, and status transition.
- The relevant PS2Recomp commit or patch.
- If possible, the expected before/after values for the resource object status and callback arguments.

Please do not request or upload the ISO or extracted copyrighted assets. Logs and screenshots should be sanitized of local absolute paths and personal usernames.

## Local evidence files

The local run produced:

- `artifacts/resourcestatus2.log`
- `artifacts/resourcestatus2.err`
- `artifacts/runtime_surface_45s.png`
- `build/PS2ClangNinja/ps2xRuntime/ps2EntryRunner_resourcestatus2.exe`

Only the small text excerpts under `docs/evidence/` are intended for public issue discussion. The full logs and executable remain ignored/local.
