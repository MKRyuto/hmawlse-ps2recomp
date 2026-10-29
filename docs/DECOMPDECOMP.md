# decompdecomp

This project uses [decompdecomp](https://github.com/n-delic/decompdecomp) as an external local analysis tool. It is not vendored into this repository.

Install it using the upstream release/source instructions, then verify that the Python interpreter used by this project can import:

```python
from decompnet.app.engine import RomNetwork
```

The local import command is:

```powershell
.venv\Scripts\python.exe tools\ps2_pipeline.py import-decomp --workspace artifacts\decomp
```

The database, split output, ISO, ELF, and generated game data remain under ignored local paths. Only sanitized notes and evidence belong in this repository.
