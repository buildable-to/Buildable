# SPDX-License-Identifier: LGPL-2.1-or-later

# DrawingAssistant Module - 2D structural drawing AI assistant

# Root level files
SET(DrawingAssistant_SRCS
    Init.py
    InitGui.py
    __init__.py
    DrawingPanel.py
    Theme.py
    project_claude_template.md
)

# LLM backend implementations
SET(DrawingAssistant_backends
    backends/__init__.py
    backends/claude_code.py
)

# Core business logic
SET(DrawingAssistant_core
    core/__init__.py
    core/context.py
    core/source.py
    core/snapshot.py
    core/changes.py
    core/executor.py
    core/preview.py
)

# Session and logging persistence
SET(DrawingAssistant_persistence
    persistence/__init__.py
    persistence/session.py
    persistence/activity.py
)

# Qt UI widgets
SET(DrawingAssistant_widgets
    widgets/__init__.py
    widgets/chat.py
    widgets/message_model.py
    widgets/message_delegate.py
    widgets/code_block.py
    widgets/syntax.py
    widgets/change.py
    widgets/preview.py
    widgets/plan.py
    widgets/step_preview.py
    widgets/context_selection.py
    widgets/progress_indicator.py
    widgets/activity.py
)

# Combine all sources for IDE visibility
SET(DrawingAssistant_ALL_SRCS
    ${DrawingAssistant_SRCS}
    ${DrawingAssistant_backends}
    ${DrawingAssistant_core}
    ${DrawingAssistant_persistence}
    ${DrawingAssistant_widgets}
)

SOURCE_GROUP("" FILES ${DrawingAssistant_SRCS})
SOURCE_GROUP("backends" FILES ${DrawingAssistant_backends})
SOURCE_GROUP("core" FILES ${DrawingAssistant_core})
SOURCE_GROUP("persistence" FILES ${DrawingAssistant_persistence})
SOURCE_GROUP("widgets" FILES ${DrawingAssistant_widgets})

ADD_CUSTOM_TARGET(DrawingAssistant ALL
    SOURCES ${DrawingAssistant_ALL_SRCS}
)

fc_copy_sources(DrawingAssistant "${CMAKE_BINARY_DIR}/Mod/DrawingAssistant" ${DrawingAssistant_ALL_SRCS})

# Install with directory structure preserved
INSTALL(FILES ${DrawingAssistant_SRCS} DESTINATION Mod/DrawingAssistant)
INSTALL(FILES ${DrawingAssistant_backends} DESTINATION Mod/DrawingAssistant/backends)
INSTALL(FILES ${DrawingAssistant_core} DESTINATION Mod/DrawingAssistant/core)
INSTALL(FILES ${DrawingAssistant_persistence} DESTINATION Mod/DrawingAssistant/persistence)
INSTALL(FILES ${DrawingAssistant_widgets} DESTINATION Mod/DrawingAssistant/widgets)
