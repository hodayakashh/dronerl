"""Value heatmap overlay for the Q-table visualisation."""

from __future__ import annotations

import numpy as np
import pygame

from dronerl.agent.q_table import QTable
from dronerl.environment.grid import CellType, Grid

_ALPHA = 160  # overlay transparency (0-255)


class HeatmapOverlay:
    """Draws a semi-transparent orange/red gradient over non-wall cells.

    Colour intensity reflects ``max_a Q(s, a)`` for each cell, normalised
    between the global min and max Q-values on the grid.
    """

    def __init__(self, cell_size: int, rows: int, cols: int) -> None:
        """Initialise the overlay.

        Args:
            cell_size: Pixel size of each grid cell.
            rows: Grid row count.
            cols: Grid column count.
        """
        self._cell = cell_size
        self._rows = rows
        self._cols = cols

    def draw(self, surface: pygame.Surface, q_table: QTable, grid: Grid) -> None:
        """Blit the heatmap onto *surface*.

        Args:
            surface: Pygame surface to draw on.
            q_table: Current Q-table for value lookup.
            grid: Grid used to skip WALL cells.
        """
        values = [
            q_table.max_value(r, c)
            for r in range(self._rows)
            for c in range(self._cols)
            if grid.get_cell(r, c) is not CellType.WALL
        ]
        if not values:
            return
        vmin, vmax = float(np.min(values)), float(np.max(values))

        overlay = pygame.Surface((self._cell, self._cell), pygame.SRCALPHA)
        for r in range(self._rows):
            for c in range(self._cols):
                if grid.get_cell(r, c) is CellType.WALL:
                    continue
                v = q_table.max_value(r, c)
                color = self._value_to_color(v, vmin, vmax)
                overlay.fill((*color, _ALPHA))
                surface.blit(overlay, (c * self._cell, r * self._cell))

    def _value_to_color(
        self, v: float, vmin: float, vmax: float
    ) -> tuple[int, int, int]:
        """Map a scalar value to an orange/red RGB colour.

        Returns uniform mid-orange when vmin == vmax (all values equal).
        """
        t = 0.5 if vmax == vmin else (v - vmin) / (vmax - vmin)
        r = 255
        g = int(140 * (1.0 - t))
        b = 0
        return (r, g, b)
