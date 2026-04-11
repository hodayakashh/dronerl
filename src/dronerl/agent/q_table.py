"""Q-Table wrapper backed by a NumPy float32 array."""

from __future__ import annotations

from pathlib import Path

import numpy as np


class QTable:
    """Stores Q-values as a (rows × cols × n_actions) NumPy array.

    All values are initialised to zero and stored as float32 for memory
    efficiency.  Persistence is handled via NumPy's ``.npy`` format.
    """

    def __init__(self, rows: int, cols: int, n_actions: int) -> None:
        """Allocate a zero-filled Q-table.

        Args:
            rows: Grid row count (must be > 0).
            cols: Grid column count (must be > 0).
            n_actions: Number of discrete actions (must be > 0).

        Raises:
            ValueError: If any dimension is not positive.
        """
        if rows <= 0:
            raise ValueError(f"rows must be > 0, got {rows}")
        if cols <= 0:
            raise ValueError(f"cols must be > 0, got {cols}")
        if n_actions <= 0:
            raise ValueError(f"n_actions must be > 0, got {n_actions}")
        self._rows = rows
        self._cols = cols
        self._n_actions = n_actions
        self._table = np.zeros((rows, cols, n_actions), dtype=np.float32)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def shape(self) -> tuple[int, int, int]:
        """Shape of the underlying array: (rows, cols, n_actions)."""
        return (self._rows, self._cols, self._n_actions)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, r: int, c: int) -> np.ndarray:
        """Return the full Q-value slice for state (r, c).

        Returns:
            1-D array of length n_actions.
        """
        return self._table[r, c]

    def get_value(self, r: int, c: int, a: int) -> float:
        """Return Q(s, a) for state (r, c) and action a."""
        return float(self._table[r, c, a])

    def set_value(self, r: int, c: int, a: int, value: float) -> None:
        """Set Q(s, a) for state (r, c) and action a."""
        self._table[r, c, a] = value

    def best_action(self, r: int, c: int) -> int:
        """Return argmax_a Q(s, a) for state (r, c)."""
        return int(np.argmax(self._table[r, c]))

    def max_value(self, r: int, c: int) -> float:
        """Return max_a Q(s, a) for state (r, c)."""
        return float(np.max(self._table[r, c]))

    def reset(self) -> None:
        """Zero all Q-values in place."""
        self._table[:] = 0.0

    def save(self, path: str | Path) -> None:
        """Persist the Q-table to a ``.npy`` file.

        Args:
            path: Destination file path (will be created/overwritten).
        """
        np.save(str(path), self._table)

    def load(self, path: str | Path) -> None:
        """Load Q-values from a ``.npy`` file.

        Args:
            path: Source file path.

        Raises:
            ValueError: If the loaded array shape does not match this table.
        """
        data = np.load(str(path))
        expected = (self._rows, self._cols, self._n_actions)
        if data.shape != expected:
            raise ValueError(f"Shape mismatch: expected {expected}, got {data.shape}")
        self._table = data.astype(np.float32)

    def __repr__(self) -> str:
        return (
            f"QTable(rows={self._rows}, cols={self._cols}, "
            f"n_actions={self._n_actions}, dtype={self._table.dtype})"
        )
