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


class EmergencyView:
    def __init__(self, parent: ctk.CTkFrame, app: SmartTrafficApp):
        self.parent = parent
        self.app = app
        self._build_ui()

    def _build_ui(self):
        create_section_header(
            self.parent,
            "Emergency Vehicle Priority Preemption System",
            "Deterministic safety-controlled priority override for Ambulances and Fire Engines",
        )

        # Top Status Row
        status_row = ctk.CTkFrame(self.parent, fg_color="transparent")
        status_row.pack(fill="x", pady=(0, 16))

        self.card_preempt, self.lbl_preempt = create_kpi_card(
            status_row, "Preemption State", "IDLE", GREEN, "Signal controller status"
        )
        self.card_active, self.lbl_active = create_kpi_card(
            status_row, "Active Emergency Vehicles", "0", RED, "Approaching intersection"
        )
        self.card_corridor, self.lbl_corridor = create_kpi_card(
            status_row, "Priority Corridor", "None", CYAN, "Corridor with green preemption"
        )

        # Split Layout: Left (Spawn Controls) & Right (Preemption Queue & Safety Specs)
        layout = ctk.CTkFrame(self.parent, fg_color="transparent")
        layout.pack(fill="both", expand=True)

        # Left Panel: Spawn Emergency Vehicles
        left_panel = ctk.CTkFrame(layout, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER, width=420)
        left_panel.pack(side="left", fill="y", padx=(0, 12))
        left_panel.pack_propagate(False)

        ctk.CTkLabel(left_panel, text="MANUAL PRIORITY INJECTION", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=18, pady=(16, 12))

        # Ambulance Spawning
        ctk.CTkLabel(left_panel, text="🚑 Spawn Ambulance", text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=18, pady=(4, 6))
        amb_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        amb_row.pack(fill="x", padx=18, pady=(0, 14))
        for idx, app_name in enumerate(APPROACHES):
            ctk.CTkButton(
                amb_row,
                text=app_name,
                width=85,
                fg_color="#a82835",
                hover_color="#c73242",
                command=lambda i=idx: self._spawn(i, "ambulance"),
            ).pack(side="left", padx=2)

        # Fire Engine Spawning
        ctk.CTkLabel(left_panel, text="🚒 Spawn Fire Engine", text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=18, pady=(4, 6))
        fire_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        fire_row.pack(fill="x", padx=18, pady=(0, 16))
        for idx, app_name in enumerate(APPROACHES):
            ctk.CTkButton(
                fire_row,
                text=app_name,
                width=85,
                fg_color="#bd3a13",
                hover_color="#de481b",
                command=lambda i=idx: self._spawn(i, "fire_engine"),
            ).pack(side="left", padx=2)

        # Academic Distinction Note
        note_box = ctk.CTkFrame(left_panel, fg_color="#122538", corner_radius=8, border_width=1, border_color="#1e3e5c")
        note_box.pack(fill="x", padx=18, pady=(10, 18))
        ctk.CTkLabel(note_box, text="SAFETY CONTROLLER VS RL POLICY", text_color=CYAN, font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
        explanation = (
            "Emergency preemption is an explicit safety-critical override enforced by the "
            "centralized Signal Safety Controller. It is intentionally separate from the "
            "learned tabular Q-table to guarantee 100% deterministic safety and prevent collision risks."
        )
        ctk.CTkLabel(note_box, text=explanation, text_color=MUTED, font=ctk.CTkFont(size=10), justify="left", wraplength=340).pack(anchor="w", padx=12, pady=(0, 10))

        # Right Panel: Active Requests & Safety Protocol State Machine
        right_panel = ctk.CTkFrame(layout, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        right_panel.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(right_panel, text="PREEMPTION STATE MACHINE & ACTIVE QUEUE", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=18, pady=(16, 10))

        self.queue_box = ctk.CTkTextbox(right_panel, fg_color="#0a1b2b", text_color=TEXT, font=ctk.CTkFont(family="Consolas", size=11))
        self.queue_box.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        self.update_data()

    def _spawn(self, approach_idx: int, veh_type: str):
        self.app.request_emergency_vehicle(approach_idx, veh_type)
        self.app.dashboard.add_event(f"Emergency {veh_type.title()} spawned on {APPROACHES[approach_idx]} approach.")
        self.update_data()

    def update_data(self):
        controller = self.app.env.signal_controller
        active_evs = [v for v in self.app.env.vehicles if v.emergency and not v.crossed]

        if controller.preemption_active:
            self.lbl_preempt.configure(text="PREEMPTION ACTIVE", text_color=RED)
            corridor_str = "North-South" if (controller.emergency_queue and controller.emergency_queue[0] in (0, 1)) else "East-West"
            self.lbl_corridor.configure(text=corridor_str, text_color=CYAN)
        else:
            self.lbl_preempt.configure(text="IDLE / NORMAL RL", text_color=GREEN)
            self.lbl_corridor.configure(text="None", text_color=MUTED)

        self.lbl_active.configure(text=str(len(active_evs)))

        # Update queue text
        self.queue_box.configure(state="normal")
        self.queue_box.delete("1.0", "end")
        text = [
            "=================== EMERGENCY PREEMPTION STATUS ===================",
            f"Preemption Active:   {controller.preemption_active}",
            f"Current Signal Phase: {controller.phase_name} ({controller.phase_time}s)",
            f"Pending Queue:       {[APPROACHES[a] for a in controller.emergency_queue]}",
            "",
            "--- ACTIVE EMERGENCY VEHICLES ---",
        ]
        if not active_evs:
            text.append("No active emergency vehicles detected approaching intersection.")
        else:
            for ev in active_evs:
                text.append(f"• ID #{ev.id}: {ev.vehicle_type.upper()} on {APPROACHES[ev.approach]} approach | Pos: {ev.position:.2f} | Wait: {ev.wait_time:.1f}s")

        text.extend([
            "",
            "--- PREEMPTION PROTOCOL SEQUENCE ---",
            "1. Detection: Vehicle registered on approach approach.",
            "2. Safety Verification: If corridor is already green, extend until clear.",
            "3. Clearance: If conflicting corridor is green, safely transition to yellow (2s).",
            "4. Priority Green: Green granted exclusively to emergency corridor.",
            "5. Resumption: Upon clearance, normal Q-learning policy control resumes safely.",
        ])

        self.queue_box.insert("end", "\n".join(text))
        self.queue_box.configure(state="disabled")
