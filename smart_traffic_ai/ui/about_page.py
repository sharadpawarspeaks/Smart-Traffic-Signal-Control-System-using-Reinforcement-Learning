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

if TYPE_CHECKING:
    from smart_traffic_ai.ui.main_window import SmartTrafficApp


class AboutView:
    def __init__(self, parent: ctk.CTkFrame, app: SmartTrafficApp):
        self.parent = parent
        self.app = app
        self._build_ui()

    def _build_ui(self):
        create_section_header(
            self.parent,
            "Smart Traffic AI | Project Documentation & Technical Specification",
            "B.Tech Artificial Intelligence and Machine Learning Practical Examination Project",
        )

        scroll_box = ctk.CTkScrollableFrame(self.parent, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        scroll_box.pack(fill="both", expand=True)

        content = """
========================================================================================
SMART TRAFFIC SIGNAL CONTROL SYSTEM USING REINFORCEMENT LEARNING
========================================================================================

1. ABSTRACT
-----------
Urban traffic congestion leads to substantial economic losses, fuel wastage, and increased
greenhouse gas emissions. Conventional traffic light controllers utilize predetermined,
fixed-time signal plans that fail to adapt dynamically to asymmetric or fluctuating traffic
densities. This project presents Smart Traffic AI, an autonomous four-way intersection signal
control system built with genuine tabular Q-learning and an independent centralized Signal
Safety Controller. The reinforcement learning agent learns optimal corridor phase transitions
by maximizing throughput and minimizing cumulative vehicle waiting times, while the safety
controller guarantees conflict-free signal transitions and handles emergency preemption.

2. PROBLEM STATEMENT
--------------------
Fixed-time traffic controllers switch phases according to rigid timer cycles regardless of whether
one approach has heavy queues and the opposing approach is completely empty. This causes:
  * Excessive idle vehicle delays on congested approaches.
  * Green time wasted on empty roads.
  * Inability to dynamically prioritize emergency responders (ambulances and fire engines).

3. SYSTEM ARCHITECTURE
----------------------
The system is partitioned into modular, decoupled tiers:
  * Environment & Physics (smart_traffic_ai.environment):
      - Models vehicle generation, safe car-following headway, deceleration, and stop line rules.
      - Discretizes continuous queues into manageable state buckets (Low: 0-4, Med: 5-9, High: 10+).
  * Centralized Signal Safety Controller (smart_traffic_ai.controllers.signal_controller):
      - Strictly prevents conflicting greens (North-South Green and East-West Green are mutually exclusive).
      - Enforces mandatory Yellow clearance intervals (2-3s) before corridor handoff.
      - Enforces minimum green (5s) and maximum green (35s) bounds to prevent flicker and starvation.
      - Implements deterministic emergency preemption override.
  * Reinforcement Learning Agent (smart_traffic_ai.agents.q_learning_agent):
      - Tabular Q-learning implemented from scratch without black-box APIs or hardcoded heuristics.
      - Epsilon-greedy action selection balancing exploration and exploitation.
  * Performance Telemetry & Persistence (smart_traffic_ai.services):
      - Metrics tracking: delay variance, max queue, throughput per minute.
      - JSON persistence for Q-tables and settings; CSV export for benchmark results.
  * Presentation Layer (smart_traffic_ai.ui):
      - CustomTkinter dark navy dashboard with interactive Canvas and standalone Pygame visualization.

4. REINFORCEMENT LEARNING FORMULATION
-------------------------------------
A. State Representation:
   State s = (North_cat, South_cat, East_cat, West_cat, Current_Phase)
   Where queue categories:
     - 0 (Low): 0 to 4 waiting vehicles
     - 1 (Medium): 5 to 9 waiting vehicles
     - 2 (High): 10 or more waiting vehicles
   Phases:
     - 0: North-South Green
     - 1: North-South Yellow
     - 2: East-West Green
     - 3: East-West Yellow
   Total state space size: 3^4 * 4 = 324 discrete states (ideal for fast convergence).

B. Action Space:
   - Action 0: Prioritize North-South corridor (request NS Green)
   - Action 1: Prioritize East-West corridor (request EW Green)
   - Action 2: Extend active green phase (+5 seconds)

C. Bellman Optimality Update Equation:
   Q(s, a) = Q(s, a) + α * [r + γ * max_a' Q(s', a') - Q(s, a)]
   Where:
     - α (Alpha): Learning rate (default 0.15)
     - γ (Gamma): Discount factor for future rewards (default 0.92)
     - r: Immediate reward received after transition
     - s': Resulting next state
     - ε (Epsilon): Exploration rate decaying with factor 0.995 down to ε_min = 0.05

D. Transparent Reward Function:
   Reward = (w_pass * ΔPassed) - (w_wait * ΔWait) - (w_queue * ΣQueues) - Penalty_Switch - Penalty_Starve
   - Pass bonus (+3.0 per vehicle cleared): rewards throughput.
   - Wait penalty (-0.20 per second waited): penalizes delays.
   - Queue penalty (-0.05 per waiting vehicle): penalizes congestion buildup.
   - Switch penalty (-0.40): discourages unnecessary rapid phase changes.
   - Starvation penalty (-0.10 * max_wait): penalizes neglecting starved approaches.

5. EMERGENCY VEHICLE PRIORITY PROTOCOL
--------------------------------------
Emergency vehicle preemption is an explicit safety mechanism managed by the Signal Safety Controller:
  1. Detection of Ambulance or Fire Engine on any of the 4 approaches.
  2. If the corridor is already green, green is maintained.
  3. If the conflicting corridor is green, immediate safe transition to Yellow (2s) is triggered.
  4. Emergency corridor is opened to green exclusively.
  5. Conflicting emergency requests are queued and served via safe FIFO sequence.
  6. Once the emergency vehicle crosses the intersection, normal RL policy control resumes.

6. FIXED-TIME BASELINE BENCHMARKING
-----------------------------------
A standard pre-timed controller (20s NS Green, 2s Yellow, 20s EW Green, 2s Yellow) is evaluated
under the identical random seed, duration, and vehicle arrival schedule to calculate:
  Improvement (%) = ((Baseline_Average_Wait - RL_Average_Wait) / Baseline_Average_Wait) * 100

7. ACADEMIC DISCLAIMER
----------------------
This software is developed strictly for educational demonstration in university examinations.
It is a simulated environment and must not be connected to or deployed on actual municipal
traffic signal infrastructure.
"""
        txt = ctk.CTkTextbox(
            scroll_box,
            fg_color="#081726",
            text_color=TEXT,
            font=ctk.CTkFont(family="Consolas", size=11),
            activate_scrollbars=True,
        )
        txt.pack(fill="both", expand=True, padx=16, pady=16)
        txt.insert("1.0", content.strip())
        txt.configure(state="disabled")
