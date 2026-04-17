"""
Copyright (c) Modding Forge
"""

import ctypes
import logging
import threading
from typing import Optional

from ._const import CCH_RM_SESSION_KEY
from ._errors import DllLoadError
from ._structs import RM_PROCESS_INFO, RM_UNIQUE_PROCESS

log: logging.Logger = logging.getLogger("restartmgr.dll")
"""Module-level logger."""

_dll_instance: Optional[ctypes.WinDLL] = None
"""Module-level singleton handle for the loaded rstrtmgr.dll."""

_dll_lock: threading.Lock = threading.Lock()
"""Lock guarding the lazy initialisation of `_dll_instance`."""

RM_WRITE_STATUS_CALLBACK = ctypes.WINFUNCTYPE(
    None,
    ctypes.c_uint32,
)
"""
Callback type for `RM_WRITE_STATUS_CALLBACK`.

The callback receives a single `UINT` percentage argument.
"""


def load_dll() -> ctypes.WinDLL:
    """
    Loads `rstrtmgr.dll` and caches it in a module-level
    singleton.

    The DLL is only loaded once; subsequent calls return the
    cached handle.

    Returns:
        ctypes.WinDLL: The loaded DLL handle.

    Raises:
        DllLoadError: If the DLL cannot be loaded.
    """

    global _dll_instance
    if _dll_instance is not None:
        return _dll_instance

    with _dll_lock:
        if _dll_instance is not None:
            return _dll_instance

        try:
            dll = ctypes.WinDLL("rstrtmgr.dll")
        except OSError as exc:
            raise DllLoadError(
                f"Failed to load rstrtmgr.dll: {exc}"
            ) from exc

        _configure_exports(dll)
        _dll_instance = dll
        log.debug("rstrtmgr.dll loaded successfully.")
        return dll


def _configure_exports(dll: ctypes.WinDLL) -> None:
    """
    Sets argument and return types for all used
    `rstrtmgr.dll` exports.

    Args:
        dll (ctypes.WinDLL): The loaded DLL handle.
    """

    # DWORD RmStartSession(
    #   DWORD *pSessionHandle,
    #   DWORD dwSessionFlags,
    #   WCHAR[] strSessionKey
    # )
    dll.RmStartSession.restype = ctypes.c_uint32
    dll.RmStartSession.argtypes = [
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.c_uint32,
        ctypes.c_wchar * (CCH_RM_SESSION_KEY + 1),
    ]

    # DWORD RmEndSession(DWORD dwSessionHandle)
    dll.RmEndSession.restype = ctypes.c_uint32
    dll.RmEndSession.argtypes = [
        ctypes.c_uint32,
    ]

    # DWORD RmRegisterResources(
    #   DWORD dwSessionHandle,
    #   UINT nFiles,
    #   LPCWSTR[] rgsFileNames,
    #   UINT nApplications,
    #   RM_UNIQUE_PROCESS[] rgApplications,
    #   UINT nServices,
    #   LPCWSTR[] rgsServiceNames
    # )
    dll.RmRegisterResources.restype = ctypes.c_uint32
    dll.RmRegisterResources.argtypes = [
        ctypes.c_uint32,
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_wchar_p),
        ctypes.c_uint,
        ctypes.POINTER(RM_UNIQUE_PROCESS),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_wchar_p),
    ]

    # DWORD RmGetList(
    #   DWORD dwSessionHandle,
    #   UINT *pnProcInfoNeeded,
    #   UINT *pnProcInfo,
    #   RM_PROCESS_INFO[] rgAffectedApps,
    #   LPDWORD lpdwRebootReasons
    # )
    dll.RmGetList.restype = ctypes.c_uint32
    dll.RmGetList.argtypes = [
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.POINTER(RM_PROCESS_INFO),
        ctypes.POINTER(ctypes.c_uint32),
    ]

    # DWORD RmShutdown(
    #   DWORD dwSessionHandle,
    #   ULONG lActionFlags,
    #   RM_WRITE_STATUS_CALLBACK fnStatus
    # )
    dll.RmShutdown.restype = ctypes.c_uint32
    dll.RmShutdown.argtypes = [
        ctypes.c_uint32,
        ctypes.c_ulong,
        RM_WRITE_STATUS_CALLBACK,
    ]

    # DWORD RmRestart(
    #   DWORD dwSessionHandle,
    #   DWORD dwRestartFlags,
    #   RM_WRITE_STATUS_CALLBACK fnStatus
    # )
    dll.RmRestart.restype = ctypes.c_uint32
    dll.RmRestart.argtypes = [
        ctypes.c_uint32,
        ctypes.c_uint32,
        RM_WRITE_STATUS_CALLBACK,
    ]
