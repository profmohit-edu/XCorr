"""Analyzer integration boundary for XCorr.

The :mod:`analyzers` package contains the shared contracts and isolated tool
adapters used to execute smart-contract analyzers, parse their native output,
and normalize findings at the application boundary. Analyzer integrations
remain independent of correlation, evaluation, and presentation policies.

Only names declared in :data:`__all__` form the stable package-level public
API. Tool-specific implementations belong to their own analyzer subpackages.
"""

from __future__ import annotations

from typing import Final

__version__: Final[str] = "0.1.0"

__all__: Final[tuple[str, ...]] = ("__version__",)
