# Current Status

## Verified

- ISO and boot ELF extraction work locally.
- Ghidra, decompdecomp, and PS2Recomp are part of the analysis workflow.
- PS2Recomp generated C++ and a Windows runtime builds locally.
- EE/IOP startup, memory-card setup, CDVD search, DVCI/RPC activity, GS initialization, and initial VU1 upload are observed.
- Title assets were identified locally in `DATA0000.AFS`.

## Not verified

The title screen has not been reached. The latest host screenshot is a black runtime surface, not a successful title-screen boot.

## Current blocker

The asynchronous resource loader repeatedly polls guest object `0x49DA78` with status `0x2`:

```text
[resource-status-get] pc=0x1196f8 object=0x49da78 b1=0x2 ...
[resource-wait] object=0x49da78 status=0x2
[resource-loop] pc=0x17a868 ra=0x17a868 a0=0x49da78 ...
```

DVCI functions `0x400` and `0x422` execute and the EE callback at `0x1303E0` runs, but no completion transition is observed for the resource object. The working hypothesis is a missing or incorrect game-specific completion path between EE resource state, IOP RPC/DVCI, and the callback/queue.

VIF has not reached later title rendering packets. The first observed VIF activity only uploads VU1 microcode, so GS work is not the first confirmed blocker.

## Evidence

- [`resource_status_excerpt.log`](evidence/resource_status_excerpt.log)
- [`iop_callback_excerpt.err`](evidence/iop_callback_excerpt.err)
- Local-only screenshot: `artifacts/runtime_surface_45s.png`
- Community post draft: [`COMMUNITY_HELP.md`](COMMUNITY_HELP.md)

## Next investigation

When unpaused, trace the completion message from the IOP result through the EE callback and resource queue. Do not treat a status bypass as a final fix unless a fresh screenshot proves the title screen.
