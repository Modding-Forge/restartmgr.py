"""
Copyright (c) Modding Forge
"""

from __future__ import annotations

import pytest

from restartmgr._errors import (
    DllLoadError,
    GetListError,
    ResourceRegistrationError,
    RestartError,
    RestartManagerError,
    SessionError,
    ShutdownError,
)


class TestExceptionHierarchy:
    """
    Tests the exception class hierarchy in
    `restartmgr._errors`.
    """

    def test_base_is_exception(self) -> None:
        """Tests that RestartManagerError inherits Exception."""

        # given / when / then
        assert issubclass(RestartManagerError, Exception)

    def test_dll_load_error_is_subclass(self) -> None:
        """Tests DllLoadError is a RestartManagerError."""

        # given / when / then
        assert issubclass(
            DllLoadError, RestartManagerError,
        )

    def test_session_error_is_subclass(self) -> None:
        """Tests SessionError is a RestartManagerError."""

        # given / when / then
        assert issubclass(
            SessionError, RestartManagerError,
        )

    def test_resource_registration_error(self) -> None:
        """
        Tests ResourceRegistrationError is a
        RestartManagerError.
        """

        # given / when / then
        assert issubclass(
            ResourceRegistrationError,
            RestartManagerError,
        )

    def test_get_list_error_is_subclass(self) -> None:
        """Tests GetListError is a RestartManagerError."""

        # given / when / then
        assert issubclass(
            GetListError, RestartManagerError,
        )

    def test_shutdown_error_is_subclass(self) -> None:
        """Tests ShutdownError is a RestartManagerError."""

        # given / when / then
        assert issubclass(
            ShutdownError, RestartManagerError,
        )

    def test_restart_error_is_subclass(self) -> None:
        """Tests RestartError is a RestartManagerError."""

        # given / when / then
        assert issubclass(
            RestartError, RestartManagerError,
        )

    def test_all_catchable_by_base(self) -> None:
        """
        Tests that every subclass exception can be caught
        as RestartManagerError.
        """

        # given
        classes: list[type[RestartManagerError]] = [
            DllLoadError,
            SessionError,
            ResourceRegistrationError,
            GetListError,
            ShutdownError,
            RestartError,
        ]

        # when / then
        for cls in classes:
            if cls is DllLoadError:  # noqa: SIM108
                err = cls("test")
            else:
                err = cls(42, "test")  # type: ignore[arg-type]
            with pytest.raises(RestartManagerError):
                raise err


class TestDllLoadError:
    """
    Tests `DllLoadError`.
    """

    def test_message(self) -> None:
        """Tests that the message is stored correctly."""

        # given
        err = DllLoadError("not found")

        # when / then
        assert str(err) == "not found"

    def test_no_error_code_attribute(self) -> None:
        """Tests that DllLoadError has no error_code."""

        # given
        err = DllLoadError("oops")

        # when / then
        assert not hasattr(err, "error_code")


class TestSessionError:
    """
    Tests `SessionError`.
    """

    def test_error_code_property(self) -> None:
        """Tests that error_code returns the stored code."""

        # given
        err = SessionError(42, "test")

        # when
        code: int = err.error_code

        # then
        assert code == 42

    def test_default_message(self) -> None:
        """Tests the auto-generated default message."""

        # given
        err = SessionError(7)

        # when
        msg: str = str(err)

        # then
        assert "7" in msg

    def test_custom_message(self) -> None:
        """Tests that a custom message overrides default."""

        # given
        err = SessionError(99, "custom failure")

        # when / then
        assert str(err) == "custom failure"


class TestResourceRegistrationError:
    """
    Tests `ResourceRegistrationError`.
    """

    def test_error_code_property(self) -> None:
        """Tests error_code property access."""

        # given
        err = ResourceRegistrationError(160)

        # when / then
        assert err.error_code == 160

    def test_default_message_contains_code(self) -> None:
        """Tests the default message includes the code."""

        # given
        err = ResourceRegistrationError(160)

        # when / then
        assert "160" in str(err)


class TestGetListError:
    """
    Tests `GetListError`.
    """

    def test_error_code_property(self) -> None:
        """Tests error_code property access."""

        # given
        err = GetListError(234)

        # when / then
        assert err.error_code == 234

    def test_custom_message(self) -> None:
        """Tests custom message."""

        # given
        err = GetListError(5, "access denied")

        # when / then
        assert str(err) == "access denied"


class TestShutdownError:
    """
    Tests `ShutdownError`.
    """

    def test_error_code_property(self) -> None:
        """Tests error_code property access."""

        # given
        err = ShutdownError(351)

        # when / then
        assert err.error_code == 351

    def test_default_message(self) -> None:
        """Tests the default message."""

        # given
        err = ShutdownError(351)

        # when / then
        assert "351" in str(err)


class TestRestartError:
    """
    Tests `RestartError`.
    """

    def test_error_code_property(self) -> None:
        """Tests error_code property access."""

        # given
        err = RestartError(352)

        # when / then
        assert err.error_code == 352

    def test_default_message(self) -> None:
        """Tests the default message."""

        # given
        err = RestartError(776)

        # when / then
        assert "776" in str(err)
