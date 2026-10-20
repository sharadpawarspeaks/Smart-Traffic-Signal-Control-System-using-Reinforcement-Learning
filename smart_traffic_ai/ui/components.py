from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional
import customtkinter as ctk

# Color Palette
BG = "#071525"
SIDEBAR = "#091b2d"
PANEL = "#0d2134"
PANEL_2 = "#102b43"
BORDER = "#1b3854"
CYAN = "#27d3e6"
BLUE = "#3182f6"
GREEN = "#31d17c"
AMBER = "#f4b942"
RED = "#ff5d67"
TEXT = "#edf6ff"
MUTED = "#8da8bd"


def create_kpi_card(
    parent: ctk.CTkBaseClass,
    title: str,
    initial_value: str = "0",
    color: str = CYAN,
    subtitle: str = "",
) -> tuple[ctk.CTkFrame, ctk.CTkLabel]:
    card = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
    card.pack(side="left", fill="both", expand=True, padx=5)

    ctk.CTkLabel(
        card,
        text=title.upper(),
        text_color=MUTED,
        font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
    ).pack(anchor="w", padx=16, pady=(14, 2))

    val_label = ctk.CTkLabel(
        card,
        text=initial_value,
        text_color=color,
        font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
    )
    val_label.pack(anchor="w", padx=16, pady=(0, 2))

    if subtitle:
        ctk.CTkLabel(
            card,
            text=subtitle,
            text_color="#5a7d96",
            font=ctk.CTkFont(family="Segoe UI", size=10),
        ).pack(anchor="w", padx=16, pady=(0, 10))
    else:
        ctk.CTkFrame(card, height=8, fg_color="transparent").pack()

    return card, val_label


def create_section_header(
    parent: ctk.CTkBaseClass,
    title: str,
    subtitle: str = "",
) -> ctk.CTkFrame:
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", pady=(8, 12))

    ctk.CTkLabel(
        frame,
        text=title,
        text_color=TEXT,
        font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
    ).pack(anchor="w")

    if subtitle:
        ctk.CTkLabel(
            frame,
            text=subtitle,
            text_color=MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        ).pack(anchor="w", pady=(2, 0))

    return frame
