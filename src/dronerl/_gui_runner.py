"""Pygame game-loop implementation — internal, called only from DroneRLSDK."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dronerl.sdk import DroneRLSDK


def run_gui_loop(sdk: DroneRLSDK) -> None:  # noqa: C901
    """Execute the interactive Pygame training loop.

    All state is owned by *sdk*; this function only drives the event loop.
    """
    import pygame

    from dronerl.gui.arrows import ArrowOverlay
    from dronerl.gui.dashboard import Dashboard
    from dronerl.gui.heatmap import HeatmapOverlay
    from dronerl.gui.renderer import Renderer

    pygame.init()
    cfg_ns = sdk._make_config_ns()  # noqa: SLF001
    renderer = Renderer(sdk._grid, cfg_ns)  # noqa: SLF001
    dashboard = Dashboard(cfg_ns)
    cell = int(cfg_ns.gui.cell_size)
    heatmap = HeatmapOverlay(cell, sdk._grid.rows, sdk._grid.cols)  # noqa: SLF001
    arrows = ArrowOverlay(cell)

    show_hm = show_ar = paused = fast = False
    state = sdk._env.reset()  # noqa: SLF001
    ep_reward = 0.0
    ep_steps = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_w:
                    show_hm = not show_hm
                elif event.key == pygame.K_a:
                    show_ar = not show_ar
                elif event.key == pygame.K_f:
                    fast = not fast
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_s:
                    sdk.save_q_table()
                elif event.key == pygame.K_l:
                    sdk.load_q_table()
                elif event.key == pygame.K_r:
                    sdk._agent.reset()  # noqa: SLF001
                    sdk._episode_rewards.clear()  # noqa: SLF001
                    sdk._goals_reached = 0  # noqa: SLF001
                    state = sdk._env.reset()  # noqa: SLF001
                    ep_reward, ep_steps = 0.0, 0
                elif event.key == pygame.K_e:
                    sdk.launch_level_editor()

        if not paused and running:
            action = sdk._agent.select_action(state)  # noqa: SLF001
            ns, reward, done = sdk._env.step(action)  # noqa: SLF001
            sdk._agent.update(state, action, reward, ns, done)  # noqa: SLF001
            state = ns
            ep_reward += reward
            ep_steps += 1
            if done:
                ct = sdk._env.grid.get_cell(*state).name  # noqa: SLF001
                sdk._goals_reached += int(ct == "GOAL")  # noqa: SLF001
                sdk._episode_rewards.append(ep_reward)  # noqa: SLF001
                sdk._agent.end_episode()  # noqa: SLF001
                state = sdk._env.reset()  # noqa: SLF001
                ep_reward, ep_steps = 0.0, 0

        if not fast and running:
            ep_list = sdk._episode_rewards  # noqa: SLF001
            goal_rate = sdk._goals_reached / max(1, len(ep_list))  # noqa: SLF001
            renderer.clear()
            renderer.draw_grid(state, len(ep_list), ep_steps, paused=paused)
            if show_hm:
                heatmap.draw(renderer._screen, sdk._q_table, sdk._grid)  # noqa: SLF001
            if show_ar:
                arrows.draw(renderer._screen, sdk._q_table, sdk._grid)  # noqa: SLF001
            dashboard.update(len(ep_list), ep_reward,
                             sdk._agent.epsilon, ep_steps, goal_rate, ep_list)  # noqa: SLF001
            dashboard.draw(renderer._screen)  # noqa: SLF001
            renderer.draw_status_bar("Training", paused, show_hm, show_ar)
            renderer.flip()
            renderer.tick()

    pygame.quit()
