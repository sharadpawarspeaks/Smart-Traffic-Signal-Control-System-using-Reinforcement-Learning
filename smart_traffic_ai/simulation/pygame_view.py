"""
Standalone / Interactive Pygame renderer for the Smart Traffic AI intersection.
Renders realistic 4-way road geometry, lane markings, traffic signals,
and vehicle types (cars, motorcycles, buses, ambulances, fire engines) with animations.
"""

from __future__ import annotations

import math
import sys
import pygame

from smart_traffic_ai.agents.q_learning_agent import QLearningAgent
from smart_traffic_ai.environment.traffic_environment import TrafficEnvironment
from smart_traffic_ai.environment.intersection import APPROACHES


def run_pygame_simulation(seed: int | None = 42, agent: QLearningAgent | None = None) -> None:
    pygame.init()
    pygame.font.init()

    width, height = 980, 720
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Smart Traffic AI | Live Pygame Intersection Simulation")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("Segoe UI", 18, bold=True)
    font_bold = pygame.font.SysFont("Segoe UI", 14, bold=True)
    font_regular = pygame.font.SysFont("Segoe UI", 12)

    env = TrafficEnvironment(seed=seed)
    if agent is None:
        agent = QLearningAgent(seed=seed)

    running = True
    paused = False
    flash_timer = 0

    road_width = 160
    cx, cy = width // 2, height // 2

    while running:
        dt = clock.tick(30)
        flash_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    env.reset(seed=seed)
                elif event.key == pygame.K_n:
                    env.request_emergency(0, "ambulance")
                elif event.key == pygame.K_s:
                    env.request_emergency(1, "fire_engine")
                elif event.key == pygame.K_e:
                    env.request_emergency(2, "ambulance")
                elif event.key == pygame.K_w:
                    env.request_emergency(3, "fire_engine")
                elif event.key == pygame.K_ESCAPE:
                    running = False

        if not paused:
            # RL agent selects action
            state = env.get_state()
            action = agent.choose_action(state, explore=False)
            state, reward, done, _ = env.step(action)
            if done:
                env.reset()

        # Render background
        screen.fill((7, 21, 37))  # Dark Navy BG

        # Draw Roads (Asphalt: #142230)
        road_color = (20, 34, 48)
        border_color = (35, 58, 80)
        pygame.draw.rect(screen, road_color, (0, cy - road_width // 2, width, road_width))
        pygame.draw.rect(screen, road_color, (cx - road_width // 2, 0, road_width, height))

        # Road curbs / borders
        pygame.draw.line(screen, border_color, (0, cy - road_width // 2), (cx - road_width // 2, cy - road_width // 2), 2)
        pygame.draw.line(screen, border_color, (cx + road_width // 2, cy - road_width // 2), (width, cy - road_width // 2), 2)
        pygame.draw.line(screen, border_color, (0, cy + road_width // 2), (cx - road_width // 2, cy + road_width // 2), 2)
        pygame.draw.line(screen, border_color, (cx + road_width // 2, cy + road_width // 2), (width, cy + road_width // 2), 2)

        pygame.draw.line(screen, border_color, (cx - road_width // 2, 0), (cx - road_width // 2, cy - road_width // 2), 2)
        pygame.draw.line(screen, border_color, (cx - road_width // 2, cy + road_width // 2), (cx - road_width // 2, height), 2)
        pygame.draw.line(screen, border_color, (cx + road_width // 2, 0), (cx + road_width // 2, cy - road_width // 2), 2)
        pygame.draw.line(screen, border_color, (cx + road_width // 2, cy + road_width // 2), (cx + road_width // 2, height), 2)

        # Crosswalks
        for offset in range(-road_width // 2 + 10, road_width // 2, 16):
            # North crosswalk
            pygame.draw.rect(screen, (75, 95, 115), (cx + offset, cy - road_width // 2 - 18, 8, 14))
            # South crosswalk
            pygame.draw.rect(screen, (75, 95, 115), (cx + offset, cy + road_width // 2 + 4, 8, 14))
            # West crosswalk
            pygame.draw.rect(screen, (75, 95, 115), (cx - road_width // 2 - 18, cy + offset, 14, 8))
            # East crosswalk
            pygame.draw.rect(screen, (75, 95, 115), (cx + road_width // 2 + 4, cy + offset, 14, 8))

        # Lane dividers (dashed)
        dash_len = 16
        gap_len = 16
        dash_color = (95, 115, 130)

        # Horizontal dashes
        for x in range(0, cx - road_width // 2 - 20, dash_len + gap_len):
            pygame.draw.line(screen, dash_color, (x, cy), (x + dash_len, cy), 2)
        for x in range(cx + road_width // 2 + 20, width, dash_len + gap_len):
            pygame.draw.line(screen, dash_color, (x, cy), (x + dash_len, cy), 2)

        # Vertical dashes
        for y in range(0, cy - road_width // 2 - 20, dash_len + gap_len):
            pygame.draw.line(screen, dash_color, (cx, y), (cx, y + dash_len), 2)
        for y in range(cy + road_width // 2 + 20, height, dash_len + gap_len):
            pygame.draw.line(screen, dash_color, (cx, y), (cx, y + dash_len), 2)

        # Stop lines (Solid)
        stop_color = (220, 230, 240)
        pygame.draw.line(screen, stop_color, (cx - road_width // 2, cy - road_width // 2), (cx, cy - road_width // 2), 4)  # North
        pygame.draw.line(screen, stop_color, (cx, cy + road_width // 2), (cx + road_width // 2, cy + road_width // 2), 4)  # South
        pygame.draw.line(screen, stop_color, (cx + road_width // 2, cy - road_width // 2), (cx + road_width // 2, cy), 4)  # East
        pygame.draw.line(screen, stop_color, (cx - road_width // 2, cy), (cx - road_width // 2, cy + road_width // 2), 4)  # West

        # Draw Traffic Lights
        phase = env.phase
        # North signal (controls North southbound approach: right side of north road)
        # South signal (controls South northbound approach)
        # East signal (controls East westbound approach)
        # West signal (controls West eastbound approach)
        ns_is_green = (phase == 0)
        ns_is_yellow = (phase == 1)
        ew_is_green = (phase == 2)
        ew_is_yellow = (phase == 3)

        def draw_light_box(x, y, is_green, is_yellow):
            pygame.draw.rect(screen, (15, 20, 28), (x, y, 22, 54), border_radius=4)
            pygame.draw.rect(screen, (50, 70, 90), (x, y, 22, 54), width=1, border_radius=4)
            # Red light
            red_on = not (is_green or is_yellow)
            pygame.draw.circle(screen, (255, 60, 60) if red_on else (60, 20, 20), (x + 11, y + 10), 6)
            # Yellow light
            pygame.draw.circle(screen, (255, 210, 50) if is_yellow else (60, 50, 15), (x + 11, y + 27), 6)
            # Green light
            pygame.draw.circle(screen, (40, 230, 110) if is_green else (15, 55, 25), (x + 11, y + 44), 6)

        draw_light_box(cx - road_width // 2 - 28, cy - road_width // 2 - 60, ns_is_green, ns_is_yellow)  # North
        draw_light_box(cx + road_width // 2 + 6, cy + road_width // 2 + 6, ns_is_green, ns_is_yellow)   # South
        draw_light_box(cx + road_width // 2 + 6, cy - road_width // 2 - 60, ew_is_green, ew_is_yellow)  # East
        draw_light_box(cx - road_width // 2 - 28, cy + road_width // 2 + 6, ew_is_green, ew_is_yellow)  # West

        # Render Vehicles
        siren_on = (flash_timer // 250) % 2 == 0
        for v in env.vehicles:
            pos = v.position
            # Compute screen coordinates based on approach and position
            # Approach 0: North -> moving South (top to bottom)
            # Approach 1: South -> moving North (bottom to top)
            # Approach 2: East -> moving West (right to left)
            # Approach 3: West -> moving East (left to right)
            if v.approach == 0:
                vx = cx - road_width // 4
                vy = (cy - road_width // 2) * min(1.0, pos) + (road_width * max(0.0, pos - 1.0) * 3)
                v_w, v_h = 24, int(v.length * 4.0)
            elif v.approach == 1:
                vx = cx + road_width // 4
                vy = height - (height - (cy + road_width // 2)) * min(1.0, pos) - (road_width * max(0.0, pos - 1.0) * 3)
                v_w, v_h = 24, int(v.length * 4.0)
            elif v.approach == 2:
                vx = width - (width - (cx + road_width // 2)) * min(1.0, pos) - (road_width * max(0.0, pos - 1.0) * 3)
                vy = cy - road_width // 4
                v_w, v_h = int(v.length * 4.0), 24
            else:  # Approach 3
                vx = (cx - road_width // 2) * min(1.0, pos) + (road_width * max(0.0, pos - 1.0) * 3)
                vy = cy + road_width // 4
                v_w, v_h = int(v.length * 4.0), 24

            v_rect = pygame.Rect(int(vx - v_w / 2), int(vy - v_h / 2), v_w, v_h)
            pygame.draw.rect(screen, v.pygame_color, v_rect, border_radius=4)
            pygame.draw.rect(screen, (220, 240, 255), v_rect, width=1, border_radius=4)

            # Flashing emergency siren
            if v.emergency:
                siren_color = (255, 30, 30) if siren_on else (40, 150, 255)
                pygame.draw.circle(screen, siren_color, (int(vx), int(vy)), 5)

        # HUD Panel at top
        hud_rect = pygame.Rect(20, 16, width - 40, 52)
        pygame.draw.rect(screen, (13, 33, 52), hud_rect, border_radius=8)
        pygame.draw.rect(screen, (28, 54, 80), hud_rect, width=1, border_radius=8)

        # Brand / Title
        title_surf = font_title.render("SMART TRAFFIC AI", True, (39, 211, 230))
        screen.blit(title_surf, (36, 28))

        # Metrics
        m = env.get_metrics()
        info_str = f"Phase: {m['phase_name']} ({env.phase_time}s)  |  Waiting: {m['waiting']}  |  Passed: {m['passed']}  |  Avg Wait: {m['average_wait']:.1f}s  |  Reward: {m['episode_reward']:.1f}"
        info_surf = font_bold.render(info_str, True, (237, 246, 255))
        screen.blit(info_surf, (220, 30))

        # Emergency Alert Banner
        if env.emergency_approach is not None:
            alert_surf = font_bold.render("🚨 EMERGENCY VEHICLE PRIORITY ACTIVE", True, (255, 93, 103))
            screen.blit(alert_surf, (width - 340, 30))

        # Bottom Instructions
        instruct = "Controls: [Space] Pause/Resume  |  [N/S/E/W] Spawn Emergency Vehicle  |  [R] Reset  |  [Esc] Exit"
        inst_surf = font_regular.render(instruct, True, (141, 168, 189))
        screen.blit(inst_surf, (30, height - 30))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    run_pygame_simulation()
