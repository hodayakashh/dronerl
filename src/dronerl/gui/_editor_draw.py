"""Drawing mixin and colour/palette constants for the LevelEditor overlay.

Why: extracted from level_editor.py to keep both files within the 150 code-line limit
while separating rendering concerns from editing logic.
"""

from __future__ import annotations

import pygame

from dronerl.environment.grid import CellType
from dronerl.gui.renderer import CELL_COLORS

# ── palette & keyboard mapping ─────────────────────────────────────────────────
_CYCLE: list[CellType] = [
    CellType.EMPTY, CellType.WALL, CellType.TRAP,
    CellType.WIND, CellType.GOAL, CellType.START,
]
_PALETTE: list[CellType] = _CYCLE
_FONT_SIZE = 13
_HINT_ACTIONS = "[LClick] Add   [RClick] Remove"
_HINT_MAIN = "[S] Save+Exit   [R] Reset   [ESC] Exit   [1-6] Object"
_LABELS: dict[CellType, str] = {
    CellType.EMPTY: "Empty", CellType.WALL: "Wall", CellType.TRAP: "Trap",
    CellType.WIND: "Wind", CellType.GOAL: "Goal", CellType.START: "Start",
}
_SHORTCUT_KEYS: dict[int, CellType] = {
    pygame.K_1: CellType.EMPTY, pygame.K_2: CellType.WALL,
    pygame.K_3: CellType.TRAP,  pygame.K_4: CellType.WIND,
    pygame.K_5: CellType.GOAL,  pygame.K_6: CellType.START,
}

# ── colours ────────────────────────────────────────────────────────────────────
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
    (1, CellType.EMPTY, "Open"),   (2, CellType.WALL, "Blocked"),
    (3, CellType.TRAP, "Penalty"), (4, CellType.WIND, "Drift"),
    (5, CellType.GOAL, "Target"),  (6, CellType.START, "Spawn"),
]


class EditorDrawMixin:
    """Mixin that provides all Pygame rendering for the level editor.

    Why: separates drawing code from editing logic so each file stays under 150 lines.

    Depends on the host class exposing:
        _screen, _grid, _cell, _font, _brush, _status, _status_ticks
    """

    def _draw(self) -> None:
        """Redraw the full editor frame: grid cells, side panel, toolbar, status."""
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
            color = _STATUS_WARN if self._status.lower().startswith("warning") else _STATUS_OK
            txt = self._font.render(self._status, True, color)
            self._screen.blit(txt, (self._grid.cols * self._cell + 10,
                                    self._grid.rows * self._cell - 18))
        pygame.display.flip()

    def _draw_side_panel(self) -> None:
        """Draw right panel with active-brush indicator and colour legend."""
        panel_x = self._grid.cols * self._cell
        panel_w = self._screen.get_width() - panel_x
        panel_h = self._grid.rows * self._cell
        pygame.draw.rect(self._screen, _PANEL_BG, pygame.Rect(panel_x, 0, panel_w, panel_h))
        pygame.draw.line(self._screen, _PANEL_BORDER, (panel_x, 0), (panel_x, panel_h), 1)
        x, y = panel_x + 10, 10
        self._screen.blit(self._font.render("Editor", True, _TEXT), (x, y))
        self._screen.blit(
            self._font.render(f"Object: {_LABELS[self._brush]}", True, _STATUS_OK), (x, y + 16)
        )
        self._screen.blit(self._font.render("Tab: change object", True, _TEXT_DIM), (x, y + 32))
        legend_y = y + 80
        self._screen.blit(self._font.render("Choose Color", True, _TEXT), (x, legend_y))
        for i, (num, ct, short) in enumerate(_LEGEND_ROWS):
            row_y = legend_y + 18 + i * 18
            row_rect = pygame.Rect(x - 4, row_y - 1, 206, 16)
            pygame.draw.rect(self._screen, _ROW_ACTIVE if ct is self._brush else _ROW_BG,
                             row_rect, border_radius=3)
            swatch = pygame.Rect(x, row_y + 1, 12, 12)
            pygame.draw.rect(self._screen, CELL_COLORS.get(ct, (220, 220, 220)), swatch)
            pygame.draw.rect(self._screen, (110, 110, 120), swatch, 1)
            self._screen.blit(
                self._font.render(f"[{num}] {_LABELS[ct]} ({short})", True, _TEXT_DIM),
                (x + 18, row_y),
            )

    def _draw_toolbar(self) -> None:
        """Draw bottom status bar showing edit mode and keyboard hints."""
        y = self._grid.rows * self._cell
        pygame.draw.rect(self._screen, _BAR_BG, pygame.Rect(0, y, self._screen.get_width(), 28))
        pygame.draw.line(self._screen, _BAR_BORDER, (0, y), (self._screen.get_width(), y), 1)
        self._screen.blit(self._font.render("[EDIT MODE]", True, _TEXT), (8, y + 3))
        self._screen.blit(
            self._font.render(f"[Object] {_LABELS[self._brush]}", True, _STATUS_OK), (100, y + 3)
        )
        x = 8
        for text, color in [(_HINT_ACTIONS, _TEXT_DIM), (_HINT_MAIN, _TEXT_DIM)]:
            seg = self._font.render(text, True, color)
            self._screen.blit(seg, (x, y + 15))
            x += seg.get_width() + 28
