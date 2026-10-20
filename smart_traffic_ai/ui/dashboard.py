from __future__ import annotations

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
    create_kpi_card,
)
from smart_traffic_ai.environment.intersection import APPROACHES
from smart_traffic_ai.controllers.signal_controller import PHASE_NAMES

if TYPE_CHECKING:
    from smart_traffic_ai.ui.main_window import SmartTrafficApp


class DashboardView:
    def __init__(self, parent: ctk.CTkFrame, app: SmartTrafficApp):
        self.parent = parent
        self.app = app
        self.kpi_labels: dict[str, ctk.CTkLabel] = {}
        self.density_bars = []
        self.events_list: list[str] = [
            "System initialized. Ready for simulation.",
            "Q-learning agent loaded.",
            "Signal Safety Controller active.",
        ]
        self._build_ui()

    def _build_ui(self):
        # 1. Six KPI Cards Row
        kpi_row = ctk.CTkFrame(self.parent, fg_color="transparent")
        kpi_row.pack(fill="x", pady=(0, 16))

        cards_data = [
            ("Total Vehicles", "0", CYAN, "Spawned vehicles"),
            ("Vehicles Waiting", "0", AMBER, "Currently stopped"),
            ("Vehicles Passed", "0", GREEN, "Crossed intersection"),
            ("Avg Waiting Time", "0.0 s", AMBER, "Per vehicle delay"),
            ("Avg Queue Length", "0.0", RED, "Across 4 corridors"),
            ("Emergency Vehicles", "0", RED, "Active priority requests"),
        ]

        for title, val, col, sub in cards_data:
            _, label = create_kpi_card(kpi_row, title, val, col, sub)
            self.kpi_labels[title] = label

        # 2. Main Content Split: Left (Intersection Canvas) & Right (Panels)
        main_split = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_split.pack(fill="both", expand=True)

        # Left: Intersection Preview
        left_panel = ctk.CTkFrame(main_split, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        header_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        header_frame.pack(fill="x", padx=18, pady=(16, 8))

        ctk.CTkLabel(
            header_frame,
            text="FOUR-WAY INTERSECTION PREVIEW",
            text_color=TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
        ).pack(side="left")

        self.phase_badge = ctk.CTkLabel(
            header_frame,
            text="PHASE: NS GREEN (0s)",
            text_color=GREEN,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        )
        self.phase_badge.pack(side="right")

        self.canvas = tk.Canvas(left_panel, width=540, height=420, bg="#0a1b2b", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Right: AI Decision + Traffic Density + Recent Events
        right_panel = ctk.CTkFrame(main_split, fg_color="transparent", width=380)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        # AI Decision Panel
        dec_panel = ctk.CTkFrame(right_panel, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        dec_panel.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            dec_panel,
            text="AI DECISION MONITOR",
            text_color=TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 6))

        self.dec_state_label = ctk.CTkLabel(dec_panel, text="State: (0, 0, 0, 0, 0)", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.dec_state_label.pack(anchor="w", padx=16, pady=1)

        self.dec_action_label = ctk.CTkLabel(dec_panel, text="Action: 0 (Prioritize NS)", text_color=CYAN, font=ctk.CTkFont(size=12, weight="bold"))
        self.dec_action_label.pack(anchor="w", padx=16, pady=2)

        self.dec_reward_label = ctk.CTkLabel(dec_panel, text="Immediate Reward: +0.00  |  Cumulative: 0.00", text_color=TEXT, font=ctk.CTkFont(size=11))
        self.dec_reward_label.pack(anchor="w", padx=16, pady=2)

        self.dec_reason_label = ctk.CTkLabel(
            dec_panel,
            text="Dynamic reasoning: Waiting for first decision step.",
            text_color="#8da8bd",
            justify="left",
            wraplength=340,
            font=ctk.CTkFont(size=11),
        )
        self.dec_reason_label.pack(anchor="w", padx=16, pady=(4, 14))

        # Traffic Density Overview (Horizontal bars)
        dens_panel = ctk.CTkFrame(right_panel, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        dens_panel.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            dens_panel,
            text="APPROACH TRAFFIC DENSITY",
            text_color=TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 6))

        for name in APPROACHES:
            row = ctk.CTkFrame(dens_panel, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(row, text=name, text_color=MUTED, width=50, anchor="w", font=ctk.CTkFont(size=11)).pack(side="left")
            p_bar = ctk.CTkProgressBar(row, height=8, progress_color=CYAN, fg_color="#182b3a")
            p_bar.pack(side="left", fill="x", expand=True, padx=8)
            p_bar.set(0)
            val_lbl = ctk.CTkLabel(row, text="0", text_color=TEXT, width=30, anchor="e", font=ctk.CTkFont(size=11, weight="bold"))
            val_lbl.pack(side="right")
            self.density_bars.append((p_bar, val_lbl))

        ctk.CTkFrame(dens_panel, height=8, fg_color="transparent").pack()

        # Recent Events Log
        events_panel = ctk.CTkFrame(right_panel, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        events_panel.pack(fill="both", expand=True)
        ctk.CTkLabel(
            events_panel,
            text="RECENT EVENT LOG",
            text_color=TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 6))

        self.events_box = ctk.CTkTextbox(
            events_panel,
            fg_color="#0a1b2b",
            text_color=MUTED,
            font=ctk.CTkFont(family="Consolas", size=10),
            activate_scrollbars=True,
        )
        self.events_box.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self._refresh_events_box()

    def add_event(self, text: str):
        self.events_list.append(text)
        if len(self.events_list) > 40:
            self.events_list.pop(0)
        self._refresh_events_box()

    def _refresh_events_box(self):
        if not hasattr(self, "events_box") or not self.events_box.winfo_exists():
            return
        self.events_box.configure(state="normal")
        self.events_box.delete("1.0", "end")
        for ev in reversed(self.events_list[-15:]):
            self.events_box.insert("end", f"• {ev}\n")
        self.events_box.configure(state="disabled")

    def draw_intersection(self):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return

        c = self.canvas
        c.delete("all")
        w = max(500, c.winfo_width())
        h = max(380, c.winfo_height())
        cx, cy = w // 2, h // 2
        road_w = 120

        # Draw Asphalt Roads
        c.create_rectangle(0, cy - road_w // 2, w, cy + road_w // 2, fill="#182b38", outline="")
        c.create_rectangle(cx - road_w // 2, 0, cx + road_w // 2, h, fill="#182b38", outline="")

        # Crosswalks
        for offset in range(-road_w // 2 + 8, road_w // 2, 14):
            # North
            c.create_rectangle(cx + offset, cy - road_w // 2 - 14, cx + offset + 7, cy - road_w // 2 - 2, fill="#486173", outline="")
            # South
            c.create_rectangle(cx + offset, cy + road_w // 2 + 2, cx + offset + 7, cy + road_w // 2 + 14, fill="#486173", outline="")
            # West
            c.create_rectangle(cx - road_w // 2 - 14, cy + offset, cx - road_w // 2 - 2, cy + offset + 7, fill="#486173", outline="")
            # East
            c.create_rectangle(cx + road_w // 2 + 2, cy + offset, cx + road_w // 2 + 14, cy + offset + 7, fill="#486173", outline="")

        # Lane dividers
        c.create_line(0, cy, cx - road_w // 2 - 14, cy, fill="#688090", dash=(8, 8), width=2)
        c.create_line(cx + road_w // 2 + 14, cy, w, cy, fill="#688090", dash=(8, 8), width=2)
        c.create_line(cx, 0, cx, cy - road_w // 2 - 14, fill="#688090", dash=(8, 8), width=2)
        c.create_line(cx, cy + road_w // 2 + 14, cx, h, fill="#688090", dash=(8, 8), width=2)

        # Stop lines
        c.create_line(cx - road_w // 2, cy - road_w // 2, cx, cy - road_w // 2, fill="#d0e0ec", width=3)  # North
        c.create_line(cx, cy + road_w // 2, cx + road_w // 2, cy + road_w // 2, fill="#d0e0ec", width=3)  # South
        c.create_line(cx + road_w // 2, cy - road_w // 2, cx + road_w // 2, cy, fill="#d0e0ec", width=3)  # East
        c.create_line(cx - road_w // 2, cy, cx - road_w // 2, cy + road_w // 2, fill="#d0e0ec", width=3)  # West

        # Intersection Box
        c.create_rectangle(cx - road_w // 2, cy - road_w // 2, cx + road_w // 2, cy + road_w // 2, fill="#223644", outline="#3b5668")

        # Approach Labels
        c.create_text(cx, 16, text="NORTH", fill=MUTED, font=("Segoe UI", 9, "bold"))
        c.create_text(cx, h - 14, text="SOUTH", fill=MUTED, font=("Segoe UI", 9, "bold"))
        c.create_text(w - 24, cy, text="EAST", fill=MUTED, font=("Segoe UI", 9, "bold"))
        c.create_text(24, cy, text="WEST", fill=MUTED, font=("Segoe UI", 9, "bold"))

        # Traffic Lights & Signals
        phase = self.app.env.phase
        ns_green = phase == 0
        ns_yellow = phase == 1
        ew_green = phase == 2
        ew_yellow = phase == 3

        def draw_signal_lamp(x, y, is_grn, is_yel):
            c.create_rectangle(x - 8, y - 22, x + 8, y + 22, fill="#0c1822", outline="#2f495e")
            # Red
            r_col = RED if not (is_grn or is_yel) else "#401518"
            c.create_oval(x - 5, y - 18, x + 5, y - 8, fill=r_col, outline="")
            # Yellow
            y_col = AMBER if is_yel else "#3b3010"
            c.create_oval(x - 5, y - 5, x + 5, y + 5, fill=y_col, outline="")
            # Green
            g_col = GREEN if is_grn else "#10381e"
            c.create_oval(x - 5, y + 8, x + 5, y + 18, fill=g_col, outline="")

        draw_signal_lamp(cx - road_w // 2 - 14, cy - road_w // 2 - 28, ns_green, ns_yellow)
        draw_signal_lamp(cx + road_w // 2 + 14, cy + road_w // 2 + 28, ns_green, ns_yellow)
        draw_signal_lamp(cx + road_w // 2 + 28, cy - road_w // 2 - 14, ew_green, ew_yellow)
        draw_signal_lamp(cx - road_w // 2 - 28, cy + road_w // 2 + 14, ew_green, ew_yellow)

        # Vehicles Queue Rendering
        queues = self.app.env._queues()
        active_vehicles = self.app.env.vehicles

        # Render North vehicles
        n_vehs = [v for v in active_vehicles if v.approach == 0 and not v.crossed]
        for idx, v in enumerate(n_vehs[:8]):
            vy = (cy - road_w // 2) - 16 - (idx * 20)
            vx = cx - road_w // 4
            color = RED if v.emergency else v.color
            c.create_rectangle(vx - 8, vy - 6, vx + 8, vy + 6, fill=color, outline="#ffffff" if v.emergency else "")

        # Render South vehicles
        s_vehs = [v for v in active_vehicles if v.approach == 1 and not v.crossed]
        for idx, v in enumerate(s_vehs[:8]):
            vy = (cy + road_w // 2) + 16 + (idx * 20)
            vx = cx + road_w // 4
            color = RED if v.emergency else v.color
            c.create_rectangle(vx - 8, vy - 6, vx + 8, vy + 6, fill=color, outline="#ffffff" if v.emergency else "")

        # Render East vehicles
        e_vehs = [v for v in active_vehicles if v.approach == 2 and not v.crossed]
        for idx, v in enumerate(e_vehs[:8]):
            vx = (cx + road_w // 2) + 16 + (idx * 20)
            vy = cy - road_w // 4
            color = RED if v.emergency else v.color
            c.create_rectangle(vx - 6, vy - 8, vx + 6, vy + 8, fill=color, outline="#ffffff" if v.emergency else "")

        # Render West vehicles
        w_vehs = [v for v in active_vehicles if v.approach == 3 and not v.crossed]
        for idx, v in enumerate(w_vehs[:8]):
            vx = (cx - road_w // 2) - 16 - (idx * 20)
            vy = cy + road_w // 4
            color = RED if v.emergency else v.color
            c.create_rectangle(vx - 6, vy - 8, vx + 6, vy + 8, fill=color, outline="#ffffff" if v.emergency else "")

        # Center Status Text
        c.create_text(
            cx,
            cy,
            text=f"{PHASE_NAMES[phase]}\n{self.app.env.phase_time}s elapsed",
            fill=TEXT,
            font=("Segoe UI", 11, "bold"),
            justify="center",
        )

    def update_data(self):
        metrics = self.app.env.get_metrics()

        # Update KPIs
        self.kpi_labels["Total Vehicles"].configure(text=str(metrics["total_vehicles"]))
        self.kpi_labels["Vehicles Waiting"].configure(text=str(metrics["waiting"]))
        self.kpi_labels["Vehicles Passed"].configure(text=str(metrics["passed"]))
        self.kpi_labels["Avg Waiting Time"].configure(text=f"{metrics['average_wait']:.1f} s")
        self.kpi_labels["Avg Queue Length"].configure(text=f"{metrics['average_queue']:.1f}")
        self.kpi_labels["Emergency Vehicles"].configure(text=str(metrics["active_emergencies"]))

        # Phase badge
        self.phase_badge.configure(
            text=f"PHASE: {metrics['phase_name'].upper()} ({self.app.env.phase_time}s)",
            text_color=GREEN if self.app.env.phase in (0, 2) else AMBER,
        )

        # Traffic density bars
        queues = metrics["queues"]
        for idx, (p_bar, val_lbl) in enumerate(self.density_bars):
            q_val = queues[idx]
            p_bar.set(min(1.0, q_val / 12.0))
            if q_val >= 10:
                p_bar.configure(progress_color=RED)
            elif q_val >= 5:
                p_bar.configure(progress_color=AMBER)
            else:
                p_bar.configure(progress_color=CYAN)
            val_lbl.configure(text=str(q_val))

        # AI Decision
        state = self.app.env.get_state()
        self.dec_state_label.configure(text=f"Observed State: {state}")
        self.dec_reward_label.configure(
            text=f"Cumulative Episode Reward: {metrics['episode_reward']:.2f}"
        )
        self.dec_reason_label.configure(text=self.app.env.last_decision_reason)

        # Draw intersection
        self.draw_intersection()
