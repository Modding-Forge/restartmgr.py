"""
Copyright (c) Modding Forge
"""

from __future__ import annotations

import datetime
from dataclasses import FrozenInstanceError, asdict

import pytest

from restartmgr._const import (
    RmAppStatus,
    RmAppType,
    RmRebootReason,
)
from restartmgr.types import GetListResult, ProcessInfo


class TestProcessInfoCreation:
    """
    Tests `ProcessInfo` model construction.
    """

    def test_minimal_creation(self) -> None:
        """Tests creating a ProcessInfo with required fields."""

        # given / when
        info = ProcessInfo(
            pid=1234,
            start_time=None,
            app_name="test.exe",
            service_short_name=None,
            app_type=RmAppType.UNKNOWN,
            app_status=RmAppStatus.UNKNOWN,
            ts_session_id=-1,
            restartable=False,
        )

        # then
        assert info.pid == 1234
        assert info.start_time is None
        assert info.app_name == "test.exe"
        assert info.service_short_name is None

    def test_full_creation(self) -> None:
        """Tests creating a ProcessInfo with all fields set."""

        # given
        now = datetime.datetime(
            2024, 6, 15, 12, 30,
            tzinfo=datetime.UTC,
        )

        # when
        info = ProcessInfo(
            pid=5678,
            start_time=now,
            app_name="notepad.exe",
            service_short_name="Notepad",
            app_type=RmAppType.MAIN_WINDOW,
            app_status=RmAppStatus.RUNNING,
            ts_session_id=1,
            restartable=True,
        )

        # then
        assert info.pid == 5678
        assert info.start_time == now
        assert info.app_name == "notepad.exe"
        assert info.service_short_name == "Notepad"
        assert info.app_type == RmAppType.MAIN_WINDOW
        assert info.app_status == RmAppStatus.RUNNING
        assert info.ts_session_id == 1
        assert info.restartable is True

    def test_service_process(self) -> None:
        """Tests creating a ProcessInfo for a service."""

        # given / when
        info = ProcessInfo(
            pid=800,
            start_time=None,
            app_name="Windows Update",
            service_short_name="wuauserv",
            app_type=RmAppType.SERVICE,
            app_status=RmAppStatus.RUNNING,
            ts_session_id=0,
            restartable=True,
        )

        # then
        assert info.app_type == RmAppType.SERVICE
        assert info.service_short_name == "wuauserv"


class TestProcessInfoFrozen:
    """
    Tests `ProcessInfo` immutability.
    """

    def test_pid_immutable(self) -> None:
        """Tests that pid cannot be changed."""

        # given
        info = ProcessInfo(
            pid=1,
            start_time=None,
            app_name="a",
            service_short_name=None,
            app_type=RmAppType.UNKNOWN,
            app_status=RmAppStatus.UNKNOWN,
            ts_session_id=-1,
            restartable=False,
        )

        # when / then
        with pytest.raises(FrozenInstanceError):
            info.pid = 999  # type: ignore[misc]

    def test_app_name_immutable(self) -> None:
        """Tests that app_name cannot be changed."""

        # given
        info = ProcessInfo(
            pid=1,
            start_time=None,
            app_name="original",
            service_short_name=None,
            app_type=RmAppType.UNKNOWN,
            app_status=RmAppStatus.UNKNOWN,
            ts_session_id=-1,
            restartable=False,
        )

        # when / then
        with pytest.raises(FrozenInstanceError):
            info.app_name = "changed"  # type: ignore[misc]


class TestProcessInfoSerialization:
    """
    Tests `ProcessInfo` serialization.
    """

    def test_asdict(self) -> None:
        """Tests that asdict() returns all fields."""

        # given
        info = ProcessInfo(
            pid=42,
            start_time=None,
            app_name="test",
            service_short_name=None,
            app_type=RmAppType.CONSOLE,
            app_status=RmAppStatus.RUNNING,
            ts_session_id=2,
            restartable=True,
        )

        # when
        data: dict = asdict(info)  # type: ignore[type-arg]

        # then
        assert data["pid"] == 42
        assert data["app_name"] == "test"
        assert data["app_type"] == RmAppType.CONSOLE
        assert data["restartable"] is True

    def test_asdict_json_serializable(self) -> None:
        """Tests that asdict() output is JSON-serializable."""

        # given
        import json
        info = ProcessInfo(
            pid=42,
            start_time=None,
            app_name="test",
            service_short_name=None,
            app_type=RmAppType.CONSOLE,
            app_status=RmAppStatus.RUNNING,
            ts_session_id=2,
            restartable=True,
        )

        # when
        data = asdict(info)
        data["app_type"] = data["app_type"].value
        data["app_status"] = data["app_status"].value
        json_str: str = json.dumps(data)

        # then
        assert '"pid": 42' in json_str
        assert '"app_name": "test"' in json_str


class TestGetListResult:
    """
    Tests `GetListResult` model.
    """

    def test_empty_result(self) -> None:
        """Tests creation with no processes."""

        # given / when
        result = GetListResult(
            processes=[],
            reboot_reason=RmRebootReason.NONE,
        )

        # then
        assert result.processes == []
        assert result.reboot_reason == RmRebootReason.NONE

    def test_with_processes(self) -> None:
        """Tests creation with multiple processes."""

        # given
        p1 = ProcessInfo(
            pid=100,
            start_time=None,
            app_name="app1",
            service_short_name=None,
            app_type=RmAppType.MAIN_WINDOW,
            app_status=RmAppStatus.RUNNING,
            ts_session_id=1,
            restartable=True,
        )
        p2 = ProcessInfo(
            pid=200,
            start_time=None,
            app_name="app2",
            service_short_name="svc2",
            app_type=RmAppType.SERVICE,
            app_status=RmAppStatus.RUNNING,
            ts_session_id=0,
            restartable=True,
        )

        # when
        result = GetListResult(
            processes=[p1, p2],
            reboot_reason=RmRebootReason.NONE,
        )

        # then
        assert len(result.processes) == 2
        assert result.processes[0].pid == 100
        assert result.processes[1].pid == 200

    def test_with_reboot_reason(self) -> None:
        """Tests creation with a non-trivial reboot reason."""

        # given / when
        result = GetListResult(
            processes=[],
            reboot_reason=(
                RmRebootReason.CRITICAL_PROCESS
                | RmRebootReason.PERMISSION_DENIED
            ),
        )

        # then
        assert (
            RmRebootReason.CRITICAL_PROCESS
            in result.reboot_reason
        )
        assert (
            RmRebootReason.PERMISSION_DENIED
            in result.reboot_reason
        )

    def test_frozen(self) -> None:
        """Tests that GetListResult is immutable."""

        # given
        result = GetListResult(
            processes=[],
            reboot_reason=RmRebootReason.NONE,
        )

        # when / then
        with pytest.raises(FrozenInstanceError):
            result.processes = []  # type: ignore[misc]
