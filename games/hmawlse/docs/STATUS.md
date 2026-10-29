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

Feedback is useful but is not the only workstream. Clean local runs without the
status-2 bypass now narrow the failure to the resource completion data path:

- The generated getter at guest `0x1196F8` reads only byte `object+1`; it does
  not write the resource state.
- The consumer at `0x17A750` accepts status `0x3` as complete. Status `0x2`
  returns to the polling path, so treating `0x2` as complete would be an
  experiment, not a faithful fix.
- The target resource object `0x49DA78` is written to status `0x1` at
  `0x1189B8` and status `0x2` at `0x118EEC`. The status-3 branch at
  `0x118EB4` is not taken because the load still has remaining work.
- On the resume path, `0x119370` calls completion helper `0x11FDA0` with
  source object `0x4AC0C8`. The helper reads source `+0x8 = 0x5D9CA0` and
  source `+0x58 = 0`, then returns `0`; the resource status is set back to
  `0x1`.
- Source initialization at `0x11F8E8` and slot allocation at `0x11FAC0` were
  reached for `0x4AC0C8` with zero callback/data arguments. The observed
  source `+0x58` writes are only `0` from `0x11FD84`; no completion value was
  observed.
- The IOP path executes DVCI `0x400`/`0x422`, invokes EE callback `0x1303E0`,
  and returns buffers. The callback dispatches queue table `0x5DC770` to
  handler `0x17A5C0`, whose generated body only adjusts/restores the stack and
  returns. This proves dispatch reaches the callback; it does not prove that
  the callback updates the target resource.
- The work queue at `0x5DC760` invokes `0x11A008` with argument `0`; it is a
  separate maintenance queue, not the target completion transition.
- `0x132150` and `0x132190` are separate entry points sharing generated file
  `sub_001320F8_0x1320f8.cpp`; the runtime function table maps both entries,
  so this is not currently explained by a missing entry-point dispatch.

- A targeted SIF `writeEeRange` hook was attempted, but the existing generated
  build invalidated its PCH and began rebuilding thousands of generated objects;
  the hook was reverted and produced no runtime evidence.
- Static review found a second concrete IOP-to-EE path in
  `ps2xIOP/src/emulator/services/iop_rpc.cpp`: the RPC receive path copies
  `returnPointer` bytes to `request.receive.address` through
  `m_host.writeGuest`. No current trace records that destination, so this is
  the next targeted instrumentation point; it may explain the source-field
  update without changing game semantics.

## Evidence

- [`resource_status_excerpt.log`](evidence/resource_status_excerpt.log)
- [`iop_callback_excerpt.err`](evidence/iop_callback_excerpt.err)
- Local-only screenshot: `artifacts/runtime_surface_45s.png`
- Community post draft: [`COMMUNITY_HELP.md`](COMMUNITY_HELP.md)

## Next investigation

When unpaused, trace the completion message from the IOP result through the EE callback and resource queue. Do not treat a status bypass as a final fix unless a fresh screenshot proves the title screen.
