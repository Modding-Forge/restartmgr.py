"""
Copyright (c) Modding Forge
"""

from restartmgr._const import (
    CCH_RM_MAX_APP_NAME,
    CCH_RM_MAX_SVC_NAME,
    CCH_RM_SESSION_KEY,
    ERROR_ACCESS_DENIED,
    ERROR_BAD_ARGUMENTS,
    ERROR_CANCELLED,
    ERROR_FAIL_NOACTION_REBOOT,
    ERROR_FAIL_RESTART,
    ERROR_FAIL_SHUTDOWN,
    ERROR_INVALID_HANDLE,
    ERROR_MAX_SESSIONS_REACHED,
    ERROR_MORE_DATA,
    ERROR_OUTOFMEMORY,
    ERROR_REQUEST_OUT_OF_SEQUENCE,
    ERROR_SEM_TIMEOUT,
    ERROR_SUCCESS,
    ERROR_WRITE_FAULT,
    RM_INVALID_PROCESS,
    RM_INVALID_TS_SESSION,
    WIN32_ERROR_NAMES,
    RmAppStatus,
    RmAppType,
    RmRebootReason,
    RmShutdownType,
)


class TestStringLengthConstants:
    """
    Tests string-length constants from `restartmanager.h`.
    """

    def test_session_key_length(self) -> None:
        """Tests that CCH_RM_SESSION_KEY is 32."""

        # given / when / then
        assert CCH_RM_SESSION_KEY == 32

    def test_max_app_name_length(self) -> None:
        """Tests that CCH_RM_MAX_APP_NAME is 255."""

        # given / when / then
        assert CCH_RM_MAX_APP_NAME == 255

    def test_max_svc_name_length(self) -> None:
        """Tests that CCH_RM_MAX_SVC_NAME is 63."""

        # given / when / then
        assert CCH_RM_MAX_SVC_NAME == 63


class TestSentinelValues:
    """
    Tests sentinel values.
    """

    def test_invalid_ts_session(self) -> None:
        """Tests RM_INVALID_TS_SESSION is -1."""

        # given / when / then
        assert RM_INVALID_TS_SESSION == -1

    def test_invalid_process(self) -> None:
        """Tests RM_INVALID_PROCESS is -1."""

        # given / when / then
        assert RM_INVALID_PROCESS == -1


class TestRmAppType:
    """
    Tests `RmAppType` integer enum.
    """

    def test_all_members_present(self) -> None:
        """Tests that all expected members exist."""

        # given
        expected: dict[str, int] = {
            "UNKNOWN": 0,
            "MAIN_WINDOW": 1,
            "OTHER_WINDOW": 2,
            "SERVICE": 3,
            "EXPLORER": 4,
            "CONSOLE": 5,
            "CRITICAL": 1000,
        }

        # when / then
        for name, value in expected.items():
            assert RmAppType[name] == value

    def test_int_conversion(self) -> None:
        """Tests that members convert to int."""

        # given / when / then
        assert int(RmAppType.SERVICE) == 3

    def test_from_int(self) -> None:
        """Tests construction from integer."""

        # given / when
        result = RmAppType(1000)

        # then
        assert result is RmAppType.CRITICAL


class TestRmAppStatus:
    """
    Tests `RmAppStatus` integer flag enum.
    """

    def test_all_members_present(self) -> None:
        """Tests that all expected members exist."""

        # given
        expected: dict[str, int] = {
            "UNKNOWN": 0x0,
            "RUNNING": 0x1,
            "STOPPED": 0x2,
            "STOPPED_OTHER": 0x4,
            "RESTARTED": 0x8,
            "ERROR_ON_STOP": 0x10,
            "ERROR_ON_RESTART": 0x20,
            "SHUTDOWN_MASKED": 0x40,
            "RESTART_MASKED": 0x80,
        }

        # when / then
        for name, value in expected.items():
            assert RmAppStatus[name] == value

    def test_or_combination(self) -> None:
        """Tests bitwise OR on flags."""

        # given
        combined = (
            RmAppStatus.RUNNING
            | RmAppStatus.STOPPED
            | RmAppStatus.RESTARTED
        )

        # when / then
        assert RmAppStatus.RUNNING in combined
        assert RmAppStatus.STOPPED in combined
        assert RmAppStatus.RESTARTED in combined
        assert RmAppStatus.ERROR_ON_STOP not in combined

    def test_and_check(self) -> None:
        """Tests bitwise AND check on flags."""

        # given
        status = RmAppStatus(0x11)

        # when / then
        assert status & RmAppStatus.RUNNING
        assert status & RmAppStatus.ERROR_ON_STOP


