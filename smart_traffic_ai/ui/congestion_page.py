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
    create_kpi_card,
)
from smart_traffic_ai.environment.intersection import APPROACHES

if TYPE_CHECKING:
    from smart_traffic_ai.ui.main_window import SmartTrafficApp


class CongestionView:
    def __init__(self, parent: ctk.CTkFrame, app: SmartTrafficApp):
        self.parent = parent
        self.app = app
        self.corridor_cards = []
        self._build_ui()

    def _build_ui(self):
        create_section_header(
            self.parent,
            "Congestion Heatmap & Corridor Fairness Monitor",
            "Real-time queue tracking, delay variance, and starvation alert detection",
        )

        # Top Fairness KPIs
        kpi_row = ctk.CTkFrame(self.parent, fg_color="transparent")
        kpi_row.pack(fill="x", pady=(0, 16))

        _, self.lbl_fairness = create_kpi_card(kpi_row, "Fairness Status", "Balanced", GREEN, "Approach delay parity")
        _, self.lbl_max_wait = create_kpi_card(kpi_row, "Max Individual Wait", "0.0 s", AMBER, "Longest single vehicle delay")
        _, self.lbl_longest_app = create_kpi_card(kpi_row, "Most Delayed Corridor", "None", CYAN, "Highest accumulated wait")
        _, self.lbl_variance = create_kpi_card(kpi_row, "Delay Variance (σ²)", "0.00", MUTED, "Inter-approach disparity")

        # 4 Corridor Heatmap Cards
        ctk.CTkLabel(self.parent, text="APPROACH CONGESTION HEATMAP", text_color=TEXT, font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 8))

        heat_row = ctk.CTkFrame(self.parent, fg_color="transparent")
        heat_row.pack(fill="x", pady=(0, 16))

        for name in APPROACHES:
            card = ctk.CTkFrame(heat_row, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
            card.pack(side="left", fill="both", expand=True, padx=4)

            ctk.CTkLabel(card, text=name.upper(), text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=14, pady=(12, 2))

            level_badge = ctk.CTkLabel(card, text="LOW CONGESTION", text_color=GREEN, font=ctk.CTkFont(size=11, weight="bold"))
            level_badge.pack(anchor="w", padx=14, pady=(0, 6))

            p_bar = ctk.CTkProgressBar(card, height=10, progress_color=GREEN, fg_color="#182b3a")
            p_bar.pack(fill="x", padx=14, pady=4)
            p_bar.set(0)

            stats_lbl = ctk.CTkLabel(card, text="Queue: 0  |  Avg Wait: 0.0s", text_color=MUTED, font=ctk.CTkFont(size=11))
            stats_lbl.pack(anchor="w", padx=14, pady=(2, 12))

            self.corridor_cards.append({
                "badge": level_badge,
                "bar": p_bar,
                "stats": stats_lbl,
                "frame": card,
            })

        # Bottom: Diagnostic Details & Starvation Alert Box
        bot_frame = ctk.CTkFrame(self.parent, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        bot_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(bot_frame, text="FAIRNESS & CONGESTION DIAGNOSTICS", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(14, 8))

        self.diag_box = ctk.CTkTextbox(bot_frame, fg_color="#0a1b2b", text_color=TEXT, font=ctk.CTkFont(family="Consolas", size=11))
        self.diag_box.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        self.update_data()

    def update_data(self):
        queues = self.app.env._queues()
        fairness = self.app.env.metrics_service.compute_fairness(self.app.env.vehicles, queues)

        # Update KPIs
        if fairness.is_starved:
            self.lbl_fairness.configure(text="STARVATION DETECTED", text_color=RED)
        else:
            self.lbl_fairness.configure(text="BALANCED", text_color=GREEN)

        self.lbl_max_wait.configure(text=f"{fairness.max_individual_wait:.1f} s")
        self.lbl_longest_app.configure(text=fairness.longest_waiting_approach_name)
        self.lbl_variance.configure(text=f"{fairness.approach_wait_variance:.2f}")

        # Approach waits
        app_waits = [0.0, 0.0, 0.0, 0.0]
        for v in self.app.env.vehicles:
            if not v.crossed:
                app_waits[v.approach] += v.wait_time

        # Update heatmap cards
        for idx, item in enumerate(self.corridor_cards):
            q_cnt = queues[idx]
            avg_w = app_waits[idx] / max(1, q_cnt)
            item["bar"].set(min(1.0, q_cnt / 14.0))

            if q_cnt >= 10:
                item["badge"].configure(text="HIGH CONGESTION", text_color=RED)
                item["bar"].configure(progress_color=RED)
            elif q_cnt >= 5:
                item["badge"].configure(text="MODERATE", text_color=AMBER)
                item["bar"].configure(progress_color=AMBER)
            else:
                item["badge"].configure(text="LOW CONGESTION", text_color=GREEN)
                item["bar"].configure(progress_color=GREEN)

            item["stats"].configure(text=f"Queue: {q_cnt} veh  |  Avg Wait: {avg_w:.1f}s")

        # Diagnostics textbox
        self.diag_box.configure(state="normal")
        self.diag_box.delete("1.0", "end")

        diag_lines = [
            f"Timestamp: Simulation Second {self.app.env.time}",
            f"Active Corridor Phase: {self.app.env.signal_controller.phase_name}",
            "",
            "Approach Status Breakdown:",
        ]
        for i, name in enumerate(APPROACHES):
            status = "NORMAL"
            if i in fairness.starved_approaches:
                status = "⚠️ STARVED (Exceeds Threshold)"
            diag_lines.append(
                f"  [{name:5s}] Queue: {queues[i]:2d} vehicles | Total Wait: {app_waits[i]:5.1f}s | Status: {status}"
            )

        diag_lines.extend([
            "",
            f"Fairness Evaluation: Delay variance between approaches is {fairness.approach_wait_variance:.2f}.",
            "Reinforcement Learning Penalty: Reward function incorporates a negative starvation weight",
            "when an approach's wait time exceeds the configured threshold, discouraging policy bias.",
        ])

        self.diag_box.insert("end", "\n".join(diag_lines))
        self.diag_box.configure(state="disabled")
