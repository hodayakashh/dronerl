"""Interactive level editor with brush painting and keyboard shortcuts."""

from __future__ import annotations

from pathlib import Path

import pygame
import yaml

from dronerl.environment.grid import CellType, Grid
from dronerl.gui._editor_draw import (
    _FONT_SIZE,
    _LABELS,
    _PALETTE,
    _SHORTCUT_KEYS,
    EditorDrawMixin,
)

_SAVE_PATH = Path("config/custom_level.yaml")


class LevelEditor(EditorDrawMixin):
    """Blocking interactive grid editor overlaid on the Pygame window.

    Left-click  paints the currently selected brush.
    Right-click resets a cell to EMPTY.
    Dragging with left/right mouse button keeps painting/erasing.
    Keys 1..6 select brush: EMPTY, WALL, TRAP, WIND, GOAL, START.
    S key       saves the layout to ``config/custom_level.yaml`` and exits.
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
        self._brush = CellType.WALL
        self._painting_button = 0
        self._status = ""
        self._status_ticks = 0

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
                        running = False
                    elif event.key == pygame.K_r:
                        self._reset_grid()
                    elif event.key in _SHORTCUT_KEYS:
                        self._brush = _SHORTCUT_KEYS[event.key]
                        self._notify(f"Object: {_LABELS[self._brush]}")
                    elif event.key == pygame.K_TAB:
                        self._cycle_brush()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    r, c = self._pixel_to_cell(event.pos)
                    if event.button in (1, 3) and self._grid.in_bounds(r, c):
                        self._painting_button = event.button
                        self._paint_at(r, c, event.button)
                    elif event.button == 4:
                        self._cycle_brush(-1)
                    elif event.button == 5:
                        self._cycle_brush(1)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button in (1, 3):
                        self._painting_button = 0
                elif event.type == pygame.MOUSEMOTION and self._painting_button:
                    r, c = self._pixel_to_cell(event.pos)
                    if self._grid.in_bounds(r, c):
                        self._paint_at(r, c, self._painting_button)
        return self._grid

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _pixel_to_cell(self, pos: tuple[int, int]) -> tuple[int, int]:
        """Convert a pixel (x, y) position to grid (row, col) coordinates."""
        x, y = pos
        return y // self._cell, x // self._cell

    def _paint_at(self, r: int, c: int, button: int) -> None:
        """Apply paint/erase operation at a specific cell."""
        if button == 3:
            self._grid.set_cell(r, c, CellType.EMPTY)
            return
        if self._brush in (CellType.GOAL, CellType.START):
            self._clear_existing(self._brush, keep=(r, c))
        self._grid.set_cell(r, c, self._brush)

    def _clear_existing(self, cell_type: CellType, keep: tuple[int, int]) -> None:
        """Ensure singleton cell types (GOAL/START) exist at one position only."""
        for r in range(self._grid.rows):
            for c in range(self._grid.cols):
                if (r, c) != keep and self._grid.get_cell(r, c) is cell_type:
                    self._grid.set_cell(r, c, CellType.EMPTY)

    def _cycle_brush(self, direction: int = 1) -> None:
        """Cycle selected brush forward/backward through palette."""
        idx = _PALETTE.index(self._brush)
        self._brush = _PALETTE[(idx + direction) % len(_PALETTE)]
        self._notify(f"Object: {_LABELS[self._brush]}")

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
        missing = [name for name, ct in (("start", CellType.START), ("goal", CellType.GOAL))
                   if not self._has(ct)]
        if missing:
            self._notify(f"Warning: saved without {', '.join(missing)}")
        else:
            self._notify("Saved config/custom_level.yaml")

    def _notify(self, text: str) -> None:
        """Show short-lived status message at the bottom of editor."""
        self._status = text
        self._status_ticks = 180
