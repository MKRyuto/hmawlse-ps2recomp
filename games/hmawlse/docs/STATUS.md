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

## Parallel investigation while awaiting community feedback

Feedback is useful but is not the only workstream. A clean local run without the status-2 bypass already narrows the failure:

- The generated getter at guest `0x1196F8` reads only byte `object+1`; it does not write the resource state.
- The consumer at `0x17A750` accepts status `0x3` as complete. Status `0x2` returns to the polling path, so treating `0x2` as complete would be an experiment, not a faithful fix.
- The IOP path executes DVCI `0x400`, invokes the guest callback, and returns a buffer. That proves dispatch reaches the callback; it does not prove that the callback updates `0x49DA78+1`.
- Static control-flow now shows `0x17A560 -> 0x11AD00 -> 0x132190` registering callback target `0x17A5C0` in queue table `0x5DC770`. The registered `0x17A5C0` handler only adjusts/restores the stack and returns; this is a lead, not proof that it is the missing status writer.
- `0x132150` and `0x132190` are separate entry points sharing generated file `sub_001320F8_0x1320f8.cpp`; the runtime function table maps both entries, so this is not currently explained by a missing entry-point dispatch.

- The clean no-bypass run remains in the `0x17A868`/`0x17A87C` polling path while the host surface stays black. This is the baseline for further traces.

The next local experiment is to identify the exact writer of `object+1` and correlate it with the callback/queue path. No new bypass will be published as a fix.

## Evidence

- [`resource_status_excerpt.log`](evidence/resource_status_excerpt.log)
- [`iop_callback_excerpt.err`](evidence/iop_callback_excerpt.err)
- Local-only screenshot: `artifacts/runtime_surface_45s.png`
- Community post draft: [`COMMUNITY_HELP.md`](COMMUNITY_HELP.md)

## Next investigation

When unpaused, trace the completion message from the IOP result through the EE callback and resource queue. Do not treat a status bypass as a final fix unless a fresh screenshot proves the title screen.
