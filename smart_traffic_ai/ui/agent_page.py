from __future__ import annotations

from pathlib import Path
import threading
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

if TYPE_CHECKING:
    from smart_traffic_ai.ui.main_window import SmartTrafficApp


class AgentView:
    def __init__(self, parent: ctk.CTkFrame, app: SmartTrafficApp):
        self.parent = parent
        self.app = app
        self._build_ui()

    def _build_ui(self):
        create_section_header(
            self.parent,
            "Reinforcement Learning Q-Table & Policy Inspector",
            "Tabular Bellman optimality: Q(s, a) = Q(s, a) + α [r + γ max Q(s', a') - Q(s, a)]",
        )

        # Top Stat Badges
        stats_row = ctk.CTkFrame(self.parent, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 14))

        self.status_card = ctk.CTkFrame(stats_row, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        self.status_card.pack(side="left", fill="both", expand=True, padx=4)
        ctk.CTkLabel(self.status_card, text="AGENT STATUS", text_color=MUTED, font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=16, pady=(12, 2))
        self.status_lbl = ctk.CTkLabel(self.status_card, text="Untrained", text_color=AMBER, font=ctk.CTkFont(size=20, weight="bold"))
        self.status_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        self.states_card = ctk.CTkFrame(stats_row, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        self.states_card.pack(side="left", fill="both", expand=True, padx=4)
        ctk.CTkLabel(self.states_card, text="EXPLORED STATES", text_color=MUTED, font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=16, pady=(12, 2))
        self.states_lbl = ctk.CTkLabel(self.states_card, text="0", text_color=CYAN, font=ctk.CTkFont(size=20, weight="bold"))
        self.states_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        self.eps_card = ctk.CTkFrame(stats_row, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        self.eps_card.pack(side="left", fill="both", expand=True, padx=4)
        ctk.CTkLabel(self.eps_card, text="CURRENT EPSILON (ε)", text_color=MUTED, font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=16, pady=(12, 2))
        self.eps_lbl = ctk.CTkLabel(self.eps_card, text="1.000", text_color=GREEN, font=ctk.CTkFont(size=20, weight="bold"))
        self.eps_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # Main Split: Left (Hyperparameters & Training) & Right (Q-table Inspector)
        main_split = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_split.pack(fill="both", expand=True)

        left_ctrl = ctk.CTkFrame(main_split, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER, width=360)
        left_ctrl.pack(side="left", fill="y", padx=(0, 12))
        left_ctrl.pack_propagate(False)

        ctk.CTkLabel(left_ctrl, text="HYPERPARAMETERS", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(16, 10))

        # Alpha
        self.alpha_lbl = ctk.CTkLabel(left_ctrl, text=f"Learning Rate (α): {self.app.agent.alpha:.2f}", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.alpha_lbl.pack(anchor="w", padx=16)
        self.alpha_slider = ctk.CTkSlider(left_ctrl, from_=0.01, to=0.50, number_of_steps=49, command=self._on_alpha_change)
        self.alpha_slider.set(self.app.agent.alpha)
        self.alpha_slider.pack(fill="x", padx=16, pady=(2, 10))

        # Gamma
        self.gamma_lbl = ctk.CTkLabel(left_ctrl, text=f"Discount Factor (γ): {self.app.agent.gamma:.2f}", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.gamma_lbl.pack(anchor="w", padx=16)
        self.gamma_slider = ctk.CTkSlider(left_ctrl, from_=0.50, to=0.99, number_of_steps=49, command=self._on_gamma_change)
        self.gamma_slider.set(self.app.agent.gamma)
        self.gamma_slider.pack(fill="x", padx=16, pady=(2, 10))

        # Epsilon Decay
        self.decay_lbl = ctk.CTkLabel(left_ctrl, text=f"Exploration Decay: {self.app.agent.decay:.3f}", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.decay_lbl.pack(anchor="w", padx=16)
        self.decay_slider = ctk.CTkSlider(left_ctrl, from_=0.950, to=0.999, number_of_steps=49, command=self._on_decay_change)
        self.decay_slider.set(self.app.agent.decay)
        self.decay_slider.pack(fill="x", padx=16, pady=(2, 16))

        # Training Controls
        ctk.CTkLabel(left_ctrl, text="TRAINING WORKBENCH", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(8, 6))

        ep_frame = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        ep_frame.pack(fill="x", padx=16, pady=(0, 8))
        self.ep_lbl = ctk.CTkLabel(ep_frame, text="Episodes: 25", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.ep_lbl.pack(anchor="w")
        self.ep_slider = ctk.CTkSlider(ep_frame, from_=5, to=100, number_of_steps=19, command=lambda v: self.ep_lbl.configure(text=f"Episodes: {int(v)}"))
        self.ep_slider.set(25)
        self.ep_slider.pack(fill="x", pady=2)

        self.train_btn = ctk.CTkButton(left_ctrl, text="⚡ Train RL Agent", fg_color=GREEN, hover_color="#24b364", command=self._start_training)
        self.train_btn.pack(fill="x", padx=16, pady=(0, 6))

        self.progress_bar = ctk.CTkProgressBar(left_ctrl, fg_color="#182b3a", progress_color=CYAN)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=16, pady=(0, 12))

        # Save / Load / Reset Buttons
        btn_box = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(btn_box, text="💾 Save Q-Table", width=155, fg_color="#184260", hover_color="#20557c", command=self._save_q_table).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_box, text="📂 Load Q-Table", width=155, fg_color="#184260", hover_color="#20557c", command=self._load_q_table).pack(side="left")

        ctk.CTkButton(left_ctrl, text="↺ Clear / Reset Q-Table", fg_color="#36222b", hover_color="#4f2e3c", text_color="#ff9ea6", command=self._reset_q_table).pack(fill="x", padx=16, pady=(0, 16))

        # Right: Q-table Live Inspector
        right_panel = ctk.CTkFrame(main_split, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        right_panel.pack(side="right", fill="both", expand=True)

        header_box = ctk.CTkFrame(right_panel, fg_color="transparent")
        header_box.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(header_box, text="TOP EXPLORED STATES & Q-VALUES", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(header_box, text="↻ Refresh", width=70, fg_color=PANEL_2, hover_color=BORDER, command=self.update_data).pack(side="right")

        # Table Column Headers
        col_headers = ctk.CTkFrame(right_panel, fg_color="#142738", corner_radius=6)
        col_headers.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(col_headers, text="State (N,S,E,W,Ph)", width=130, anchor="w", text_color=CYAN, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=8, pady=6)
        ctk.CTkLabel(col_headers, text="Q(Act 0: NS)", width=110, text_color=TEXT, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=4)
        ctk.CTkLabel(col_headers, text="Q(Act 1: EW)", width=110, text_color=TEXT, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=4)
        ctk.CTkLabel(col_headers, text="Q(Act 2: Ext)", width=110, text_color=TEXT, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=4)
        ctk.CTkLabel(col_headers, text="Best Action", width=90, text_color=GREEN, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=4)
        ctk.CTkLabel(col_headers, text="Visits", width=60, text_color=MUTED, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=4)

        self.table_scroll = ctk.CTkScrollableFrame(right_panel, fg_color="#0a1b2b", corner_radius=6)
        self.table_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.update_data()

    def _on_alpha_change(self, val: float):
        self.app.agent.alpha = round(val, 3)
        self.alpha_lbl.configure(text=f"Learning Rate (α): {val:.2f}")

    def _on_gamma_change(self, val: float):
        self.app.agent.gamma = round(val, 3)
        self.gamma_lbl.configure(text=f"Discount Factor (γ): {val:.2f}")

    def _on_decay_change(self, val: float):
        self.app.agent.decay = round(val, 3)
        self.decay_lbl.configure(text=f"Exploration Decay: {val:.3f}")

    def _save_q_table(self):
        target = Path("data") / "q_table.json"
        self.app.agent.save(target)
        self.app.dashboard.add_event(f"Q-table saved to {target} ({len(self.app.agent.q_table)} states).")

    def _load_q_table(self):
        target = Path("data") / "q_table.json"
        if self.app.agent.load(target):
            self.app.dashboard.add_event(f"Loaded Q-table ({len(self.app.agent.q_table)} states).")
            self.update_data()
        else:
            self.app.dashboard.add_event(f"No Q-table found at {target}.")

    def _reset_q_table(self):
        self.app.agent.reset_training()
        self.app.dashboard.add_event("Q-table cleared. Agent reset to untrained.")
        self.update_data()

    def _start_training(self):
        episodes = int(self.ep_slider.get())
        self.train_btn.configure(state="disabled", text="Training in progress...")
        self.progress_bar.set(0)
        self.app.set_app_status("TRAINING", AMBER)

        def worker():
            def cb(ep, total, rew):
                pct = ep / total
                self.parent.after(0, lambda: self.progress_bar.set(pct))

            runner = self.app.experiment_runner
            runner.train(self.app.agent, episodes=episodes, progress_callback=cb)
            self.app.agent.save(Path("data") / "q_table.json")

            def done():
                self.train_btn.configure(state="normal", text="⚡ Train RL Agent")
                self.progress_bar.set(1.0)
                self.app.set_app_status("READY", GREEN)
                self.app.dashboard.add_event(f"Completed {episodes} training episodes.")
                self.update_data()

            self.parent.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def update_data(self):
        agent = self.app.agent
        # Update badge cards
        if agent.is_trained:
            self.status_lbl.configure(text="Trained", text_color=GREEN)
        else:
            self.status_lbl.configure(text="Untrained", text_color=AMBER)

        self.states_lbl.configure(text=str(len(agent.q_table)))
        self.eps_lbl.configure(text=f"{agent.epsilon:.3f}")

        # Update Q-table rows
        for widget in self.table_scroll.winfo_children():
            widget.destroy()

        top_states = agent.get_top_states(limit=25)
        if not top_states:
            ctk.CTkLabel(
                self.table_scroll,
                text="Q-table is currently empty. Train the agent or run the simulation to populate states.",
                text_color=MUTED,
                font=ctk.CTkFont(size=12),
            ).pack(pady=40)
            return

        for state_key, values, best_action, visits in top_states:
            row = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=state_key, width=130, anchor="w", text_color=CYAN, font=ctk.CTkFont(size=11)).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=f"{values[0]:.2f}", width=110, text_color=TEXT, font=ctk.CTkFont(size=11)).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=f"{values[1]:.2f}", width=110, text_color=TEXT, font=ctk.CTkFont(size=11)).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=f"{values[2]:.2f}", width=110, text_color=TEXT, font=ctk.CTkFont(size=11)).pack(side="left", padx=4)

            act_name = ["NS Green", "EW Green", "Extend"][best_action]
            ctk.CTkLabel(row, text=f"Act {best_action} ({act_name})", width=90, text_color=GREEN, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=str(visits), width=60, text_color=MUTED, font=ctk.CTkFont(size=11)).pack(side="left", padx=4)
