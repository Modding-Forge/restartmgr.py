"""
Copyright (c) Modding Forge
"""

import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from restartmgr._const import (
    RmAppStatus,
    RmAppType,
    RmRebootReason,
)
from restartmgr._structs import RM_PROCESS_INFO
from restartmgr.api import (
    _convert_process_info,
    _filetime_to_datetime,
    get_locking_processes,
    who_locks,
)
from restartmgr.types import GetListResult, ProcessInfo


class TestFiletimeToDatetime:
    """
    Tests `_filetime_to_datetime` helper.
    """

    def test_zero_returns_none(self) -> None:
        """Tests that zero FILETIME yields None."""

        # given / when
        result = _filetime_to_datetime(0, 0)

        # then
        assert result is None

    def test_known_timestamp(self) -> None:
        """
        Tests conversion of a known FILETIME to its expected
        UTC datetime.
        """

        # given - derive ticks from a known datetime
        expected = datetime.datetime(
            2024, 1, 1, tzinfo=datetime.UTC,
        )
        epoch = datetime.datetime(
            1601, 1, 1, tzinfo=datetime.UTC,
        )
        delta = expected - epoch
        ticks: int = int(
            delta.total_seconds() * 10_000_000,
        )
        low: int = ticks & 0xFFFFFFFF
        high: int = ticks >> 32

        # when
        result = _filetime_to_datetime(low, high)

        # then
        assert result is not None
        assert result == expected

    def test_epoch_start(self) -> None:
        """
        Tests that ticks=1 produces a datetime very close to
        the Windows epoch.
        """

        # given - 1 tick = 0.1 microsecond
        low: int = 1
        high: int = 0

        # when
        result = _filetime_to_datetime(low, high)

        # then
        assert result is not None
        epoch = datetime.datetime(
            1601, 1, 1, tzinfo=datetime.UTC,
        )
        assert (result - epoch).total_seconds() < 1.0

    def test_high_only(self) -> None:
        """Tests with only the high DWORD set."""

        # given
        low: int = 0
        high: int = 1

        # when
        result = _filetime_to_datetime(low, high)

        # then
        assert result is not None
        assert result > datetime.datetime(
            1601, 1, 1, tzinfo=datetime.UTC,
        )

    def test_roundtrip_consistency(self) -> None:
        """
        Tests that encoding and decoding a datetime produces
        the same result.
        """

        # given
        original = datetime.datetime(
            2025, 7, 15, 14, 30, 45,
            tzinfo=datetime.UTC,
        )
        epoch = datetime.datetime(
            1601, 1, 1, tzinfo=datetime.UTC,
        )
        delta = original - epoch
        ticks: int = int(
            delta.total_seconds() * 10_000_000,
        )
        low: int = ticks & 0xFFFFFFFF
        high: int = ticks >> 32

        # when
        result = _filetime_to_datetime(low, high)

        # then
        assert result is not None
        diff = abs(
            (result - original).total_seconds(),
        )
        assert diff < 1.0


