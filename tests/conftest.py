"""Repository-wide test bootstrap for Windows native-library ordering."""

from __future__ import annotations

import sys


if sys.platform == "win32":
    # ViennaRNA 2.7.2's wheel can fail to initialize when its extension is
    # loaded after other large native runtimes during pytest collection.  Load
    # it first; this is test-process setup only and changes no application code.
    import RNA  # noqa: F401
