"""Interactive level editor with brush painting and keyboard shortcuts."""

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
_PALETTE: list[CellType] = _CYCLE
_SAVE_PATH = Path("config/custom_level.yaml")
_FONT_SIZE = 13
_HINT_ACTIONS = "[LClick] Add   [RClick] Remove"
_HINT_MAIN = "[S] Save+Exit   [R] Reset   [ESC] Exit   [1-6] Object"
_LABELS: dict[CellType, str] = {
    CellType.EMPTY: "Empty",
    CellType.WALL: "Wall",
    CellType.TRAP: "Trap",
    CellType.WIND: "Wind",
    CellType.GOAL: "Goal",
    CellType.START: "Start",
}
_SHORTCUT_KEYS = {
    pygame.K_1: CellType.EMPTY,
    pygame.K_2: CellType.WALL,
    pygame.K_3: CellType.TRAP,
    pygame.K_4: CellType.WIND,
    pygame.K_5: CellType.GOAL,
    pygame.K_6: CellType.START,
}
_BG = (24, 26, 33)
_PANEL_BG = (10, 11, 16)
_PANEL_BORDER = (56, 60, 74)
_BAR_BG = (30, 30, 30)
_BAR_BORDER = (56, 60, 74)
_ROW_BG = (31, 35, 46)
_ROW_ACTIVE = (48, 86, 68)
_TEXT = (226, 230, 240)
_TEXT_DIM = (162, 170, 188)
_STATUS_OK = (120, 255, 160)
_STATUS_WARN = (255, 200, 120)
_LEGEND_ROWS: list[tuple[int, CellType, str]] = [
    (1, CellType.EMPTY, "Open"),
    (2, CellType.WALL, "Blocked"),
    (3, CellType.TRAP, "Penalty"),
    (4, CellType.WIND, "Drift"),
    (5, CellType.GOAL, "Target"),
    (6, CellType.START, "Spawn"),
]


class LevelEditor:
    """Blocking interactive grid editor overlaid on the Pygame window.

    Left-click  paints the currently selected brush.
    Right-click resets a cell to EMPTY.
    Dragging with left/right mouse button keeps painting/erasing.
    Keys 1..6 select brush: EMPTY, WALL, TRAP, WIND, GOAL, START.
    S key       saves the layout to ``config/custom_level.yaml`` and exits editor.
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

    def _draw(self) -> None:
        """Redraw the grid with editor overlay."""
        self._screen.fill(_BG)
        for r in range(self._grid.rows):
            for c in range(self._grid.cols):
                ct = self._grid.get_cell(r, c)
                rect = pygame.Rect(c * self._cell, r * self._cell, self._cell, self._cell)
                pygame.draw.rect(self._screen, CELL_COLORS.get(ct, (220, 220, 220)), rect)
                pygame.draw.rect(self._screen, (100, 100, 100), rect, 1)
        self._draw_side_panel()
        self._draw_toolbar()
        if self._status_ticks > 0:
            self._status_ticks -= 1
            status_color = _STATUS_WARN if self._status.lower().startswith("warning") else _STATUS_OK
            txt = self._font.render(self._status, True, status_color)
            self._screen.blit(txt, (self._grid.cols * self._cell + 10,
                                    self._grid.rows * self._cell - 18))
        pygame.display.flip()

    def _draw_side_panel(self) -> None:
        """Draw right panel with concise help and color legend."""
        panel_x = self._grid.cols * self._cell
        panel_w = self._screen.get_width() - panel_x
        panel_h = self._grid.rows * self._cell
        panel = pygame.Rect(panel_x, 0, panel_w, panel_h)
        pygame.draw.rect(self._screen, _PANEL_BG, panel)
        pygame.draw.line(self._screen, _PANEL_BORDER, (panel_x, 0), (panel_x, panel_h), 1)

        x = panel_x + 10
        y = 10
        title = self._font.render("Editor", True, _TEXT)
        self._screen.blit(title, (x, y))
        active = self._font.render(f"Object: {_LABELS[self._brush]}", True, _STATUS_OK)
        self._screen.blit(active, (x, y + 16))
        tab_help = self._font.render("Tab: change object", True, _TEXT_DIM)
        self._screen.blit(tab_help, (x, y + 32))

        legend_y = y + 80
        legend_title = self._font.render("Choose Color", True, _TEXT)
        self._screen.blit(legend_title, (x, legend_y))
        for i, (num, ct, short) in enumerate(_LEGEND_ROWS):
            row_y = legend_y + 18 + i * 18
            row_rect = pygame.Rect(x - 4, row_y - 1, 206, 16)
            pygame.draw.rect(self._screen, _ROW_BG, row_rect, border_radius=3)
            if ct is self._brush:
                pygame.draw.rect(self._screen, _ROW_ACTIVE, row_rect, border_radius=3)
            swatch = pygame.Rect(x, row_y + 1, 12, 12)
            pygame.draw.rect(self._screen, CELL_COLORS.get(ct, (220, 220, 220)), swatch)
            pygame.draw.rect(self._screen, (110, 110, 120), swatch, 1)
            label = self._font.render(f"[{num}] {_LABELS[ct]} ({short})", True, _TEXT_DIM)
            self._screen.blit(label, (x + 18, row_y))

    def _draw_toolbar(self) -> None:
        """Draw regular-mode-like bottom status bar for editor controls."""
        y = self._grid.rows * self._cell
        bar = pygame.Rect(0, y, self._screen.get_width(), 28)
        pygame.draw.rect(self._screen, _BAR_BG, bar)
        pygame.draw.line(self._screen, _BAR_BORDER, (0, y), (self._screen.get_width(), y), 1)
        mode_txt = self._font.render("[EDIT MODE]", True, _TEXT)
        object_txt = self._font.render(f"[Object] {_LABELS[self._brush]}", True, _STATUS_OK)
        self._screen.blit(mode_txt, (8, y + 3))
        self._screen.blit(object_txt, (100, y + 3))

        # Render bottom hints left-to-right for consistent spacing.
        segments = [
            (_HINT_ACTIONS, _TEXT_DIM),
            (_HINT_MAIN, _TEXT_DIM),
        ]
        x = 8
        for text, color in segments:
            seg = self._font.render(text, True, color)
            self._screen.blit(seg, (x, y + 15))
            x += seg.get_width() + 28

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
