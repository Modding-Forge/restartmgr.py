"""
Copyright (c) Modding Forge
"""


class RestartManagerError(Exception):
    """
    Base exception for all restartmgr errors.
    """

    _error_code: int

    def __init__(
        self,
        error_code: int = 0,
        message: str = "",
    ) -> None:
        """
        Initialises the error with a Win32 error code.

        Args:
            error_code (int): The Win32 error code returned
                by the Restart Manager function.
            message (str): Optional human-readable
                description.
        """

        self._error_code = error_code
        super().__init__(
            message
            or f"Restart Manager error "
            f"(code {error_code})"
        )

    @property
    def error_code(self) -> int:
        """
        The Win32 error code that caused the exception.

        Returns:
            int: Win32 error code.
        """

        return self._error_code


class DllLoadError(RestartManagerError):
    """
    Raised when `rstrtmgr.dll` cannot be loaded.
    """

    def __init__(self, message: str = "") -> None:
        """
        Initialises the error with a message.

        Args:
            message (str): Human-readable description.
        """

        super().__init__(0, message)


class SessionError(RestartManagerError):
    """
    Raised when a session operation fails
    (start / join / end).
    """

    pass


class ResourceRegistrationError(RestartManagerError):
    """
    Raised when resource registration via
    `RmRegisterResources` fails.
    """

    pass


class GetListError(RestartManagerError):
    """
    Raised when `RmGetList` fails with an unrecoverable
    error.
    """

    pass


class ShutdownError(RestartManagerError):
    """
    Raised when `RmShutdown` fails.
    """

    pass


class RestartError(RestartManagerError):
    """
    Raised when `RmRestart` fails.
    """

    pass
