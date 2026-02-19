# Plan Mode — Two-Phase LLM Flow

## Overview

Plan mode splits drawing generation into two phases:

1. **Phase 1 (Plan)** — Claude explores the project read-only and returns a numbered execution plan
2. **User Review** — The plan is shown in a PlanWidget for approval or refinement
3. **Phase 2 (Execute)** — Claude implements the approved plan with full file editing access

This gives the user visibility and control over what Claude will build before any files are modified.

## Architecture

```
User: "Design a pad footing 2x2m"
          │
          ▼
  ┌─────────────────────────┐
  │  Phase 1: Plan          │
  │  --tools Read,Glob,Grep │  ← No Edit/Write/ExitPlanMode in context
  │  --resume (new session) │
  └───────────┬─────────────┘
              │ Plan text returned in result
              ▼
  ┌─────────────────────────┐
  │  PlanWidget             │
  │  - Rendered markdown    │
  │  - Approve / Keep       │
  │    Planning             │
  └───────────┬─────────────┘
              │
    ┌─────────┴──────────┐
    │                    │
    ▼                    ▼
  User approves     User types follow-up
    │                    │
    ▼                    ▼
  Phase 2            Phase 1 again
  (execute)          (refine plan)
```

## Key Design Decision: `--tools` vs `--allowedTools`

The critical insight that makes plan mode work:

| Flag | What it does | Effect on ExitPlanMode |
|------|-------------|----------------------|
| `--tools Read,Glob,Grep` | **Restricts which tools exist in context** | Removed entirely — Claude can't call it |
| `--allowedTools Read,Glob,Grep` | Auto-approves listed tools (others still available) | Still in context — Claude calls it |
| `--disallowedTools ExitPlanMode` | Blacklists specific tools from context | Would also work, but whitelist is safer |

We use `--tools` for Phase 1 because it deterministically prevents Claude from calling `ExitPlanMode` (a built-in Claude Code tool that hijacks plan responses). The plan text comes back in the `result` field of the stream-json output.

## Phase 1: Plan Generation

**Trigger**: User has the "Plan" pill toggled on in the input bar when sending a message.

**DrawingPanel.py** (`_on_send`):
```python
if self._chat.is_plan_mode():
    plan_prompt = f"""Create a detailed execution plan for this drawing request.
    User request: {user_input}
    ...
    """
    self.worker = LLMWorker(
        self.llm, plan_prompt, context, conversation,
        all_screenshots, read_only=True    # ← triggers --tools restriction
    )
```

**claude_code.py** (`chat`):
```python
if read_only:
    cmd.extend(["--tools", "Read,Glob,Grep"])
```

### Response Handling

The plan text arrives in two possible locations:
1. **Primary**: The `result` event's `result` field (normal path)
2. **Fallback**: Accumulated `text` blocks from `assistant` message events

**DrawingPanel._on_response** detects plan mode and routes to the widget:
```python
if self._plan_mode_request:
    self._plan_mode_request = False
    self._chat.add_plan_message(response, self._plan_user_request or "")
    self._plan_pending_refinement = response  # Enable refinement on follow-up
    return
```

## PlanWidget: User Review

**widgets/plan.py** renders the plan as markdown using `_md_to_html()` from `message_delegate.py`. The plan text is displayed as a QLabel with `RichText` format, matching assistant message styling.

The widget provides two actions:
- **Approve Plan** → `planApproved` signal → Phase 2 code generation
- **Keep Planning** → `planKeepPlanning` signal → dims widget, re-enables input

After showing a plan, `_plan_pending_refinement` is automatically set, so if the user types a follow-up message (with or without clicking "Keep Planning"), it triggers plan refinement instead of creating a new independent plan.

## Plan Refinement

When the user sends a message while `_plan_pending_refinement` is set:

```python
# In _on_send():
if self._plan_pending_refinement:
    current_plan = self._plan_pending_refinement
    self._plan_pending_refinement = None
    refinement_prompt = f"""The user wants to modify the current plan.
    Current plan: {current_plan}
    User feedback: {user_input}
    Revise the plan based on this feedback..."""
    self.worker = LLMWorker(self.llm, refinement_prompt, ..., read_only=True)
```

The refined plan appears as a new PlanWidget, with the old one dimmed.

## Phase 2: Code Generation

**DrawingPanel._generate_code_from_plan**:

```python
code_prompt = f"""The user approved this execution plan:
{plan_text}
Original request: {self._plan_user_request or ""}
Now implement this plan by editing the page files in pages/."""

self._plan_worker = LLMWorker(
    self.llm, code_prompt, context, conversation,
    self._get_top_view_screenshots()
    # read_only defaults to False → --allowedTools used instead
)
```

Phase 2 uses `--resume` with the same session ID from Phase 1, so Claude retains all the file exploration context from planning. `--allowedTools Read,Glob,Grep,Edit,Write` gives full editing access.

The response flows into the standard `_on_response` handler, which detects edited files and triggers the preview/self-review pipeline.

## Session Continuity

Both phases share the same Claude Code session via `--resume`:

```
Phase 1: claude -p --tools Read,Glob,Grep ...
         → session_id captured from result event

Phase 2: claude -p --allowedTools Read,Glob,Grep,Edit,Write --resume <session_id> ...
         → Claude remembers all files it read during planning
```

The `--tools` and `--allowedTools` flags are per-invocation, not per-session.

## State Management

```python
# DrawingPanel state fields:
self._plan_mode_request: bool           # True during Phase 1 only
self._pending_plan: str                 # Approved plan text (for Phase 2)
self._plan_user_request: str            # Original user message
self._plan_pending_refinement: str      # Current plan text (enables refinement)
self._plan_worker: LLMWorker            # Phase 2 worker thread
```

State transitions:
- Phase 1 response → `_plan_mode_request = False`, `_plan_pending_refinement = response`
- User approves → `_pending_plan = plan_text`, `_plan_pending_refinement = None`, Phase 2 starts
- User sends follow-up → `_plan_pending_refinement` consumed, new Phase 1 (refinement)
- "Keep Planning" click → `_plan_pending_refinement` re-set (already set automatically)
- Cancel → all plan state cleared
