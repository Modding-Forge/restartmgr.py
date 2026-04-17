"""
Copyright (c) Modding Forge
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from restartmgr._const import RmAppType, RmRebootReason
from restartmgr._session import RmSession
from restartmgr.api import get_locking_processes, who_locks
from restartmgr.types import GetListResult, ProcessInfo

_IS_WINDOWS: bool = sys.platform == "win32"

pytestmark = pytest.mark.skipif(
    not _IS_WINDOWS,
    reason="Restart Manager is Windows-only.",
)


class TestWhoLocksIntegration:
    """
    Integration tests for `who_locks()` using real file
    locks on the current Windows system.
    """

    def test_unlocked_file_returns_empty(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Tests that an unlocked file returns an empty list.
        """

        # given
        target: Path = tmp_path / "unlocked.txt"
        target.write_text("hello")

        # when
        result: list[ProcessInfo] = who_locks(target)

        # then
        assert result == []

    def test_locked_file_detects_locker(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Tests that a file locked by a subprocess is detected.
        """

        # given
        target: Path = tmp_path / "locked.txt"
        target.write_text("data")

        script: str = (
            "import time, sys\n"
            "f = open(sys.argv[1], 'r+b')\n"
            "import msvcrt\n"
            "msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)\n"
            "print('LOCKED', flush=True)\n"
            "time.sleep(30)\n"
        )

        proc = subprocess.Popen(
            [sys.executable, "-c", script, str(target)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            assert proc.stdout is not None
            line: str = proc.stdout.readline().decode().strip()
            assert line == "LOCKED"

            # when
            result: list[ProcessInfo] = who_locks(target)

            # then
            assert len(result) >= 1
            names: list[str] = [
                p.app_name.lower() for p in result
            ]
            assert any("python" in n for n in names)
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_multiple_files(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Tests who_locks() with multiple file paths.
        """

        # given
        a: Path = tmp_path / "a.txt"
        b: Path = tmp_path / "b.txt"
        a.write_text("aaa")
        b.write_text("bbb")

        # when - neither file is locked
        result: list[ProcessInfo] = who_locks(a, b)

        # then
        assert result == []

    def test_path_object_and_string(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Tests that both str and Path arguments work.
        """

        # given
        target: Path = tmp_path / "mixed.txt"
        target.write_text("x")

        # when
        r1: list[ProcessInfo] = who_locks(target)
        r2: list[ProcessInfo] = who_locks(str(target))

        # then
        assert r1 == r2 == []


class TestGetLockingProcessesIntegration:
    """
    Integration tests for `get_locking_processes()`.
    """

    def test_unlocked_returns_no_reboot(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Tests that an unlocked file has NONE reboot reason.
        """

        # given
        target: Path = tmp_path / "file.txt"
        target.write_text("hi")

        # when
        result: GetListResult = get_locking_processes(target)

        # then
        assert result.processes == []
        assert result.reboot_reason == RmRebootReason.NONE

    def test_locked_file_returns_process_info(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Tests that a locked file returns process details.
        """

        # given
        target: Path = tmp_path / "locked2.txt"
        target.write_text("data")

        script: str = (
            "import time, sys\n"
            "f = open(sys.argv[1], 'r+b')\n"
            "import msvcrt\n"
            "msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)\n"
            "print('LOCKED', flush=True)\n"
            "time.sleep(30)\n"
        )

        proc = subprocess.Popen(
            [sys.executable, "-c", script, str(target)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            assert proc.stdout is not None
            line: str = proc.stdout.readline().decode().strip()
            assert line == "LOCKED"

            # when
            result: GetListResult = get_locking_processes(
                target,
            )

            # then
            assert len(result.processes) >= 1
            p: ProcessInfo = result.processes[0]
            assert p.pid > 0
            assert "python" in p.app_name.lower()
            assert isinstance(p.app_type, RmAppType)
        finally:
            proc.terminate()
            proc.wait(timeout=5)


class TestRmSessionIntegration:
    """
    Integration tests for `RmSession` lifecycle.
    """

    def test_start_and_end(self) -> None:
        """Tests that a session can be started and ended."""

        # given
        session = RmSession()

        # when
        session.start()

        # then
        assert session.handle is not None
        assert session.session_key is not None
        assert len(session.session_key) > 0

        # cleanup
        session.end()
        assert session.handle is None

    def test_context_manager(self) -> None:
        """Tests the with-statement lifecycle."""

        # given / when
        with RmSession() as session:
            # then
            assert session.handle is not None
            assert session.session_key is not None

        assert session.handle is None

    def test_register_files_and_get_list(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Tests the full register → get_list pipeline on
        an unlocked file.
        """

        # given
        target: Path = tmp_path / "session_test.txt"
        target.write_text("content")

        # when
        with RmSession() as session:
            session.register_files([str(target)])
            infos, reason = session.get_list()

        # then
        assert infos == []
        assert reason == RmRebootReason.NONE

    def test_register_files_locked(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Tests register → get_list pipeline on a locked file.
        """

        # given
        target: Path = tmp_path / "sess_locked.txt"
        target.write_text("data")

        script: str = (
            "import time, sys\n"
            "f = open(sys.argv[1], 'r+b')\n"
            "import msvcrt\n"
            "msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)\n"
            "print('LOCKED', flush=True)\n"
            "time.sleep(30)\n"
        )

        proc = subprocess.Popen(
            [sys.executable, "-c", script, str(target)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            assert proc.stdout is not None
            proc.stdout.readline()

            # when
            with RmSession() as session:
                session.register_files([str(target)])
                infos, reason = session.get_list()

            # then
            assert len(infos) >= 1
            names: list[str] = [
                i.strAppName.lower() for i in infos
            ]
            assert any("python" in n for n in names)
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_register_services_no_error(self) -> None:
        """
        Tests that registering a nonexistent service name
        does not raise (RM accepts it silently).
        """

        # given / when / then - should not raise
        with RmSession() as session:
            session.register_services(
                ["nonexistent_service_xyz"],
            )

    def test_double_end_is_safe(self) -> None:
        """Tests calling end() twice does not raise."""

        # given
        session = RmSession()
        session.start()

        # when / then
        session.end()
        session.end()  # second call is a no-op

    def test_multiple_register_calls(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Tests that multiple register_files() calls within
        one session work.
        """

        # given
        a: Path = tmp_path / "multi_a.txt"
        b: Path = tmp_path / "multi_b.txt"
        a.write_text("a")
        b.write_text("b")

        # when / then - should not raise
        with RmSession() as session:
            session.register_files([str(a)])
            session.register_files([str(b)])
            infos, _ = session.get_list()
            assert infos == []
