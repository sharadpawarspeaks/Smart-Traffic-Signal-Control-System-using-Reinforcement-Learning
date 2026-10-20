from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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

if TYPE_CHECKING:
    from smart_traffic_ai.ui.main_window import SmartTrafficApp


class AnalyticsView:
    def __init__(self, parent: ctk.CTkFrame, app: SmartTrafficApp):
        self.parent = parent
        self.app = app
        self.chart_type = "queues"  # queues, wait, throughput, reward, comparison
        self.canvas = None
        self._build_ui()

    def _build_ui(self):
        create_section_header(
            self.parent,
            "Simulation Performance Analytics & Matplotlib Plots",
            "Continuous empirical evaluation: delay curves, throughput dynamics, and reward convergence",
        )

        # Chart Selector & Action Buttons Bar
        top_bar = ctk.CTkFrame(self.parent, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        top_bar.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(top_bar, text="SELECT CHART:", text_color=MUTED, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(16, 8), pady=12)

        charts = [
            ("Queue Dynamics", "queues"),
            ("Average Waiting Time", "wait"),
            ("Vehicles Passed", "passed"),
            ("Reward Convergence", "reward"),
            ("Baseline vs RL Comparison", "comparison"),
        ]

        self.chart_btns = {}
        for title, key in charts:
            btn = ctk.CTkButton(
                top_bar,
                text=title,
                fg_color=PANEL_2 if key == self.chart_type else "transparent",
                hover_color=PANEL_2,
                text_color=TEXT if key == self.chart_type else MUTED,
                height=32,
                command=lambda k=key: self._select_chart(k),
            )
            btn.pack(side="left", padx=4, pady=10)
            self.chart_btns[key] = btn

        ctk.CTkFrame(top_bar, fg_color="transparent").pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            top_bar,
            text="📷 Export Plot",
            width=95,
            height=32,
            fg_color="#184260",
            hover_color="#20557c",
            command=self._export_plot,
        ).pack(side="right", padx=(0, 16), pady=10)

        ctk.CTkButton(
            top_bar,
            text="↻ Refresh",
            width=75,
            height=32,
            fg_color=PANEL_2,
            hover_color=BORDER,
            command=self.render_chart,
        ).pack(side="right", padx=(0, 8), pady=10)

        # Chart Container
        self.chart_frame = ctk.CTkFrame(self.parent, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        self.chart_frame.pack(fill="both", expand=True)

        self.render_chart()

    def _select_chart(self, key: str):
        self.chart_type = key
        for k, btn in self.chart_btns.items():
            btn.configure(
                fg_color=PANEL_2 if k == key else "transparent",
                text_color=TEXT if k == key else MUTED,
            )
        self.render_chart()

    def render_chart(self):
        # Clear existing canvas if present
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            plt.close("all")

        # Create styled Matplotlib figure
        fig, ax = plt.subplots(figsize=(9, 5), dpi=100)
        fig.patch.set_facecolor("#0d2134")
        ax.set_facecolor("#081726")

        ax.tick_params(colors="#8da8bd", which="both")
        for spine in ax.spines.values():
            spine.set_color("#1b3854")
        ax.grid(True, linestyle="--", alpha=0.3, color="#2f4e6d")

        service = self.app.env.metrics_service
        times = service.history_time

        if self.chart_type == "queues":
            ax.set_title("Queue Length Dynamics by Corridor Over Time", color="#edf6ff", fontsize=13, weight="bold")
            ax.set_xlabel("Simulation Second", color="#8da8bd")
            ax.set_ylabel("Queued Vehicles", color="#8da8bd")

            if times and service.history_queues:
                colors = ["#27d3e6", "#3182f6", "#f4b942", "#ff5d67"]
                for i in range(4):
                    q_data = [q[i] for q in service.history_queues]
                    ax.plot(times, q_data, label=APPROACHES[i], color=colors[i], linewidth=2.0)
                ax.legend(facecolor="#0d2134", edgecolor="#1b3854", labelcolor="#edf6ff")
            else:
                ax.text(0.5, 0.5, "No queue history recorded yet. Start the simulation to generate telemetry.", color="#8da8bd", ha="center", va="center", transform=ax.transAxes)

        elif self.chart_type == "wait":
            ax.set_title("Average Vehicle Waiting Time Over Time", color="#edf6ff", fontsize=13, weight="bold")
            ax.set_xlabel("Simulation Second", color="#8da8bd")
            ax.set_ylabel("Average Delay (seconds)", color="#8da8bd")

            if times and service.history_avg_wait:
                ax.plot(times, service.history_avg_wait, color="#f4b942", linewidth=2.2, label="Avg Wait (s)")
                ax.legend(facecolor="#0d2134", edgecolor="#1b3854", labelcolor="#edf6ff")
            else:
                ax.text(0.5, 0.5, "No telemetry collected yet.", color="#8da8bd", ha="center", va="center", transform=ax.transAxes)

        elif self.chart_type == "passed":
            ax.set_title("Cumulative Vehicles Passed Intersection Over Time", color="#edf6ff", fontsize=13, weight="bold")
            ax.set_xlabel("Simulation Second", color="#8da8bd")
            ax.set_ylabel("Vehicles Passed", color="#8da8bd")

            if times and service.history_passed:
                ax.plot(times, service.history_passed, color="#31d17c", linewidth=2.2, label="Vehicles Discharged")
                ax.legend(facecolor="#0d2134", edgecolor="#1b3854", labelcolor="#edf6ff")
            else:
                ax.text(0.5, 0.5, "No vehicle discharge data yet.", color="#8da8bd", ha="center", va="center", transform=ax.transAxes)

        elif self.chart_type == "reward":
            ax.set_title("Step Reward Signal History", color="#edf6ff", fontsize=13, weight="bold")
            ax.set_xlabel("Simulation Second", color="#8da8bd")
            ax.set_ylabel("Instantaneous Reward", color="#8da8bd")

            if times and service.history_rewards:
                ax.plot(times, service.history_rewards, color="#27d3e6", linewidth=1.8, label="Reward")
                ax.axhline(0, color="#53758e", linestyle=":", alpha=0.7)
                ax.legend(facecolor="#0d2134", edgecolor="#1b3854", labelcolor="#edf6ff")
            else:
                ax.text(0.5, 0.5, "No reward signals recorded yet.", color="#8da8bd", ha="center", va="center", transform=ax.transAxes)

        elif self.chart_type == "comparison":
            ax.set_title("Fixed-Time Baseline vs Learned Q-Learning Controller", color="#edf6ff", fontsize=13, weight="bold")

            # Check if demo or comparison data exists
            if hasattr(self.app, "last_comparison") and self.app.last_comparison:
                comp = self.app.last_comparison
                b = comp["baseline"]
                r = comp["rl"]
                metrics_names = ["Avg Wait (s)", "Avg Queue", "Throughput (/min)"]
                b_vals = [b.average_wait, b.average_queue, b.throughput_per_minute]
                r_vals = [r.average_wait, r.average_queue, r.throughput_per_minute]

                import numpy as np
                x = np.arange(len(metrics_names))
                width = 0.35

                ax.bar(x - width/2, b_vals, width, label="Fixed-Time Baseline", color="#f4b942")
                ax.bar(x + width/2, r_vals, width, label="Q-Learning Agent", color="#31d17c")

                ax.set_xticks(x)
                ax.set_xticklabels(metrics_names, color="#edf6ff")
                ax.legend(facecolor="#0d2134", edgecolor="#1b3854", labelcolor="#edf6ff")
            else:
                ax.text(
                    0.5, 0.5,
                    "Run 'Compare Controllers' on the Experiments page to generate comparative telemetry.",
                    color="#8da8bd", ha="center", va="center", transform=ax.transAxes
                )

        fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=14, pady=14)

    def _export_plot(self):
        target = Path("data") / f"analytics_{self.chart_type}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(target, facecolor="#0d2134", edgecolor="none")
        self.app.dashboard.add_event(f"Exported analytics chart to {target}.")

    def update_data(self):
        # Periodically refresh chart if active
        self.render_chart()
