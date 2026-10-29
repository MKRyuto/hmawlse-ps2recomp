# Contributing

## Scope

Contributions should improve the reproducible analysis or runtime path for `SLUS_211.71`. Keep game-specific work under `games/hmawlse/` when it can be isolated there. Change shared `ps2x*` modules only when the behavior is reusable or the game-specific boundary is documented.

## Data boundary

Use a legally owned local copy of the game. Never commit or request the ISO, ELF, extracted disc files, generated game translation, memory dumps, save cards, or full runtime logs.

## Reports

A useful issue includes:

1. Host and tool versions.
2. Exact ELF identity and region.
3. The command or script used.
4. A short sanitized log excerpt.
5. A screenshot for visible runtime claims.
6. The expected result and the first observed failure.

Use [`games/hmawlse/docs/COMMUNITY_HELP.md`](games/hmawlse/docs/COMMUNITY_HELP.md) as the evidence template.

## Changes

- Keep generated output under ignored local paths.
- Keep Ghidra projects and decompdecomp databases local.
- Add a focused test or a reproducible command for runtime behavior changes when possible.
- Preserve upstream license and notice files.
- Do not call a run playable or title-complete without a fresh visual proof.
