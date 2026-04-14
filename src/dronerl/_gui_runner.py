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
    cfg_ns = sdk.get_config_ns()
    renderer = Renderer(sdk.grid, cfg_ns)
    dashboard = Dashboard(cfg_ns)
    cell = int(cfg_ns.gui.cell_size)
    notify_duration = int(getattr(cfg_ns.gui, "notify_duration_ticks", 90))
    fast_steps = int(getattr(cfg_ns.gui, "fast_mode_steps", 200))
    heatmap = HeatmapOverlay(cell, sdk.grid.rows, sdk.grid.cols)
    arrows = ArrowOverlay(cell)

    show_hm = show_ar = paused = fast = False
    state = sdk.env.reset()
    ep_reward = 0.0
    ep_steps = 0
    running = True
    notify = ""
    notify_ticks = 0

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
                    notify = "PAUSED" if paused else "RESUMED"
                elif event.key == pygame.K_s:
                    sdk.save_q_table()
                    notify = "Brain saved!"
                elif event.key == pygame.K_l:
                    notify = "Brain loaded!" if sdk.load_q_table() else "No save found!"
                elif event.key == pygame.K_r:
                    sdk.agent.reset()
                    sdk.episode_rewards.clear()
                    sdk.goals_reached = 0
                    state = sdk.env.reset()
                    ep_reward, ep_steps = 0.0, 0
                    notify = "Hard reset!"
                elif event.key == pygame.K_e:
                    sdk.launch_level_editor()
                    renderer = Renderer(sdk.grid, cfg_ns)
                    heatmap = HeatmapOverlay(cell, sdk.grid.rows, sdk.grid.cols)
                    state = sdk.env.reset()
                    ep_reward, ep_steps = 0.0, 0
                    notify = "Level updated!"
                notify_ticks = notify_duration

        steps = fast_steps if fast else 1
        if not paused and running:
            for _ in range(steps):
                action = sdk.agent.select_action(state)
                ns, reward, done = sdk.env.step(action)
                sdk.agent.update(state, action, reward, ns, done)
                state = ns
                ep_reward += reward
                ep_steps += 1
                if done:
                    ct = sdk.env.grid.get_cell(*state).name
                    sdk.goals_reached += int(ct == "GOAL")
                    sdk.episode_rewards.append(ep_reward)
                    sdk.agent.end_episode()
                    state = sdk.env.reset()
                    ep_reward, ep_steps = 0.0, 0

        if notify_ticks > 0:
            notify_ticks -= 1
            if notify_ticks == 0:
                notify = ""

        ep_list = sdk.episode_rewards
        goal_rate = sdk.goals_reached / max(1, len(ep_list))
        renderer.clear()
        renderer.draw_grid(state, len(ep_list), ep_steps, paused=paused)
        if show_hm:
            heatmap.draw(renderer.screen, sdk.get_q_table(), sdk.grid)
        if show_ar:
            arrows.draw(renderer.screen, sdk.get_q_table(), sdk.grid)
        dashboard.update(len(ep_list), ep_reward,
                         sdk.agent.epsilon, ep_steps, goal_rate, ep_list)
        dashboard.draw(renderer.screen)
        dashboard.draw_notification(renderer.screen, notify)
        mode = "Fast" if fast else "Training"
        renderer.draw_status_bar(mode, paused, show_hm, show_ar, notify)
        renderer.flip()
        if not fast:
            renderer.tick()

    pygame.quit()
