"""
Dependency bootstrap for rhino3dm.

For Blender 4.2+ extensions, the wheels declared in blender_manifest.toml
are installed automatically by Blender's package manager. This module
simply verifies that rhino3dm is importable and reports a clear error if not.
"""

import importlib

_rhino3dm_error = None


def ensure_rhino3dm():
    """
    Ensure rhino3dm is importable. Returns (success: bool, error: str | None).

    In Blender 4.2+, wheels listed in blender_manifest.toml are installed
    automatically by Blender when the extension is enabled. This function
    just verifies the import works.
    """
    global _rhino3dm_error

    try:
        importlib.import_module('rhino3dm')
        return True, None
    except ImportError as e:
        _rhino3dm_error = (
            f'rhino3dm is not available: {e}. '
            f'Try disabling and re-enabling the extension in Blender Preferences, '
            f'then restart Blender. On macOS, you may also need to run: '
            f'xattr -rd com.apple.quarantine '
            f'"~/Library/Application Support/Blender/4.2/extensions/"'
        )
        return False, _rhino3dm_error


def get_last_error():
    """Return the last error message from ensure_rhino3dm(), if any."""
    return _rhino3dm_error
