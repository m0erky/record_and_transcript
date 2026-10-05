"""Wiederverwendbare GUI-Hilfsfunktionen."""

from __future__ import annotations

import customtkinter as ctk


def labeled_option_menu(
    parent: ctk.CTkBaseClass,
    label: str,
    values: list[str],
    default: str,
    width: int = 220,
) -> tuple[ctk.CTkLabel, ctk.CTkOptionMenu]:
    label_widget = ctk.CTkLabel(parent, text=label)
    menu = ctk.CTkOptionMenu(parent, values=values, width=width)
    menu.set(default)
    return label_widget, menu


def labeled_checkbox(
    parent: ctk.CTkBaseClass,
    text: str,
    default: bool = True,
) -> ctk.CTkCheckBox:
    checkbox = ctk.CTkCheckBox(parent, text=text)
    if default:
        checkbox.select()
    return checkbox
