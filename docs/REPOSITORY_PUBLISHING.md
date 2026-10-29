# Publishing Notes

This repository follows the game-project layout used by active PS2 recompilation/decompilation projects:

```text
CMakeLists.txt
ps2xAnalyzer/ ps2xRecomp/ ps2xRuntime/ ps2xIOP/ ps2xTest/
games/hmawlse/
tools/
docs/
```

PS2Recomp modules are part of this repository because this project carries runtime and analyzer changes. Game-specific material belongs under `games/hmawlse/`. decompdecomp is installed externally and is not copied into this repository.

The repository contains no game data. Do not commit the ISO, boot ELF, extracted disc files, generated game translation, memory dumps, save cards, full runtime logs, or generated executables. The local `.gitignore` protects the known paths, but review `git status` before every commit.

Keep upstream PS2Recomp license and notice files intact. The root runtime is based on [PS2Recomp](https://github.com/ran-j/PS2Recomp), while the game-specific project is not affiliated with or endorsed by the game copyright holder.

Public issue material belongs under `games/hmawlse/docs/`, with only sanitized excerpts under `games/hmawlse/docs/evidence/`.
