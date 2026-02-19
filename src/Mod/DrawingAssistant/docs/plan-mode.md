# Plan Mode — Two-Phase LLM Flow

## Overview

Plan mode splits drawing generation into two phases:

1. **Phase 1 (Plan)** — Claude explores the project read-only and returns a numbered execution plan
2. **User Review** — The plan is shown in a PlanWidget for approval, editing, or cancellation
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
  │  - Parse numbered steps │
  │  - Approve / Edit /     │
  │    Cancel               │
  └───────────┬─────────────┘
              │ User approves
              ▼
  ┌──────────────────────────────┐
  │  Phase 2: Execute            │
  │  --allowedTools R,G,Gr,E,W   │  ← Full tool access
  │  --resume (same session)     │  ← Retains Phase 1 context
  └───────────┬──────────────────┘
              │ Files edited
              ▼
  ┌─────────────────────────┐
  │  Preview / Self-Review  │  ← Standard flow from here
  └─────────────────────────┘
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

**Trigger**: User has "Plan mode" checked in the toolbar when sending a message.

**DrawingPanel.py** (`_on_send`, line 728-748):
```python
if self._plan_mode_request:
    plan_prompt = f"""Create a detailed execution plan for this drawing request.

User request: {user_input}

Read existing page files first to understand the current state...
Format:
## Plan
1. **Action**: Specific description with numbers
2. **Action**: Description
..."""

    self.worker = LLMWorker(
        self.llm, plan_prompt, context, conversation,
        all_screenshots, read_only=True    # ← triggers --tools restriction
    )
```

**claude_code.py** (`chat`, line 316-317):
```python
if read_only:
    cmd.extend(["--tools", "Read,Glob,Grep"])
```

The system prompt also includes a plan mode section telling Claude to output numbered steps without editing files.

### Response Handling

The plan text arrives in two possible locations:
1. **Primary**: The `result` event's `result` field (normal path)
2. **Fallback**: Accumulated `text` blocks from `assistant` message events

```python
assistant_text_parts = []  # Fallback accumulator

# In the NDJSON parsing loop:
if block.get("type") == "text":
    assistant_text_parts.append(block.get("text", ""))

# After loop:
if not result_text and assistant_text_parts:
    result_text = "\n".join(assistant_text_parts)
```

**DrawingPanel._on_response** (line 843-849) detects plan mode and routes to the widget:
```python
if self._plan_mode_request:
    self._plan_mode_request = False
    self._chat.add_plan_message(response, self._plan_user_request or "")
    return
```

## PlanWidget: User Review

**widgets/plan.py** parses the plan text into numbered steps using regex:

```python
# Split at "N. " boundaries, then parse each chunk:
# "N. **Action**: Description (may be multi-line)"
chunks = re.split(r'(?=(?:^|\n)\s*\d+\.\s)', plan_text)
```

The widget provides three actions:
- **Approve** → `planApproved` signal → `_on_plan_approved()`
- **Edit + Approve** → `planEdited` signal → `_on_plan_edited(edited_text)`
- **Cancel** → `planCancelled` signal → `_on_plan_cancelled()`

Users can toggle between view mode (parsed steps with numbered badges) and edit mode (raw text editor) to modify the plan before approving.

## Phase 2: Code Generation

**DrawingPanel._generate_code_from_plan** (line 1493-1546):

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

Key: Phase 2 uses `--resume` with the same session ID from Phase 1, so Claude retains all the file exploration context from planning. But now `--allowedTools Read,Glob,Grep,Edit,Write` gives full editing access.

The response flows into the standard `_on_response` handler, which detects edited files and triggers the preview/self-review pipeline.

## Session Continuity

Both phases share the same Claude Code session via `--resume`:

```
Phase 1: claude -p --tools Read,Glob,Grep ...
         → session_id captured from result event

Phase 2: claude -p --allowedTools Read,Glob,Grep,Edit,Write --resume <session_id> ...
         → Claude remembers all files it read during planning
```

The `--tools` and `--allowedTools` flags are per-invocation, not per-session. This means Phase 2 gets full tool access even though Phase 1 was restricted.

## Cost

Typical plan mode costs (from testing):
- Phase 1 (plan): ~$0.15 (reads files, generates plan text)
- Phase 2 (code): ~$0.20 (implements plan, edits files)
- Total: ~$0.35

Compare to non-plan mode: ~$0.25-0.65 (single shot, no user review)

## State Management

```python
# DrawingPanel state fields:
self._plan_mode_request: bool    # True during Phase 1 only
self._pending_plan: str          # Approved plan text (for Phase 2)
self._plan_user_request: str     # Original user message
self._plan_worker: LLMWorker     # Phase 2 worker thread
```

State cleanup:
- `_plan_mode_request` → cleared in `_on_response` after Phase 1
- `_pending_plan` and `_plan_user_request` → cleared in `_on_response` after Phase 2
- On cancel: both cleared immediately in `_on_plan_cancelled`
