# PawPal+ Project Reflection

## 1. System Design

- core actions: enter owner/pet info, add/edit tasks, see suggested plan

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Owner: represents a human user with available minutes, preferred time windows, and preference rules; exposes methods to report available minutes, check whether a task is allowed, compute valid windows, and update remaining time.
Pet: models an animal with species/age/activity and health notes; provides per-pet adjustments (e.g., adjust task duration), safety/fit checks, and optional defaults.
Task: holds scheduling-friendly metadata (id, category, duration, priority, preferred window, deadline, frequency, enabled, notes) and small decision APIs (score, feasibility, requires_exact_time).
Scheduler: encapsulates a strategy and weighting configuration; ranks tasks, selects a feasible set given owner/pet constraints, builds explanations, and outputs a plan (scheduled, skipped, total minutes, explanation).
Relationships: Owner → Pet (owns), Pet → Task (has/defaults); Scheduler depends on Owner, Pet, and Task to generate plans.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Added Owner.tasks and Pet.owner to make ownership explicit so tasks can be queried/filtered per-owner and per-pet constraints (simplifies multi-pet/multi-owner flows).

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers owner available time, task priority, task deadlines, owner preferences (e.g., no late walks), and pet suitability. I prioritized time and priority first because those are the core constraints a busy owner faces; preferences and pet fit came second since they refine the plan but don't block it.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
 
- Greedy-first scheduling vs. global optimality: the scheduler uses a simple greedy
	ranking and first-fit placement strategy and performs lightweight conflict detection
	afterwards instead of running an expensive global optimizer that guarantees no
	overlaps. This keeps the implementation simple and fast for the MVP, but it may
	produce suboptimal schedules or require manual conflict resolution for edge cases.
	For a consumer app with short planning horizons (a single day) this tradeoff
	favors responsiveness and easier reasoning about scheduler behavior.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI for initial UML brainstorming, generating test cases, and drafting the README features section. The most helpful prompts were specific ones that asked for code examples or described exact requirements; vague questions about "how to schedule" produced less actionable responses.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

AI suggested a complex backtracking scheduler, but I rejected it because it was overkill for a single-day plan and harder to debug. I tested my simpler greedy approach against manual test cases and confirmed it handled the core scenarios correctly.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested sorting correctness, recurrence task creation, conflict detection, and owner preference filtering. These tests were critical because they verify the core scheduling decisions—if these fail, the whole planner breaks.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm fairly confident (4/5) in the core behaviors, but I'd test multi-pet scheduling edge cases, very long task durations, and timezone-aware recurring tasks if I had more time.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with the clean separation of concerns—Task, Owner, Pet, and Scheduler are loosely coupled, making the code easy to test and extend.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I'd add persistent storage (a database), richer recurrence rules (e.g., every other day), and a smarter conflict resolver that can swap or reschedule tasks instead of just warning.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

I learned that simple, explainable algorithms are often better than complex ones for MVP products—the scheduler is faster to debug and easier for users to understand and predict.
