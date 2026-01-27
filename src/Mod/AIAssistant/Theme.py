# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Theme - Centralized design tokens for the AI Assistant UI.
Supports dark and light themes, following the system FreeCAD theme.
"""

import FreeCAD

# =============================================================================
# COLOR PALETTES
# =============================================================================

_COLORS_DARK = {
    # Background colors (ultra-dark, refined)
    "bg_primary": "#09090b",
    "bg_secondary": "#0f0f11",
    "bg_tertiary": "#18181b",
    "bg_input": "#0c0c0e",
    "bg_hover": "#1f1f23",

    # Border colors
    "border_subtle": "#1c1c1f",
    "border_default": "#27272a",
    "border_focus": "#3b82f6",
    "border_hover": "#3f3f46",

    # Text colors
    "text_primary": "#fafafa",
    "text_secondary": "#a1a1aa",
    "text_muted": "#71717a",
    "text_placeholder": "#a1a1aa",

    # Accent colors
    "accent_primary": "#3b82f6",
    "accent_primary_hover": "#2563eb",
    "accent_success": "#22c55e",
    "accent_success_hover": "#16a34a",
    "accent_error": "#ef4444",
    "accent_error_hover": "#dc2626",
    "accent_warning": "#f59e0b",
    "accent_info": "#3b82f6",

    # Message-specific colors
    "user_msg_text": "#fafafa",
    "assistant_card_bg": "#0f0f11",
    "assistant_card_border": "#1c1c1f",
    "assistant_text": "#e4e4e7",
    "system_text": "#a1a1aa",
    "error_bg": "rgba(239, 68, 68, 0.08)",
    "error_border": "#7f1d1d",
    "error_text": "#fca5a5",

    # Code block colors
    "code_bg": "#09090b",
    "code_border": "#1c1c1f",
    "code_header_bg": "#0f0f11",
    "code_text": "#e4e4e7",

    # Preview widget colors
    "preview_bg": "rgba(59, 130, 246, 0.05)",
    "preview_border": "rgba(59, 130, 246, 0.2)",
    "preview_text": "#93c5fd",

    # Change widget colors
    "change_created": "#22c55e",
    "change_created_bg": "rgba(34, 197, 94, 0.08)",
    "change_modified": "#3b82f6",
    "change_modified_bg": "rgba(59, 130, 246, 0.08)",
    "change_deleted": "#ef4444",
    "change_deleted_bg": "rgba(239, 68, 68, 0.08)",

    # Skeleton/loading colors
    "skeleton_base": "#18181b",
    "skeleton_shimmer": "#27272a",

    # Scrollbar colors
    "scrollbar_bg": "transparent",
    "scrollbar_handle": "#27272a",
    "scrollbar_handle_hover": "#3f3f46",

    # Debug panel colors
    "debug_accent": "#3b82f6",
    "debug_bg": "rgba(59, 130, 246, 0.08)",
    "debug_border": "rgba(59, 130, 246, 0.3)",
}

_COLORS_LIGHT = {
    # Background colors
    "bg_primary": "#ffffff",
    "bg_secondary": "#f8f9fa",
    "bg_tertiary": "#f0f1f3",
    "bg_input": "#ffffff",
    "bg_hover": "#e9ecef",

    # Border colors
    "border_subtle": "#e9ecef",
    "border_default": "#dee2e6",
    "border_focus": "#3b82f6",
    "border_hover": "#ced4da",

    # Text colors
    "text_primary": "#1a1a1a",
    "text_secondary": "#4b5563",
    "text_muted": "#6b7280",
    "text_placeholder": "#6b7280",

    # Accent colors (same hues, slightly adjusted for light bg)
    "accent_primary": "#2563eb",
    "accent_primary_hover": "#1d4ed8",
    "accent_success": "#16a34a",
    "accent_success_hover": "#15803d",
    "accent_error": "#dc2626",
    "accent_error_hover": "#b91c1c",
    "accent_warning": "#d97706",
    "accent_info": "#2563eb",

    # Message-specific colors
    "user_msg_text": "#1a1a1a",
    "assistant_card_bg": "#f8f9fa",
    "assistant_card_border": "#e9ecef",
    "assistant_text": "#374151",
    "system_text": "#6b7280",
    "error_bg": "rgba(220, 38, 38, 0.06)",
    "error_border": "#fca5a5",
    "error_text": "#b91c1c",

    # Code block colors
    "code_bg": "#f4f5f7",
    "code_border": "#e2e4e8",
    "code_header_bg": "#ebedf0",
    "code_text": "#374151",

    # Preview widget colors
    "preview_bg": "rgba(37, 99, 235, 0.05)",
    "preview_border": "rgba(37, 99, 235, 0.2)",
    "preview_text": "#1d4ed8",

    # Change widget colors
    "change_created": "#16a34a",
    "change_created_bg": "rgba(22, 163, 74, 0.08)",
    "change_modified": "#2563eb",
    "change_modified_bg": "rgba(37, 99, 235, 0.08)",
    "change_deleted": "#dc2626",
    "change_deleted_bg": "rgba(220, 38, 38, 0.08)",

    # Skeleton/loading colors
    "skeleton_base": "#e9ecef",
    "skeleton_shimmer": "#dee2e6",

    # Scrollbar colors
    "scrollbar_bg": "transparent",
    "scrollbar_handle": "#ced4da",
    "scrollbar_handle_hover": "#adb5bd",

    # Debug panel colors
    "debug_accent": "#2563eb",
    "debug_bg": "rgba(37, 99, 235, 0.06)",
    "debug_border": "rgba(37, 99, 235, 0.25)",
}

# Active color palette — updated in-place by set_theme()
COLORS = dict(_COLORS_DARK)

# Track current theme state
_is_dark = True

# Callbacks registered by UI components to refresh on theme change
_theme_change_callbacks = []


def is_dark_theme():
    """Return True if the current theme is dark."""
    return _is_dark


def detect_dark_theme():
    """Detect whether FreeCAD is using a dark theme."""
    try:
        hGrp = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/MainWindow")
        theme = hGrp.GetString("Theme", "")
        if "dark" in theme.lower():
            return True
        if "light" in theme.lower():
            return False
    except Exception:
        pass
    # Fallback: check Qt palette
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPalette
        palette = QApplication.palette()
        bg = palette.color(QPalette.ColorRole.Window)
        return bg.lightness() < 128
    except Exception:
        return True  # Default to dark


def set_theme(dark=True):
    """Switch the active color palette. Call refresh callbacks."""
    global _is_dark
    _is_dark = dark
    source = _COLORS_DARK if dark else _COLORS_LIGHT
    COLORS.update(source)
    FreeCAD.Console.PrintMessage(
        f"AIAssistant: Theme set to {'dark' if dark else 'light'}\n"
    )
    for cb in _theme_change_callbacks:
        try:
            cb()
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"AIAssistant: Theme callback error: {e}\n")


def on_theme_change(callback):
    """Register a callback to be called when the theme changes."""
    _theme_change_callbacks.append(callback)


def remove_theme_callback(callback):
    """Remove a previously registered theme change callback."""
    try:
        _theme_change_callbacks.remove(callback)
    except ValueError:
        pass


# Auto-detect on import
set_theme(detect_dark_theme())

# =============================================================================
# TYPOGRAPHY
# =============================================================================

FONTS = {
    # Font families
    "family_sans": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "family_mono": "'JetBrains Mono', 'SF Mono', 'Fira Code', 'Consolas', monospace",

    # Font sizes
    "size_xs": "11px",
    "size_sm": "12px",
    "size_base": "14px",
    "size_lg": "16px",
    "size_xl": "18px",

    # Font weights
    "weight_normal": "400",
    "weight_medium": "500",
    "weight_semibold": "600",
    "weight_bold": "700",

    # Line heights
    "line_height_tight": "1.3",
    "line_height_normal": "1.5",
    "line_height_relaxed": "1.7",
}

# =============================================================================
# SPACING
# =============================================================================

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "2xl": 32,
}

# =============================================================================
# BORDER RADIUS
# =============================================================================

RADIUS = {
    "xs": "4px",
    "sm": "6px",
    "md": "10px",
    "lg": "14px",
    "xl": "18px",
    "full": "9999px",
}

# =============================================================================
# ANIMATIONS
# =============================================================================

ANIMATION = {
    "duration_fast": 100,     # ms
    "duration_normal": 150,   # ms
    "duration_slow": 250,     # ms
    "shimmer_duration": 1500, # ms for full shimmer cycle
}

# =============================================================================
# COMPONENT-SPECIFIC STYLES
# =============================================================================

def get_scrollbar_style():
    """Get scrollbar stylesheet."""
    return f"""
        QScrollBar:vertical {{
            background-color: {COLORS['scrollbar_bg']};
            width: 8px;
            border-radius: 4px;
            margin: 4px 2px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {COLORS['scrollbar_handle']};
            border-radius: 4px;
            min-height: 40px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['scrollbar_handle_hover']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
    """


def get_button_primary_style():
    """Get primary button stylesheet (blue)."""
    return f"""
        QPushButton {{
            background-color: {COLORS['accent_primary']};
            color: #ffffff;
            border: none;
            border-radius: {RADIUS['md']};
            font-weight: {FONTS['weight_medium']};
            font-size: {FONTS['size_base']};
            padding: 10px 20px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['accent_primary_hover']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['accent_primary']};
        }}
        QPushButton:disabled {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_muted']};
        }}
    """


def get_button_ghost_style():
    """Get ghost button stylesheet (transparent with border)."""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['text_secondary']};
            border: 1px solid {COLORS['border_default']};
            border-radius: {RADIUS['sm']};
            font-size: {FONTS['size_sm']};
            padding: 6px 12px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['bg_hover']};
            border-color: {COLORS['border_hover']};
            color: {COLORS['text_primary']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['bg_tertiary']};
        }}
    """


def get_button_success_style():
    """Get success button stylesheet (green)."""
    return f"""
        QPushButton {{
            background-color: {COLORS['accent_success']};
            color: #ffffff;
            border: none;
            border-radius: {RADIUS['md']};
            font-weight: {FONTS['weight_medium']};
            font-size: {FONTS['size_base']};
            padding: 10px 20px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['accent_success_hover']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['accent_success']};
        }}
        QPushButton:disabled {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_muted']};
        }}
    """


def get_input_frame_style():
    """Get input frame stylesheet."""
    return f"""
        QFrame {{
            background-color: {COLORS['bg_input']};
            border: 1px solid {COLORS['border_default']};
            border-radius: {RADIUS['lg']};
        }}
        QFrame:focus-within {{
            border-color: {COLORS['border_focus']};
        }}
    """


def get_text_input_style():
    """Get text input stylesheet."""
    return f"""
        QTextEdit {{
            background-color: transparent;
            color: {COLORS['text_primary']};
            border: none;
            font-size: {FONTS['size_base']};
            padding: 4px 0;
            selection-background-color: {COLORS['accent_primary']};
        }}
        QTextEdit::placeholder {{
            color: {COLORS['text_placeholder']};
        }}
    """
