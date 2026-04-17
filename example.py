"""
Copyright (c) Modding Forge

Example script demonstrating all features of the `restartmgr`
package.

Run on Windows with:

    python example.py

The script will:

1. Use the high-level `who_locks()` function on a self-locked
   temp file.
2. Use `get_locking_processes()` for detailed results
   including reboot reason.
3. Use `RmSession` as a context manager to perform the full
   session lifecycle manually.
4. Register multiple files in one session.
5. Demonstrate that unlocked files return an empty result.
"""

import json
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

from restartmgr import (
    GetListResult,
    ProcessInfo,
    RestartManagerError,
    RmSession,
    get_locking_processes,
    who_locks,
)

SEPARATOR: str = "-" * 60


def print_process(proc: ProcessInfo) -> None:
    """
    Pretty-prints a single ProcessInfo entry.

    Args:
        proc (ProcessInfo): The process to print.
    """

    print(f"  PID:            {proc.pid}")
    print(f"  App name:       '{proc.app_name}'")
    print(f"  App type:       {proc.app_type.name}")
    print(f"  App status:     {proc.app_status!r}")
    print(f"  Service name:   {proc.service_short_name}")
    print(f"  TS session ID:  {proc.ts_session_id}")
    print(f"  Restartable:    {proc.restartable}")
    print(f"  Start time:     {proc.start_time}")
    print()


def demo_who_locks(locked_path: Path) -> None:
    """
    Demonstrates the simple `who_locks()` API.

    Args:
        locked_path (Path): Path to a file currently locked
            by a subprocess.
    """

    print(SEPARATOR)
    print("1) who_locks() - simple high-level API")
    print(SEPARATOR)
    print(f"   File: {locked_path}")
    print()

    lockers: list[ProcessInfo] = who_locks(locked_path)
    print(f"   Processes locking this file: {len(lockers)}")
    print()
    for p in lockers:
        print_process(p)


def demo_get_locking_processes(
    locked_path: Path,
) -> None:
    """
    Demonstrates `get_locking_processes()` which returns
    the full result including reboot reason flags.

    Args:
        locked_path (Path): Path to a file currently locked
            by a subprocess.
    """

    print(SEPARATOR)
    print(
        "2) get_locking_processes() - full result with "
        "reboot reason",
    )
    print(SEPARATOR)

    result: GetListResult = get_locking_processes(
        locked_path,
    )
    print(
        f"   Reboot reason: {result.reboot_reason.name} "
        f"(value={int(result.reboot_reason)})",
    )
    print(
        f"   Number of lockers: {len(result.processes)}",
    )
    print()
    for p in result.processes:
        print_process(p)


def demo_session_context_manager(
    locked_path: Path,
) -> None:
    """
    Demonstrates `RmSession` as a context manager with
    manual register → get_list.

    Args:
        locked_path (Path): Path to a file currently locked
            by a subprocess.
    """

    print(SEPARATOR)
    print("3) RmSession context manager - manual lifecycle")
    print(SEPARATOR)

    with RmSession() as session:
        print(f"   Session handle:  {session.handle}")
        print(f"   Session key:     '{session.session_key}'")
        print()

        session.register_files([str(locked_path)])
        infos, reason = session.get_list()

        print(
            f"   Affected processes: {len(infos)}",
        )
        print(
            f"   Reboot reason:      {reason.name}",
        )
        print()

        for raw in infos:
            print(
                f"  PID: {raw.Process.dwProcessId}  "
                f"App: '{raw.strAppName}'",
            )

    print()
    print("   Session ended automatically.")
    print()


def demo_multiple_files(
    locked_path: Path,
    unlocked_path: Path,
) -> None:
    """
    Demonstrates registering multiple files in one session.

    Args:
        locked_path (Path): A locked file.
        unlocked_path (Path): An unlocked file.
    """

    print(SEPARATOR)
    print("4) Multiple files in one session")
    print(SEPARATOR)
    print(f"   Locked:   {locked_path}")
    print(f"   Unlocked: {unlocked_path}")
    print()

    lockers: list[ProcessInfo] = who_locks(
        locked_path,
        unlocked_path,
    )
    print(f"   Total lockers: {len(lockers)}")
    for p in lockers:
        print_process(p)


def demo_unlocked_file(path: Path) -> None:
    """
    Demonstrates that an unlocked file returns no lockers.

    Args:
        path (Path): An unlocked file.
    """

    print(SEPARATOR)
    print("5) Unlocked file - empty result")
    print(SEPARATOR)
    print(f"   File: {path}")

    lockers: list[ProcessInfo] = who_locks(path)
    print(f"   Lockers: {len(lockers)}")
    assert len(lockers) == 0
    print("   OK - no lockers found as expected.")
    print()


def demo_serialization(locked_path: Path) -> None:
    """
    Demonstrates dataclass serialization of ProcessInfo.

    Args:
        locked_path (Path): Path to a file currently locked
            by a subprocess.
    """

    print(SEPARATOR)
    print("6) Dataclass serialization")
    print(SEPARATOR)

    lockers: list[ProcessInfo] = who_locks(locked_path)
    if lockers:
        p: ProcessInfo = lockers[0]
        print("   asdict():")
        for key, val in asdict(p).items():
            print(f"     {key}: {val!r}")
        print()
        print("   JSON:")
        data = asdict(p)
        data["start_time"] = (
            data["start_time"].isoformat()
            if data["start_time"] else None
        )
        data["app_type"] = data["app_type"].value
        data["app_status"] = data["app_status"].value
        print(f"     {json.dumps(data, indent=2)}")
    else:
        print("   (no lockers to serialize)")
    print()


def main() -> None:
    """
    Runs all demos.

    Creates a temporary file, locks it from a subprocess,
    then runs each demonstration in turn.
    """

    print()
    print("=" * 60)
    print("  restartmgr - example script")
    print("=" * 60)
    print()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir: Path = Path(tmp)

        locked_file: Path = tmp_dir / "locked_demo.txt"
        locked_file.write_text("This file will be locked.")

        unlocked_file: Path = tmp_dir / "unlocked_demo.txt"
        unlocked_file.write_text("This file stays free.")

        locker_script: str = (
            "import time, sys, msvcrt\n"
            "f = open(sys.argv[1], 'r+b')\n"
            "msvcrt.locking("
            "f.fileno(), msvcrt.LK_NBLCK, 1)\n"
            "print('LOCKED', flush=True)\n"
            "time.sleep(120)\n"
        )

        proc = subprocess.Popen(
            [
                sys.executable,
                "-c",
                locker_script,
                str(locked_file),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            assert proc.stdout is not None
            line: str = (
                proc.stdout.readline().decode().strip()
            )
            if line != "LOCKED":
                print(f"ERROR: expected 'LOCKED', got '{line}'")
                return

            print(
                f"Locker subprocess started (PID {proc.pid})",
            )
            print()

            demo_who_locks(locked_file)
            demo_get_locking_processes(locked_file)
            demo_session_context_manager(locked_file)
            demo_multiple_files(locked_file, unlocked_file)
            demo_unlocked_file(unlocked_file)
            demo_serialization(locked_file)

            print("=" * 60)
            print("  All demos completed successfully!")
            print("=" * 60)
            print()

        except RestartManagerError as exc:
            print(f"Restart Manager error: {exc}")
            sys.exit(1)
        finally:
            proc.terminate()
            proc.wait(timeout=5)
            print(
                f"Locker subprocess terminated "
                f"(PID {proc.pid}).",
            )


if __name__ == "__main__":
    main()
