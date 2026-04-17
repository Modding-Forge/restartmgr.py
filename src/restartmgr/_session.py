"""
Copyright (c) Modding Forge
"""

from __future__ import annotations

import ctypes
import logging
from collections.abc import Callable
from typing import Optional

from ._const import (
    CCH_RM_SESSION_KEY,
    ERROR_MORE_DATA,
    ERROR_SUCCESS,
    RmRebootReason,
    RmShutdownType,
)
from ._dll import RM_WRITE_STATUS_CALLBACK, load_dll
from ._errors import (
    GetListError,
    ResourceRegistrationError,
    RestartError,
    SessionError,
    ShutdownError,
)
from ._structs import RM_PROCESS_INFO, RM_UNIQUE_PROCESS

log: logging.Logger = logging.getLogger("RmSession")
"""Module-level logger."""

_MAX_RETRY: int = 5
"""
Maximum number of retries for the `RmGetList` two-step
pattern when `ERROR_MORE_DATA` is returned.
"""


class RmSession:
    """
    Thin wrapper around a Restart Manager session.

    Manages the lifecycle of `RmStartSession` /
    `RmEndSession` and provides methods for resource
    registration, process listing, shutdown, and restart.
    """

    __handle: Optional[ctypes.c_uint32]
    __session_key: Optional[str]

    def __init__(self) -> None:
        """
        Creates an uninitialised session object.

        Call :meth:`start` to open the session.
        """

        self.__handle = None
        self.__session_key = None

    @property
    def handle(self) -> Optional[ctypes.c_uint32]:
        """
        The native session handle, or `None` if not started.

        Returns:
            Optional[ctypes.c_uint32]: Session handle.
        """

        return self.__handle

    @property
    def session_key(self) -> Optional[str]:
        """
        The session key string, or `None` if not started.

        Returns:
            Optional[str]: Session key.
        """

        return self.__session_key

    def start(self) -> None:
        """
        Opens a new Restart Manager session via
        `RmStartSession`.

        Raises:
            SessionError: If the DLL call fails.
        """

        dll = load_dll()
        handle = ctypes.c_uint32(0)
        key_buf = ctypes.create_unicode_buffer(
            CCH_RM_SESSION_KEY + 1,
        )
        result: int = dll.RmStartSession(
            ctypes.byref(handle),
            0,
            key_buf,
        )
        if result != ERROR_SUCCESS:
            raise SessionError(
                result,
                f"RmStartSession failed (code {result}).",
            )
        self.__handle = handle
        self.__session_key = key_buf.value
        log.debug(
            f"Session started: handle={handle.value}, "
            f"key='{self.__session_key}'",
        )

    def end(self) -> None:
        """
        Closes the Restart Manager session via
        `RmEndSession`.

        Safe to call even when the session is not started.

        Raises:
            SessionError: If the DLL call fails.
        """

        if self.__handle is None:
            return
        dll = load_dll()
        result: int = dll.RmEndSession(self.__handle)
        handle_val: int = self.__handle.value
        self.__handle = None
        self.__session_key = None
        if result != ERROR_SUCCESS:
            raise SessionError(
                result,
                f"RmEndSession failed (code {result}).",
            )
        log.debug(
            f"Session ended: handle={handle_val}",
        )

    def register_files(
        self,
        paths: list[str],
    ) -> None:
        """
        Registers file paths with the session.

        Args:
            paths (list[str]): Absolute file paths to register.

        Raises:
            SessionError: If no session is active.
            ResourceRegistrationError: If the DLL call fails.
        """

        self.__require_handle()
        if not paths:
            return
        dll = load_dll()
        arr = (ctypes.c_wchar_p * len(paths))(*paths)
        result: int = dll.RmRegisterResources(
            self.__handle,
            len(paths),
            arr,
            0,
            None,
            0,
            None,
        )
        if result != ERROR_SUCCESS:
            raise ResourceRegistrationError(
                result,
                "RmRegisterResources failed "
                f"(code {result}).",
            )
        log.debug(
            f"Registered {len(paths)} file(s).",
        )

    def register_processes(
        self,
        processes: list[RM_UNIQUE_PROCESS],
    ) -> None:
        """
        Registers processes with the session.

        Args:
            processes (list[RM_UNIQUE_PROCESS]): Processes to
                register.

        Raises:
            SessionError: If no session is active.
            ResourceRegistrationError: If the DLL call fails.
        """

        self.__require_handle()
        if not processes:
            return
        dll = load_dll()
        n: int = len(processes)
        arr = (RM_UNIQUE_PROCESS * n)(*processes)
        result: int = dll.RmRegisterResources(
            self.__handle,
            0,
            None,
            n,
            arr,
            0,
            None,
        )
        if result != ERROR_SUCCESS:
            raise ResourceRegistrationError(
                result,
                "RmRegisterResources failed "
                f"(code {result}).",
            )
        log.debug(
            f"Registered {n} process(es).",
        )

    def register_services(
        self,
        service_names: list[str],
    ) -> None:
        """
        Registers Windows service short names with the session.

        Args:
            service_names (list[str]): Service short names to
                register.

        Raises:
            SessionError: If no session is active.
            ResourceRegistrationError: If the DLL call fails.
        """

        self.__require_handle()
        if not service_names:
            return
        dll = load_dll()
        n: int = len(service_names)
        arr = (ctypes.c_wchar_p * n)(*service_names)
        result: int = dll.RmRegisterResources(
            self.__handle,
            0,
            None,
            0,
            None,
            n,
            arr,
        )
        if result != ERROR_SUCCESS:
            raise ResourceRegistrationError(
                result,
                "RmRegisterResources failed "
                f"(code {result}).",
            )
        log.debug(
            f"Registered {n} service(s).",
        )

    def get_list(
        self,
    ) -> tuple[list[RM_PROCESS_INFO], RmRebootReason]:
        """
        Retrieves the list of affected applications and
        services via the `RmGetList` two-step pattern.

        Returns:
            tuple[list[RM_PROCESS_INFO], RmRebootReason]:
                A tuple of the process info list and the
                reboot reason flags.

        Raises:
            SessionError: If no session is active.
            GetListError: If the DLL call fails after retries.
        """

        self.__require_handle()
        dll = load_dll()

        for _ in range(_MAX_RETRY):
            needed = ctypes.c_uint(0)
            count = ctypes.c_uint(0)
            reboot = ctypes.c_uint32(0)

            result: int = dll.RmGetList(
                self.__handle,
                ctypes.byref(needed),
                ctypes.byref(count),
                None,
                ctypes.byref(reboot),
            )

            if (
                result == ERROR_SUCCESS
                and needed.value == 0
            ):
                return (
                    [],
                    RmRebootReason(reboot.value),
                )

            if result not in (
                ERROR_SUCCESS,
                ERROR_MORE_DATA,
            ):
                raise GetListError(
                    result,
                    f"RmGetList failed (code {result}).",
                )

            buf_size: int = needed.value
            buf = (RM_PROCESS_INFO * buf_size)()
            count = ctypes.c_uint(buf_size)
            reboot = ctypes.c_uint32(0)

            result = dll.RmGetList(
                self.__handle,
                ctypes.byref(needed),
                ctypes.byref(count),
                buf,
                ctypes.byref(reboot),
            )

            if result == ERROR_SUCCESS:
                infos: list[RM_PROCESS_INFO] = list(
                    buf[: count.value]
                )
                log.debug(
                    f"RmGetList returned {count.value} "
                    f"process(es).",
                )
                return (
                    infos,
                    RmRebootReason(reboot.value),
                )

            if result == ERROR_MORE_DATA:
                log.debug(
                    "RmGetList returned ERROR_MORE_DATA, "
                    "retrying.",
                )
                continue

            raise GetListError(
                result,
                f"RmGetList failed (code {result}).",
            )

        raise GetListError(
            ERROR_MORE_DATA,
            "RmGetList: buffer was never large enough "
            f"after {_MAX_RETRY} retries.",
        )

    def shutdown(
        self,
        action_flags: RmShutdownType = (
            RmShutdownType.FORCE_SHUTDOWN
        ),
        status_callback: Optional[
            Callable[[int], None]
        ] = None,
    ) -> None:
        """
        Shuts down applications via `RmShutdown`.

        Args:
            action_flags (RmShutdownType): Shutdown behaviour
                flags.
            status_callback
                (Optional[Callable[[int], None]]):
                Optional progress callback.

        Raises:
            SessionError: If no session is active.
            ShutdownError: If the DLL call fails.
        """

        self.__require_handle()
        dll = load_dll()
        cb = (
            RM_WRITE_STATUS_CALLBACK(status_callback)
            if status_callback is not None
            else RM_WRITE_STATUS_CALLBACK(0)
        )
        result: int = dll.RmShutdown(
            self.__handle,
            action_flags,
            cb,
        )
        if result != ERROR_SUCCESS:
            raise ShutdownError(
                result,
                f"RmShutdown failed (code {result}).",
            )
        log.debug("RmShutdown completed successfully.")

    def restart(
        self,
        status_callback: Optional[
            Callable[[int], None]
        ] = None,
    ) -> None:
        """
        Restarts applications via `RmRestart`.

        Args:
            status_callback
                (Optional[Callable[[int], None]]):
                Optional progress callback.

        Raises:
            SessionError: If no session is active.
            RestartError: If the DLL call fails.
        """

        self.__require_handle()
        dll = load_dll()
        cb = (
            RM_WRITE_STATUS_CALLBACK(status_callback)
            if status_callback is not None
            else RM_WRITE_STATUS_CALLBACK(0)
        )
        result: int = dll.RmRestart(
            self.__handle,
            0,
            cb,
        )
        if result != ERROR_SUCCESS:
            raise RestartError(
                result,
                f"RmRestart failed (code {result}).",
            )
        log.debug("RmRestart completed successfully.")

    def __require_handle(self) -> None:
        """
        Asserts that the session has been started.

        Raises:
            SessionError: If no session is active.
        """

        if self.__handle is None:
            raise SessionError(
                0,
                "No active session. Call start() first.",
            )

    def __enter__(self) -> RmSession:
        """
        Starts the session and returns `self`.

        Returns:
            RmSession: This session instance.
        """

        self.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: object,
    ) -> None:
        """
        Ends the session unconditionally.

        Args:
            exc_type (Optional[type[BaseException]]): The
                exception type, if any.
            exc_val (Optional[BaseException]): The exception
                value, if any.
            exc_tb (object): The traceback, if any.
        """

        self.end()
