from __future__ import annotations

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
from smart_traffic_ai.services.storage_service import DEFAULT_SETTINGS

if TYPE_CHECKING:
    from smart_traffic_ai.ui.main_window import SmartTrafficApp


class SettingsView:
    def __init__(self, parent: ctk.CTkFrame, app: SmartTrafficApp):
        self.parent = parent
        self.app = app
        self._build_ui()

    def _build_ui(self):
        create_section_header(
            self.parent,
            "System Configuration & Algorithmic Parameters",
            "Fine-tune safety timing bounds, reinforcement learning reward weights, and persistence defaults",
        )

        settings = self.app.storage_service.load_settings()

        # Two Column Configuration Grid
        cols_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        cols_frame.pack(fill="both", expand=True)

        # Left Column: Signal Safety Timing Bounds
        left_col = ctk.CTkFrame(cols_frame, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(left_col, text="SIGNAL SAFETY TIMING BOUNDS", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=18, pady=(16, 12))

        # Min green
        self.min_g_lbl = ctk.CTkLabel(left_col, text=f"Minimum Green Duration: {self.app.env.signal_controller.min_green}s", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.min_g_lbl.pack(anchor="w", padx=18)
        self.min_g_slider = ctk.CTkSlider(left_col, from_=3, to=15, number_of_steps=12, command=lambda v: self.min_g_lbl.configure(text=f"Minimum Green Duration: {int(v)}s"))
        self.min_g_slider.set(self.app.env.signal_controller.min_green)
        self.min_g_slider.pack(fill="x", padx=18, pady=(2, 12))

        # Max green
        self.max_g_lbl = ctk.CTkLabel(left_col, text=f"Maximum Green Duration: {self.app.env.signal_controller.max_green}s", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.max_g_lbl.pack(anchor="w", padx=18)
        self.max_g_slider = ctk.CTkSlider(left_col, from_=15, to=60, number_of_steps=45, command=lambda v: self.max_g_lbl.configure(text=f"Maximum Green Duration: {int(v)}s"))
        self.max_g_slider.set(self.app.env.signal_controller.max_green)
        self.max_g_slider.pack(fill="x", padx=18, pady=(2, 12))

        # Yellow duration
        self.yel_lbl = ctk.CTkLabel(left_col, text=f"Yellow Interval Duration: {self.app.env.signal_controller.yellow_duration}s", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.yel_lbl.pack(anchor="w", padx=18)
        self.yel_slider = ctk.CTkSlider(left_col, from_=1, to=5, number_of_steps=4, command=lambda v: self.yel_lbl.configure(text=f"Yellow Interval Duration: {int(v)}s"))
        self.yel_slider.set(self.app.env.signal_controller.yellow_duration)
        self.yel_slider.pack(fill="x", padx=18, pady=(2, 16))

        # Starvation Threshold
        self.starve_thresh_lbl = ctk.CTkLabel(left_col, text=f"Starvation Alert Threshold: {int(self.app.env.metrics_service.starvation_threshold)}s", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.starve_thresh_lbl.pack(anchor="w", padx=18)
        self.starve_thresh_slider = ctk.CTkSlider(left_col, from_=20, to=90, number_of_steps=14, command=lambda v: self.starve_thresh_lbl.configure(text=f"Starvation Alert Threshold: {int(v)}s"))
        self.starve_thresh_slider.set(self.app.env.metrics_service.starvation_threshold)
        self.starve_thresh_slider.pack(fill="x", padx=18, pady=(2, 16))

        # Right Column: Reward Function Formulation Weights
        right_col = ctk.CTkFrame(cols_frame, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        right_col.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(right_col, text="REWARD FUNCTION WEIGHT FORMULATION", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=18, pady=(16, 12))

        # Weight Pass
        self.w_pass_lbl = ctk.CTkLabel(right_col, text=f"Throughput Reward Weight: +{self.app.env.weight_pass:.2f}", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.w_pass_lbl.pack(anchor="w", padx=18)
        self.w_pass_slider = ctk.CTkSlider(right_col, from_=0.5, to=6.0, number_of_steps=55, command=lambda v: self.w_pass_lbl.configure(text=f"Throughput Reward Weight: +{v:.2f}"))
        self.w_pass_slider.set(self.app.env.weight_pass)
        self.w_pass_slider.pack(fill="x", padx=18, pady=(2, 10))

        # Weight Wait
        self.w_wait_lbl = ctk.CTkLabel(right_col, text=f"Waiting Delay Penalty Weight: -{self.app.env.weight_wait:.2f}", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.w_wait_lbl.pack(anchor="w", padx=18)
        self.w_wait_slider = ctk.CTkSlider(right_col, from_=0.05, to=0.80, number_of_steps=75, command=lambda v: self.w_wait_lbl.configure(text=f"Waiting Delay Penalty Weight: -{v:.2f}"))
        self.w_wait_slider.set(self.app.env.weight_wait)
        self.w_wait_slider.pack(fill="x", padx=18, pady=(2, 10))

        # Weight Queue
        self.w_queue_lbl = ctk.CTkLabel(right_col, text=f"Queue Length Penalty Weight: -{self.app.env.weight_queue:.2f}", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.w_queue_lbl.pack(anchor="w", padx=18)
        self.w_queue_slider = ctk.CTkSlider(right_col, from_=0.01, to=0.30, number_of_steps=29, command=lambda v: self.w_queue_lbl.configure(text=f"Queue Length Penalty Weight: -{v:.2f}"))
        self.w_queue_slider.set(self.app.env.weight_queue)
        self.w_queue_slider.pack(fill="x", padx=18, pady=(2, 10))

        # Weight Switch
        self.w_sw_lbl = ctk.CTkLabel(right_col, text=f"Phase Switch Penalty: -{self.app.env.weight_switch:.2f}", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.w_sw_lbl.pack(anchor="w", padx=18)
        self.w_sw_slider = ctk.CTkSlider(right_col, from_=0.0, to=1.5, number_of_steps=30, command=lambda v: self.w_sw_lbl.configure(text=f"Phase Switch Penalty: -{v:.2f}"))
        self.w_sw_slider.set(self.app.env.weight_switch)
        self.w_sw_slider.pack(fill="x", padx=18, pady=(2, 16))

        # Bottom Button Bar
        btn_bar = ctk.CTkFrame(self.parent, fg_color="transparent")
        btn_bar.pack(fill="x", pady=(14, 0))

        self.save_btn = ctk.CTkButton(btn_bar, text="💾 Save Configuration", fg_color=GREEN, hover_color="#24b364", width=160, command=self._save_settings)
        self.save_btn.pack(side="left", padx=(0, 10))

        self.reset_btn = ctk.CTkButton(btn_bar, text="↺ Reset Defaults", fg_color="#2a3847", hover_color="#36495c", width=140, command=self._reset_defaults)
        self.reset_btn.pack(side="left")

        self.status_msg = ctk.CTkLabel(btn_bar, text="", text_color=CYAN, font=ctk.CTkFont(size=11))
        self.status_msg.pack(side="left", padx=16)

    def _save_settings(self):
        new_settings = {
            "min_green": int(self.min_g_slider.get()),
            "max_green": int(self.max_g_slider.get()),
            "yellow_duration": int(self.yel_slider.get()),
            "starvation_threshold": float(self.starve_thresh_slider.get()),
            "weight_pass": float(self.w_pass_slider.get()),
            "weight_wait": float(self.w_wait_slider.get()),
            "weight_queue": float(self.w_queue_slider.get()),
            "weight_switch": float(self.w_sw_slider.get()),
        }

        # Apply to live simulation environment
        ctrl = self.app.env.signal_controller
        ctrl.min_green = new_settings["min_green"]
        ctrl.max_green = new_settings["max_green"]
        ctrl.yellow_duration = new_settings["yellow_duration"]

        self.app.env.metrics_service.starvation_threshold = new_settings["starvation_threshold"]
        self.app.env.weight_pass = new_settings["weight_pass"]
        self.app.env.weight_wait = new_settings["weight_wait"]
        self.app.env.weight_queue = new_settings["weight_queue"]
        self.app.env.weight_switch = new_settings["weight_switch"]

        self.app.storage_service.save_settings(new_settings)
        self.status_msg.configure(text="✓ Settings saved and applied to simulation.")
        self.app.dashboard.add_event("Updated signal timing and reward parameters.")

    def _reset_defaults(self):
        d = DEFAULT_SETTINGS
        self.min_g_slider.set(d["min_green"])
        self.min_g_lbl.configure(text=f"Minimum Green Duration: {d['min_green']}s")

        self.max_g_slider.set(d["max_green"])
        self.max_g_lbl.configure(text=f"Maximum Green Duration: {d['max_green']}s")

        self.yel_slider.set(d["yellow_duration"])
        self.yel_lbl.configure(text=f"Yellow Interval Duration: {d['yellow_duration']}s")

        self.starve_thresh_slider.set(d["starvation_threshold"])
        self.starve_thresh_lbl.configure(text=f"Starvation Alert Threshold: {int(d['starvation_threshold'])}s")

        self.w_pass_slider.set(d["weight_pass"])
        self.w_pass_lbl.configure(text=f"Throughput Reward Weight: +{d['weight_pass']:.2f}")

        self.w_wait_slider.set(d["weight_wait"])
        self.w_wait_lbl.configure(text=f"Waiting Delay Penalty Weight: -{d['weight_wait']:.2f}")

        self.w_queue_slider.set(d["weight_queue"])
        self.w_queue_lbl.configure(text=f"Queue Length Penalty Weight: -{d['weight_queue']:.2f}")

        self.w_sw_slider.set(d["weight_switch"])
        self.w_sw_lbl.configure(text=f"Phase Switch Penalty: -{d['weight_switch']:.2f}")

        self._save_settings()
        self.status_msg.configure(text="✓ Defaults restored.")