class TestRmRebootReason:
    """
    Tests `RmRebootReason` integer flag enum.
    """

    def test_all_members_present(self) -> None:
        """Tests that all expected members exist."""

        # given
        expected: dict[str, int] = {
            "NONE": 0x0,
            "PERMISSION_DENIED": 0x1,
            "SESSION_MISMATCH": 0x2,
            "CRITICAL_PROCESS": 0x4,
            "CRITICAL_SERVICE": 0x8,
            "DETECTED_SELF": 0x10,
        }

        # when / then
        for name, value in expected.items():
            assert RmRebootReason[name] == value

    def test_combined_reasons(self) -> None:
        """Tests combining multiple reboot reasons."""

        # given
        combined = (
            RmRebootReason.PERMISSION_DENIED
            | RmRebootReason.CRITICAL_PROCESS
        )

        # when / then
        assert int(combined) == 0x5


class TestRmShutdownType:
    """
    Tests `RmShutdownType` integer flag enum.
    """

    def test_force_shutdown_value(self) -> None:
        """Tests FORCE_SHUTDOWN is 0x1."""

        # given / when / then
        assert RmShutdownType.FORCE_SHUTDOWN == 0x1

    def test_shutdown_only_registered_value(self) -> None:
        """Tests SHUTDOWN_ONLY_REGISTERED is 0x10."""

        # given / when / then
        assert (
            RmShutdownType.SHUTDOWN_ONLY_REGISTERED == 0x10
        )

    def test_combined(self) -> None:
        """Tests combining both flags."""

        # given
        combined = (
            RmShutdownType.FORCE_SHUTDOWN
            | RmShutdownType.SHUTDOWN_ONLY_REGISTERED
        )

        # when / then
        assert int(combined) == 0x11


class TestWin32ErrorCodes:
    """
    Tests Win32 error code constants and their name mapping.
    """

    def test_error_success(self) -> None:
        """Tests ERROR_SUCCESS is 0."""

        # given / when / then
        assert ERROR_SUCCESS == 0

    def test_error_more_data(self) -> None:
        """Tests ERROR_MORE_DATA is 234."""

        # given / when / then
        assert ERROR_MORE_DATA == 234

    def test_error_max_sessions_reached(self) -> None:
        """Tests ERROR_MAX_SESSIONS_REACHED is 353."""

        # given / when / then
        assert ERROR_MAX_SESSIONS_REACHED == 353

    def test_all_codes_in_name_map(self) -> None:
        """
        Tests that every defined code has an entry in
        WIN32_ERROR_NAMES.
        """

        # given
        codes: list[int] = [
            ERROR_SUCCESS,
            ERROR_ACCESS_DENIED,
            ERROR_INVALID_HANDLE,
            ERROR_OUTOFMEMORY,
            ERROR_WRITE_FAULT,
            ERROR_SEM_TIMEOUT,
            ERROR_BAD_ARGUMENTS,
            ERROR_MORE_DATA,
            ERROR_FAIL_NOACTION_REBOOT,
            ERROR_FAIL_SHUTDOWN,
            ERROR_FAIL_RESTART,
            ERROR_MAX_SESSIONS_REACHED,
            ERROR_REQUEST_OUT_OF_SEQUENCE,
            ERROR_CANCELLED,
        ]

        # when / then
        for code in codes:
            assert code in WIN32_ERROR_NAMES
            assert isinstance(WIN32_ERROR_NAMES[code], str)

    def test_name_map_values_match(self) -> None:
        """
        Tests that selected WIN32_ERROR_NAMES entries match
        the expected constant names.
        """

        # given / when / then
        assert (
            WIN32_ERROR_NAMES[ERROR_SUCCESS]
            == "ERROR_SUCCESS"
        )
        assert (
            WIN32_ERROR_NAMES[ERROR_MORE_DATA]
            == "ERROR_MORE_DATA"
        )
        assert (
            WIN32_ERROR_NAMES[ERROR_CANCELLED]
            == "ERROR_CANCELLED"
        )
