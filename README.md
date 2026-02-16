# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

- **Greedy, explainable planner:** a lightweight first-fit scheduler ranks tasks by a computed score (priority, deadline, owner/pet fit) and fills the owner's available minutes.
- **Per-run score cache:** scores are cached during a planning run to avoid repeated computation and keep the planner responsive for interactive UIs.
- **Pet-aware adjustments:** task durations are adjusted by pet attributes (age, activity level) and basic recommendation rules filter inappropriate tasks (e.g., walks for non-dogs).
- **Recurrence support (MVP):** completing tasks can auto-create the next occurrence for common frequencies (daily, weekly), represented by a `due_date` field.
- **Conflict detection:** after placement the scheduler emits overlap warnings when scheduled intervals collide across pets; this keeps the planner simple while surfacing issues to the user.
- **Sorting & filtering helpers:** utility methods provide convenient time-based ordering and completion filtering for UI views and previews.

These features prioritize clarity and speed for small-to-medium task sets; future work can add global constraint solving and richer recurrence expansion.
