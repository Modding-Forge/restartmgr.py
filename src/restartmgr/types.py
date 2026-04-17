"""
Copyright (c) Modding Forge
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Optional

from ._const import RmAppStatus, RmAppType, RmRebootReason


@dataclass(frozen=True, slots=True)
class ProcessInfo:
    """
    Immutable model describing a process that is using one or
    more registered resources.
    """

    pid: int
    """The process identifier."""

    start_time: Optional[datetime.datetime]
    """
    Process creation time (UTC), or `None` if unavailable.
    """

    app_name: str
    """
    Application name (or service long name for services).
    """

    service_short_name: Optional[str]
    """
    Service short name, or `None` if the process is not a
    service.
    """

    app_type: RmAppType
    """The type of the application."""

    app_status: RmAppStatus
    """Bitmask of the current application status."""

    ts_session_id: int
    """
    Terminal Services session ID, or `-1` if unknown.
    """

    restartable: bool
    """
    `True` if the application can be restarted by the
    Restart Manager.
    """


@dataclass(frozen=True, slots=True)
class GetListResult:
    """
    Immutable model wrapping the full result of an
    `RmGetList` call.
    """

    processes: list[ProcessInfo]
    """List of processes using registered resources."""

    reboot_reason: RmRebootReason
    """Flags describing why a reboot may be needed."""
