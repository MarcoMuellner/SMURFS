# File: smurfs/smurfs_ui/notifications.py
from typing import Optional
import dash_mantine_components as dmc
from dash import html


def show_success_notification(message: str, title: Optional[str] = None) -> dict:
    """Show a success notification."""
    return {
        "message": message,
        "title": title or "Success",
        "color": "green",
        "icon": html.I(className="fas fa-check-circle"),
        "autoClose": 5000
    }


def show_error_notification(message: str, title: Optional[str] = None) -> dict:
    """Show an error notification."""
    return {
        "message": message,
        "title": title or "Error",
        "color": "red",
        "icon": html.I(className="fas fa-exclamation-circle"),
        "autoClose": 8000
    }


def show_warning_notification(message: str, title: Optional[str] = None) -> dict:
    """Show a warning notification."""
    return {
        "message": message,
        "title": title or "Warning",
        "color": "yellow",
        "icon": html.I(className="fas fa-exclamation-triangle"),
        "autoClose": 6000
    }


def show_info_notification(message: str, title: Optional[str] = None) -> dict:
    """Show an info notification."""
    return {
        "message": message,
        "title": title or "Information",
        "color": "blue",
        "icon": html.I(className="fas fa-info-circle"),
        "autoClose": 5000
    }


def show_processing_notification(message: str = "Processing...") -> dict:
    """Show a processing notification."""
    return {
        "message": message,
        "title": "Processing",
        "color": "blue",
        "loading": True,
        "autoClose": False
    }