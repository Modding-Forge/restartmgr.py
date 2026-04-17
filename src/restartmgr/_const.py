"""
Copyright (c) Modding Forge
"""

from enum import IntEnum, IntFlag

CCH_RM_SESSION_KEY: int = 32
"""Maximum number of characters in a session key string."""

CCH_RM_MAX_APP_NAME: int = 255
"""Maximum number of characters in an application name."""

CCH_RM_MAX_SVC_NAME: int = 63
"""Maximum number of characters in a service short name."""

RM_INVALID_TS_SESSION: int = -1
"""
Sentinel value for an unknown Terminal Services session ID.
"""

RM_INVALID_PROCESS: int = -1
"""
Sentinel value for an invalid process ID.
"""


class RmAppType(IntEnum):
    """
    Specifies the type of application described by an
    `RM_PROCESS_INFO` structure.
    """

    UNKNOWN = 0
    """The application cannot be classified."""

    MAIN_WINDOW = 1
    """A stand-alone Windows application with a top-level window."""

    OTHER_WINDOW = 2
    """A Windows application without a top-level window."""

    SERVICE = 3
    """A Windows service."""

    EXPLORER = 4
    """Windows Explorer."""

    CONSOLE = 5
    """A stand-alone console application."""

    CRITICAL = 1000
    """
    A critical process that cannot be shut down without a
    system restart.
    """


class RmAppStatus(IntFlag):
    """
    Bitmask describing the current status of an application
    acted upon by the Restart Manager.
    """

    UNKNOWN = 0x0
    """Status is unknown."""

    RUNNING = 0x1
    """The application is currently running."""

    STOPPED = 0x2
    """The Restart Manager has stopped the application."""

    STOPPED_OTHER = 0x4
    """An external action has stopped the application."""

    RESTARTED = 0x8
    """The Restart Manager has restarted the application."""

    ERROR_ON_STOP = 0x10
    """Error encountered when stopping the application."""

    ERROR_ON_RESTART = 0x20
    """Error encountered when restarting the application."""

    SHUTDOWN_MASKED = 0x40
    """Shutdown is masked by a filter."""

    RESTART_MASKED = 0x80
    """Restart is masked by a filter."""


class RmRebootReason(IntFlag):
    """
    Describes why a system restart is needed.
    """

    NONE = 0x0
    """No restart required."""

    PERMISSION_DENIED = 0x1
    """Insufficient privileges to shut down a process."""

    SESSION_MISMATCH = 0x2
    """Processes are running in another TS session."""

    CRITICAL_PROCESS = 0x4
    """A critical process must be shut down."""

    CRITICAL_SERVICE = 0x8
    """A critical service must be shut down."""

    DETECTED_SELF = 0x10
    """The current process must be shut down."""


class RmShutdownType(IntFlag):
    """
    Configures the shutdown behaviour for `RmShutdown`.
    """

    FORCE_SHUTDOWN = 0x1
    """
    Force unresponsive applications and services to shut down
    after the timeout period.
    """

    SHUTDOWN_ONLY_REGISTERED = 0x10
    """
    Shut down applications only if all have been registered
    for restart.
    """


ERROR_SUCCESS: int = 0
"""The function completed successfully."""

ERROR_ACCESS_DENIED: int = 5
"""Access denied."""

ERROR_INVALID_HANDLE: int = 6
"""Invalid handle."""

ERROR_OUTOFMEMORY: int = 14
"""Not enough memory."""

ERROR_WRITE_FAULT: int = 29
"""Cannot write to the specified device."""

ERROR_SEM_TIMEOUT: int = 121
"""Registry write mutex timeout."""

ERROR_BAD_ARGUMENTS: int = 160
"""One or more arguments are incorrect."""

ERROR_MORE_DATA: int = 234
"""Buffer too small; more data is available."""

ERROR_FAIL_NOACTION_REBOOT: int = 350
"""
No shutdown performed; a system restart is required first.
"""

ERROR_FAIL_SHUTDOWN: int = 351
"""Some applications could not be shut down."""

ERROR_FAIL_RESTART: int = 352
"""One or more applications could not be restarted."""

ERROR_MAX_SESSIONS_REACHED: int = 353
"""Maximum number of sessions has been reached."""

ERROR_REQUEST_OUT_OF_SEQUENCE: int = 776
"""
`RmRestart` called before `RmShutdown`.
"""

ERROR_CANCELLED: int = 1223
"""The current operation was cancelled by the user."""

WIN32_ERROR_NAMES: dict[int, str] = {
    ERROR_SUCCESS: "ERROR_SUCCESS",
    ERROR_ACCESS_DENIED: "ERROR_ACCESS_DENIED",
    ERROR_INVALID_HANDLE: "ERROR_INVALID_HANDLE",
    ERROR_OUTOFMEMORY: "ERROR_OUTOFMEMORY",
    ERROR_WRITE_FAULT: "ERROR_WRITE_FAULT",
    ERROR_SEM_TIMEOUT: "ERROR_SEM_TIMEOUT",
    ERROR_BAD_ARGUMENTS: "ERROR_BAD_ARGUMENTS",
    ERROR_MORE_DATA: "ERROR_MORE_DATA",
    ERROR_FAIL_NOACTION_REBOOT: "ERROR_FAIL_NOACTION_REBOOT",
    ERROR_FAIL_SHUTDOWN: "ERROR_FAIL_SHUTDOWN",
    ERROR_FAIL_RESTART: "ERROR_FAIL_RESTART",
    ERROR_MAX_SESSIONS_REACHED: "ERROR_MAX_SESSIONS_REACHED",
    ERROR_REQUEST_OUT_OF_SEQUENCE: (
        "ERROR_REQUEST_OUT_OF_SEQUENCE"
    ),
    ERROR_CANCELLED: "ERROR_CANCELLED",
}
"""Maps Win32 error codes to their symbolic names."""
