"""Policy arrows overlay — draws the greedy action for each cell."""

from __future__ import annotations

import math

import pygame

from dronerl.agent.q_table import QTable
from dronerl.constants import Action
from dronerl.environment.grid import CellType, Grid

_WHITE = (255, 255, 255)
_GREEN = (60, 220, 80)

# Arrow direction vectors: (dx, dy) in screen space (y-axis points down)
_DIRECTION: dict[int, tuple[float, float]] = {
    Action.UP: (0.0, -1.0),
    Action.DOWN: (0.0, 1.0),
    Action.LEFT: (-1.0, 0.0),
    Action.RIGHT: (1.0, 0.0),
}


class ArrowOverlay:
    """Draws a directional arrow per non-wall cell showing the greedy policy."""

    def __init__(self, cell_size: int) -> None:
        """Initialise the overlay.

        Args:
            cell_size: Pixel size of each grid cell.
        """
        self._cell = cell_size

    def draw(self, surface: pygame.Surface, q_table: QTable, grid: Grid) -> None:
        """Draw one arrow per non-wall cell on *surface*.

        Args:
            surface: Pygame surface to draw on.
            q_table: Q-table used to determine best action per cell.
            grid: Grid used to skip WALL cells.
        """
        for r in range(grid.rows):
            for c in range(grid.cols):
                if grid.get_cell(r, c) is CellType.WALL:
                    continue
                action = q_table.best_action(r, c)
                cx = c * self._cell + self._cell // 2
                cy = r * self._cell + self._cell // 2
                color = _GREEN if grid.get_cell(r, c) is CellType.GOAL else _WHITE
                self._draw_arrow(surface, (cx, cy), action, color)

    def _draw_arrow(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        action: int,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a single filled polygon arrow.

        Args:
            surface: Target surface.
            center: (x, y) pixel centre of the cell.
            action: Action index determining arrow direction.
            color: RGB colour of the arrow.
        """
        cx, cy = center
        dx, dy = _DIRECTION[action]
        length = self._cell * 0.35
        width = self._cell * 0.12
        perp_x, perp_y = -dy, dx

        tip = (cx + dx * length, cy + dy * length)
        base_l = (cx - dx * length * 0.3 + perp_x * width,
                  cy - dy * length * 0.3 + perp_y * width)
        base_r = (cx - dx * length * 0.3 - perp_x * width,
                  cy - dy * length * 0.3 - perp_y * width)

        pts = [
            (int(tip[0]), int(tip[1])),
            (int(base_l[0]), int(base_l[1])),
            (int(base_r[0]), int(base_r[1])),
        ]
        if _points_valid(pts):
            pygame.draw.polygon(surface, color, pts)


def _points_valid(pts: list[tuple[int, int]]) -> bool:
    """Return True if all polygon points are finite numbers."""
    return all(math.isfinite(x) and math.isfinite(y) for x, y in pts)