class TestConvertProcessInfo:
    """
    Tests `_convert_process_info` helper.
    """

    def test_basic_conversion(self) -> None:
        """
        Tests converting an RM_PROCESS_INFO to ProcessInfo.
        """

        # given
        raw = RM_PROCESS_INFO()
        raw.Process.dwProcessId = 42
        raw.Process.ProcessStartTime.dwLowDateTime = 0
        raw.Process.ProcessStartTime.dwHighDateTime = 0
        raw.strAppName = "testapp.exe"
        raw.strServiceShortName = ""
        raw.ApplicationType = RmAppType.CONSOLE
        raw.AppStatus = RmAppStatus.RUNNING
        raw.TSSessionId = 1
        raw.bRestartable = 1

        # when
        result: ProcessInfo = _convert_process_info(raw)

        # then
        assert result.pid == 42
        assert result.app_name == "testapp.exe"
        assert result.service_short_name is None
        assert result.app_type == RmAppType.CONSOLE
        assert result.app_status == RmAppStatus.RUNNING
        assert result.ts_session_id == 1
        assert result.restartable is True
        assert result.start_time is None

    def test_service_conversion(self) -> None:
        """
        Tests conversion when the process is a service.
        """

        # given
        raw = RM_PROCESS_INFO()
        raw.Process.dwProcessId = 800
        raw.strAppName = "Windows Update"
        raw.strServiceShortName = "wuauserv"
        raw.ApplicationType = RmAppType.SERVICE
        raw.AppStatus = RmAppStatus.RUNNING
        raw.TSSessionId = 0
        raw.bRestartable = 1

        # when
        result: ProcessInfo = _convert_process_info(raw)

        # then
        assert result.service_short_name == "wuauserv"
        assert result.app_type == RmAppType.SERVICE

    def test_start_time_converted(self) -> None:
        """
        Tests that a non-zero ProcessStartTime is converted
        to a datetime.
        """

        # given
        raw = RM_PROCESS_INFO()
        raw.Process.dwProcessId = 10
        raw.Process.ProcessStartTime.dwLowDateTime = 1000
        raw.Process.ProcessStartTime.dwHighDateTime = 1
        raw.strAppName = "app"
        raw.strServiceShortName = ""
        raw.ApplicationType = 0
        raw.AppStatus = 0
        raw.TSSessionId = 0
        raw.bRestartable = 0

        # when
        result: ProcessInfo = _convert_process_info(raw)

        # then
        assert result.start_time is not None

    def test_restartable_false(self) -> None:
        """Tests that bRestartable=0 maps to False."""

        # given
        raw = RM_PROCESS_INFO()
        raw.Process.dwProcessId = 1
        raw.strAppName = "x"
        raw.strServiceShortName = ""
        raw.ApplicationType = 0
        raw.AppStatus = 0
        raw.TSSessionId = 0
        raw.bRestartable = 0

        # when
        result: ProcessInfo = _convert_process_info(raw)

        # then
        assert result.restartable is False


class TestWhoLocks:
    """
    Tests `who_locks()` high-level function.
    """

    def test_no_paths_raises_value_error(self) -> None:
        """Tests that who_locks() without paths raises."""

        # given / when / then
        with pytest.raises(ValueError, match="path"):
            who_locks()

    @patch("restartmgr.api.RmSession")
    def test_returns_empty_list(
        self,
        mock_session_cls: MagicMock,
    ) -> None:
        """Tests who_locks() when no lockers are found."""

        # given
        mock_session = MagicMock()
        mock_session.get_list.return_value = (
            [],
            RmRebootReason.NONE,
        )
        mock_session.__enter__ = MagicMock(
            return_value=mock_session,
        )
        mock_session.__exit__ = MagicMock(
            return_value=False,
        )
        mock_session_cls.return_value = mock_session

        # when
        result = who_locks("C:\\test.txt")

        # then
        assert result == []
        mock_session.register_files.assert_called_once_with(
            ["C:\\test.txt"],
        )
        mock_session.__exit__.assert_called_once()

    @patch("restartmgr.api.RmSession")
    def test_returns_converted_processes(
        self,
        mock_session_cls: MagicMock,
    ) -> None:
        """
        Tests that who_locks() converts raw structs to
        ProcessInfo.
        """

        # given
        raw = RM_PROCESS_INFO()
        raw.Process.dwProcessId = 1234
        raw.strAppName = "notepad.exe"
        raw.strServiceShortName = ""
        raw.ApplicationType = RmAppType.MAIN_WINDOW
        raw.AppStatus = RmAppStatus.RUNNING
        raw.TSSessionId = 1
        raw.bRestartable = 1

        mock_session = MagicMock()
        mock_session.get_list.return_value = (
            [raw],
            RmRebootReason.NONE,
        )
        mock_session.__enter__ = MagicMock(
            return_value=mock_session,
        )
        mock_session.__exit__ = MagicMock(
            return_value=False,
        )
        mock_session_cls.return_value = mock_session

        # when
        result = who_locks("C:\\file.txt")

        # then
        assert len(result) == 1
        assert result[0].pid == 1234
        assert result[0].app_name == "notepad.exe"

    @patch("restartmgr.api.RmSession")
    def test_multiple_paths(
        self,
        mock_session_cls: MagicMock,
    ) -> None:
        """Tests who_locks() with multiple paths."""

        # given
        mock_session = MagicMock()
        mock_session.get_list.return_value = (
            [],
            RmRebootReason.NONE,
        )
        mock_session.__enter__ = MagicMock(
            return_value=mock_session,
        )
        mock_session.__exit__ = MagicMock(
            return_value=False,
        )
        mock_session_cls.return_value = mock_session

        # when
        who_locks("C:\\a.txt", "C:\\b.txt", "C:\\c.txt")

        # then
        mock_session.register_files.assert_called_once_with(
            ["C:\\a.txt", "C:\\b.txt", "C:\\c.txt"],
        )

    @patch("restartmgr.api.RmSession")
    def test_path_objects_converted(
        self,
        mock_session_cls: MagicMock,
    ) -> None:
        """Tests that Path objects are converted to strings."""

        # given
        mock_session = MagicMock()
        mock_session.get_list.return_value = (
            [],
            RmRebootReason.NONE,
        )
        mock_session.__enter__ = MagicMock(
            return_value=mock_session,
        )
        mock_session.__exit__ = MagicMock(
            return_value=False,
        )
        mock_session_cls.return_value = mock_session
        p = Path("C:\\file.txt")

        # when
        who_locks(p)

        # then
        mock_session.register_files.assert_called_once_with(
            ["C:\\file.txt"],
        )

    @patch("restartmgr.api.RmSession")
    def test_session_ends_on_exception(
        self,
        mock_session_cls: MagicMock,
    ) -> None:
        """
        Tests that the session is always ended, even when
        an exception occurs.
        """

        # given
        mock_session = MagicMock()
        mock_session.register_files.side_effect = (
            RuntimeError("boom")
        )
        mock_session.__enter__ = MagicMock(
            return_value=mock_session,
        )
        mock_session.__exit__ = MagicMock(
            return_value=False,
        )
        mock_session_cls.return_value = mock_session

        # when / then
        with pytest.raises(RuntimeError):
            who_locks("C:\\x.txt")
        mock_session.__exit__.assert_called_once()


