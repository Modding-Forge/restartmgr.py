# restartmgr

[![PyPI - Version](https://img.shields.io/pypi/v/restartmgr)](https://pypi.org/project/restartmgr/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/restartmgr)](https://pypi.org/project/restartmgr/) [![PyPI - License](https://img.shields.io/pypi/l/restartmgr)](LICENSE) [![Tests](https://github.com/Modding-Forge/restartmgr.py/actions/workflows/ci.yml/badge.svg)](https://github.com/Modding-Forge/restartmgr.py/actions/workflows/ci.yml)

Python ctypes bindings for the **Windows Restart Manager API**
(`rstrtmgr.dll`). Find out which processes are locking a file - and
optionally shut them down and restart them - all from pure Python, no C
extension required.

> **Windows only** - calls `rstrtmgr.dll` directly via `ctypes`.
> Zero runtime dependencies.

---

## Installation

```bash
uv add restartmgr
```

or

```bash
pip install restartmgr
```

Python 3.12+ and Windows are required.

---

## Quick start

### Which processes lock a file?

```python
from pathlib import Path
from restartmgr import who_locks

lockers = who_locks(Path(r"C:\path\to\locked_file.txt"))

for p in lockers:
    print(f"PID {p.pid}  {p.app_name}  ({p.app_type.name})")
```

### Detailed result with reboot reason

```python
from restartmgr import get_locking_processes

result = get_locking_processes(r"C:\file_a.txt", r"C:\file_b.txt")

print(f"Reboot reason: {result.reboot_reason.name}")
for p in result.processes:
    print(f"  {p.pid}  {p.app_name}  restartable={p.restartable}")
```

### Full session lifecycle

```python
from restartmgr import RmSession, RmShutdownType

with RmSession() as session:
    session.register_files([r"C:\path\to\file.txt"])

    # Query which processes hold a lock
    infos, reboot_reason = session.get_list()
    for info in infos:
        print(info.Process.dwProcessId, info.strAppName)

    # Shut down those processes
    session.shutdown(
        action_flags=RmShutdownType.FORCE_SHUTDOWN,
    )

    # ... do your work on the file ...

    # Restart the previously shut-down processes
    session.restart()
```

---

## License

MIT - see [LICENSE](LICENSE).

---

## About Modding Forge

restartmgr was built for the Python tooling powering
**[Modding Forge](https://moddingforge.com)** - a community dedicated to
Skyrim modding. If you enjoy modding or want to connect with other modders,
come say hi!
