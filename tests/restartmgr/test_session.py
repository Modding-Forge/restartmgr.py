"""
Copyright (c) Modding Forge
"""

from unittest.mock import MagicMock, patch

import pytest

from restartmgr._const import (
    ERROR_BAD_ARGUMENTS,
    ERROR_INVALID_HANDLE,
    ERROR_SUCCESS,
    RmRebootReason,
    RmShutdownType,
)
from restartmgr._errors import (
    GetListError,
    ResourceRegistrationError,
    RestartError,
    SessionError,
    ShutdownError,
)
from restartmgr._session import RmSession


class TestRmSessionProperties:
    """
    Tests `RmSession` initial state and properties.
    """

    def test_handle_is_none_initially(self) -> None:
        """Tests that handle is None before start()."""

        # given
        session = RmSession()

        # when / then
        assert session.handle is None

    def test_session_key_is_none_initially(self) -> None:
        """Tests that session_key is None before start()."""

        # given
        session = RmSession()

        # when / then
        assert session.session_key is None


class TestRmSessionEnd:
    """
    Tests `RmSession.end()` behaviour.
    """

    def test_end_without_start_is_safe(self) -> None:
        """Tests that end() does nothing when not started."""

        # given
        session = RmSession()

        # when / then - should not raise
        session.end()

    @patch("restartmgr._session.load_dll")
    def test_end_calls_dll(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that end() calls RmEndSession on the DLL."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmEndSession.return_value = 0
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when
        session.end()

        # then
        mock_dll.RmEndSession.assert_called_once()

    @patch("restartmgr._session.load_dll")
    def test_end_clears_handle(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that end() sets handle to None."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmEndSession.return_value = 0
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when
        session.end()

        # then
        assert session.handle is None
        assert session.session_key is None

    @patch("restartmgr._session.load_dll")
    def test_end_failure_raises_session_error(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that end() raises SessionError on failure."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmEndSession.return_value = (
            ERROR_INVALID_HANDLE
        )
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when / then
        with pytest.raises(SessionError) as exc_info:
            session.end()
        assert exc_info.value.error_code == (
            ERROR_INVALID_HANDLE
        )


class TestRmSessionStart:
    """
    Tests `RmSession.start()`.
    """

    @patch("restartmgr._session.load_dll")
    def test_start_sets_handle(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that start() sets the session handle."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_load.return_value = mock_dll
        session = RmSession()

        # when
        session.start()

        # then
        assert session.handle is not None

    @patch("restartmgr._session.load_dll")
    def test_start_failure_raises_session_error(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that start() raises SessionError on failure."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = (
            ERROR_BAD_ARGUMENTS
        )
        mock_load.return_value = mock_dll
        session = RmSession()

        # when / then
        with pytest.raises(SessionError) as exc_info:
            session.start()
        assert exc_info.value.error_code == (
            ERROR_BAD_ARGUMENTS
        )


class TestRmSessionRegisterPreconditions:
    """
    Tests that register methods require an active session.
    """

    def test_register_files_without_start(self) -> None:
        """Tests register_files() raises without start()."""

        # given
        session = RmSession()

        # when / then
        with pytest.raises(SessionError):
            session.register_files(["C:\\test.txt"])

    def test_register_processes_without_start(self) -> None:
        """Tests register_processes() raises without start()."""

        # given
        session = RmSession()

        # when / then
        with pytest.raises(SessionError):
            session.register_processes([])

    def test_register_services_without_start(self) -> None:
        """Tests register_services() raises without start()."""

        # given
        session = RmSession()

        # when / then
        with pytest.raises(SessionError):
            session.register_services(["svc"])

    def test_get_list_without_start(self) -> None:
        """Tests get_list() raises without start()."""

        # given
        session = RmSession()

        # when / then
        with pytest.raises(SessionError):
            session.get_list()

    def test_shutdown_without_start(self) -> None:
        """Tests shutdown() raises without start()."""

        # given
        session = RmSession()

        # when / then
        with pytest.raises(SessionError):
            session.shutdown()

    def test_restart_without_start(self) -> None:
        """Tests restart() raises without start()."""

        # given
        session = RmSession()

        # when / then
        with pytest.raises(SessionError):
            session.restart()


class TestRmSessionRegisterFiles:
    """
    Tests `RmSession.register_files()` with mocked DLL.
    """

    @patch("restartmgr._session.load_dll")
    def test_register_files_success(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that register_files() calls the DLL."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmRegisterResources.return_value = 0
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when
        session.register_files(
            ["C:\\a.txt", "C:\\b.txt"],
        )

        # then
        mock_dll.RmRegisterResources.assert_called_once()

    @patch("restartmgr._session.load_dll")
    def test_register_files_empty_is_noop(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that an empty list does not call the DLL."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when
        session.register_files([])

        # then
        mock_dll.RmRegisterResources.assert_not_called()

    @patch("restartmgr._session.load_dll")
    def test_register_files_failure(
        self,
        mock_load: MagicMock,
    ) -> None:
        """
        Tests that register_files() raises
        ResourceRegistrationError on failure.
        """

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmRegisterResources.return_value = (
            ERROR_BAD_ARGUMENTS
        )
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when / then
        with pytest.raises(ResourceRegistrationError):
            session.register_files(["C:\\a.txt"])


class TestRmSessionRegisterServices:
    """
    Tests `RmSession.register_services()` with mocked DLL.
    """

    @patch("restartmgr._session.load_dll")
    def test_register_services_success(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that register_services() calls the DLL."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmRegisterResources.return_value = 0
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when
        session.register_services(["wuauserv"])

        # then
        mock_dll.RmRegisterResources.assert_called_once()

    @patch("restartmgr._session.load_dll")
    def test_register_services_empty_is_noop(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that an empty list is a no-op."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when
        session.register_services([])

        # then
        mock_dll.RmRegisterResources.assert_not_called()


class TestRmSessionGetList:
    """
    Tests `RmSession.get_list()` with mocked DLL.
    """

    @patch("restartmgr._session.load_dll")
    def test_get_list_empty(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests get_list() when no processes are returned."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0

        def fake_get_list(
            handle, needed, count, buf, reboot,
        ):  # type: ignore[no-untyped-def]
            """Simulates RmGetList returning zero processes."""

            needed._obj.value = 0
            return ERROR_SUCCESS

        mock_dll.RmGetList.side_effect = fake_get_list
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when
        infos, reason = session.get_list()

        # then
        assert infos == []
        assert reason == RmRebootReason.NONE

    @patch("restartmgr._session.load_dll")
    def test_get_list_failure_raises(
        self,
        mock_load: MagicMock,
    ) -> None:
        """
        Tests get_list() raises GetListError on
        non-recoverable failure.
        """

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmGetList.return_value = (
            ERROR_INVALID_HANDLE
        )
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when / then
        with pytest.raises(GetListError) as exc_info:
            session.get_list()
        assert exc_info.value.error_code == (
            ERROR_INVALID_HANDLE
        )


class TestRmSessionShutdown:
    """
    Tests `RmSession.shutdown()` with mocked DLL.
    """

    @patch("restartmgr._session.load_dll")
    def test_shutdown_success(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that shutdown() succeeds."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmShutdown.return_value = 0
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when / then - should not raise
        session.shutdown()
        mock_dll.RmShutdown.assert_called_once()

    @patch("restartmgr._session.load_dll")
    def test_shutdown_failure_raises(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that shutdown() raises ShutdownError."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmShutdown.return_value = 351
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when / then
        with pytest.raises(ShutdownError):
            session.shutdown()

    @patch("restartmgr._session.load_dll")
    def test_shutdown_custom_flags(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests shutdown with SHUTDOWN_ONLY_REGISTERED."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmShutdown.return_value = 0
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when
        session.shutdown(
            RmShutdownType.SHUTDOWN_ONLY_REGISTERED,
        )

        # then
        mock_dll.RmShutdown.assert_called_once()


class TestRmSessionRestart:
    """
    Tests `RmSession.restart()` with mocked DLL.
    """

    @patch("restartmgr._session.load_dll")
    def test_restart_success(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that restart() succeeds."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmRestart.return_value = 0
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when / then - should not raise
        session.restart()
        mock_dll.RmRestart.assert_called_once()

    @patch("restartmgr._session.load_dll")
    def test_restart_failure_raises(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that restart() raises RestartError."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmRestart.return_value = 352
        mock_load.return_value = mock_dll
        session = RmSession()
        session.start()

        # when / then
        with pytest.raises(RestartError):
            session.restart()


class TestRmSessionContextManager:
    """
    Tests `RmSession` context manager protocol.
    """

    @patch("restartmgr._session.load_dll")
    def test_context_manager_starts_and_ends(
        self,
        mock_load: MagicMock,
    ) -> None:
        """
        Tests that __enter__ calls start() and __exit__
        calls end().
        """

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmEndSession.return_value = 0
        mock_load.return_value = mock_dll

        # when
        with RmSession() as session:
            assert session.handle is not None

        # then
        mock_dll.RmStartSession.assert_called_once()
        mock_dll.RmEndSession.assert_called_once()

    @patch("restartmgr._session.load_dll")
    def test_context_manager_ends_on_exception(
        self,
        mock_load: MagicMock,
    ) -> None:
        """
        Tests that __exit__ is called even when an exception
        occurs inside the with-block.
        """

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmEndSession.return_value = 0
        mock_load.return_value = mock_dll

        # when / then
        with pytest.raises(RuntimeError), RmSession():
            raise RuntimeError("boom")

        mock_dll.RmEndSession.assert_called_once()

    @patch("restartmgr._session.load_dll")
    def test_context_manager_returns_self(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Tests that __enter__ returns the session itself."""

        # given
        mock_dll = MagicMock()
        mock_dll.RmStartSession.return_value = 0
        mock_dll.RmEndSession.return_value = 0
        mock_load.return_value = mock_dll
        session = RmSession()

        # when
        with session as ctx:
            result = ctx

        # then
        assert result is session
