from __future__ import annotations

import threading
import tkinter as tk
from typing import TYPE_CHECKING
import customtkinter as ctk

from smart_traffic_ai.ui.components import (
    BG,
    PANEL,
    PANEL_2,
    BORDER,
    CYAN,
    BLUE,
    GREEN,
    AMBER,
    RED,
    TEXT,
    MUTED,
    create_section_header,
)
from smart_traffic_ai.environment.intersection import APPROACHES
from smart_traffic_ai.simulation.traffic_generator import TRAFFIC_PRESETS

if TYPE_CHECKING:
    from smart_traffic_ai.ui.main_window import SmartTrafficApp


class LiveSimulationView:
    def __init__(self, parent: ctk.CTkFrame, app: SmartTrafficApp):
        self.parent = parent
        self.app = app
        self.arrival_sliders = []
        self._build_ui()

    def _build_ui(self):
        create_section_header(
            self.parent,
            "Interactive Four-Way Traffic Simulation",
            "Real-time signal control, vehicle movement physics, and traffic demand injection",
        )

        # Main Layout Split: Left (Controls & Configuration) & Right (Interactive Canvas)
        layout = ctk.CTkFrame(self.parent, fg_color="transparent")
        layout.pack(fill="both", expand=True)

        left_ctrl = ctk.CTkFrame(layout, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER, width=360)
        left_ctrl.pack(side="left", fill="y", padx=(0, 12))
        left_ctrl.pack_propagate(False)

        # Simulation Speed & Engine Controls
        ctk.CTkLabel(left_ctrl, text="SIMULATION SPEED & CONTROLS", text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(16, 8))

        btn_row = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 10))

        self.play_btn = ctk.CTkButton(btn_row, text="▶ Start", fg_color=GREEN, hover_color="#24b364", width=75, command=self.app.toggle_simulation)
        self.play_btn.pack(side="left", padx=(0, 6))

        self.step_btn = ctk.CTkButton(btn_row, text="⏭ Step", fg_color="#1f3d59", hover_color="#275075", width=70, command=self.app.step_simulation_once)
        self.step_btn.pack(side="left", padx=(0, 6))

        ctk.CTkButton(btn_row, text="↺ Reset", fg_color="#2a3847", hover_color="#36495c", width=70, command=self.app.reset_simulation).pack(side="left")

        speed_frame = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        speed_frame.pack(fill="x", padx=16, pady=(0, 12))
        self.speed_lbl = ctk.CTkLabel(speed_frame, text="Speed: 1.0x", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.speed_lbl.pack(anchor="w")
        self.speed_slider = ctk.CTkSlider(speed_frame, from_=0.2, to=3.0, number_of_steps=14, command=self._on_speed_change)
        self.speed_slider.set(1.0)
        self.speed_slider.pack(fill="x", pady=4)

        # Traffic Presets
        ctk.CTkLabel(left_ctrl, text="TRAFFIC INTENSITY PRESETS", text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(10, 6))
        preset_row = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        preset_row.pack(fill="x", padx=16, pady=(0, 10))

        for preset in ("Low", "Medium", "High"):
            ctk.CTkButton(
                preset_row,
                text=preset,
                width=65,
                fg_color="#1b344b",
                hover_color=PANEL_2,
                command=lambda p=preset: self._apply_preset(p),
            ).pack(side="left", padx=2)

        # Arrival Rates Per Corridor
        ctk.CTkLabel(left_ctrl, text="CORRIDOR ARRIVAL RATES (veh/sec)", text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(6, 6))
        for idx, name in enumerate(APPROACHES):
            row = ctk.CTkFrame(left_ctrl, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=2)
            lbl = ctk.CTkLabel(row, text=f"{name}: {self.app.env.arrival_rates[idx]:.2f}", text_color=MUTED, width=80, anchor="w", font=ctk.CTkFont(size=11))
            lbl.pack(side="left")
            slider = ctk.CTkSlider(
                row,
                from_=0.02,
                to=0.60,
                number_of_steps=29,
                command=lambda val, i=idx, l=lbl: self._on_arrival_change(i, val, l),
            )
            slider.set(self.app.env.arrival_rates[idx])
            slider.pack(side="right", fill="x", expand=True, padx=(4, 0))
            self.arrival_sliders.append((slider, lbl))

        # Emergency Priority Quick Injection
        ctk.CTkLabel(left_ctrl, text="SPAWN EMERGENCY VEHICLE", text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(14, 6))
        em_row = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        em_row.pack(fill="x", padx=16, pady=(0, 10))

        for app_idx, app_name in enumerate(("North", "South", "East", "West")):
            ctk.CTkButton(
                em_row,
                text=app_name[0],
                width=45,
                fg_color=RED,
                hover_color="#e03e49",
                command=lambda a=app_idx: self.app.request_emergency_vehicle(a, "ambulance"),
            ).pack(side="left", padx=2)

        # Pygame Standalone Window Launcher
        ctk.CTkButton(
            left_ctrl,
            text="⛶  Launch Pygame 60FPS Window",
            fg_color="#184260",
            hover_color="#20557c",
            command=self._launch_standalone_pygame,
        ).pack(fill="x", padx=16, pady=(12, 16))

        # Right: Interactive Visualizer Canvas
        right_panel = ctk.CTkFrame(layout, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        right_panel.pack(side="right", fill="both", expand=True)

        self.canvas = tk.Canvas(right_panel, bg="#081726", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=14, pady=14)

    def _on_speed_change(self, val: float):
        self.app.sim_speed = float(val)
        self.speed_lbl.configure(text=f"Speed: {val:.1f}x")

    def _apply_preset(self, preset: str):
        rates = TRAFFIC_PRESETS[preset]
        self.app.env.generator.set_preset(preset)
        self.app.env.arrival_rates = list(rates)
        for i, (slider, lbl) in enumerate(self.arrival_sliders):
            slider.set(rates[i])
            lbl.configure(text=f"{APPROACHES[i]}: {rates[i]:.2f}")
        self.app.dashboard.add_event(f"Traffic preset changed to {preset}.")

    def _on_arrival_change(self, index: int, val: float, lbl: ctk.CTkLabel):
        self.app.env.arrival_rates[index] = round(val, 2)
        self.app.env.generator.arrival_rates[index] = round(val, 2)
        lbl.configure(text=f"{APPROACHES[index]}: {val:.2f}")

    def _launch_standalone_pygame(self):
        def worker():
            from smart_traffic_ai.simulation.pygame_view import run_pygame_simulation
            run_pygame_simulation(seed=self.app.env.seed, agent=self.app.agent)
        threading.Thread(target=worker, daemon=True).start()

    def update_data(self):
        # Synchronize play button label
        if self.app.running:
            self.play_btn.configure(text="⏸ Pause", fg_color=AMBER, hover_color="#d49b2f")
        else:
            self.play_btn.configure(text="▶ Start", fg_color=GREEN, hover_color="#24b364")

        # Redraw canvas
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return

        c = self.canvas
        c.delete("all")
        w = max(500, c.winfo_width())
        h = max(380, c.winfo_height())
        cx, cy = w // 2, h // 2
        road_w = 140

        # Draw Roads
        c.create_rectangle(0, cy - road_w // 2, w, cy + road_w // 2, fill="#182b38", outline="")
        c.create_rectangle(cx - road_w // 2, 0, cx + road_w // 2, h, fill="#182b38", outline="")

        # Stop lines
        c.create_line(cx - road_w // 2, cy - road_w // 2, cx, cy - road_w // 2, fill="#d0e0ec", width=3)
        c.create_line(cx, cy + road_w // 2, cx + road_w // 2, cy + road_w // 2, fill="#d0e0ec", width=3)
        c.create_line(cx + road_w // 2, cy - road_w // 2, cx + road_w // 2, cy, fill="#d0e0ec", width=3)
        c.create_line(cx - road_w // 2, cy, cx - road_w // 2, cy + road_w // 2, fill="#d0e0ec", width=3)

        # Center intersection
        c.create_rectangle(cx - road_w // 2, cy - road_w // 2, cx + road_w // 2, cy + road_w // 2, fill="#223644", outline="#3b5668")

        # Approach Labels
        c.create_text(cx, 16, text="NORTH APPROACH", fill=MUTED, font=("Segoe UI", 9, "bold"))
        c.create_text(cx, h - 14, text="SOUTH APPROACH", fill=MUTED, font=("Segoe UI", 9, "bold"))
        c.create_text(w - 60, cy - 20, text="EAST APPROACH", fill=MUTED, font=("Segoe UI", 9, "bold"))
        c.create_text(60, cy + 20, text="WEST APPROACH", fill=MUTED, font=("Segoe UI", 9, "bold"))

        # Render Active Moving Vehicles
        for v in self.app.env.vehicles:
            pos = v.position
            # Approach coordinate mapping
            if v.approach == 0:  # North
                vx = cx - road_w // 4
                vy = (cy - road_w // 2) * min(1.0, pos) + (road_w * max(0.0, pos - 1.0) * 2.5)
                vw, vh = 18, int(v.length * 2.5)
            elif v.approach == 1:  # South
                vx = cx + road_w // 4
                vy = h - (h - (cy + road_w // 2)) * min(1.0, pos) - (road_w * max(0.0, pos - 1.0) * 2.5)
                vw, vh = 18, int(v.length * 2.5)
            elif v.approach == 2:  # East
                vx = w - (w - (cx + road_w // 2)) * min(1.0, pos) - (road_w * max(0.0, pos - 1.0) * 2.5)
                vy = cy - road_w // 4
                vw, vh = int(v.length * 2.5), 18
            else:  # West
                vx = (cx - road_w // 2) * min(1.0, pos) + (road_w * max(0.0, pos - 1.0) * 2.5)
                vy = cy + road_w // 4
                vw, vh = int(v.length * 2.5), 18

            color = RED if v.emergency else v.color
            c.create_rectangle(vx - vw / 2, vy - vh / 2, vx + vw / 2, vy + vh / 2, fill=color, outline="#ffffff" if v.emergency else "")
