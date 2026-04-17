"""
Copyright (c) Modding Forge
"""

from __future__ import annotations


class RestartManagerError(Exception):
    """
    Base exception for all restartmgr errors.
    """

    pass


class DllLoadError(RestartManagerError):
    """
    Raised when `rstrtmgr.dll` cannot be loaded.
    """

    pass


class SessionError(RestartManagerError):
    """
    Raised when a session operation fails (start / join / end).
    """

    __error_code: int

    def __init__(
        self,
        error_code: int,
        message: str = "",
    ) -> None:
        """
        Initialises the error with a Win32 error code.

        Args:
            error_code (int): The Win32 error code returned by
                the Restart Manager function.
            message (str): Optional human-readable description.
        """

        self.__error_code = error_code
        super().__init__(
            message
            or f"Session error (code {error_code})"
        )

    @property
    def error_code(self) -> int:
        """
        The Win32 error code that caused the exception.

        Returns:
            int: Win32 error code.
        """

        return self.__error_code


class ResourceRegistrationError(RestartManagerError):
    """
    Raised when resource registration via
    `RmRegisterResources` fails.
    """

    __error_code: int

    def __init__(
        self,
        error_code: int,
        message: str = "",
    ) -> None:
        """
        Initialises the error with a Win32 error code.

        Args:
            error_code (int): The Win32 error code returned by
                `RmRegisterResources`.
            message (str): Optional human-readable description.
        """

        self.__error_code = error_code
        super().__init__(
            message
            or (
                "Resource registration error "
                f"(code {error_code})"
            )
        )

    @property
    def error_code(self) -> int:
        """
        The Win32 error code that caused the exception.

        Returns:
            int: Win32 error code.
        """

        return self.__error_code


class GetListError(RestartManagerError):
    """
    Raised when `RmGetList` fails with an unrecoverable error.
    """

    __error_code: int

    def __init__(
        self,
        error_code: int,
        message: str = "",
    ) -> None:
        """
        Initialises the error with a Win32 error code.

        Args:
            error_code (int): The Win32 error code returned by
                `RmGetList`.
            message (str): Optional human-readable description.
        """

        self.__error_code = error_code
        super().__init__(
            message
            or f"RmGetList error (code {error_code})"
        )

    @property
    def error_code(self) -> int:
        """
        The Win32 error code that caused the exception.

        Returns:
            int: Win32 error code.
        """

        return self.__error_code


class ShutdownError(RestartManagerError):
    """
    Raised when `RmShutdown` fails.
    """

    __error_code: int

    def __init__(
        self,
        error_code: int,
        message: str = "",
    ) -> None:
        """
        Initialises the error with a Win32 error code.

        Args:
            error_code (int): The Win32 error code returned by
                `RmShutdown`.
            message (str): Optional human-readable description.
        """

        self.__error_code = error_code
        super().__init__(
            message
            or f"RmShutdown error (code {error_code})"
        )

    @property
    def error_code(self) -> int:
        """
        The Win32 error code that caused the exception.

        Returns:
            int: Win32 error code.
        """

        return self.__error_code


class RestartError(RestartManagerError):
    """
    Raised when `RmRestart` fails.
    """

    __error_code: int

    def __init__(
        self,
        error_code: int,
        message: str = "",
    ) -> None:
        """
        Initialises the error with a Win32 error code.

        Args:
            error_code (int): The Win32 error code returned by
                `RmRestart`.
            message (str): Optional human-readable description.
        """

        self.__error_code = error_code
        super().__init__(
            message
            or f"RmRestart error (code {error_code})"
        )

    @property
    def error_code(self) -> int:
        """
        The Win32 error code that caused the exception.

        Returns:
            int: Win32 error code.
        """

        return self.__error_code
