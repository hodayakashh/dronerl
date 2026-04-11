"""Smoke tests for GUI modules — verify no crash with headless Pygame."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from dronerl.agent.q_table import QTable
from dronerl.environment.grid import CellType, Grid


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _config() -> SimpleNamespace:
    cfg = SimpleNamespace()
    cfg.gui = SimpleNamespace(fps=60, cell_size=40, window_title="Test", dashboard_width=200)
    cfg.grid = SimpleNamespace(rows=4, cols=4)
    return cfg


def _grid4() -> Grid:
    g = Grid(4, 4)
    g.set_cell(3, 3, CellType.GOAL)
    g.set_cell(1, 1, CellType.WALL)
    g.set_cell(0, 2, CellType.WIND)
    return g


def _qtable4() -> QTable:
    qt = QTable(4, 4, 4)
    qt.set_value(0, 0, 2, 3.0)
    return qt


# ---------------------------------------------------------------------------
# Renderer smoke tests
# ---------------------------------------------------------------------------


def test_renderer_init_no_crash(pygame_init: None) -> None:
    from dronerl.gui.renderer import Renderer
    r = Renderer(_grid4(), _config())
    assert r is not None


def test_renderer_clear_no_crash(pygame_init: None) -> None:
    from dronerl.gui.renderer import Renderer
    r = Renderer(_grid4(), _config())
    r.clear()


def test_renderer_draw_grid_no_crash(pygame_init: None) -> None:
    from dronerl.gui.renderer import Renderer
    r = Renderer(_grid4(), _config())
    r.clear()
    r.draw_grid((0, 0), episode=1, step=5, mode="Training", paused=False)


def test_renderer_draw_status_bar_paused(pygame_init: None) -> None:
    from dronerl.gui.renderer import Renderer
    r = Renderer(_grid4(), _config())
    r.clear()
    r.draw_status_bar("Training", paused=True, show_heatmap=True, show_arrows=False)


def test_renderer_draw_status_bar_running(pygame_init: None) -> None:
    from dronerl.gui.renderer import Renderer
    r = Renderer(_grid4(), _config())
    r.clear()
    r.draw_status_bar("Training", paused=False, show_heatmap=False, show_arrows=True)


def test_renderer_flip_no_crash(pygame_init: None) -> None:
    from dronerl.gui.renderer import Renderer
    r = Renderer(_grid4(), _config())
    r.clear()
    r.draw_grid((1, 0), 0, 0)
    r.flip()


# ---------------------------------------------------------------------------
# Heatmap smoke tests
# ---------------------------------------------------------------------------


def test_heatmap_draw_no_crash(pygame_init: None) -> None:
    import pygame
    from dronerl.gui.heatmap import HeatmapOverlay
    surf = pygame.display.get_surface()
    ho = HeatmapOverlay(cell_size=40, rows=4, cols=4)
    ho.draw(surf, _qtable4(), _grid4())


def test_heatmap_draw_all_zeros_no_crash(pygame_init: None) -> None:
    import pygame
    from dronerl.gui.heatmap import HeatmapOverlay
    surf = pygame.display.get_surface()
    ho = HeatmapOverlay(cell_size=40, rows=4, cols=4)
    ho.draw(surf, QTable(4, 4, 4), _grid4())


# ---------------------------------------------------------------------------
# Arrows smoke tests
# ---------------------------------------------------------------------------


def test_arrows_draw_no_crash(pygame_init: None) -> None:
    import pygame
    from dronerl.gui.arrows import ArrowOverlay
    surf = pygame.display.get_surface()
    ao = ArrowOverlay(cell_size=40)
    ao.draw(surf, _qtable4(), _grid4())


# ---------------------------------------------------------------------------
# Dashboard smoke tests
# ---------------------------------------------------------------------------


def test_dashboard_init_no_crash(pygame_init: None) -> None:
    from dronerl.gui.dashboard import Dashboard
    d = Dashboard(_config())
    assert d is not None


def test_dashboard_update_and_draw_no_crash(pygame_init: None) -> None:
    import pygame
    from dronerl.gui.dashboard import Dashboard
    surf = pygame.display.get_surface()
    d = Dashboard(_config())
    d.update(10, -30.0, 0.5, 120, 0.4, [-10.0, -5.0, 2.0, 8.0])
    d.draw(surf)


def test_dashboard_draw_empty_history(pygame_init: None) -> None:
    import pygame
    from dronerl.gui.dashboard import Dashboard
    surf = pygame.display.get_surface()
    d = Dashboard(_config())
    d.update(0, 0.0, 1.0, 0, 0.0, [])
    d.draw(surf)


# ---------------------------------------------------------------------------
# LevelEditor smoke tests
# ---------------------------------------------------------------------------


def test_level_editor_init_no_crash(pygame_init: None) -> None:
    import pygame
    from dronerl.gui.level_editor import LevelEditor
    surf = pygame.display.get_surface()
    ed = LevelEditor(surf, _grid4(), cell_size=40)
    assert ed is not None
