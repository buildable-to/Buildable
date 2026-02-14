# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Drawing Assistant Panel - Main dock widget for 2D structural drawing with AI.
Features a modern Cursor-like chat interface for Draft + TechDraw + Spreadsheet.
"""

import re
import subprocess
from datetime import datetime

import FreeCAD
import FreeCADGui
from PySide6 import QtWidgets, QtCore, QtGui

FreeCAD.Console.PrintMessage("DrawingAssistant: DrawingPanel.py loaded\n")

from pathlib import Path

from . import Theme
from .backends import claude_code as ClaudeCodeBackend
from .core import context as ContextBuilder
from .core import executor as CodeExecutor
from .core import snapshot as SnapshotManager
from .core import changes as ChangeDetector
from .core import source as SourceManager
from .core.preview import PreviewManager, SandboxReviewSession
from .persistence import activity as ActivityLogger
from .persistence.session import SessionManager
from .widgets.chat import ChatWidget
from .widgets.context_selection import ContextSelectionWidget


# Maximum attempts to auto-fix code that fails preview
MAX_FIX_ATTEMPTS = 3

def _svg_to_png(svg_path: str, png_path: str, width: int = 2000) -> bool:
    """Render an SVG to PNG, stripping FreeCAD's custom namespaces first.

    Qt's QSvgRenderer chokes on custom namespace attributes
    (freecad:editable, inkscape:label, etc.).  Stripping them is safe —
    they are metadata, not rendering instructions.
    """
    try:
        from PySide6 import QtSvg
    except ImportError:
        FreeCAD.Console.PrintWarning(
            "DrawingAssistant: PySide6.QtSvg not available, skipping sheet PNG\n"
        )
        return False

    try:
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_text = f.read()

        # Strip namespace declarations and prefixed attributes that
        # QSvgRenderer cannot handle.
        svg_text = re.sub(
            r'\s+xmlns:(?:freecad|inkscape|sodipodi|dc|cc|rdf)="[^"]*"',
            "", svg_text,
        )
        svg_text = re.sub(
            r'\s+(?:freecad|inkscape|sodipodi|dc|cc|rdf):\w+(?::\w+)*="[^"]*"',
            "", svg_text,
        )

        renderer = QtSvg.QSvgRenderer(svg_text.encode("utf-8"))
        if not renderer.isValid():
            FreeCAD.Console.PrintWarning(
                f"DrawingAssistant: QSvgRenderer invalid for {svg_path}\n"
            )
            return False

        svg_size = renderer.defaultSize()
        if svg_size.width() <= 0:
            return False
        height = int(width * svg_size.height() / svg_size.width())

        image = QtGui.QImage(
            QtCore.QSize(width, height), QtGui.QImage.Format_ARGB32
        )
        image.fill(QtCore.Qt.white)
        painter = QtGui.QPainter(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)
        renderer.render(painter)
        painter.end()

        return image.save(png_path, "PNG")
    except Exception as e:
        FreeCAD.Console.PrintWarning(
            f"DrawingAssistant: SVG→PNG failed: {e}\n"
        )
        return False


def _close_techdraw_mdi_tabs():
    """Close TechDraw MDI tabs before object deletion.

    TechDraw's QGVPage::drawBackground() accesses the DrawPage C++ object.
    If the DrawPage is freed while QGVPage still exists, expose events can
    trigger a paint on freed memory (SIGSEGV).  setUpdatesEnabled(False)
    does NOT prevent this — expose events bypass it.

    Closing the MDI subwindow destroys QGVPage entirely.  FreeCAD recreates
    TechDraw tabs automatically when new DrawPages are created and
    doc.recompute() runs.
    """
    try:
        mdi = FreeCADGui.getMainWindow().centralWidget()
        for sub in list(mdi.subWindowList()):
            widget = sub.widget()
            if widget and "MDIViewPage" in widget.metaObject().className():
                sub.close()
    except Exception:
        pass


_SKIP_TYPES = ("App::Origin", "App::Plane", "App::Line")


def _clear_objects(doc, object_names=None):
    """Delete document objects in reverse order (SIGSEGV-safe).

    Closes TechDraw MDI tabs first to prevent paint-on-freed-memory crashes,
    then deletes objects in reverse document order (children before parents).

    Args:
        doc: FreeCAD document.
        object_names: If provided, only delete these object names.
                      If None, delete all (except Origin/Plane/Line).
    """
    _close_techdraw_mdi_tabs()
    filter_set = set(object_names) if object_names else None
    removed = 0
    for obj in reversed(doc.Objects):
        if obj.TypeId in _SKIP_TYPES:
            continue
        if filter_set is not None and obj.Name not in filter_set:
            continue
        try:
            doc.removeObject(obj.Name)
            removed += 1
        except Exception:
            pass
    doc.recompute()
    scope = f"{len(filter_set)} targeted" if filter_set else "all"
    FreeCAD.Console.PrintMessage(
        f"DrawingAssistant: Cleared {removed} objects ({scope})\n"
    )


def _find_techdraw_pages(doc) -> list:
    """Return all TechDraw::DrawPage objects in the document."""
    if not doc:
        return []
    return [obj for obj in doc.Objects if obj.TypeId == "TechDraw::DrawPage"]


class LLMWorker(QtCore.QThread):
    """Background worker for LLM API calls."""
    finished = QtCore.Signal(str)
    error = QtCore.Signal(str)
    tool_call = QtCore.Signal(str, dict)  # For progress indicator updates

    def __init__(self, llm, user_input, context, conversation,
                 multi_angle_screenshots=None):
        super().__init__()
        self.llm = llm
        self.user_input = user_input
        self.context = context
        self.conversation = conversation
        self.multi_angle_screenshots = multi_angle_screenshots

    def run(self):
        try:
            # Set up callback to emit tool_call signal
            def on_tool_call(tool_name, tool_input):
                self.tool_call.emit(tool_name, tool_input)
            self.llm.on_tool_call = on_tool_call

            response = self.llm.chat(
                self.user_input, self.context, self.conversation,
                multi_angle_screenshots=self.multi_angle_screenshots
            )
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            # Clean up callback
            self.llm.on_tool_call = None


class DrawingAssistantDockWidget(QtWidgets.QDockWidget):
    """Main Drawing Assistant dock widget with modern chat interface."""

    def __init__(self, parent=None):
        super().__init__("Drawing Assistant", parent)
        self.setObjectName("DrawingAssistantPanel")
        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )

        # Initialize Claude Code backend
        self._project_dir = self._get_project_dir()
        self.llm = ClaudeCodeBackend.ClaudeCodeBackend(self._project_dir)
        FreeCAD.Console.PrintMessage(
            f"DrawingAssistant: Using Claude Code backend (project: {self._project_dir})\n"
        )

        self.worker = None
        self._fix_worker = None  # Worker for auto-fix requests
        self._plan_worker = None  # Worker for plan mode phase 2
        self.pending_input = None
        self._last_code = ""
        self._last_execution_warnings = []  # Warnings from last code execution
        self._last_execution_error = None  # Error message from last failed execution
        self._last_multi_angle_screenshots = []  # Paths to multi-angle screenshots

        # Self-review state
        self._self_review_worker = None
        self._self_review_attempt = 0
        self._self_review_change_set = None
        self._max_self_review_attempts = 2

        # Sandbox self-review state
        self._sandbox_session: SandboxReviewSession = None
        self._sandbox_review_worker = None
        self._sandbox_review_response = ""

        # Plan mode state
        self._pending_plan = None
        self._plan_user_request = None
        self._plan_mode_request = False

        # Session manager for persisting conversations
        self.session_manager = SessionManager()

        # Preview manager
        self._preview_manager = PreviewManager()

        # Start console observer to capture errors for AI context
        ContextBuilder.start_console_observer()

        self._setup_ui()
        self._connect_signals()

        # Ensure pages/ directory exists for saved documents
        self._ensure_pages_dir()

        # Ensure CLAUDE.md exists for Claude Code backend
        self._ensure_claude_md()

        # Log panel opened
        ActivityLogger.log_panel_opened()

        # Watch for theme changes
        self._setup_theme_observer()

    def _setup_ui(self):
        """Build the UI."""
        main = QtWidgets.QWidget()
        main.setStyleSheet(f"background-color: {Theme.COLORS['bg_primary']};")
        layout = QtWidgets.QVBoxLayout(main)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QtWidgets.QWidget()
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.COLORS['bg_secondary']};
                border-bottom: 1px solid {Theme.COLORS['border_subtle']};
            }}
        """)
        header.setFixedHeight(48)
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(14, 0, 10, 0)
        header_layout.setSpacing(6)

        # Title area with mode switcher and session subtitle
        title_area = QtWidgets.QWidget()
        title_area.setStyleSheet("background: transparent;")
        title_area_layout = QtWidgets.QVBoxLayout(title_area)
        title_area_layout.setContentsMargins(0, 6, 0, 6)
        title_area_layout.setSpacing(2)

        from AIAssistant.widgets.mode_switcher import ModeSegmentedControl
        self._mode_switcher = ModeSegmentedControl(
            active_mode="drawing", theme_module=Theme
        )
        self._mode_switcher.modeChanged.connect(self._on_mode_changed)
        title_area_layout.addWidget(self._mode_switcher)

        # Session title label
        self._session_label = QtWidgets.QLabel("")
        self._session_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.COLORS['text_muted']};
                font-size: {Theme.FONTS['size_xs']};
                background: transparent;
            }}
        """)
        self._session_label.hide()
        title_area_layout.addWidget(self._session_label)

        header_layout.addWidget(title_area)
        header_layout.addStretch()

        # Header button style
        header_btn_style = f"""
            QToolButton {{
                color: {Theme.COLORS['text_secondary']};
                background: transparent;
                border: none;
                font-size: {Theme.FONTS['size_sm']};
                padding: 6px 10px;
                border-radius: {Theme.RADIUS['xs']};
            }}
            QToolButton:hover {{
                color: {Theme.COLORS['text_primary']};
                background-color: {Theme.COLORS['bg_hover']};
            }}
            QToolButton::menu-indicator {{
                image: none;
            }}
        """

        # Sessions button
        self.sessions_btn = QtWidgets.QToolButton()
        self.sessions_btn.setText("Sessions")
        self.sessions_btn.setToolTip("View and switch sessions")
        self.sessions_btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.sessions_btn.setStyleSheet(header_btn_style)
        header_layout.addWidget(self.sessions_btn)

        # Settings button
        self.settings_btn = QtWidgets.QToolButton()
        self.settings_btn.setText("...")
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.settings_btn.setStyleSheet(header_btn_style.replace(
            f"font-size: {Theme.FONTS['size_sm']};",
            f"font-size: {Theme.FONTS['size_lg']};"
        ))
        self._setup_settings_menu()
        header_layout.addWidget(self.settings_btn)

        # Clear button
        clear_btn = QtWidgets.QToolButton()
        clear_btn.setText("Clear")
        clear_btn.setToolTip("Clear chat")
        clear_btn.setStyleSheet(header_btn_style)
        clear_btn.clicked.connect(self._on_clear)
        header_layout.addWidget(clear_btn)

        layout.addWidget(header)

        # Context selection widget (above chat)
        self._context_widget = ContextSelectionWidget()
        layout.addWidget(self._context_widget)

        # Chat widget
        self._chat = ChatWidget()
        layout.addWidget(self._chat, stretch=1)

        self.setWidget(main)
        self.setMinimumWidth(380)
        self.setMinimumHeight(500)

    def _setup_settings_menu(self):
        """Setup the settings dropdown menu."""
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Theme.COLORS['bg_secondary']};
                color: {Theme.COLORS['text_primary']};
                border: 1px solid {Theme.COLORS['border_default']};
                border-radius: {Theme.RADIUS['sm']};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                border-radius: {Theme.RADIUS['xs']};
            }}
            QMenu::item:selected {{
                background-color: {Theme.COLORS['bg_hover']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {Theme.COLORS['border_subtle']};
                margin: 4px 8px;
            }}
        """)

        self.context_action = menu.addAction("Include document context")
        self.context_action.setCheckable(True)
        self.context_action.setChecked(True)

        self.autorun_action = menu.addAction("Auto-run code")
        self.autorun_action.setCheckable(True)
        self.autorun_action.setChecked(False)

        self.auto_accept_action = menu.addAction("Auto-accept previews")
        self.auto_accept_action.setCheckable(True)
        self.auto_accept_action.setChecked(False)

        self.self_review_action = menu.addAction("Self-review before showing")
        self.self_review_action.setCheckable(True)
        self.self_review_action.setChecked(False)
        self.self_review_action.setToolTip(
            "Claude reviews the result and can fix issues before showing to you"
        )

        self.plan_mode_action = menu.addAction("Plan mode (2-phase)")
        self.plan_mode_action.setCheckable(True)
        self.plan_mode_action.setChecked(False)

        self.streaming_action = menu.addAction("Streaming animation")
        self.streaming_action.setCheckable(True)
        self.streaming_action.setChecked(True)

        self.debug_action = menu.addAction("Debug mode")
        self.debug_action.setCheckable(True)
        self.debug_action.setChecked(False)
        self.debug_action.toggled.connect(self._on_debug_toggled)

        menu.addSeparator()

        clear_history = menu.addAction("Clear conversation history")
        clear_history.triggered.connect(self._clear_conversation)

        self.settings_btn.setMenu(menu)

    def _setup_theme_observer(self):
        """Watch FreeCAD theme preference changes via ParameterGrp observer."""
        class _ThemeObserver:
            def __init__(self, panel):
                self._panel = panel

            def slotParamChanged(self, param_grp, tp, entry, value):
                if entry in ("Theme", "StyleSheet"):
                    QtCore.QTimer.singleShot(200, self._panel._on_theme_param_changed)

        self._theme_observer = _ThemeObserver(self)
        self._theme_param_grp = FreeCAD.ParamGet(
            "User parameter:BaseApp/Preferences/MainWindow"
        )
        try:
            self._theme_param_grp.AttachManager(self._theme_observer)
        except Exception as e:
            FreeCAD.Console.PrintWarning(
                f"DrawingAssistant: Could not attach theme observer: {e}\n"
            )

    def _on_theme_param_changed(self):
        """Handle theme parameter change (deferred via singleShot)."""
        is_dark = Theme.detect_dark_theme()
        if is_dark != Theme._is_dark:
            Theme.set_theme(is_dark)
            self._apply_theme()

    def _apply_theme(self):
        """Re-apply theme colors by rebuilding the UI."""
        # Save state
        old_messages = []
        try:
            old_messages = list(self._chat._chat_list._model._messages)
        except Exception:
            pass

        # Save settings checkboxes state
        settings_state = {}
        for attr in ("context_action", "autorun_action", "auto_accept_action",
                      "self_review_action", "plan_mode_action", "streaming_action", "debug_action"):
            try:
                settings_state[attr] = getattr(self, attr).isChecked()
            except Exception:
                pass

        old_widget = self.widget()
        self._setup_ui()
        self._connect_signals()
        if old_widget:
            old_widget.deleteLater()

        # Restore settings
        for attr, checked in settings_state.items():
            try:
                getattr(self, attr).setChecked(checked)
            except Exception:
                pass

        # Restore messages
        if old_messages:
            try:
                model = self._chat._chat_list._model
                for msg in old_messages:
                    model.add_message(msg.text, msg.role, changes=msg.changes)
            except Exception as e:
                FreeCAD.Console.PrintWarning(
                    f"DrawingAssistant: Could not restore messages after theme change: {e}\n"
                )

    def _connect_signals(self):
        """Connect UI signals."""
        self._chat.messageSubmitted.connect(self._on_send)
        self._chat.runCodeRequested.connect(self._on_run_code)
        self._chat.previewApproved.connect(self._on_preview_approved)
        self._chat.previewCancelled.connect(self._on_preview_cancelled)

        # Plan mode signals
        self._chat.planApproved.connect(self._on_plan_approved)
        self._chat.planEdited.connect(self._on_plan_edited)
        self._chat.planCancelled.connect(self._on_plan_cancelled)

        # Connect to session manager for auto-save
        self._chat._chat_list._model.message_added.connect(
            self.session_manager.save_message
        )

        # Setup sessions menu - use aboutToShow to refresh before displaying
        self._sessions_menu = QtWidgets.QMenu(self)
        self._sessions_menu.aboutToShow.connect(self._refresh_sessions_menu)
        self.sessions_btn.setMenu(self._sessions_menu)

    def _refresh_sessions_menu(self):
        """Refresh the sessions dropdown menu."""
        menu = self._sessions_menu
        menu.clear()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Theme.COLORS['bg_secondary']};
                color: {Theme.COLORS['text_primary']};
                border: 1px solid {Theme.COLORS['border_default']};
                border-radius: {Theme.RADIUS['sm']};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                border-radius: {Theme.RADIUS['xs']};
            }}
            QMenu::item:selected {{
                background-color: {Theme.COLORS['bg_hover']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {Theme.COLORS['border_subtle']};
                margin: 4px 8px;
            }}
        """)

        new_session = menu.addAction("+ New Session")
        new_session.triggered.connect(self._on_new_session)
        menu.addSeparator()

        # List recent sessions
        sessions = self.session_manager.list_sessions()[:10]
        current_id = self.session_manager.get_current_session_id()

        if sessions:
            for session in sessions:
                label = self._format_session_item(session)
                if session["session_id"] == current_id:
                    label = "● " + label
                action = menu.addAction(label)
                action.setData(session["session_id"])
                action.triggered.connect(
                    lambda checked, sid=session["session_id"]: self._on_load_session(sid)
                )
        else:
            no_sessions = menu.addAction("No sessions yet")
            no_sessions.setEnabled(False)

        menu.addSeparator()
        open_folder = menu.addAction("Open sessions folder...")
        open_folder.triggered.connect(self._open_sessions_folder)

    def _format_session_item(self, session):
        """Format session for display in menu."""
        try:
            created = datetime.fromisoformat(session["created"])
            now = datetime.now()

            if created.date() == now.date():
                date_str = created.strftime("Today %H:%M")
            elif created.date() == (now.date().replace(day=now.day - 1)):
                date_str = created.strftime("Yesterday %H:%M")
            else:
                date_str = created.strftime("%b %d %H:%M")

            preview = session.get("preview", "")[:30]
            if preview:
                return f"{date_str} - {preview}"
            return date_str
        except Exception:
            return session["session_id"]

    def _on_new_session(self):
        """Start a new session."""
        self._on_clear()
        self.session_manager.clear_current_session()
        self._session_label.hide()
        self._chat.add_system_message("New session started")
        ActivityLogger.log_session_cleared()

    def _on_load_session(self, session_id):
        """Load a previous session."""
        ActivityLogger.log_session_loaded(session_id)
        messages = self.session_manager.load_session(session_id)
        self._chat.clear_chat()

        # Update session title in header
        self._update_session_title(session_id, messages)

        # Temporarily disconnect to avoid re-saving loaded messages
        try:
            self._chat._chat_list._model.message_added.disconnect(
                self.session_manager.save_message
            )
        except RuntimeError:
            pass

        show_debug = self.debug_action.isChecked()
        FreeCAD.Console.PrintMessage(
            f"DrawingAssistant: Loading session {session_id}, {len(messages)} messages, show_debug={show_debug}\n"
        )

        for i, msg in enumerate(messages):
            self._chat.add_message_from_dict(msg, show_debug=show_debug)
            if i % 5 == 0:
                QtCore.QCoreApplication.processEvents()

        # Reconnect the signal
        self._chat._chat_list._model.message_added.connect(
            self.session_manager.save_message
        )

    def _update_session_title(self, session_id: str, messages: list):
        """Update the session title in the header."""
        try:
            session_date = datetime.strptime(session_id, "%Y-%m-%d_%H-%M-%S")
            now = datetime.now()

            if session_date.date() == now.date():
                date_str = session_date.strftime("Today %H:%M")
            else:
                date_str = session_date.strftime("%b %d, %H:%M")
        except ValueError:
            date_str = session_id

        preview = ""
        for msg in messages:
            if msg.get("role") == "user":
                text = msg.get("text", "")
                preview = text[:40] + "..." if len(text) > 40 else text
                break

        title_text = f"{date_str} - {preview}" if preview else date_str
        self._session_label.setText(title_text)
        self._session_label.show()

    def _open_sessions_folder(self):
        """Open the sessions folder in file manager."""
        import sys
        folder_path = str(self.session_manager._sessions_dir)
        try:
            if sys.platform == "win32":
                import os
                os.startfile(folder_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder_path])
            else:
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to open sessions folder: {e}\n")

    def _on_send(self, user_input: str):
        """Handle message submission."""
        if not user_input:
            return

        # Prevent double-send
        if self.worker and self.worker.isRunning():
            return

        # Require document to be saved first
        doc = FreeCAD.ActiveDocument
        if not doc or not doc.FileName:
            self._prompt_save_document()
            return

        self.pending_input = user_input

        # Log user prompt to console for debugging
        preview = user_input.replace('\n', ' ')
        FreeCAD.Console.PrintMessage(f"DrawingAssistant: User: {preview}\n")

        # Log message sent
        ActivityLogger.log_message_sent(
            user_input, session_id=self.session_manager.get_current_session_id()
        )

        # Show typing indicator
        self._chat.show_typing(show_review_phase=self.self_review_action.isChecked())
        self._chat.set_input_enabled(False)

        # Update project directory (handles document changes)
        self._update_project_dir()

        # Ensure pages/ directory exists
        self._ensure_pages_dir()

        # Backup pages/ before Claude potentially edits them
        SourceManager.backup_pages()

        # Build context if enabled
        context = ""
        if self.context_action.isChecked():
            objects_filter = self._context_widget.get_context_objects()
            context = ContextBuilder.build_context(objects_filter=objects_filter)

        # Append warnings from last execution to context
        if self._last_execution_warnings:
            warnings_text = "\n".join(self._last_execution_warnings)
            context += (
                f"\n\n### Warnings from Previous Execution:\n```\n{warnings_text}\n```\n"
                "Please learn from these warnings and avoid using deprecated APIs."
            )
            self._last_execution_warnings = []

        # Append error from last execution to context
        if self._last_execution_error:
            context += (
                f"\n\n### Error from Previous Execution:\n```\n{self._last_execution_error}\n```\n"
                "Please fix this error in your next code generation."
            )
            self._last_execution_error = None

        # Get conversation history
        conversation = self._chat.get_conversation_history()

        # Check if plan mode is enabled
        self._plan_mode_request = self.plan_mode_action.isChecked()

        if self._plan_mode_request:
            # Phase 1: Request plan only
            self._plan_user_request = user_input
            plan_prompt = f"""PLAN MODE: Analyze this request and create an execution plan.

User request: {user_input}

Output ONLY a plan in this format:
## Plan
1. **[Action]**: [Description of what will be created/modified]
2. **[Action]**: [Description]
...

Do NOT write any code. Only output the numbered plan steps."""

            self.worker = LLMWorker(
                self.llm, plan_prompt, context, conversation,
                self._last_multi_angle_screenshots
            )
        else:
            # Normal mode: request code directly
            self.worker = LLMWorker(
                self.llm, user_input, context, conversation,
                self._last_multi_angle_screenshots
            )

        self.worker.finished.connect(self._on_response)
        self.worker.error.connect(self._on_error)
        self.worker.tool_call.connect(self._on_tool_call)
        self.worker.start()

    def _on_response(self, response: str):
        """Handle successful LLM response - create preview or show plan."""
        self._chat.hide_typing()
        self._chat.set_input_enabled(True)

        self._last_code = response

        # Log response received
        tool_calls = getattr(self.llm, 'last_tool_calls', []) or []
        session_id = self.session_manager.get_current_session_id()
        ActivityLogger.log_response_received(
            self.llm.last_duration_ms,
            getattr(self.llm, 'last_cost', 0),
            len(tool_calls),
            model=self.llm.model,
            session_id=session_id
        )

        if tool_calls:
            ActivityLogger.log_tool_calls(tool_calls, session_id=session_id)

        ActivityLogger.log_llm_response(response, session_id=session_id)

        # Log full request/response for debugging
        self.session_manager.log_llm_request(
            user_message=self.pending_input or "",
            system_prompt=self.llm.last_system_prompt,
            context=self.llm.last_context,
            conversation_history=self.llm.last_conversation,
            response=response,
            model=self.llm.model,
            api_url=self.llm.api_url,
            duration_ms=self.llm.last_duration_ms,
            success=True,
            tool_calls=getattr(self.llm, 'last_tool_calls', None),
            cost_usd=getattr(self.llm, 'last_cost', 0)
        )

        # Handle plan mode response (Phase 1)
        if self._plan_mode_request:
            self._plan_mode_request = False
            FreeCAD.Console.PrintMessage("DrawingAssistant: Plan mode - showing plan for approval\n")
            self._chat.add_plan_message(response, self._plan_user_request or "")
            self.pending_input = None
            return

        # Check if Claude edited page files directly
        if getattr(self.llm, 'source_was_edited', False):
            edited = getattr(self.llm, 'edited_files', [])
            FreeCAD.Console.PrintMessage(
                f"DrawingAssistant: Detected page edit(s): {edited} - using diff preview\n"
            )
            ActivityLogger.log_drawing_edited(len(tool_calls))

            # Capture snapshot now (document state is still pre-execution)
            snapshot_id, snapshot_path = SnapshotManager.save_snapshot()
            if snapshot_id:
                self.session_manager.add_snapshot_reference(snapshot_id)
                doc = FreeCAD.ActiveDocument
                obj_count = len(doc.Objects) if doc else 0
                ActivityLogger.log_snapshot_saved(snapshot_id, object_count=obj_count)

            self._handle_source_edit_response(response)
            self.pending_input = None
            return

        # Claude didn't edit any pages - clear backup
        SourceManager.clear_backup()

        FreeCAD.Console.PrintMessage(
            f"DrawingAssistant: Text response length: {len(response)}, "
            f"preview: {response[:100] if response else '(empty)'}...\n"
        )

        # With Claude Code backend, if no files were edited, this is always
        # a pure text response — even if Claude used Read/Glob tool calls to
        # gather context before answering. Show it directly.
        if isinstance(self.llm, ClaudeCodeBackend.ClaudeCodeBackend):
            self._show_traditional_response(response)
            self.pending_input = None
            return

        # Parse description and code from response (legacy HTTP backend path)
        description, code = self._parse_response(response)

        # If auto-run is enabled, skip preview and execute directly
        if self.autorun_action.isChecked():
            self._show_traditional_response(response)
            QtCore.QTimer.singleShot(500, lambda: self._on_run_code(code))
            return

        # If no code found, show as regular message
        if not code.strip():
            self._show_traditional_response(response)
            self.pending_input = None
            return

        # Try to create preview with auto-fix if needed
        self._attempt_preview_with_autofix(description, code, response)
        self.pending_input = None

    def _handle_source_edit_response(self, response: str, attempt: int = 1):
        """Handle response where Claude edited page files directly.

        1. Get NEW pages/ content from disk (Claude already edited them)
        2. Create persistent sandbox and execute
        3. If self-review enabled: Claude reviews sandbox, can iterate
        4. Show preview to user (after Claude is satisfied)
        5. On approve: execute on real document
        6. On cancel: restore from backup

        Args:
            response: Claude's text response (explanation of changes)
            attempt: Current attempt number (1-based) for auto-fix loop
        """
        old_source = SourceManager.get_backup_combined()
        new_source = SourceManager.read_all_pages()

        FreeCAD.Console.PrintMessage(
            f"DrawingAssistant: Old pages length: {len(old_source) if old_source else 0}, "
            f"New pages length: {len(new_source) if new_source else 0}\n"
        )

        # If no backup or no change, just show the text response
        if old_source is None or old_source == new_source:
            FreeCAD.Console.PrintMessage("DrawingAssistant: No page changes detected\n")
            SourceManager.clear_backup()
            tool_calls = getattr(self.llm, 'last_tool_calls', None)
            self._chat.add_assistant_message(response, tool_calls=tool_calls)
            return

        # Store response for later use in finalize
        self._sandbox_review_response = response

        # Create persistent sandbox for self-review
        FreeCAD.Console.PrintMessage(
            f"DrawingAssistant: Creating sandbox for review (attempt {attempt})...\n"
        )
        success, error_msg, session = self._preview_manager.create_sandbox_for_review(new_source)

        # Capture warnings from sandbox execution
        sandbox_warnings = self._preview_manager.get_last_warnings()
        if sandbox_warnings:
            self._last_execution_warnings.extend(sandbox_warnings)
            self._preview_manager.clear_warnings()

        if success and session:
            self._chat.hide_typing()
            self._sandbox_session = session

            FreeCAD.Console.PrintMessage(
                f"DrawingAssistant: Sandbox created with {len(session.object_shapes)} objects\n"
            )
            ActivityLogger.log_preview_created(len(session.object_shapes), False)

            # Check if self-review is enabled
            if self._context_widget.show_review_feedback():
                self._run_sandbox_self_review()
            else:
                self._finalize_sandbox_preview()

        elif error_msg.startswith("EXECUTION_ERROR:"):
            exec_error = error_msg[len("EXECUTION_ERROR:"):]
            FreeCAD.Console.PrintWarning(
                f"DrawingAssistant: Drawing execution failed (attempt {attempt}): {exec_error[:200]}...\n"
            )

            if attempt >= MAX_FIX_ATTEMPTS:
                FreeCAD.Console.PrintWarning(
                    f"DrawingAssistant: Max auto-fix attempts ({MAX_FIX_ATTEMPTS}) reached, giving up\n"
                )
                self._chat.hide_typing()
                SourceManager.restore_pages()
                self._chat.add_error_message(
                    f"Code execution failed after {MAX_FIX_ATTEMPTS} fix attempts.\n\n"
                    f"Last error:\n```\n{exec_error[:500]}\n```"
                )
                return

            FreeCAD.Console.PrintMessage(
                f"DrawingAssistant: Requesting fix from Claude (attempt {attempt + 1})...\n"
            )
            self._chat.show_typing(show_review_phase=self.self_review_action.isChecked())
            self._request_source_fix(new_source, exec_error, response, attempt)
        else:
            FreeCAD.Console.PrintWarning(f"DrawingAssistant: Diff preview failed: {error_msg}\n")
            self._chat.hide_typing()
            SourceManager.restore_pages()
            self._chat.add_error_message(f"Preview failed: {error_msg}")

    def _attempt_preview_with_autofix(self, description: str, code: str,
                                       original_response: str, attempt: int = 1):
        """Try to create preview, auto-fix errors if needed."""
        if attempt > 1:
            self._chat.show_typing(show_review_phase=self.self_review_action.isChecked())
            FreeCAD.Console.PrintMessage(f"DrawingAssistant: Auto-fix attempt {attempt}...\n")

        FreeCAD.Console.PrintMessage(f"DrawingAssistant: Creating preview (attempt {attempt})...\n")
        success, error_msg = self._preview_manager.create_preview(code)

        if success:
            preview_items = self._preview_manager.get_preview_summary()
            is_deletion = self._preview_manager.is_deletion_preview()
            FreeCAD.Console.PrintMessage(
                f"DrawingAssistant: Preview created with {len(preview_items)} objects "
                f"(deletion={is_deletion})\n"
            )
            ActivityLogger.log_preview_created(len(preview_items), is_deletion)

            if attempt > 1:
                self._chat.hide_typing()

            if is_deletion:
                default_desc = "I'll delete the following objects:"
            else:
                default_desc = "I'll create the following objects:"

            auto_approve = self.auto_accept_action.isChecked()
            tool_calls = getattr(self.llm, 'last_tool_calls', None)

            self._chat.add_preview_message(
                description=description or default_desc,
                preview_items=preview_items,
                code=code,
                is_deletion=is_deletion,
                auto_approve=auto_approve,
                tool_calls=tool_calls
            )
            return

        # Deletion failures should NOT trigger auto-fix
        is_deletion_attempt = self._preview_manager.is_deletion_preview() or \
                              bool(self._preview_manager._detect_deletion_targets(code))

        if is_deletion_attempt:
            FreeCAD.Console.PrintWarning(f"DrawingAssistant: Deletion preview failed: {error_msg}\n")
            self._chat.hide_typing()
            self._preview_manager.clear_preview()
            self._chat.add_error_message(f"Cannot delete: {error_msg}")
            return

        if attempt >= MAX_FIX_ATTEMPTS:
            FreeCAD.Console.PrintWarning(
                "DrawingAssistant: Max auto-fix attempts reached, showing code block\n"
            )
            self._chat.hide_typing()
            self._preview_manager.clear_preview()
            self._show_traditional_response(original_response)
            return

        FreeCAD.Console.PrintMessage("DrawingAssistant: Preview failed, requesting fix from LLM...\n")
        self._chat.show_typing(show_review_phase=self.self_review_action.isChecked())
        self._request_code_fix(description, code, error_msg, original_response, attempt)

    def _request_code_fix(self, description: str, code: str, error: str,
                          original_response: str, attempt: int):
        """Send error to LLM and request fixed code."""
        fix_prompt = f"""The following FreeCAD Python code failed with an error:

```python
{code}
```

Error:
{error}

Please fix the code. The code runs in a SANDBOX where existing document objects are NOT available.
If you need to reference existing objects, recreate them or use hardcoded values.

Return ONLY the fixed Python code in a ```python code block, no explanation needed."""

        self._fix_worker = LLMWorker(self.llm, fix_prompt, "", [])
        self._fix_worker.finished.connect(
            lambda fixed_response: self._on_fix_response(
                description, fixed_response, original_response, attempt
            )
        )
        self._fix_worker.error.connect(self._on_fix_error)
        self._fix_worker.start()

    def _on_fix_response(self, description: str, response: str,
                         original_response: str, attempt: int):
        """Handle fixed code from LLM."""
        _, fixed_code = self._parse_response(response)

        if fixed_code.strip():
            self._attempt_preview_with_autofix(
                description, fixed_code, original_response, attempt + 1
            )
        else:
            FreeCAD.Console.PrintWarning(
                "DrawingAssistant: Couldn't parse fixed code, showing original\n"
            )
            self._chat.hide_typing()
            self._preview_manager.clear_preview()
            self._show_traditional_response(original_response)

    def _on_fix_error(self, error_msg: str):
        """Handle error from fix request."""
        FreeCAD.Console.PrintError(f"DrawingAssistant: Auto-fix request failed: {error_msg}\n")
        self._chat.hide_typing()
        self._preview_manager.clear_preview()
        if self._last_code:
            self._show_traditional_response(self._last_code)

    def _request_source_fix(self, failed_source: str, error: str,
                            original_response: str, attempt: int):
        """Send execution error to Claude and request fixed page files."""
        self._source_fix_original_response = original_response
        self._source_fix_attempt = attempt

        fix_prompt = f"""The page file(s) you just edited failed to execute with this error:

```
{error[:1500]}
```

Please fix the page file using the Edit tool. Common issues:
- Draft.make_circle(radius, placement): 2nd arg must be FreeCAD.Placement, NOT a Vector
- Draft.make_linear_dimension() ViewObject has NO ArrowSize attribute
- Using undefined variables
- Object "failed to compute": Usually means incorrect parameter types or values
- Geometry validation failed: Check API usage

Read the relevant page file to understand what went wrong, then fix it."""

        self._source_fix_worker = LLMWorker(self.llm, fix_prompt, "", [])
        self._source_fix_worker.finished.connect(self._on_source_fix_response)
        self._source_fix_worker.error.connect(self._on_source_fix_error)
        self._source_fix_worker.start()

    def _on_source_fix_response(self, response: str):
        """Handle response from source fix request."""
        attempt = getattr(self, '_source_fix_attempt', 1)
        original_response = getattr(self, '_source_fix_original_response', response)

        if getattr(self.llm, 'source_was_edited', False):
            FreeCAD.Console.PrintMessage(
                f"DrawingAssistant: Claude fixed page files, retrying preview (attempt {attempt + 1})\n"
            )
            self._handle_source_edit_response(original_response, attempt + 1)
        else:
            FreeCAD.Console.PrintWarning(
                "DrawingAssistant: Claude didn't edit any pages in fix response\n"
            )
            self._chat.hide_typing()
            SourceManager.restore_pages()
            self._chat.add_error_message(
                f"Could not auto-fix page files. Claude's response:\n\n{response}"
            )

    def _on_source_fix_error(self, error_msg: str):
        """Handle error from source fix request."""
        FreeCAD.Console.PrintError(f"DrawingAssistant: Source fix request failed: {error_msg}\n")
        self._chat.hide_typing()
        SourceManager.restore_pages()
        self._chat.add_error_message(f"Auto-fix failed: {error_msg}")

    def _parse_response(self, response: str) -> tuple:
        """Parse LLM response to extract description and code."""
        import re

        # Try to find Python code block with closing fence
        code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            code = code_match.group(1).strip()
            description = response[:code_match.start()].strip()
            description = re.sub(r'\n+', ' ', description)
            return (description, code)

        # Try any code block
        code_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            code = code_match.group(1).strip()
            description = response[:code_match.start()].strip()
            description = re.sub(r'\n+', ' ', description)
            return (description, code)

        # Handle unclosed code blocks
        unclosed_match = re.search(r'```python\s*\n(.*)', response, re.DOTALL)
        if unclosed_match:
            code = unclosed_match.group(1).strip()
            description = response[:unclosed_match.start()].strip()
            description = re.sub(r'\n+', ' ', description)
            FreeCAD.Console.PrintWarning(
                "DrawingAssistant: Detected unclosed code block - response may be truncated\n"
            )
            return (description, code)

        # No code block found - check if it looks like Python code
        code_indicators = [
            'import FreeCAD',
            'FreeCAD.',
            'Draft.',
            'TechDraw',
            'Spreadsheet',
            'doc.addObject',
            'doc.removeObject',
            '.removeObject(',
            'doc.recompute()',
            'make_wire',
            'make_circle',
            'make_text',
            'make_dimension',
            'make_linear_dimension',
            'make_rectangle',
            'DrawPage',
            'DrawSVGTemplate',
        ]
        if any(indicator in response for indicator in code_indicators):
            return ("", response.strip())

        # Pure text response
        return (response.strip(), "")

    def _show_traditional_response(self, response: str):
        """Show response as traditional code block."""
        debug_info = None
        if self.debug_action.isChecked():
            debug_info = {
                "duration_ms": self.llm.last_duration_ms,
                "model": self.llm.model,
                "context_length": len(self.llm.last_context),
                "system_prompt": self.llm.last_system_prompt,
                "context": self.llm.last_context,
                "conversation_history": self.llm.last_conversation,
                "user_message": self.pending_input or "",
            }

        use_streaming = self.streaming_action.isChecked()
        tool_calls = getattr(self.llm, 'last_tool_calls', None)
        self._chat.add_assistant_message(
            response, stream=use_streaming, debug_info=debug_info, tool_calls=tool_calls
        )

    def _on_error(self, error_msg: str):
        """Handle LLM error."""
        self._chat.hide_typing()
        self._chat.set_input_enabled(True)

        ActivityLogger.log_error(error_msg, context=self.pending_input)

        self.session_manager.log_llm_request(
            user_message=self.pending_input or "",
            system_prompt=self.llm.last_system_prompt,
            context=self.llm.last_context,
            conversation_history=self.llm.last_conversation,
            response="",
            model=self.llm.model,
            api_url=self.llm.api_url,
            duration_ms=self.llm.last_duration_ms,
            success=False,
            error=error_msg,
            tool_calls=getattr(self.llm, 'last_tool_calls', None),
            cost_usd=getattr(self.llm, 'last_cost', 0)
        )

        self._chat.add_error_message(error_msg)
        self.pending_input = None

    def _on_tool_call(self, tool_name: str, tool_input: dict):
        """Handle tool call event from LLM - update progress indicator."""
        self._chat.update_progress_phase(tool_name, tool_input)

    def _on_preview_approved(self, code: str):
        """Handle user approval of preview - execute code for real."""
        FreeCAD.Console.PrintMessage("DrawingAssistant: Preview approved - executing code\n")
        ActivityLogger.log_preview_approved()

        self._preview_manager.clear_preview()

        # Check if this is a page edit (backup exists) vs old-style patch
        if SourceManager.has_backup():
            FreeCAD.Console.PrintMessage("DrawingAssistant: Executing edited pages\n")

            before_snapshot = SnapshotManager.capture_current_state()

            doc = FreeCAD.ActiveDocument
            if doc:
                success, message, warnings = self._execute_pages_smart(doc)
            else:
                success, message, warnings = False, "No active document", []

            if warnings:
                self._last_execution_warnings.extend(warnings)

            after_snapshot = SnapshotManager.capture_current_state()

            if success:
                SourceManager.clear_backup()

                self._capture_multi_angle_screenshots()

                change_set = ChangeDetector.detect_changes(
                    before_snapshot, after_snapshot, code=""
                )
                change_set.execution_success = success
                change_set.execution_message = message

                self._show_change_result(change_set)
            else:
                FreeCAD.Console.PrintError(
                    f"DrawingAssistant: Drawing execution failed: {message}\n"
                )
                SourceManager.restore_pages()

                # Re-execute the restored pages to restore document objects
                CodeExecutor.clear_page_object_map()
                _clear_objects(doc)
                restored_pages = SourceManager.list_pages()
                if restored_pages:
                    FreeCAD.Console.PrintMessage(
                        "DrawingAssistant: Re-executing backup to restore objects\n"
                    )
                    CodeExecutor.execute_pages(restored_pages)

                self._last_execution_error = message
                self._chat.add_error_message(f"Execution error: {message}")
        else:
            self._on_run_code(code, already_executed=True)

    def _execute_pages_smart(self, doc) -> tuple:
        """Execute pages with incremental rebuild when possible.

        Checks whether only regular (non-helper) pages changed and a valid
        object mapping exists.  If so, clears only the changed pages' objects
        and re-executes only those pages.  Otherwise falls back to a full
        rebuild that also builds the mapping for next time.

        Returns:
            Tuple of (success: bool, message: str, warnings: list)
        """
        modified, added, deleted = SourceManager.get_changed_pages()
        page_map = CodeExecutor.get_page_object_map()
        tracked_doc = CodeExecutor.get_tracked_doc_name()

        all_changed = modified + added + deleted
        can_incremental = (
            page_map is not None
            and all_changed
            and not any(f.startswith("_") for f in all_changed)
            and all(f in page_map for f in modified + deleted)
            and tracked_doc == doc.Name
        )

        if can_incremental:
            return self._execute_incremental(doc, modified, added, deleted, page_map)

        reason = "first run" if page_map is None else "full rebuild required"
        FreeCAD.Console.PrintMessage(
            f"DrawingAssistant: Full rebuild ({reason})\n"
        )
        _clear_objects(doc)
        page_paths = SourceManager.list_pages()
        return CodeExecutor.execute_pages(page_paths)

    def _execute_incremental(self, doc, modified, added, deleted, page_map) -> tuple:
        """Execute only the changed pages, clearing their old objects first.

        Falls back to full rebuild if any page fails to execute.
        """
        changed_desc = ", ".join(modified + added)
        FreeCAD.Console.PrintMessage(
            f"DrawingAssistant: Incremental execution for: {changed_desc}\n"
        )

        # Selective clear: only changed + deleted pages' objects
        objects_to_clear = set()
        for f in modified + deleted:
            objects_to_clear.update(page_map.get(f, set()))

        if objects_to_clear:
            _clear_objects(doc, objects_to_clear)

        # Selective execute: modified + added pages only
        pages_dir = SourceManager.get_pages_dir()
        helper_paths = SourceManager.list_helper_pages()

        all_warnings = []
        for filename in sorted(modified + added, key=SourceManager.page_sort_key_str):
            page_path = pages_dir / filename
            success, msg, warnings, new_objs = CodeExecutor.execute_single_page(
                page_path, helper_paths
            )
            all_warnings.extend(warnings)
            if not success:
                FreeCAD.Console.PrintWarning(
                    f"DrawingAssistant: Incremental failed for {filename}: {msg}\n"
                    "  Falling back to full rebuild\n"
                )
                CodeExecutor.clear_page_object_map()
                _clear_objects(doc)
                page_paths = SourceManager.list_pages()
                return CodeExecutor.execute_pages(page_paths)
            CodeExecutor.update_page_object_map(filename, new_objs)

        for filename in deleted:
            CodeExecutor.remove_from_page_object_map(filename)

        return True, "Incremental execution succeeded", all_warnings

    def _on_preview_cancelled(self):
        """Handle user cancellation of preview."""
        FreeCAD.Console.PrintMessage("DrawingAssistant: Preview cancelled\n")
        ActivityLogger.log_preview_cancelled()

        self._preview_manager.cancel()

        # Restore pages from backup if this was a page edit
        if SourceManager.has_backup():
            FreeCAD.Console.PrintMessage("DrawingAssistant: Restoring pages from backup\n")
            SourceManager.restore_pages()
            ActivityLogger.log_drawing_restored()

        self._chat.add_system_message("Preview cancelled")

    def _on_plan_approved(self, plan_text: str):
        """Handle plan approval - request code generation (Phase 2)."""
        FreeCAD.Console.PrintMessage(
            "DrawingAssistant: Plan approved - requesting code generation\n"
        )
        ActivityLogger.log_plan_approved(plan_text)
        self._pending_plan = plan_text
        self._generate_code_from_plan(plan_text)

    def _on_plan_edited(self, edited_plan: str):
        """Handle plan edit and approval."""
        FreeCAD.Console.PrintMessage(
            "DrawingAssistant: Plan edited and approved - requesting code generation\n"
        )
        ActivityLogger.log_plan_edited(edited=edited_plan)
        self._pending_plan = edited_plan
        self._generate_code_from_plan(edited_plan)

    def _on_plan_cancelled(self):
        """Handle plan cancellation."""
        FreeCAD.Console.PrintMessage("DrawingAssistant: Plan cancelled\n")
        ActivityLogger.log_plan_cancelled()
        self._pending_plan = None
        self._plan_user_request = None
        self._chat.add_system_message("Plan cancelled")

    def _generate_code_from_plan(self, plan_text: str):
        """Request code generation based on approved plan (Phase 2)."""
        if self._plan_worker and self._plan_worker.isRunning():
            return

        self._chat.show_typing(show_review_phase=self.self_review_action.isChecked())
        self._chat.set_input_enabled(False)

        context = ""
        if self.context_action.isChecked():
            objects_filter = self._context_widget.get_context_objects()
            context = ContextBuilder.build_context(objects_filter=objects_filter)

        if self._last_execution_warnings:
            warnings_text = "\n".join(self._last_execution_warnings)
            context += (
                f"\n\n### Warnings from Previous Execution:\n```\n{warnings_text}\n```\n"
                "Please learn from these warnings and avoid using deprecated APIs."
            )
            self._last_execution_warnings = []

        if self._last_execution_error:
            context += (
                f"\n\n### Error from Previous Execution:\n```\n{self._last_execution_error}\n```\n"
                "Please fix this error in your next code generation."
            )
            self._last_execution_error = None

        conversation = self._chat.get_conversation_history()

        code_prompt = f"""The user approved this execution plan:

{plan_text}

Original request: {self._plan_user_request or ""}

Now write the FreeCAD Python code to implement this plan exactly as specified.
Return ONLY the Python code in a ```python code block."""

        self._plan_worker = LLMWorker(
            self.llm, code_prompt, context, conversation,
            self._last_multi_angle_screenshots
        )
        self._plan_worker.finished.connect(self._on_plan_code_response)
        self._plan_worker.error.connect(self._on_error)
        self._plan_worker.start()

    def _on_plan_code_response(self, response: str):
        """Handle code response from plan (Phase 2)."""
        self._chat.hide_typing()
        self._chat.set_input_enabled(True)

        self._pending_plan = None
        self._plan_user_request = None
        self._last_code = response

        self.session_manager.log_llm_request(
            user_message="[Plan Phase 2: Code Generation]",
            system_prompt=self.llm.last_system_prompt,
            context=self.llm.last_context,
            conversation_history=self.llm.last_conversation,
            response=response,
            model=self.llm.model,
            api_url=self.llm.api_url,
            duration_ms=self.llm.last_duration_ms,
            success=True,
            tool_calls=getattr(self.llm, 'last_tool_calls', None),
            cost_usd=getattr(self.llm, 'last_cost', 0)
        )

        description, code = self._parse_response(response)

        if not code.strip():
            self._show_traditional_response(response)
            return

        self._attempt_preview_with_autofix(description, code, response)

    def _on_run_code(self, code: str, already_executed: bool = False):
        """Execute the provided code and display changes."""
        if not code.strip():
            return

        before_snapshot = SnapshotManager.capture_current_state()

        success, message, warnings = CodeExecutor.execute(code)
        if warnings:
            self._last_execution_warnings.extend(warnings)
        ActivityLogger.log_code_executed(success, message, code=code)

        after_snapshot = SnapshotManager.capture_current_state()

        change_set = ChangeDetector.detect_changes(
            before_snapshot, after_snapshot,
            code="" if already_executed else code
        )
        change_set.execution_success = success
        change_set.execution_message = message

        if success:
            self._capture_multi_angle_screenshots()

            self._self_review_attempt = 0
            self._run_self_review(change_set)
        else:
            self._last_execution_error = message
            self._chat.add_error_message(f"Execution error: {message}")

    def _on_mode_changed(self, mode: str):
        """Handle segmented control mode change."""
        if mode == "3d":
            try:
                grp = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/AIAssistant")
                grp.SetString("LastMode", mode)
            except Exception:
                pass
            import AIAssistant
            AIAssistant.show()

    def _on_clear(self):
        """Clear the chat UI."""
        self._chat.clear_chat()
        self._last_code = ""

    def _clear_conversation(self):
        """Clear conversation history and start new session."""
        self._on_clear()
        self.session_manager.clear_current_session()
        self._chat.add_system_message("Conversation cleared - new session started")
        ActivityLogger.log_session_cleared()

    def _on_debug_toggled(self, checked: bool):
        """Handle debug mode toggle."""
        current_id = self.session_manager.get_current_session_id()
        if current_id:
            self._on_load_session(current_id)

    def _get_project_dir(self) -> str:
        """Get project directory for Claude Code working directory."""
        doc = FreeCAD.ActiveDocument
        if doc and doc.FileName:
            doc_path = Path(doc.FileName)
            project_dir = doc_path.parent / doc_path.stem
            project_dir.mkdir(parents=True, exist_ok=True)
            return str(project_dir)
        return None

    def _update_project_dir(self):
        """Update project directory when document changes."""
        new_dir = self._get_project_dir()
        if new_dir and new_dir != self._project_dir:
            self._project_dir = new_dir
            if hasattr(self.llm, 'project_dir'):
                self.llm.project_dir = new_dir
                FreeCAD.Console.PrintMessage(
                    f"DrawingAssistant: Project directory updated to {new_dir}\n"
                )
            self._ensure_claude_md()

    def _prompt_save_document(self):
        """Prompt user to save the document before using Drawing Assistant."""
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("Save Document Required")
        msg_box.setText("Please save your document first.")
        msg_box.setInformativeText(
            "The Drawing Assistant needs a saved document to store:\n"
            "• pages/ - Per-page drawing scripts\n"
            "• Sessions and snapshots\n\n"
            "Would you like to save now?"
        )
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setStandardButtons(
            QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Cancel
        )
        msg_box.setDefaultButton(QtWidgets.QMessageBox.Save)

        result = msg_box.exec()

        if result == QtWidgets.QMessageBox.Save:
            try:
                FreeCADGui.runCommand("Std_SaveAs", 0)
                self._update_project_dir()
                self._ensure_pages_dir()
                self._ensure_claude_md()
            except Exception as e:
                FreeCAD.Console.PrintError(f"DrawingAssistant: Save failed: {e}\n")

    def _ensure_claude_md(self):
        """Ensure CLAUDE.md exists in project directory for Claude Code backend."""
        if not self._project_dir:
            return

        claude_md_path = Path(self._project_dir) / "CLAUDE.md"
        if claude_md_path.exists():
            return

        try:
            template_path = Path(__file__).parent / "project_claude_template.md"
            if template_path.exists():
                freecad_source = str(Path(__file__).parent.parent.parent)
                template_content = template_path.read_text(encoding="utf-8")
                content = template_content.replace("{{FREECAD_SOURCE}}", freecad_source)
                claude_md_path.write_text(content, encoding="utf-8")
                FreeCAD.Console.PrintMessage(
                    f"DrawingAssistant: Created CLAUDE.md in {self._project_dir}\n"
                )
        except Exception as e:
            FreeCAD.Console.PrintWarning(
                f"DrawingAssistant: Failed to create CLAUDE.md: {e}\n"
            )

    def _ensure_pages_dir(self):
        """Ensure pages/ directory exists for current document."""
        doc = FreeCAD.ActiveDocument
        if doc and doc.FileName:
            if not SourceManager.exists():
                SourceManager.init_pages_dir()

    def _run_self_review(self, change_set):
        """Run self-review loop for 2D drawing results."""
        if not self.self_review_action.isChecked():
            self._show_change_result(change_set)
            return

        if not self._last_multi_angle_screenshots:
            FreeCAD.Console.PrintWarning(
                "DrawingAssistant: No screenshots for self-review, skipping\n"
            )
            self._show_change_result(change_set)
            return

        self._self_review_attempt += 1
        if self._self_review_attempt > self._max_self_review_attempts:
            FreeCAD.Console.PrintMessage(
                f"DrawingAssistant: Max self-review attempts ({self._max_self_review_attempts}) reached\n"
            )
            self._self_review_attempt = 0
            self._show_change_result(change_set)
            return

        self._self_review_change_set = change_set

        FreeCAD.Console.PrintMessage(
            f"DrawingAssistant: Running self-review (attempt {self._self_review_attempt})...\n"
        )
        self._chat.show_typing()
        self._chat.set_progress_reviewing()

        review_prompt = """I just executed code that modified the 2D drawing. Please review the screenshots.

IMPORTANT: Check carefully for:
- Draft wires/shapes positioned correctly
- Dimensions showing correct values and properly placed
- Text labels readable and in correct positions
- Grid lines aligned properly
- Missing or overlapping geometry
- TechDraw page layout issues (if applicable)

If the result looks CORRECT, respond with just: "LOOKS_GOOD"

If there are PROBLEMS, explain briefly what's wrong and edit the relevant page file to fix them."""

        self._self_review_worker = LLMWorker(
            self.llm, review_prompt, "", [],
            multi_angle_screenshots=self._last_multi_angle_screenshots
        )
        self._self_review_worker.finished.connect(self._on_self_review_response)
        self._self_review_worker.error.connect(self._on_self_review_error)
        self._self_review_worker.start()

    def _on_self_review_response(self, response: str):
        """Handle response from self-review request."""
        self._chat.hide_typing()

        ActivityLogger.log_llm_response(
            f"[Self-Review] {response}",
            session_id=self.session_manager.get_current_session_id()
        )

        if "LOOKS_GOOD" in response.upper():
            FreeCAD.Console.PrintMessage("DrawingAssistant: Self-review passed\n")
            self._self_review_attempt = 0
            self._show_change_result(self._self_review_change_set)
            self._self_review_change_set = None
            return

        if getattr(self.llm, 'source_was_edited', False):
            FreeCAD.Console.PrintMessage(
                "DrawingAssistant: Self-review found issues, Claude edited pages. Re-executing...\n"
            )

            doc = FreeCAD.ActiveDocument
            if doc:
                _clear_objects(doc)

            # Full rebuild with tracking (self-review has no backup to diff)
            page_paths = SourceManager.list_pages()
            success, message, warnings = CodeExecutor.execute_pages(page_paths)
            if warnings:
                self._last_execution_warnings.extend(warnings)

            if success:
                self._capture_multi_angle_screenshots()

                after_snapshot = SnapshotManager.capture_current_state()
                change_set = ChangeDetector.detect_changes({}, after_snapshot, code="")
                change_set.execution_success = True
                change_set.execution_message = "Re-executed after self-review fix"

                self._run_self_review(change_set)
            else:
                self._self_review_attempt = 0
                self._last_execution_error = message
                self._chat.add_error_message(f"Self-review fix failed: {message}")
        else:
            FreeCAD.Console.PrintMessage(
                "DrawingAssistant: Self-review found issues but Claude didn't fix. Showing result.\n"
            )
            self._self_review_attempt = 0
            self._show_change_result(self._self_review_change_set)
            self._chat.add_system_message(f"Self-review note: {response[:200]}...")
            self._self_review_change_set = None

    def _on_self_review_error(self, error_msg: str):
        """Handle error from self-review request."""
        FreeCAD.Console.PrintWarning(f"DrawingAssistant: Self-review failed: {error_msg}\n")
        self._chat.hide_typing()
        self._self_review_attempt = 0
        if self._self_review_change_set:
            self._show_change_result(self._self_review_change_set)
            self._self_review_change_set = None

    def _show_change_result(self, change_set):
        """Show the change result to the user."""
        if change_set.is_empty():
            self._chat.add_system_message("Code executed successfully (no object changes)")
        else:
            self._chat.add_change_message(change_set)

    def _capture_techdraw_screenshots(self, doc=None, screenshots_dir=None) -> list:
        """Export each TechDraw DrawPage as SVG then render to PNG.

        Returns list of PNG file paths.
        """
        results = []
        if doc is None:
            doc = FreeCAD.ActiveDocument
        if not doc:
            return results

        pages = _find_techdraw_pages(doc)
        if not pages:
            return results

        try:
            import TechDrawGui
        except ImportError:
            FreeCAD.Console.PrintWarning(
                "DrawingAssistant: TechDrawGui not available, skipping page screenshots\n"
            )
            return results

        if screenshots_dir is None:
            if not self._project_dir:
                return results
            screenshots_dir = Path(self._project_dir) / "screenshots"
        screenshots_dir = Path(screenshots_dir)
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        for page in pages:
            try:
                safe_label = re.sub(r"[^\w\-]", "_", page.Label).strip("_")
                if not safe_label:
                    safe_label = page.Name

                svg_path = str(screenshots_dir / f"_tmp_sheet_{safe_label}.svg")
                png_path = str(screenshots_dir / f"latest_sheet_{safe_label}.png")

                TechDrawGui.exportPageAsSvg(page, svg_path)

                if _svg_to_png(svg_path, png_path):
                    results.append(png_path)
                    FreeCAD.Console.PrintMessage(
                        f"DrawingAssistant: Captured sheet {page.Label} -> "
                        f"latest_sheet_{safe_label}.png\n"
                    )

                # Clean up temp SVG
                try:
                    Path(svg_path).unlink()
                except OSError:
                    pass

            except Exception as e:
                FreeCAD.Console.PrintWarning(
                    f"DrawingAssistant: Failed to capture sheet {page.Label}: {e}\n"
                )

        return results

    def _capture_multi_angle_screenshots(self) -> list:
        """Capture PNG screenshots of each TechDraw page."""
        if not FreeCADGui.ActiveDocument or not self._project_dir:
            return []

        screenshots_dir = Path(self._project_dir) / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        # Clean stale files from older sessions
        for pattern in ("latest_isometric.png", "latest_top.png"):
            for stale in screenshots_dir.glob(pattern):
                try:
                    stale.unlink()
                except OSError:
                    pass

        results = self._capture_techdraw_screenshots(
            doc=FreeCAD.ActiveDocument, screenshots_dir=screenshots_dir
        )
        self._last_multi_angle_screenshots = results
        return results

    # =========================================================================
    # Sandbox Self-Review
    # =========================================================================

    def _capture_sandbox_screenshots(self, sandbox_doc_name: str) -> list:
        """Capture TechDraw page screenshots from sandbox document."""
        original_doc = FreeCAD.ActiveDocument
        original_gui_doc = FreeCADGui.ActiveDocument
        try:
            sandbox_doc = FreeCAD.getDocument(sandbox_doc_name)
            if not sandbox_doc:
                FreeCAD.Console.PrintWarning(
                    f"DrawingAssistant: Sandbox doc {sandbox_doc_name} not found\n"
                )
                return []

            FreeCAD.setActiveDocument(sandbox_doc_name)
            FreeCADGui.setActiveDocument(sandbox_doc_name)
            FreeCADGui.updateGui()

            if not self._project_dir:
                return []

            screenshots_dir = Path(self._project_dir) / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)

            return self._capture_techdraw_screenshots(
                doc=sandbox_doc, screenshots_dir=screenshots_dir
            )
        except Exception as e:
            FreeCAD.Console.PrintWarning(
                f"DrawingAssistant: Sandbox screenshot error: {e}\n"
            )
            return []
        finally:
            if original_doc:
                try:
                    FreeCAD.setActiveDocument(original_doc.Name)
                except Exception:
                    pass
            if original_gui_doc:
                try:
                    FreeCADGui.setActiveDocument(original_gui_doc.Name)
                    FreeCADGui.updateGui()
                except Exception:
                    pass

    def _run_sandbox_self_review(self):
        """Run self-review with screenshots from sandbox document."""
        if not self._sandbox_session or not self._sandbox_session.is_active:
            FreeCAD.Console.PrintWarning(
                "DrawingAssistant: No active sandbox session for self-review\n"
            )
            self._finalize_sandbox_preview()
            return

        if self._sandbox_session.iteration >= self._sandbox_session.max_iterations:
            FreeCAD.Console.PrintMessage(
                "DrawingAssistant: Sandbox self-review max iterations reached, showing preview\n"
            )
            self._finalize_sandbox_preview()
            return

        FreeCAD.Console.PrintMessage(
            f"DrawingAssistant: Running sandbox self-review "
            f"(iteration {self._sandbox_session.iteration + 1})...\n"
        )
        self._chat.show_typing()
        self._chat.set_progress_reviewing()

        screenshots = self._capture_sandbox_screenshots(
            self._sandbox_session.sandbox_doc_name
        )

        if not screenshots:
            FreeCAD.Console.PrintWarning(
                "DrawingAssistant: No sandbox screenshots, skipping self-review\n"
            )
            self._chat.hide_typing()
            self._finalize_sandbox_preview()
            return

        review_prompt = """Review these screenshots of the 2D drawing I just created.

CRITICAL CHECKS:
1. **Draft geometry**: Wires, circles, and shapes should be positioned correctly
2. **Dimensions**: Values should be correct, leaders pointing to right objects
3. **Text/Labels**: Readable, properly positioned, no overlaps
4. **Grid/Axes**: If present, properly aligned and labeled
5. **TechDraw**: If a page was created, views should be placed and scaled correctly
6. **General**: Missing elements, overlapping geometry, wrong positions

If it looks correct: Start your response with [APPROVED] then describe what you see.

If there are problems: Explain what's wrong and edit the relevant page file to fix them."""

        self._sandbox_review_worker = LLMWorker(
            self.llm, review_prompt, "", [],
            multi_angle_screenshots=screenshots
        )
        self._sandbox_review_worker.finished.connect(self._on_sandbox_review_response)
        self._sandbox_review_worker.error.connect(self._on_sandbox_review_error)
        self._sandbox_review_worker.start()

    def _on_sandbox_review_response(self, response: str):
        """Handle response from sandbox self-review."""
        self._chat.hide_typing()

        ActivityLogger.log_llm_response(
            f"[Sandbox Self-Review] {response}",
            session_id=self.session_manager.get_current_session_id()
        )

        is_approved = "[APPROVED]" in response.upper()
        display_response = response.replace("[APPROVED]", "").replace("[approved]", "").strip()
        self._sandbox_review_response = display_response

        if is_approved:
            FreeCAD.Console.PrintMessage(
                "DrawingAssistant: Self-review passed, showing preview to user\n"
            )
            self._finalize_sandbox_preview()
            return

        if getattr(self.llm, 'source_was_edited', False):
            FreeCAD.Console.PrintMessage(
                "DrawingAssistant: Claude edited pages during sandbox review, re-executing...\n"
            )

            new_source = SourceManager.read_all_pages()
            success, error_msg = self._preview_manager.re_execute_in_sandbox(
                self._sandbox_session, new_source
            )

            if success:
                self._run_sandbox_self_review()
            else:
                FreeCAD.Console.PrintWarning(
                    f"DrawingAssistant: Sandbox re-execution failed: {error_msg[:100]}...\n"
                )
                self._finalize_sandbox_preview()
        else:
            FreeCAD.Console.PrintMessage(
                "DrawingAssistant: Claude noted issues but didn't edit, showing preview\n"
            )
            self._finalize_sandbox_preview()

    def _on_sandbox_review_error(self, error_msg: str):
        """Handle error from sandbox self-review request."""
        FreeCAD.Console.PrintWarning(
            f"DrawingAssistant: Sandbox self-review failed: {error_msg}\n"
        )
        self._chat.hide_typing()
        self._finalize_sandbox_preview()

    def _finalize_sandbox_preview(self):
        """Self-review complete - create preview and show to user."""
        if not self._sandbox_session:
            FreeCAD.Console.PrintWarning(
                "DrawingAssistant: No sandbox session to finalize\n"
            )
            return

        success = self._preview_manager.commit_sandbox_to_preview(self._sandbox_session)

        if success:
            preview_items = self._preview_manager.get_preview_summary()
        else:
            # 2D objects (TechDraw/Draft groups) have no Part shapes for 3D green
            # preview, but sandbox ran fine. Get object list from sandbox directly.
            # Approve handler reads pages from disk (SourceManager), not from
            # _pending_code, so no need to set it here.
            preview_items = self._preview_manager.get_sandbox_summary(self._sandbox_session)

        self._preview_manager.close_sandbox(self._sandbox_session)

        source_content = self._sandbox_session.source_content

        FreeCAD.Console.PrintMessage(
            f"DrawingAssistant: Sandbox preview finalized with {len(preview_items)} objects\n"
        )

        auto_approve = self.auto_accept_action.isChecked()

        self._chat.add_preview_message(
            description=self._sandbox_review_response or "Page files modified",
            preview_items=preview_items,
            code=source_content,
            is_deletion=False,
            auto_approve=auto_approve,
            tool_calls=None
        )

        self._sandbox_session = None

    def closeEvent(self, event):
        """Clean up when panel is closed."""
        ActivityLogger.log_panel_closed()
        ContextBuilder.stop_console_observer()
        super().closeEvent(event)
