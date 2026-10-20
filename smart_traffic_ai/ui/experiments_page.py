from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
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
from smart_traffic_ai.services.experiments import ExperimentResult, ExperimentRunner

if TYPE_CHECKING:
    from smart_traffic_ai.ui.main_window import SmartTrafficApp


class ExperimentsView:
    def __init__(self, parent: ctk.CTkFrame, app: SmartTrafficApp):
        self.parent = parent
        self.app = app
        self._build_ui()

    def _build_ui(self):
        create_section_header(
            self.parent,
            "Empirical Experimentation & Comparative Evaluation",
            "Reproducible baseline benchmarks, policy evaluation, and waiting-time reduction analysis",
        )

        # Main Split: Left (Configuration & Run Controls) & Right (Results Table & History)
        main_split = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_split.pack(fill="both", expand=True)

        left_ctrl = ctk.CTkFrame(main_split, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER, width=360)
        left_ctrl.pack(side="left", fill="y", padx=(0, 12))
        left_ctrl.pack_propagate(False)

        ctk.CTkLabel(left_ctrl, text="EXPERIMENT CONFIGURATION", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(16, 10))

        # Duration
        dur_frame = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        dur_frame.pack(fill="x", padx=16, pady=(0, 8))
        self.dur_lbl = ctk.CTkLabel(dur_frame, text="Simulation Duration: 120s", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.dur_lbl.pack(anchor="w")
        self.dur_slider = ctk.CTkSlider(dur_frame, from_=30, to=600, number_of_steps=19, command=lambda v: self.dur_lbl.configure(text=f"Simulation Duration: {int(v)}s"))
        self.dur_slider.set(120)
        self.dur_slider.pack(fill="x", pady=2)

        # Seed
        seed_frame = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        seed_frame.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkLabel(seed_frame, text="Random Seed (reproducibility):", text_color=MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.seed_entry = ctk.CTkEntry(seed_frame, height=32, fg_color="#0a1b2b", border_color=BORDER, text_color=TEXT)
        self.seed_entry.insert(0, "42")
        self.seed_entry.pack(fill="x", pady=2)

        # Execution Buttons
        ctk.CTkLabel(left_ctrl, text="BENCHMARK ACTIONS", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(8, 8))

        self.btn_compare = ctk.CTkButton(left_ctrl, text="⚔ Compare Controllers (Side-by-Side)", fg_color=GREEN, hover_color="#24b364", command=self._run_comparison)
        self.btn_compare.pack(fill="x", padx=16, pady=(0, 6))

        self.btn_fixed = ctk.CTkButton(left_ctrl, text="⏱ Run Fixed-Time Baseline", fg_color="#184260", hover_color="#20557c", command=self._run_fixed_time)
        self.btn_fixed.pack(fill="x", padx=16, pady=(0, 6))

        self.btn_rl = ctk.CTkButton(left_ctrl, text="🤖 Run RL Policy Evaluation", fg_color="#184260", hover_color="#20557c", command=self._run_rl)
        self.btn_rl.pack(fill="x", padx=16, pady=(0, 14))

        # Persistence Buttons
        ctk.CTkLabel(left_ctrl, text="DATA EXPORT", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(6, 8))
        self.btn_export_csv = ctk.CTkButton(left_ctrl, text="📄 Export CSV Results", fg_color=PANEL_2, hover_color=BORDER, command=self._export_csv)
        self.btn_export_csv.pack(fill="x", padx=16, pady=(0, 6))

        # Status text in left panel
        self.status_box = ctk.CTkLabel(left_ctrl, text="Ready to execute experiments.", text_color=MUTED, font=ctk.CTkFont(size=11), wraplength=320, justify="left")
        self.status_box.pack(anchor="w", padx=16, pady=(10, 16))

        # Right Panel: Results & Historical Experiments
        right_panel = ctk.CTkFrame(main_split, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        right_panel.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(right_panel, text="LATEST COMPARISON RESULTS", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=18, pady=(16, 8))

        self.results_box = ctk.CTkTextbox(right_panel, fg_color="#0a1b2b", text_color=TEXT, font=ctk.CTkFont(family="Consolas", size=11), height=180)
        self.results_box.pack(fill="x", padx=18, pady=(0, 14))
        self._set_default_results_text()

        # Historical Experiments Table
        ctk.CTkLabel(right_panel, text="SAVED EXPERIMENT HISTORY", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=18, pady=(4, 6))

        self.history_scroll = ctk.CTkScrollableFrame(right_panel, fg_color="#0a1b2b", corner_radius=6)
        self.history_scroll.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        self._load_history_table()

    def _set_default_results_text(self):
        self.results_box.configure(state="normal")
        self.results_box.delete("1.0", "end")
        text = (
            "Click 'Compare Controllers' to evaluate Fixed-Time vs Q-Learning under identical traffic arrivals.\n"
            "Results are calculated empirically from active simulation telemetry.\n\n"
            "Waiting-Time Improvement Formula:\n"
            "  Improvement (%) = ((Baseline Wait - RL Wait) / Baseline Wait) * 100"
        )
        self.results_box.insert("end", text)
        self.results_box.configure(state="disabled")

    def _get_config(self) -> tuple[int, int]:
        dur = int(self.dur_slider.get())
        try:
            seed = int(self.seed_entry.get())
        except ValueError:
            seed = 42
        return dur, seed

    def _run_comparison(self):
        dur, seed = self._get_config()
        self.status_box.configure(text=f"Running side-by-side comparison (duration={dur}s, seed={seed})...")
        self.btn_compare.configure(state="disabled")

        def worker():
            runner = ExperimentRunner(duration=dur, seed=seed)
            comp = runner.compare(self.app.agent, duration=dur, seed=seed)
            self.app.last_comparison = comp

            # Save to storage service
            rec = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "seed": seed,
                "duration": dur,
                "baseline_wait": round(comp["baseline"].average_wait, 2),
                "rl_wait": round(comp["rl"].average_wait, 2),
                "improvement_pct": round(comp["waiting_time_improvement"], 2),
                "baseline_passed": comp["baseline"].passed,
                "rl_passed": comp["rl"].passed,
            }
            self.app.storage_service.save_experiment(rec)

            def update_ui():
                self.btn_compare.configure(state="normal")
                self.status_box.configure(text="Comparison finished successfully.")
                self._display_comparison(comp)
                self._load_history_table()
                self.app.dashboard.add_event(f"Evaluated controllers: {comp['waiting_time_improvement']:.1f}% wait reduction.")

            self.parent.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def _run_fixed_time(self):
        dur, seed = self._get_config()
        self.status_box.configure(text=f"Running fixed-time baseline (duration={dur}s)...")

        def worker():
            runner = ExperimentRunner(duration=dur, seed=seed)
            res = runner.run_fixed_time(duration=dur, seed=seed)

            def update_ui():
                self.status_box.configure(text=f"Fixed-Time finished: Avg Wait={res.average_wait:.2f}s, Passed={res.passed}")
                self.results_box.configure(state="normal")
                self.results_box.delete("1.0", "end")
                self.results_box.insert("end", f"FIXED-TIME CONTROLLER RESULT:\nDuration: {res.duration}s | Seed: {res.seed}\nAverage Waiting Time: {res.average_wait:.2f}s\nAverage Queue Length: {res.average_queue:.2f}\nTotal Vehicles Passed: {res.passed}\nThroughput: {res.throughput_per_minute:.2f} vehicles/min\nTotal Reward: {res.reward:.2f}")
                self.results_box.configure(state="disabled")

            self.parent.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def _run_rl(self):
        dur, seed = self._get_config()
        self.status_box.configure(text=f"Running RL evaluation (duration={dur}s)...")

        def worker():
            runner = ExperimentRunner(duration=dur, seed=seed)
            res = runner.run_rl(self.app.agent, duration=dur, seed=seed)

            def update_ui():
                self.status_box.configure(text=f"RL Evaluation finished: Avg Wait={res.average_wait:.2f}s, Passed={res.passed}")
                self.results_box.configure(state="normal")
                self.results_box.delete("1.0", "end")
                self.results_box.insert("end", f"Q-LEARNING CONTROLLER RESULT:\nDuration: {res.duration}s | Seed: {res.seed}\nAverage Waiting Time: {res.average_wait:.2f}s\nAverage Queue Length: {res.average_queue:.2f}\nTotal Vehicles Passed: {res.passed}\nThroughput: {res.throughput_per_minute:.2f} vehicles/min\nTotal Reward: {res.reward:.2f}")
                self.results_box.configure(state="disabled")

            self.parent.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def _display_comparison(self, comp: dict):
        b = comp["baseline"]
        r = comp["rl"]
        imp = comp["waiting_time_improvement"]

        self.results_box.configure(state="normal")
        self.results_box.delete("1.0", "end")

        lines = [
            f"==================== CONTROLLER BENCHMARK COMPARISON ====================",
            f"Experiment Seed: {b.seed}  |  Duration: {b.duration}s  |  Timestamp: {datetime.now().strftime('%H:%M:%S')}",
            "",
            f"{'Metric':<28} | {'Fixed-Time Baseline':<20} | {'Q-Learning Agent':<20}",
            f"{'-'*74}",
            f"{'Average Waiting Time (s)':<28} | {b.average_wait:<20.2f} | {r.average_wait:<20.2f}",
            f"{'Average Queue Length':<28} | {b.average_queue:<20.2f} | {r.average_queue:<20.2f}",
            f"{'Maximum Queue Length':<28} | {b.max_queue:<20d} | {r.max_queue:<20d}",
            f"{'Total Vehicles Passed':<28} | {b.passed:<20d} | {r.passed:<20d}",
            f"{'Throughput (veh/min)':<28} | {b.throughput_per_minute:<20.2f} | {r.throughput_per_minute:<20.2f}",
            f"{'Cumulative Reward':<28} | {b.reward:<20.2f} | {r.reward:<20.2f}",
            f"{'-'*74}",
            f"WAITING-TIME IMPROVEMENT: {imp:+.2f}% ({'REDUCED DELAY' if imp > 0 else 'HIGHER DELAY'})",
        ]
        self.results_box.insert("end", "\n".join(lines))
        self.results_box.configure(state="disabled")

    def _export_csv(self):
        if not hasattr(self.app, "last_comparison") or not self.app.last_comparison:
            self.status_box.configure(text="Please run a comparison first before exporting.")
            return
        target = Path("data") / "experiment_comparison.csv"
        comp = self.app.last_comparison
        self.app.experiment_runner.export_csv([comp["baseline"], comp["rl"]], target)
        self.status_box.configure(text=f"Exported results to {target}.")
        self.app.dashboard.add_event(f"Exported experiment CSV to {target}.")

    def _load_history_table(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        history = self.app.storage_service.load_experiments()
        if not history:
            ctk.CTkLabel(
                self.history_scroll,
                text="No saved experiment records yet. Run a comparison to populate.",
                text_color=MUTED,
                font=ctk.CTkFont(size=11),
            ).pack(pady=20)
            return

        # Table header
        hdr = ctk.CTkFrame(self.history_scroll, fg_color="#142738", corner_radius=4)
        hdr.pack(fill="x", pady=2)
        ctk.CTkLabel(hdr, text="Date / Time", width=140, anchor="w", text_color=CYAN, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=6)
        ctk.CTkLabel(hdr, text="Seed", width=50, text_color=MUTED, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")
        ctk.CTkLabel(hdr, text="Duration", width=65, text_color=MUTED, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")
        ctk.CTkLabel(hdr, text="Baseline Wait", width=90, text_color=AMBER, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")
        ctk.CTkLabel(hdr, text="RL Wait", width=90, text_color=GREEN, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")
        ctk.CTkLabel(hdr, text="Improvement", width=90, text_color=CYAN, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")

        for item in reversed(history[-10:]):
            row = ctk.CTkFrame(self.history_scroll, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=item.get("timestamp", ""), width=140, anchor="w", text_color=TEXT, font=ctk.CTkFont(size=10)).pack(side="left", padx=6)
            ctk.CTkLabel(row, text=str(item.get("seed", "")), width=50, text_color=MUTED, font=ctk.CTkFont(size=10)).pack(side="left")
            ctk.CTkLabel(row, text=f"{item.get('duration', '')}s", width=65, text_color=MUTED, font=ctk.CTkFont(size=10)).pack(side="left")
            ctk.CTkLabel(row, text=f"{item.get('baseline_wait', 0):.2f}s", width=90, text_color=AMBER, font=ctk.CTkFont(size=10)).pack(side="left")
            ctk.CTkLabel(row, text=f"{item.get('rl_wait', 0):.2f}s", width=90, text_color=GREEN, font=ctk.CTkFont(size=10)).pack(side="left")
            imp_val = item.get("improvement_pct", 0)
            imp_col = GREEN if imp_val > 0 else RED
            ctk.CTkLabel(row, text=f"{imp_val:+.1f}%", width=90, text_color=imp_col, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")
