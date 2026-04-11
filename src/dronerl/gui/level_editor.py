"""Interactive level editor — click to paint cells, save to YAML."""

from __future__ import annotations

from pathlib import Path

import pygame
import yaml

from dronerl.environment.grid import CellType, Grid
from dronerl.gui.renderer import CELL_COLORS

_CYCLE: list[CellType] = [
    CellType.EMPTY,
    CellType.WALL,
    CellType.TRAP,
    CellType.WIND,
    CellType.GOAL,
    CellType.START,
]
_SAVE_PATH = Path("config/custom_level.yaml")
_FONT_SIZE = 13
_OVERLAY_COLOR = (0, 0, 0, 160)
_HINT = "LClick:cycle  RClick:clear  S:save  R:reset  ESC:exit"


class LevelEditor:
    """Blocking interactive grid editor overlaid on the Pygame window.

    Left-click  cycles the cell type: EMPTY→WALL→TRAP→WIND→GOAL→START.
    Right-click resets the cell to EMPTY.
    S key       saves the layout to ``config/custom_level.yaml``.
    R key       resets the entire grid to EMPTY.
    ESC         exits the editor and returns the modified grid.

    Constraints: at most one GOAL and one START cell are enforced.
    """

    def __init__(self, screen: pygame.Surface, grid: Grid, cell_size: int) -> None:
        """Initialise the editor.

        Args:
            screen: The active Pygame display surface.
            grid: The grid to edit in-place.
            cell_size: Pixel size of each grid cell.
        """
        self._screen = screen
        self._grid = grid
        self._cell = cell_size
        self._font = pygame.font.SysFont("monospace", _FONT_SIZE)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> Grid:
        """Run the blocking event loop and return the modified grid."""
        running = True
        while running:
            self._draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_s:
                        self._save()
                    elif event.key == pygame.K_r:
                        self._reset_grid()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    r, c = self._pixel_to_cell(event.pos)
                    if self._grid.in_bounds(r, c):
                        if event.button == 1:
                            self._cycle_cell(r, c)
                        elif event.button == 3:
                            self._grid.set_cell(r, c, CellType.EMPTY)
        return self._grid

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _draw(self) -> None:
        """Redraw the grid with editor overlay."""
        for r in range(self._grid.rows):
            for c in range(self._grid.cols):
                ct = self._grid.get_cell(r, c)
                rect = pygame.Rect(c * self._cell, r * self._cell, self._cell, self._cell)
                pygame.draw.rect(self._screen, CELL_COLORS.get(ct, (220, 220, 220)), rect)
                pygame.draw.rect(self._screen, (100, 100, 100), rect, 1)
        hint = self._font.render(_HINT, True, (255, 255, 200))
        self._screen.blit(hint, (4, self._grid.rows * self._cell + 4))
        pygame.display.flip()

    def _pixel_to_cell(self, pos: tuple[int, int]) -> tuple[int, int]:
        """Convert a pixel (x, y) position to grid (row, col) coordinates."""
        x, y = pos
        return y // self._cell, x // self._cell

    def _cycle_cell(self, r: int, c: int) -> None:
        """Advance the cell at (r, c) to the next CellType in the cycle order."""
        current = self._grid.get_cell(r, c)
        idx = _CYCLE.index(current) if current in _CYCLE else 0
        for next_ct in _CYCLE[idx + 1:] + _CYCLE:
            if next_ct in (CellType.GOAL, CellType.START) and self._has(next_ct):
                continue
            self._grid.set_cell(r, c, next_ct)
            break

    def _has(self, cell_type: CellType) -> bool:
        """Return True if the grid already contains at least one cell of *cell_type*."""
        return any(
            self._grid.get_cell(r, c) is cell_type
            for r in range(self._grid.rows)
            for c in range(self._grid.cols)
        )

    def _reset_grid(self) -> None:
        """Set every cell in the grid back to EMPTY."""
        for r in range(self._grid.rows):
            for c in range(self._grid.cols):
                self._grid.set_cell(r, c, CellType.EMPTY)

    def _save(self) -> None:
        """Serialise the current grid layout to config/custom_level.yaml."""
        layout: dict = {"walls": [], "traps": [], "winds": []}
        for r in range(self._grid.rows):
            for c in range(self._grid.cols):
                ct = self._grid.get_cell(r, c)
                if ct is CellType.WALL:
                    layout["walls"].append([r, c])
                elif ct is CellType.TRAP:
                    layout["traps"].append([r, c])
                elif ct is CellType.WIND:
                    layout["winds"].append([r, c])
                elif ct is CellType.GOAL:
                    layout["goal"] = [r, c]
                elif ct is CellType.START:
                    layout["start"] = [r, c]
        _SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _SAVE_PATH.open("w", encoding="utf-8") as fh:
            yaml.dump(layout, fh)
