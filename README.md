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

## Features

**PawPal+** implements the following core scheduling and planning features:

- **Priority-based Task Ranking:** Tasks are scored and ranked by priority, deadline urgency, owner preferences, and pet suitability to determine scheduling order.

- **Greedy First-Fit Scheduler:** A lightweight scheduling algorithm that greedily places the highest-scoring feasible tasks into the owner's available time, filling the day incrementally without backtracking.

- **Per-Run Score Caching:** Task scores are computed once and cached during a single planning session to optimize performance for interactive UI updates.

- **Pet-Aware Duration Adjustment:** Task durations are dynamically adjusted based on pet attributes (age, activity level) using configurable multipliers, ensuring realistic time estimates for different pet profiles.

- **Task Recommendation Engine:** Species-specific rules filter inappropriate tasks (e.g., preventing walks for non-dogs) and alert users to recommendations that may not be suitable for their pet.

- **Owner Preference Constraints:** Owner preferences (e.g., "no grooming on weekdays," "avoid late walks") are enforced during scheduling to respect lifestyle constraints.

- **Time Window & Deadline Handling:** Tasks support preferred scheduling windows and deadline times, with the scheduler selecting compatible time slots from the owner's preferred availability.

- **Recurring Task Management (MVP):** Completing a recurring task (daily or weekly frequency) automatically creates the next occurrence with an updated due date and adds it to both pet and owner task lists.

- **Conflict Detection:** After scheduling, the system detects and reports overlapping time intervals across all pets, alerting users to scheduling collisions without attempting automatic resolution.

- **Time-Based Sorting & Filtering:** Helper methods provide convenient sorting by representative time (deadline, preferred window start, or midnight) and filtering by completion status for UI display and task management.

## Demo

![Screenshot 1](images/Screenshot%202026-02-15%20at%2011.36.19%20PM.png)

![Screenshot 2](images/Screenshot%202026-02-15%20at%2011.36.39%20PM.png)

![Screenshot 3](images/Screenshot%202026-02-15%20at%2011.36.55%20PM.png)

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

## Testing PawPal+

Run the automated test suite:

```bash
python -m pytest
```

What the tests cover:

- **Sorting Correctness:** tasks are ordered by representative time (deadline, preferred window start, fallback midnight).
- **Recurrence Logic:** completing a recurring `daily` or `weekly` task creates the next occurrence (`due_date`) and appends it to the pet and owner.
- **Conflict Detection:** overlapping scheduled intervals are detected and reported as warnings.
- **Owner Preferences & Feasibility:** owner `allows()` and `Pet.adjust_duration()` affect selection and scheduling decisions.

Confidence Level: ★★★★☆ (4/5) — tests pass locally for the core behaviors covered; broader integration and UI tests would increase confidence.
