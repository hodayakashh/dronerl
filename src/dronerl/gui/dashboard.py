"""Real-time training dashboard rendered in the right-side panel."""

from __future__ import annotations

import pygame

from dronerl.gui.renderer import CELL_COLORS, LEGEND_LABELS

_BG = (25, 25, 25)
_TEXT = (210, 210, 210)
_GRAPH_COLOR = (80, 180, 255)
_TITLE_COLOR = (255, 255, 255)
_GRAPH_H = 80
_PADDING = 10
_MAX_HISTORY = 100
_NOTIFY_OK = (120, 255, 160)
_NOTIFY_WARN = (255, 200, 120)


class Dashboard:
    """Right-side panel showing live stats and reward history graph.

    Stats displayed:
    - Episode, Total Reward, Epsilon, Steps, Goal Rate %

    Graph:
    - Last ``_MAX_HISTORY`` episode rewards as a line graph (Pygame only).
    """

    def __init__(self, config: object) -> None:
        """Initialise dashboard dimensions from config.

        Args:
            config: SimpleNamespace with gui.cell_size, grid.rows, grid.cols,
                    and optional gui.dashboard_width (default 240).
        """
        gui = config.gui  # type: ignore[attr-defined]
        grid = config.grid  # type: ignore[attr-defined]
        cell = int(gui.cell_size)
        self._x = int(grid.cols) * cell
        self._w = getattr(gui, "dashboard_width", 240)
        self._h = int(grid.rows) * cell
        self._font_sm = pygame.font.SysFont("monospace", 12)
        self._font_title = pygame.font.SysFont("monospace", 13, bold=True)
        # Stats state
        self._episode = 0
        self._total_reward = 0.0
        self._epsilon = 1.0
        self._steps = 0
        self._goal_rate = 0.0
        self._history: list[float] = []

    def update(
        self,
        episode: int,
        total_reward: float,
        epsilon: float,
        steps: int,
        goal_rate: float,
        episode_rewards: list[float],
    ) -> None:
        """Store the latest stats for the next draw call.

        Args:
            episode: Current episode number.
            total_reward: Total reward accumulated this episode.
            epsilon: Current exploration rate.
            steps: Steps taken this episode.
            goal_rate: Fraction of episodes that reached the goal.
            episode_rewards: Full reward history list (last N used for graph).
        """
        self._episode = episode
        self._total_reward = total_reward
        self._epsilon = epsilon
        self._steps = steps
        self._goal_rate = goal_rate
        self._history = list(episode_rewards[-_MAX_HISTORY:])

    def draw(self, surface: pygame.Surface) -> None:
        """Render the full dashboard panel onto *surface*."""
        panel = pygame.Rect(self._x, 0, self._w, self._h)
        pygame.draw.rect(surface, _BG, panel)

        y = _PADDING
        title = self._font_title.render("DroneRL Dashboard", True, _TITLE_COLOR)
        surface.blit(title, (self._x + _PADDING, y))
        y += 22

        pygame.draw.line(surface, (60, 60, 60), (self._x, y), (self._x + self._w, y))
        y += 8

        stats = [
            f"Episode:  {self._episode}",
            f"Reward:   {self._total_reward:.1f}",
            f"Epsilon:  {self._epsilon:.3f}",
            f"Steps:    {self._steps}",
            f"GoalRate: {self._goal_rate * 100:.1f}%",
        ]
        for line in stats:
            surf = self._font_sm.render(line, True, _TEXT)
            surface.blit(surf, (self._x + _PADDING, y))
            y += 18
        y += 6

        graph_rect = pygame.Rect(self._x + _PADDING, y, self._w - _PADDING * 2, _GRAPH_H)
        self._draw_graph(surface, self._history, graph_rect, _GRAPH_COLOR)
        y += _GRAPH_H + 12
        self._draw_legend(surface, y)

    def draw_notification(self, surface: pygame.Surface, text: str) -> None:
        """Render transient notification near the bottom of the dashboard panel."""
        if not text:
            return

        is_warn = text.lower().startswith("no ") or text.lower().startswith("warning")
        color = _NOTIFY_WARN if is_warn else _NOTIFY_OK
        txt = self._font_sm.render(text, True, color)
        max_w = self._w - (_PADDING * 2)
        if txt.get_width() > max_w:
            clipped = text
            while clipped and self._font_sm.size(f"{clipped}...")[0] > max_w:
                clipped = clipped[:-1]
            txt = self._font_sm.render(f"{clipped}...", True, color)

        x = self._x + _PADDING
        y = self._h - txt.get_height() - _PADDING
        bg_rect = pygame.Rect(x - 4, y - 2, min(max_w, txt.get_width()) + 8, txt.get_height() + 4)
        pygame.draw.rect(surface, (35, 35, 35), bg_rect, border_radius=3)
        surface.blit(txt, (x, y))

    def _draw_legend(self, surface: pygame.Surface, y: int) -> None:
        """Draw color legend in the dashboard panel."""
        x = self._x + _PADDING
        lbl = self._font_title.render("Legend", True, _TITLE_COLOR)
        surface.blit(lbl, (x, y))
        y += 18
        sw = 12
        for ct, label in LEGEND_LABELS.items():
            pygame.draw.rect(surface, CELL_COLORS[ct], pygame.Rect(x, y + 2, sw, sw))
            pygame.draw.rect(surface, (100, 100, 100), pygame.Rect(x, y + 2, sw, sw), 1)
            surf = self._font_sm.render(label, True, _TEXT)
            surface.blit(surf, (x + sw + 5, y + 1))
            y += 17

    def _draw_graph(
        self,
        surface: pygame.Surface,
        data: list[float],
        rect: pygame.Rect,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a mini line graph inside *rect*."""
        pygame.draw.rect(surface, (40, 40, 40), rect)
        pygame.draw.rect(surface, (80, 80, 80), rect, 1)
        if len(data) < 2:
            return
        lo, hi = min(data), max(data)
        span = hi - lo if hi != lo else 1.0
        n = len(data)
        pts = [
            (
                rect.x + int((i / (n - 1)) * rect.width),
                rect.bottom - int(((v - lo) / span) * (rect.height - 4)) - 2,
            )
            for i, v in enumerate(data)
        ]
        pygame.draw.lines(surface, color, False, pts, 2)
