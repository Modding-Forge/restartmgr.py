"""
Copyright (c) Modding Forge
"""

from unittest.mock import MagicMock, patch

import pytest

from restartmgr._dll import RM_WRITE_STATUS_CALLBACK, load_dll
from restartmgr._errors import DllLoadError


class TestLoadDll:
    """
    Tests `restartmgr._dll.load_dll()`.
    """

    @patch("restartmgr._dll._dll_instance", None)
    @patch("restartmgr._dll.ctypes")
    def test_load_success(
        self,
        mock_ctypes: MagicMock,
    ) -> None:
        """Tests that load_dll() returns a WinDLL handle."""

        # given
        mock_dll = MagicMock()
        mock_ctypes.WinDLL.return_value = mock_dll

        # when
        result = load_dll()

        # then
        assert result is mock_dll
        mock_ctypes.WinDLL.assert_called_once_with(
            "rstrtmgr.dll",
        )

    @patch("restartmgr._dll._dll_instance", None)
    @patch(
        "restartmgr._dll.ctypes.WinDLL",
        side_effect=OSError("not found"),
    )
    def test_load_failure_raises_dll_load_error(
        self,
        mock_windll: MagicMock,
    ) -> None:
        """
        Tests that load_dll() raises DllLoadError when the
        DLL cannot be loaded.
        """

        # given / when / then
        with pytest.raises(DllLoadError) as exc_info:
            load_dll()
        assert "rstrtmgr.dll" in str(exc_info.value)

    def test_singleton_returns_cached(self) -> None:
        """
        Tests that load_dll() returns the cached instance
        when already loaded.
        """

        # given
        sentinel = MagicMock()
        with patch(
            "restartmgr._dll._dll_instance",
            sentinel,
        ):
            # when
            result = load_dll()

        # then
        assert result is sentinel


class TestWriteStatusCallback:
    """
    Tests `RM_WRITE_STATUS_CALLBACK` ctypes function type.
    """

    def test_callback_is_callable_type(self) -> None:
        """Tests that the callback type can be instantiated."""

        # given
        called_with: list[int] = []

        def on_status(percent: int) -> None:
            """Dummy callback."""

            called_with.append(percent)

        # when
        cb = RM_WRITE_STATUS_CALLBACK(on_status)

        # then - invoke it
        cb(50)
        assert called_with == [50]

    def test_null_callback(self) -> None:
        """Tests creating a null callback with 0."""

        # given / when
        cb = RM_WRITE_STATUS_CALLBACK(0)

        # then - should not raise on creation
        assert cb is not None
