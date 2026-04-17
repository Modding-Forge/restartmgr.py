"""
Copyright (c) Modding Forge
"""

from __future__ import annotations

import ctypes

from ._const import CCH_RM_MAX_APP_NAME, CCH_RM_MAX_SVC_NAME


class FILETIME(ctypes.Structure):
    """
    Mirrors the Win32 `FILETIME` structure (two 32-bit parts).
    """

    _fields_ = [  # pyright: ignore[reportIncompatibleVariableOverride]
        ("dwLowDateTime", ctypes.c_uint32),
        ("dwHighDateTime", ctypes.c_uint32),
    ]


class RM_UNIQUE_PROCESS(ctypes.Structure):
    """
    Uniquely identifies a process by its PID and start time.

    Maps to the native `RM_UNIQUE_PROCESS` structure defined in
    `restartmanager.h`.
    """

    _fields_ = [  # pyright: ignore[reportIncompatibleVariableOverride]
        ("dwProcessId", ctypes.c_uint32),
        ("ProcessStartTime", FILETIME),
    ]


class RM_PROCESS_INFO(ctypes.Structure):
    """
    Describes an application registered with the Restart Manager.

    Maps to the native `RM_PROCESS_INFO` structure defined in
    `restartmanager.h`.
    """

    _fields_ = [  # pyright: ignore[reportIncompatibleVariableOverride]
        ("Process", RM_UNIQUE_PROCESS),
        (
            "strAppName",
            ctypes.c_wchar * (CCH_RM_MAX_APP_NAME + 1),
        ),
        (
            "strServiceShortName",
            ctypes.c_wchar * (CCH_RM_MAX_SVC_NAME + 1),
        ),
        ("ApplicationType", ctypes.c_uint32),
        ("AppStatus", ctypes.c_ulong),
        ("TSSessionId", ctypes.c_uint32),
        ("bRestartable", ctypes.c_int32),
    ]