class TestGetLockingProcesses:
    """
    Tests `get_locking_processes()` high-level function.
    """

    def test_no_paths_raises_value_error(self) -> None:
        """
        Tests that get_locking_processes() without paths
        raises ValueError.
        """

        # given / when / then
        with pytest.raises(ValueError, match="path"):
            get_locking_processes()

    @patch("restartmgr.api.RmSession")
    def test_returns_get_list_result(
        self,
        mock_session_cls: MagicMock,
    ) -> None:
        """
        Tests that get_locking_processes() returns a
        GetListResult.
        """

        # given
        mock_session = MagicMock()
        mock_session.get_list.return_value = (
            [],
            RmRebootReason.NONE,
        )
        mock_session.__enter__ = MagicMock(
            return_value=mock_session,
        )
        mock_session.__exit__ = MagicMock(
            return_value=False,
        )
        mock_session_cls.return_value = mock_session

        # when
        result = get_locking_processes("C:\\test.txt")

        # then
        assert isinstance(result, GetListResult)
        assert result.processes == ()
        assert result.reboot_reason == RmRebootReason.NONE

    @patch("restartmgr.api.RmSession")
    def test_includes_reboot_reason(
        self,
        mock_session_cls: MagicMock,
    ) -> None:
        """
        Tests that the reboot reason is correctly passed
        through.
        """

        # given
        mock_session = MagicMock()
        reason = (
            RmRebootReason.CRITICAL_PROCESS
            | RmRebootReason.PERMISSION_DENIED
        )
        mock_session.get_list.return_value = ([], reason)
        mock_session.__enter__ = MagicMock(
            return_value=mock_session,
        )
        mock_session.__exit__ = MagicMock(
            return_value=False,
        )
        mock_session_cls.return_value = mock_session

        # when
        result = get_locking_processes("C:\\x.txt")

        # then
        assert (
            RmRebootReason.CRITICAL_PROCESS
            in result.reboot_reason
        )

    @patch("restartmgr.api.RmSession")
    def test_session_ends_on_exception(
        self,
        mock_session_cls: MagicMock,
    ) -> None:
        """
        Tests that get_locking_processes() always ends the
        session.
        """

        # given
        mock_session = MagicMock()
        mock_session.get_list.side_effect = RuntimeError(
            "fail",
        )
        mock_session.__enter__ = MagicMock(
            return_value=mock_session,
        )
        mock_session.__exit__ = MagicMock(
            return_value=False,
        )
        mock_session_cls.return_value = mock_session

        # when / then
        with pytest.raises(RuntimeError):
            get_locking_processes("C:\\x.txt")
        mock_session.__exit__.assert_called_once()
