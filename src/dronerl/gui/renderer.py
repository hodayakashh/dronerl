"""Pygame grid renderer, status bar, and legend for DroneRL."""

from __future__ import annotations

import pygame

from dronerl.environment.grid import CellType, Grid

CELL_COLORS: dict[CellType, tuple[int, int, int]] = {
    CellType.EMPTY: (55, 60, 78),
    CellType.WALL: (22, 22, 38),
    CellType.TRAP: (220, 45, 45),
    CellType.WIND: (40, 175, 210),
    CellType.GOAL: (50, 220, 90),
    CellType.START: (255, 210, 50),
}
LEGEND_LABELS: dict[CellType, str] = {
    CellType.EMPTY: "Empty",
    CellType.WALL: "Building",
    CellType.TRAP: "Trap",
    CellType.GOAL: "Goal",
    CellType.WIND: "Wind Zone",
    CellType.START: "Start",
}
STATUS_HEIGHT = 28
DRONE_COLOR = (255, 220, 0)
_DRONE_OUTLINE = (20, 20, 20)


class Renderer:
    """Renders the grid, drone, overlays, status bar, and legend."""

    def __init__(self, grid: Grid, config: object) -> None:
        """Create the Pygame window.

        Args:
            grid: The Smart City grid to render.
            config: SimpleNamespace with gui.fps, gui.cell_size, gui.window_title,
                    and optional gui.dashboard_width (default 240).
        """
        self._grid = grid
        gui = config.gui  # type: ignore[attr-defined]
        self._cell = int(gui.cell_size)
        self._fps = int(gui.fps)
        self._dash_w = getattr(gui, "dashboard_width", 240)
        w = grid.cols * self._cell + self._dash_w
        h = grid.rows * self._cell + STATUS_HEIGHT
        self._screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption(gui.window_title)
        self._clock = pygame.time.Clock()
        self._font = pygame.font.SysFont("monospace", 12)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def draw_grid(
        self,
        drone_pos: tuple[int, int],
        episode: int,
        step: int,
        mode: str = "Training",
        paused: bool = False,
    ) -> None:
        """Draw all grid cells and the drone sprite."""
        for r in range(self._grid.rows):
            for c in range(self._grid.cols):
                ct = self._grid.get_cell(r, c)
                rect = pygame.Rect(c * self._cell, r * self._cell, self._cell, self._cell)
                pygame.draw.rect(self._screen, self._cell_color(ct), rect)
                pygame.draw.rect(self._screen, (90, 95, 115), rect, 1)
        self._draw_drone(self._screen, drone_pos)

    def draw_status_bar(
        self,
        mode: str,
        paused: bool,
        show_heatmap: bool,
        show_arrows: bool,
    ) -> None:
        """Draw the bottom status bar with mode indicator and key hints."""
        y = self._grid.rows * self._cell
        bar = pygame.Rect(0, y, self._screen.get_width(), STATUS_HEIGHT)
        pygame.draw.rect(self._screen, (30, 30, 30), bar)
        state = "[PAUSED]" if paused else "[RUNNING]"
        hm = "[W]✓" if show_heatmap else "[W]"
        ar = "[A]✓" if show_arrows else "[A]"
        text = (
            f"  Mode: {mode} {state}   "
            f"[SPACE] Pause  [F] Fast  {hm} Heatmap  "
            f"{ar} Arrows  [E] Editor  [S] Save  [L] Load  [R] Reset  [ESC] Quit"
        )
        surf = self._font.render(text, True, (200, 200, 200))
        self._screen.blit(surf, (4, y + 6))

    def clear(self) -> None:
        """Fill background before drawing."""
        self._screen.fill((35, 35, 50))

    def flip(self) -> None:
        """Push the frame to the display."""
        pygame.display.flip()

    def tick(self) -> None:
        """Advance the clock by one frame."""
        self._clock.tick(self._fps)

    def handle_quit_event(self) -> bool:
        """Return True if a QUIT event is pending (does not consume events)."""
        return any(e.type == pygame.QUIT for e in pygame.event.peek([pygame.QUIT]))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _cell_color(self, cell_type: CellType) -> tuple[int, int, int]:
        return CELL_COLORS.get(cell_type, (55, 60, 78))

    def _draw_drone(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        r, c = pos
        cx = c * self._cell + self._cell // 2
        cy = r * self._cell + self._cell // 2
        arm = self._cell // 3
        # Shadow
        pygame.draw.circle(surface, _DRONE_OUTLINE, (cx + 2, cy + 2), 11)
        # Arms (outlined)
        pygame.draw.line(surface, _DRONE_OUTLINE, (cx - arm, cy), (cx + arm, cy), 5)
        pygame.draw.line(surface, _DRONE_OUTLINE, (cx, cy - arm), (cx, cy + arm), 5)
        pygame.draw.line(surface, DRONE_COLOR, (cx - arm, cy), (cx + arm, cy), 3)
        pygame.draw.line(surface, DRONE_COLOR, (cx, cy - arm), (cx, cy + arm), 3)
        # Body
        pygame.draw.circle(surface, _DRONE_OUTLINE, (cx, cy), 11)
        pygame.draw.circle(surface, DRONE_COLOR, (cx, cy), 9)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 9, 2)

