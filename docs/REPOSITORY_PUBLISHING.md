# Publishing Notes

The public repository uses upstream Git submodules for the two large external projects:

```powershell
git clone --recurse-submodules <repository-url>
```

If the outer repository was already cloned without submodules:

```powershell
git submodule update --init --recursive
```

The pinned submodule commits are the upstream commits used by the initial public snapshot. Local diagnostic changes made during the runtime bring-up are intentionally not represented as upstream commits. They remain in the local working tree until they are converted into a reviewable patch or an upstream/fork commit.

Do not commit the user-owned ISO, extracted ELF/assets, `artifacts/`, `build/`, save-card directories, full runtime logs, or generated executables. Use `docs/COMMUNITY_HELP.md` and the sanitized excerpts under `docs/evidence/` for public issue discussion.
