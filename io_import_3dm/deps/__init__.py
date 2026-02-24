"""
Dependency bootstrap for rhino3dm.

Blender ships its own isolated Python, so rhino3dm must be either:
1. Already installed in Blender's Python (via Blender 4.2+ extension wheels)
2. Extracted from a bundled wheel at runtime

This module handles both cases, including macOS quarantine stripping.
"""

import importlib
import os
import platform
import subprocess
import sys
import zipfile

WHEELS_DIR = os.path.join(os.path.dirname(__file__), 'wheels')
EXTRACT_DIR = os.path.join(os.path.dirname(__file__), '_extracted')

_rhino3dm_error = None


def ensure_rhino3dm():
    """
    Ensure rhino3dm is importable. Returns (success: bool, error: str | None).

    Tries in order:
    1. Direct import (already available)
    2. Extract bundled wheel for this platform/Python version
    3. Report failure with diagnostic message
    """
    global _rhino3dm_error

    # 1. Already importable
    try:
        importlib.import_module('rhino3dm')
        return True, None
    except ImportError:
        pass

    # 2. Try extracting from bundled wheel
    wheel = _pick_wheel()
    if wheel is None:
        py_ver = f'{sys.version_info.major}.{sys.version_info.minor}'
        machine = platform.machine()
        _rhino3dm_error = (
            f'No compatible rhino3dm wheel found for '
            f'Python {py_ver} on {sys.platform}/{machine}. '
            f'Check that wheels are bundled in {WHEELS_DIR}'
        )
        return False, _rhino3dm_error

    _extract_wheel(wheel)

    # macOS: strip quarantine attribute from extracted .so/.dylib files
    if sys.platform == 'darwin':
        _strip_quarantine(EXTRACT_DIR)

    # Inject into sys.path
    if EXTRACT_DIR not in sys.path:
        sys.path.insert(0, EXTRACT_DIR)

    # 3. Verify import
    try:
        importlib.import_module('rhino3dm')
        return True, None
    except ImportError as e:
        _rhino3dm_error = (
            f'rhino3dm wheel extracted but import failed: {e}. '
            f'On macOS, try running: '
            f'xattr -rd com.apple.quarantine "{EXTRACT_DIR}"'
        )
        return False, _rhino3dm_error


def get_last_error():
    """Return the last error message from ensure_rhino3dm(), if any."""
    return _rhino3dm_error


def _pick_wheel():
    """Select the correct bundled wheel for this Python version and platform."""
    if not os.path.isdir(WHEELS_DIR):
        return None

    py_ver = f'cp{sys.version_info.major}{sys.version_info.minor}'
    machine = platform.machine().lower()

    candidates = [f for f in os.listdir(WHEELS_DIR) if f.endswith('.whl')]

    for fname in candidates:
        if py_ver not in fname:
            continue

        if sys.platform == 'darwin':
            if 'universal2' in fname or machine in fname or 'macosx' in fname:
                return os.path.join(WHEELS_DIR, fname)
        elif sys.platform == 'win32':
            if 'win' in fname:
                return os.path.join(WHEELS_DIR, fname)
        elif sys.platform.startswith('linux'):
            if 'linux' in fname:
                return os.path.join(WHEELS_DIR, fname)

    return None


def _extract_wheel(whl_path):
    """Extract a wheel (zip archive) to EXTRACT_DIR if not already done."""
    os.makedirs(EXTRACT_DIR, exist_ok=True)

    marker = os.path.join(
        EXTRACT_DIR,
        '.extracted_' + os.path.basename(whl_path),
    )
    if os.path.exists(marker):
        return

    with zipfile.ZipFile(whl_path, 'r') as z:
        z.extractall(EXTRACT_DIR)

    # Write marker so we don't re-extract
    with open(marker, 'w') as f:
        f.write('')


def _strip_quarantine(path):
    """Remove macOS quarantine attribute from all files in a directory."""
    try:
        subprocess.run(
            ['xattr', '-rd', 'com.apple.quarantine', path],
            capture_output=True,
            timeout=10,
        )
    except Exception:
        # Non-fatal — worst case the user gets a Gatekeeper dialog
        pass
