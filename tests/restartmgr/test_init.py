"""
Copyright (c) Modding Forge
"""

import restartmgr


class TestPublicExports:
    """
    Tests that all expected symbols are exported from the
    `restartmgr` package.
    """

    def test_all_list(self) -> None:
        """Tests that __all__ contains the expected symbols."""

        # given
        expected: set[str] = {
            "DllLoadError",
            "GetListError",
            "GetListResult",
            "ProcessInfo",
            "ResourceRegistrationError",
            "RestartError",
            "RestartManagerError",
            "RmAppStatus",
            "RmAppType",
            "RmRebootReason",
            "RmSession",
            "RmShutdownType",
            "SessionError",
            "ShutdownError",
            "get_locking_processes",
            "who_locks",
        }

        # when
        actual: set[str] = set(restartmgr.__all__)

        # then
        assert actual == expected

    def test_who_locks_importable(self) -> None:
        """Tests that who_locks is importable."""

        # given / when / then
        assert callable(restartmgr.who_locks)

    def test_get_locking_processes_importable(self) -> None:
        """Tests that get_locking_processes is importable."""

        # given / when / then
        assert callable(restartmgr.get_locking_processes)

    def test_rm_session_importable(self) -> None:
        """Tests that RmSession is importable."""

        # given / when / then
        assert restartmgr.RmSession is not None

    def test_all_exceptions_importable(self) -> None:
        """Tests that all exception classes are importable."""

        # given
        classes: list[type] = [
            restartmgr.RestartManagerError,
            restartmgr.DllLoadError,
            restartmgr.SessionError,
            restartmgr.ResourceRegistrationError,
            restartmgr.GetListError,
            restartmgr.ShutdownError,
            restartmgr.RestartError,
        ]

        # when / then
        for cls in classes:
            assert issubclass(cls, Exception)

    def test_all_enums_importable(self) -> None:
        """Tests that all enum types are importable."""

        # given / when / then
        assert restartmgr.RmAppType is not None
        assert restartmgr.RmAppStatus is not None
        assert restartmgr.RmRebootReason is not None
        assert restartmgr.RmShutdownType is not None

    def test_all_models_importable(self) -> None:
        """Tests that all model classes are importable."""

        # given / when / then
        assert restartmgr.ProcessInfo is not None
        assert restartmgr.GetListResult is not None
