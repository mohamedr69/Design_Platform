# Drawings Assistant

A chat on the Drawings page. The engineer asks about the system on show, or asks for a change, and the
assistant answers from the project's memory and proposes the change for the engineer to apply.

Date: 7 October 2026. Code: `backend/app/services/drawings_chat.py`, the two `assistant` routes in
`backend/app/routers/drawings.py`, `frontend/src/components/drawings/AssistantPanel.tsx`.

## What it knows

The project's memory is built deterministically from the records every time a message is sent. It is what
the Drawings page itself shows, for the project and the system on show:

| Part | Source | Content |
|---|---|---|
| `project` | Project row | EP number, name, status, client, consultant, contractor, location, plot, scope, systems, drawings in scope, last sync |
| `systems` | `shop_drawings.summary` | Every system's floors and status counts (the system cards) |
| `system` | `shop_drawings.log` | The system on show floor by floor: drawing id and reference, floors, each submitted revision's status (and whether an engineer set it), detected files with their candidate ids, hints, remarks, open issues |
| `issues` | `drawing_issues.open_issues` | Review & Issues, with candidate ids and floor alias keys |
| `required` | `drawing_requirements.status` | Actions Required: each item's status and when it was requested |
| `events` | `shop_drawings.events` | Activity / History, the latest first |
| `vocabulary` | code | The status codes and labels, and the actions it may propose |

The system's log goes in floor by floor (the records' own grain), whichever view the page shows: the
Drawings Log's "As per IFC" view (a row per IFC plan sheet, `GET …/drawings/log?view=ifc`) is a reading of the
same records, so the assistant's answers and proposals are the same under either view.

No file is opened for it. The memory is bounded (`DRAWINGS_CHAT_MAX_ROWS`, `DRAWINGS_CHAT_MAX_EVENTS`,
`DRAWINGS_CHAT_MAX_INPUT_TOKENS`); when a tall building does not fit, the events go first, then the floors
that are approved with nothing to review, and the memory says what was left out.

## What it may do

Propose, never write. Each proposal is one of:

| Kind | Checked against | Becomes |
|---|---|---|
| `set_revision_status` | a drawing of this system, a revision `Rn`, an official status | `PUT …/sd/{id}/revisions/{rev}` |
| `confirm_revision` / `ignore_revision` | an open detected revision of this system | `POST …/candidates/{id}/confirm` or `/ignore` |
| `resolve_issue` | an open review item of this system | `POST …/issues/{id}/resolve` |
| `correct_drawing` | a drawing of this system; floors of this building | `PATCH …/sd/{id}` |
| `merge_floors` / `keep_floors_separate` | floors of this building | `POST …/floors/merge` or `/separate` |

A proposal the records refuse is dropped and the reason is shown under the answer. The page shows every
accepted proposal with **Apply** and **Dismiss**; Apply makes the same call the page's own button makes,
under the engineer's role (the creator roles). A reader role sees the proposals and cannot apply them. A
merge that brings two drawn floors together answers `merge_review` as it does from the Review & Issues tab;
the panel says to confirm it there.

## Switches

| Setting | Default | Meaning |
|---|---|---|
| `AI_ENABLED` | off | The platform's AI switch; on, the assistant is on with it |
| `DRAWINGS_CHAT_AI_ENABLED` | off | The assistant alone, with `AI_ENABLED` off for the rest of the platform (as `DRAWING_REVIEW_AI_ENABLED` and `PREP_AI_ENABLED` do for theirs); the live installation runs this way, on since 7 October 2026 with `AI_PROVIDER=claude-code` (the signed-in Claude subscription) |
| `DRAWINGS_CHAT_ENABLED` | on | The assistant alone |
| `DRAWINGS_CHAT_MODEL` | the small tier | A model for it alone |
| `DRAWINGS_CHAT_TIMEOUT_S` | 120 | One call's timeout |
| `DRAWINGS_CHAT_MAX_ROWS` / `_MAX_EVENTS` | 150 / 30 | How much of the log and history goes in |
| `DRAWINGS_CHAT_MAX_INPUT_TOKENS` / `_MAX_OUTPUT_TOKENS` | 24000 / 1500 | The call's room |
| `DRAWINGS_CHAT_MAX_CALLS_PER_PROJECT_PER_DAY` | 200 | The day's budget on a project |

A project whose AI policy is "blocked" (Project Info, AI use) gets no assistant, with the reason shown.
Every call is a usage row (`ai_usage`, task `drawings_chat`) through the same budget and cache machinery as
the compliance assistance. The conversation is kept in the browser (local storage, per project and system),
never on the server.

## Tests

`backend/tests/test_drawings_chat.py`: off with AI off; none on a blocked project; the memory is the page's
records; the answer carries only the proposals the records allow, each as the page's own call, and nothing is
written; an applied proposal is the engineer's call; a system the project lacks is refused; a failing model is
reported; the memory is cut to fit with the quiet floors first.
