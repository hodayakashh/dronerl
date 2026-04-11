"""Grid data model and CellType enumeration for the Smart City environment."""

from __future__ import annotations

from enum import Enum


class CellType(Enum):
    """Types of cells that can exist in the Smart City grid."""

    EMPTY = "empty"
    WALL = "wall"
    TRAP = "trap"
    WIND = "wind"
    GOAL = "goal"
    START = "start"


class Grid:
    """2-D grid of CellType values representing the Smart City map.

    All coordinates are (row, col) with (0, 0) at the top-left.
    """

    def __init__(self, rows: int, cols: int) -> None:
        """Allocate a rows×cols grid filled with EMPTY cells.

        Args:
            rows: Number of rows (must be > 0).
            cols: Number of columns (must be > 0).

        Raises:
            ValueError: If rows or cols are not positive.
        """
        if rows <= 0 or cols <= 0:
            raise ValueError(f"Grid dimensions must be positive, got ({rows}, {cols})")
        self._rows = rows
        self._cols = cols
        self._cells: list[list[CellType]] = [
            [CellType.EMPTY for _ in range(cols)] for _ in range(rows)
        ]

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def rows(self) -> int:
        """Number of rows."""
        return self._rows

    @property
    def cols(self) -> int:
        """Number of columns."""
        return self._cols

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_cell(self, r: int, c: int, cell_type: CellType) -> None:
        """Set the type of a cell.

        Args:
            r: Row index.
            c: Column index.
            cell_type: New CellType value.

        Raises:
            IndexError: If (r, c) is out of bounds.
        """
        self._check_bounds(r, c)
        self._cells[r][c] = cell_type

    def get_cell(self, r: int, c: int) -> CellType:
        """Return the CellType at (r, c).

        Raises:
            IndexError: If (r, c) is out of bounds.
        """
        self._check_bounds(r, c)
        return self._cells[r][c]

    def is_walkable(self, r: int, c: int) -> bool:
        """Return True if the cell is not a WALL (and is in bounds)."""
        if not self.in_bounds(r, c):
            return False
        return self._cells[r][c] is not CellType.WALL

    def in_bounds(self, r: int, c: int) -> bool:
        """Return True if (r, c) lies within the grid."""
        return 0 <= r < self._rows and 0 <= c < self._cols

    def load_from_dict(self, layout: dict) -> None:
        """Populate the grid from a layout dict.

        Expected format::

            {
                "walls":  [[r, c], ...],
                "traps":  [[r, c], ...],
                "winds":  [[r, c], ...],
                "goal":   [r, c],
                "start":  [r, c],
            }

        Missing keys are silently ignored.

        Args:
            layout: Dict describing cell positions by type.
        """
        cell_map = {
            "walls": CellType.WALL,
            "traps": CellType.TRAP,
            "winds": CellType.WIND,
        }
        for key, cell_type in cell_map.items():
            for r, c in layout.get(key, []):
                self.set_cell(r, c, cell_type)
        for key, cell_type in (("goal", CellType.GOAL), ("start", CellType.START)):
            pos = layout.get(key)
            if pos:
                self.set_cell(pos[0], pos[1], cell_type)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_bounds(self, r: int, c: int) -> None:
        """Raise IndexError if (r, c) is outside the grid dimensions."""
        if not self.in_bounds(r, c):
            raise IndexError(f"Cell ({r}, {c}) out of bounds for {self._rows}×{self._cols} grid")
