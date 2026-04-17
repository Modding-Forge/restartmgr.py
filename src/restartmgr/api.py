"""
Copyright (c) Modding Forge
"""

from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import Optional

from ._const import (
    RmAppStatus,
    RmAppType,
)
from ._session import RmSession
from ._structs import RM_PROCESS_INFO
from .types import GetListResult, ProcessInfo

log: logging.Logger = logging.getLogger("restartmgr.api")
"""Module-level logger."""

_FILETIME_EPOCH: datetime.datetime = datetime.datetime(
    1601, 1, 1, tzinfo=datetime.UTC,
)
"""Windows FILETIME epoch (1 January 1601 UTC)."""


def _filetime_to_datetime(
    low: int,
    high: int,
) -> Optional[datetime.datetime]:
    """
    Converts a Win32 `FILETIME` (two 32-bit parts) to a
    Python `datetime` in UTC.

    Returns `None` when both parts are zero (= not set).

    Args:
        low (int): Low 32-bit part of the FILETIME.
        high (int): High 32-bit part of the FILETIME.

    Returns:
        Optional[datetime.datetime]: The converted datetime
            or `None`.
    """

    if low == 0 and high == 0:
        return None
    ticks: int = (high << 32) | low
    microseconds: int = ticks // 10
    return _FILETIME_EPOCH + datetime.timedelta(
        microseconds=microseconds,
    )


def _convert_process_info(
    raw: RM_PROCESS_INFO,
) -> ProcessInfo:
    """
    Converts a raw ctypes `RM_PROCESS_INFO` structure into
    a :class:`ProcessInfo` dataclass instance.

    Args:
        raw (RM_PROCESS_INFO): The native structure.

    Returns:
        ProcessInfo: Converted model instance.
    """

    ft = raw.Process.ProcessStartTime
    svc: str = raw.strServiceShortName
    return ProcessInfo(
        pid=raw.Process.dwProcessId,
        start_time=_filetime_to_datetime(
            ft.dwLowDateTime,
            ft.dwHighDateTime,
        ),
        app_name=raw.strAppName,
        service_short_name=svc if svc else None,
        app_type=RmAppType(raw.ApplicationType),
        app_status=RmAppStatus(raw.AppStatus),
        ts_session_id=raw.TSSessionId,
        restartable=bool(raw.bRestartable),
    )


def who_locks(
    *paths: str | Path,
) -> list[ProcessInfo]:
    """
    Returns a list of processes that are currently locking
    the given file path(s).

    This is the primary high-level convenience function.
    It opens a Restart Manager session, registers the
    path(s), queries the process list, and closes the session
    in a `finally` block.

    Args:
        *paths (str | Path): One or more absolute file paths.

    Returns:
        list[ProcessInfo]: Processes locking the files. An
            empty list means no process holds a lock.

    Raises:
        ValueError: If no paths are provided.
        restartmgr.RestartManagerError: On any Restart Manager
            failure.
    """

    if not paths:
        raise ValueError(
            "At least one file path must be provided."
        )

    str_paths: list[str] = [str(p) for p in paths]
    session = RmSession()
    try:
        session.start()
        session.register_files(str_paths)
        infos, _ = session.get_list()
        return [_convert_process_info(i) for i in infos]
    finally:
        session.end()


def get_locking_processes(
    *paths: str | Path,
) -> GetListResult:
    """
    Like :func:`who_locks` but returns the full result
    including the reboot-reason flags.

    Args:
        *paths (str | Path): One or more absolute file paths.

    Returns:
        GetListResult: Full result with processes and reboot
            reason.

    Raises:
        ValueError: If no paths are provided.
        restartmgr.RestartManagerError: On any Restart Manager
            failure.
    """

    if not paths:
        raise ValueError(
            "At least one file path must be provided."
        )

    str_paths: list[str] = [str(p) for p in paths]
    session = RmSession()
    try:
        session.start()
        session.register_files(str_paths)
        infos, reason = session.get_list()
        processes: list[ProcessInfo] = [
            _convert_process_info(i) for i in infos
        ]
        return GetListResult(
            processes=processes,
            reboot_reason=reason,
        )
    finally:
        session.end()
