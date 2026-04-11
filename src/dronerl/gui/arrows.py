"""Policy arrows overlay — draws the greedy action for each cell."""

from __future__ import annotations

import math

import pygame

from dronerl.agent.q_table import QTable
from dronerl.constants import Action
from dronerl.environment.grid import CellType, Grid

# Angle in radians for each action (arrow points in movement direction)
_ANGLE: dict[int, float] = {
    Action.UP: -math.pi / 2,
    Action.DOWN: math.pi / 2,
    Action.LEFT: math.pi,
    Action.RIGHT: 0.0,
}

# 7-point arrow polygon facing right, normalised to unit scale
# Shape: shaft + wider arrowhead
_ARROW_PTS: list[tuple[float, float]] = [
    (-0.70, -0.22),  # shaft back-top
    ( 0.05, -0.22),  # shaft/neck top
    ( 0.05, -0.48),  # head base top
    ( 1.00,  0.00),  # tip
    ( 0.05,  0.48),  # head base bottom
    ( 0.05,  0.22),  # shaft/neck bottom
    (-0.70,  0.22),  # shaft back-bottom
]


class ArrowOverlay:
    """Draws a directional arrow per non-wall cell showing the greedy policy."""

    def __init__(self, cell_size: int) -> None:
        """Store the pixel size of each grid cell for scaling arrows."""
        self._cell = cell_size

    def draw(self, surface: pygame.Surface, q_table: QTable, grid: Grid) -> None:
        """Draw one arrow per non-wall cell on *surface* using an alpha overlay."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for r in range(grid.rows):
            for c in range(grid.cols):
                ct = grid.get_cell(r, c)
                if ct is CellType.WALL:
                    continue
                action = q_table.best_action(r, c)
                trained = any(
                    q_table.get_value(r, c, a) != 0.0 for a in range(4)
                )
                cx = c * self._cell + self._cell // 2
                cy = r * self._cell + self._cell // 2
                color = _arrow_color(ct, trained)
                self._draw_arrow(overlay, cx, cy, action, color)
        surface.blit(overlay, (0, 0))

    def _draw_arrow(
        self,
        surface: pygame.Surface,
        cx: int,
        cy: int,
        action: int,
        color: tuple[int, int, int, int],
    ) -> None:
        """Rotate the normalised 7-point arrow polygon and draw it on *surface*."""
        angle = _ANGLE[action]
        scale = self._cell * 0.30
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        pts = [
            (
                int(cx + (x * cos_a - y * sin_a) * scale),
                int(cy + (x * sin_a + y * cos_a) * scale),
            )
            for x, y in _ARROW_PTS
        ]
        if _valid(pts):
            pygame.draw.polygon(surface, color, pts)
            # Thin dark outline for contrast
            pygame.draw.polygon(surface, (0, 0, 0, color[3] // 2), pts, 1)


def _arrow_color(ct: CellType, trained: bool) -> tuple[int, int, int, int]:
    """Return RGBA color for an arrow based on cell type and training state."""
    if ct is CellType.GOAL:
        return (80, 255, 120, 230)
    if ct is CellType.START:
        return (255, 220, 80, 200)
    if trained:
        return (230, 230, 255, 200)
    return (140, 140, 160, 70)   # untrained: faint


def _valid(pts: list[tuple[int, int]]) -> bool:
    """Return True if all polygon points contain finite numbers."""
    return all(math.isfinite(x) and math.isfinite(y) for x, y in pts)
