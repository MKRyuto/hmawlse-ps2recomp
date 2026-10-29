# Publishing Notes

This project uses one repository. The PS2Recomp and decompdecomp source trees under `vendor/` are vendored as ordinary directories, not Git submodules.

Clone the project normally:

```powershell
git clone <repository-url>
```

The public repository may include source and reviewable patches, but it must not include the user-owned ISO, extracted ELF/assets, `artifacts/`, `build/`, save-card directories, full runtime logs, or generated executables.

Keep all upstream license and notice files inside `vendor/`.

Use `docs/COMMUNITY_HELP.md` and the sanitized excerpts under `docs/evidence/` for public issue discussion.
