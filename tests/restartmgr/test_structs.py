"""
Copyright (c) Modding Forge
"""

import ctypes

from restartmgr._const import (
    CCH_RM_MAX_APP_NAME,
    CCH_RM_MAX_SVC_NAME,
)
from restartmgr._structs import (
    FILETIME,
    RM_PROCESS_INFO,
    RM_UNIQUE_PROCESS,
)


class TestFILETIME:
    """
    Tests the `FILETIME` ctypes structure.
    """

    def test_default_zero(self) -> None:
        """Tests that a default FILETIME is all zeros."""

        # given
        ft = FILETIME()

        # when / then
        assert ft.dwLowDateTime == 0
        assert ft.dwHighDateTime == 0

    def test_field_assignment(self) -> None:
        """Tests assigning values to both fields."""

        # given
        ft = FILETIME()

        # when
        ft.dwLowDateTime = 0xDEADBEEF
        ft.dwHighDateTime = 0xCAFEBABE

        # then
        assert ft.dwLowDateTime == 0xDEADBEEF
        assert ft.dwHighDateTime == 0xCAFEBABE

    def test_size(self) -> None:
        """Tests that FILETIME is 8 bytes."""

        # given / when / then
        assert ctypes.sizeof(FILETIME) == 8


class TestRmUniqueProcess:
    """
    Tests the `RM_UNIQUE_PROCESS` ctypes structure.
    """

    def test_default_values(self) -> None:
        """Tests that defaults are zeroed."""

        # given
        proc = RM_UNIQUE_PROCESS()

        # when / then
        assert proc.dwProcessId == 0
        assert proc.ProcessStartTime.dwLowDateTime == 0
        assert proc.ProcessStartTime.dwHighDateTime == 0

    def test_field_assignment(self) -> None:
        """Tests assigning a PID and start time."""

        # given
        proc = RM_UNIQUE_PROCESS()

        # when
        proc.dwProcessId = 12345
        proc.ProcessStartTime.dwLowDateTime = 100
        proc.ProcessStartTime.dwHighDateTime = 200

        # then
        assert proc.dwProcessId == 12345
        assert proc.ProcessStartTime.dwLowDateTime == 100
        assert proc.ProcessStartTime.dwHighDateTime == 200

    def test_size(self) -> None:
        """
        Tests that RM_UNIQUE_PROCESS is 12 bytes
        (4 DWORD + 8 FILETIME).
        """

        # given / when / then
        assert ctypes.sizeof(RM_UNIQUE_PROCESS) == 12


class TestRmProcessInfo:
    """
    Tests the `RM_PROCESS_INFO` ctypes structure.
    """

    def test_default_values(self) -> None:
        """Tests that defaults are zeroed / empty."""

        # given
        info = RM_PROCESS_INFO()

        # when / then
        assert info.Process.dwProcessId == 0
        assert info.strAppName == ""
        assert info.strServiceShortName == ""
        assert info.ApplicationType == 0
        assert info.AppStatus == 0
        assert info.TSSessionId == 0
        assert info.bRestartable == 0

    def test_app_name_max_length(self) -> None:
        """
        Tests that strAppName can hold
        CCH_RM_MAX_APP_NAME characters.
        """

        # given
        info = RM_PROCESS_INFO()
        long_name: str = "A" * CCH_RM_MAX_APP_NAME

        # when
        info.strAppName = long_name

        # then
        assert info.strAppName == long_name
        assert len(info.strAppName) == CCH_RM_MAX_APP_NAME

    def test_service_name_max_length(self) -> None:
        """
        Tests that strServiceShortName can hold
        CCH_RM_MAX_SVC_NAME characters.
        """

        # given
        info = RM_PROCESS_INFO()
        long_name: str = "S" * CCH_RM_MAX_SVC_NAME

        # when
        info.strServiceShortName = long_name

        # then
        assert info.strServiceShortName == long_name

    def test_process_id_roundtrip(self) -> None:
        """Tests setting and reading back the process ID."""

        # given
        info = RM_PROCESS_INFO()

        # when
        info.Process.dwProcessId = 9999

        # then
        assert info.Process.dwProcessId == 9999

    def test_restartable_flag(self) -> None:
        """Tests setting bRestartable to TRUE (1)."""

        # given
        info = RM_PROCESS_INFO()

        # when
        info.bRestartable = 1

        # then
        assert info.bRestartable == 1

    def test_array_creation(self) -> None:
        """Tests creating an array of RM_PROCESS_INFO."""

        # given
        buf = (RM_PROCESS_INFO * 3)()

        # when
        buf[0].Process.dwProcessId = 100
        buf[1].Process.dwProcessId = 200
        buf[2].Process.dwProcessId = 300

        # then
        assert buf[0].Process.dwProcessId == 100
        assert buf[1].Process.dwProcessId == 200
        assert buf[2].Process.dwProcessId == 300
