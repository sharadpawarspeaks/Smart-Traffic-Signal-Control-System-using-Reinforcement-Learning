from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from smart_traffic_ai.agents.q_learning_agent import QLearningAgent
from smart_traffic_ai.environment.traffic_environment import TrafficEnvironment
from smart_traffic_ai.services.experiments import ExperimentRunner
from smart_traffic_ai.services.storage_service import StorageService

from smart_traffic_ai.ui.components import (
    BG,
    SIDEBAR,
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
)
from smart_traffic_ai.ui.dashboard import DashboardView
from smart_traffic_ai.ui.live_simulation import LiveSimulationView
from smart_traffic_ai.ui.agent_page import AgentView
from smart_traffic_ai.ui.emergency_page import EmergencyView
from smart_traffic_ai.ui.congestion_page import CongestionView
from smart_traffic_ai.ui.analytics_page import AnalyticsView
from smart_traffic_ai.ui.experiments_page import ExperimentsView
from smart_traffic_ai.ui.settings_page import SettingsView
from smart_traffic_ai.ui.about_page import AboutView


class SmartTrafficApp(ctk.CTk):
    """
    Main application window for Smart Traffic AI desktop dashboard.
    Orchestrates UI navigation, simulation loops, background training, and telemetry.
    """

    def __init__(self):
        super().__init__()
        self.title("Smart Traffic AI | Intelligent Signal Control System")
        self.geometry("1440x900")
        self.minsize(1150, 720)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Persistence & Services
        self.storage_service = StorageService()
        settings = self.storage_service.load_settings()

        # Core Simulation & Agent
        self.env = TrafficEnvironment(
            seed=settings.get("random_seed", 42),
            arrival_rates=settings.get("arrival_rates", (0.22, 0.20, 0.18, 0.16)),
            min_green=settings.get("min_green", 5),
            max_green=settings.get("max_green", 35),
            yellow_duration=settings.get("yellow_duration", 2),
            weight_pass=settings.get("weight_pass", 3.0),
            weight_wait=settings.get("weight_wait", 0.20),
            weight_queue=settings.get("weight_queue", 0.05),
            weight_switch=settings.get("weight_switch", 0.40),
        )

        self.agent = QLearningAgent(
            alpha=settings.get("learning_rate", 0.15),
            gamma=settings.get("discount_factor", 0.92),
            epsilon=settings.get("initial_epsilon", 1.0),
            epsilon_min=settings.get("epsilon_min", 0.05),
            decay=settings.get("epsilon_decay", 0.995),
            seed=settings.get("random_seed", 42),
        )
        # Attempt to load saved Q-table if available
        self.agent.load(Path("data") / "q_table.json")

        self.experiment_runner = ExperimentRunner(
            arrival_rates=self.env.arrival_rates,
            duration=120,
            seed=self.env.seed or 42,
        )

        # Simulation Runtime State
        self.running = False
        self.sim_speed = 1.0
        self.episode = 1
        self.active_page = "Dashboard"
        self.last_comparison = None

        self._build_ui()
        self.navigate("Dashboard")

    def _build_ui(self):
        self.configure(fg_color=BG)

        # 1. Left Sidebar Navigation
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color=SIDEBAR, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Branding Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=18, pady=(24, 20))

        ctk.CTkLabel(
            brand_frame,
            text="◈  SMART TRAFFIC AI",
            text_color=CYAN,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_frame,
            text="RL SIGNAL CONTROL CENTER",
            text_color=MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
        ).pack(anchor="w", pady=(2, 0))

        # Nav Buttons (9 Complete Sections)
        self.nav_items = [
            ("Dashboard", "📊"),
            ("Live Simulation", "🚦"),
            ("AI Agent", "🧠"),
            ("Emergency Vehicles", "🚨"),
            ("Congestion Monitor", "📈"),
            ("Analytics", "📉"),
            ("Experiments", "🧪"),
            ("Settings", "⚙"),
            ("About Project", "ℹ"),
        ]

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        for name, icon in self.nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}  {name}",
                anchor="w",
                height=38,
                fg_color="transparent",
                hover_color=PANEL_2,
                text_color=MUTED,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                command=lambda n=name: self.navigate(n),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[name] = btn

        # Bottom Disclaimer in Sidebar
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(expand=True, fill="both")
        disclaimer_box = ctk.CTkFrame(self.sidebar, fg_color="#06121f", corner_radius=6)
        disclaimer_box.pack(fill="x", padx=12, pady=(0, 16))
        ctk.CTkLabel(disclaimer_box, text="EDUCATIONAL SIMULATION", text_color="#53758e", font=ctk.CTkFont(size=9, weight="bold")).pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(disclaimer_box, text="B.Tech Practical Examination\nNot for real-world traffic control", text_color="#53758e", font=ctk.CTkFont(size=9), justify="left").pack(anchor="w", padx=10, pady=(0, 8))

        # 2. Main Content Area
        self.content_area = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)

        # Top Navigation Bar
        self.top_bar = ctk.CTkFrame(self.content_area, fg_color=PANEL, height=65, corner_radius=0, border_width=1, border_color=BORDER)
        self.top_bar.pack(fill="x")
        self.top_bar.pack_propagate(False)

        # Page Title in Top Bar
        self.page_title_lbl = ctk.CTkLabel(
            self.top_bar,
            text="Dashboard",
            text_color=TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
        )
        self.page_title_lbl.pack(side="left", padx=24)

        # Center Simulation Controls
        ctrl_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        ctrl_frame.pack(side="left", padx=16)

        self.top_play_btn = ctk.CTkButton(
            ctrl_frame,
            text="▶ Start",
            width=75,
            height=30,
            fg_color=GREEN,
            hover_color="#24b364",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.toggle_simulation,
        )
        self.top_play_btn.pack(side="left", padx=4)

        ctk.CTkButton(
            ctrl_frame,
            text="↺ Reset",
            width=70,
            height=30,
            fg_color="#182b3a",
            hover_color="#243f54",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.reset_simulation,
        ).pack(side="left", padx=4)

        # Right Indicators (Status, Mode, Alert Badge)
        indicators_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        indicators_frame.pack(side="right", padx=24)

        self.alert_badge = ctk.CTkLabel(
            indicators_frame,
            text="",
            text_color=RED,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.alert_badge.pack(side="left", padx=(0, 16))

        self.mode_lbl = ctk.CTkLabel(
            indicators_frame,
            text="MODE: EVALUATION",
            text_color=CYAN,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.mode_lbl.pack(side="left", padx=(0, 16))

        self.ep_lbl = ctk.CTkLabel(
            indicators_frame,
            text="EPISODE: 1",
            text_color=MUTED,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.ep_lbl.pack(side="left", padx=(0, 16))

        self.status_badge = ctk.CTkLabel(
            indicators_frame,
            text="●  READY",
            text_color=GREEN,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.status_badge.pack(side="left")

        # Scrollable Body Container
        self.body_container = ctk.CTkScrollableFrame(self.content_area, fg_color=BG, scrollbar_button_color=PANEL_2)
        self.body_container.pack(fill="both", expand=True, padx=20, pady=16)

    def navigate(self, page: str):
        self.active_page = page
        self.page_title_lbl.configure(text=page)

        # Update sidebar styling
        for name, btn in self.nav_buttons.items():
            if name == page:
                btn.configure(fg_color=PANEL_2, text_color=TEXT)
            else:
                btn.configure(fg_color="transparent", text_color=MUTED)

        # Clear body container
        for widget in self.body_container.winfo_children():
            widget.destroy()

        # Mount target page
        if page == "Dashboard":
            self.dashboard = DashboardView(self.body_container, self)
            self.current_view = self.dashboard
        elif page == "Live Simulation":
            self.live_view = LiveSimulationView(self.body_container, self)
            self.current_view = self.live_view
        elif page == "AI Agent":
            self.agent_view = AgentView(self.body_container, self)
            self.current_view = self.agent_view
        elif page == "Emergency Vehicles":
            self.emergency_view = EmergencyView(self.body_container, self)
            self.current_view = self.emergency_view
        elif page == "Congestion Monitor":
            self.congestion_view = CongestionView(self.body_container, self)
            self.current_view = self.congestion_view
        elif page == "Analytics":
            self.analytics_view = AnalyticsView(self.body_container, self)
            self.current_view = self.analytics_view
        elif page == "Experiments":
            self.experiments_view = ExperimentsView(self.body_container, self)
            self.current_view = self.experiments_view
        elif page == "Settings":
            self.settings_view = SettingsView(self.body_container, self)
            self.current_view = self.settings_view
        elif page == "About Project":
            self.about_view = AboutView(self.body_container, self)
            self.current_view = self.about_view

    def set_app_status(self, status: str, color: str):
        self.status_badge.configure(text=f"●  {status}", text_color=color)

    def toggle_simulation(self):
        if self.running:
            self.pause_simulation()
        else:
            self.start_simulation()

    def start_simulation(self):
        if self.running:
            return
        self.running = True
        self.set_app_status("SIMULATION ACTIVE", GREEN)
        self.top_play_btn.configure(text="⏸ Pause", fg_color=AMBER, hover_color="#d49b2f")
        if hasattr(self, "live_view") and hasattr(self.live_view, "play_btn"):
            self.live_view.play_btn.configure(text="⏸ Pause", fg_color=AMBER, hover_color="#d49b2f")
        self._sim_loop()

    def pause_simulation(self):
        self.running = False
        self.set_app_status("PAUSED", AMBER)
        self.top_play_btn.configure(text="▶ Resume", fg_color=GREEN, hover_color="#24b364")
        if hasattr(self, "live_view") and hasattr(self.live_view, "play_btn"):
            self.live_view.play_btn.configure(text="▶ Resume", fg_color=GREEN, hover_color="#24b364")

    def reset_simulation(self):
        self.running = False
        self.env.reset(seed=self.env.seed)
        self.set_app_status("READY", GREEN)
        self.top_play_btn.configure(text="▶ Start", fg_color=GREEN, hover_color="#24b364")
        if hasattr(self, "live_view") and hasattr(self.live_view, "play_btn"):
            self.live_view.play_btn.configure(text="▶ Start", fg_color=GREEN, hover_color="#24b364")
        self.alert_badge.configure(text="")
        if hasattr(self, "current_view") and hasattr(self.current_view, "update_data"):
            self.current_view.update_data()
        if hasattr(self, "dashboard"):
            self.dashboard.add_event("Simulation reset to initial state.")

    def step_simulation_once(self):
        state = self.env.get_state()
        action = self.agent.choose_action(state, explore=False)
        next_state, reward, done, info = self.env.step(action)
        self.agent.update(state, action, reward, next_state, done)
        if done:
            self.episode += 1
            self.ep_lbl.configure(text=f"EPISODE: {self.episode}")
            self.env.reset()
        if hasattr(self, "current_view") and hasattr(self.current_view, "update_data"):
            self.current_view.update_data()

    def request_emergency_vehicle(self, approach: int, vehicle_type: str = "ambulance"):
        self.env.request_emergency(approach, vehicle_type=vehicle_type)
        self.set_app_status("EMERGENCY ACTIVE", RED)
        self.alert_badge.configure(text="🚨 EMERGENCY PRIORITY")
        if hasattr(self, "dashboard"):
            self.dashboard.add_event(f"Emergency {vehicle_type.upper()} on Approach {approach}.")
        if hasattr(self, "current_view") and hasattr(self.current_view, "update_data"):
            self.current_view.update_data()

    def _sim_loop(self):
        if not self.running:
            return

        state = self.env.get_state()
        action = self.agent.choose_action(state, explore=False)
        next_state, reward, done, info = self.env.step(action)
        self.agent.update(state, action, reward, next_state, done)

        # Check emergency priority alert
        if self.env.signal_controller.preemption_active:
            self.alert_badge.configure(text="🚨 EMERGENCY PRIORITY")
        else:
            self.alert_badge.configure(text="")

        if done:
            self.episode += 1
            self.ep_lbl.configure(text=f"EPISODE: {self.episode}")
            self.env.reset()
            if hasattr(self, "dashboard"):
                self.dashboard.add_event(f"Episode {self.episode - 1} completed.")

        # Update currently active view
        if hasattr(self, "current_view") and hasattr(self.current_view, "update_data"):
            self.current_view.update_data()

        # Dynamic loop delay controlled by speed slider (default 120ms at 1.0x)
        delay_ms = max(25, int(120 / self.sim_speed))
        self.after(delay_ms, self._sim_loop)


if __name__ == "__main__":
    app = SmartTrafficApp()
    app.mainloop()
