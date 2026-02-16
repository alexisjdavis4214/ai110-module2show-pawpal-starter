from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Any
import datetime

# type aliases
Time = datetime.time
TimeRange = Tuple[Time, Time]


@dataclass
class Task:
	task_id: str
	name: str
	category: str
	duration: int
	priority: int
	preferred_window: Optional[TimeRange] = None
	deadline_time: Optional[Time] = None
	frequency: str = "daily"
	notes: Optional[str] = None
	enabled: bool = True
	completed: bool = False
	due_date: Optional[datetime.date] = None

	def score(self, owner: "Owner", pet: "Pet") -> float:
		"""Compute task score for scheduling."""
		# base on priority
		score = float(self.priority) * 10.0
		# small urgency boost if there's a deadline
		if self.deadline_time:
			score += 5.0
		# penalize if owner preferences disallow this task
		if not owner.allows(self):
			score -= 100.0
		# pet-level recommendation
		if not pet.is_task_recommended(self):
			score -= 50.0
		return score

	def is_feasible(self, remaining_minutes: int) -> bool:
		"""Return True if task fits within remaining minutes and is enabled."""
		return self.enabled and (self.duration <= remaining_minutes)

	def mark_complete(self, owner: Optional["Owner"] = None, pet: Optional["Pet"] = None, create_next: bool = True) -> Optional["Task"]:
		"""Mark this task as completed and optionally create next occurrence for recurring tasks.

		If `frequency` is 'daily' or 'weekly' and `create_next` is True, a new Task instance
		is created with `due_date` set to today + 1 day (or +7 days for weekly) and appended
		to the given `pet` and `owner` when provided. Returns the new Task or None.
		"""
		self.completed = True
		if not create_next:
			return None
		if self.frequency not in ("daily", "weekly"):
			return None
		# compute next due date
		delta_days = 1 if self.frequency == "daily" else 7
		next_date = datetime.date.today() + datetime.timedelta(days=delta_days)
		# create a new task instance for the next occurrence
		new_id = f"{self.task_id}-next-{next_date.isoformat()}"
		new_task = Task(
			task_id=new_id,
			name=self.name,
			category=self.category,
			duration=self.duration,
			priority=self.priority,
			preferred_window=self.preferred_window,
			deadline_time=self.deadline_time,
			frequency=self.frequency,
			notes=self.notes,
			enabled=self.enabled,
			completed=False,
			due_date=next_date,
		)
		# append to pet and owner if provided
		if pet is not None:
			pet.add_task(new_task)
		if owner is not None:
			owner.tasks.append(new_task)
		return new_task

	def requires_exact_time(self) -> bool:
		"""Return True when the task requires an exact time (has a deadline)."""
		return bool(self.deadline_time)

	def expand_occurrences(self, base_date: Optional[datetime.date] = None) -> List[TimeRange]:
		"""Return candidate time ranges for this task based on frequency and preferences.

		This is an MVP helper used by the planner to translate a task's abstract
		`frequency` or `preferred_window` into concrete scheduling slots. Behavior:
		- If `preferred_window` is set, that single window is returned.
		- If `frequency` is of the form '<n>x-day' (e.g. '2x-day'), returns `n`
		  evenly spaced slots between 07:00 and 21:00 on `base_date` (or today).

		Args:
			base_date: Optional date used to compute concrete datetimes for slots.

		Returns:
			List[TimeRange]: a list of (start_time, end_time) candidate slots.
		"""
		# MVP: return preferred_window if present
		if self.preferred_window:
			return [self.preferred_window]
		# simple parsing for '2x-day' => split owner's day into two generic slots
		if self.frequency.endswith("x-day"):
			n = int(self.frequency.split("x")[0]) if self.frequency.split("x")[0].isdigit() else 1
			# return n evenly spaced generic slots between 07:00-21:00
			slots: List[TimeRange] = []
			start_dt = datetime.datetime.combine(base_date or datetime.date.today(), datetime.time(7, 0))
			end_dt = datetime.datetime.combine(base_date or datetime.date.today(), datetime.time(21, 0))
			delta = (end_dt - start_dt) / max(1, n)
			for i in range(n):
				s = (start_dt + delta * i).time()
				e = (start_dt + delta * (i + 1)).time()
				slots.append((s, e))
			return slots
		return []


@dataclass
class ScheduledTask:
	task: Task
	start: Time
	end: Time
	note: Optional[str] = None


@dataclass
class Owner:
	owner_id: str
	name: str
	daily_time_available: int  # minutes
	preferred_windows: List[TimeRange] = field(default_factory=list)
	preferences: Dict[str, Any] = field(default_factory=dict)
	tasks: List[Task] = field(default_factory=list)

	def available_minutes(self) -> int:
		"""Return the owner's configured daily available minutes."""
		return int(self.daily_time_available)

	def allows(self, task: Task) -> bool:
		"""Check owner preferences to allow or block a task."""
		p = self.preferences
		# no grooming on weekdays
		if p.get("no_grooming_weekdays") and task.category == "grooming":
			if datetime.date.today().weekday() < 5:
				return False
		# avoid late walks
		if p.get("avoid_late_walks") and task.category == "walk":
			# if there's a preferred_window or deadline, ensure it ends before 21:30
			t_end = None
			if task.preferred_window:
				t_end = task.preferred_window[1]
			elif task.deadline_time:
				t_end = task.deadline_time
			if t_end and (t_end.hour > 21 or (t_end.hour == 21 and t_end.minute > 30)):
				return False
		return True

	def window_options(self, task: Task) -> List[TimeRange]:
		"""Return time range options that satisfy both owner and task preferences."""
		# Return intersections between owner preferred windows and task preference
		if task.preferred_window is None:
			return list(self.preferred_windows)
		opts: List[TimeRange] = []
		for ow in self.preferred_windows:
			# compute overlap
			start = max(ow[0], task.preferred_window[0])
			end = min(ow[1], task.preferred_window[1])
			if (start < end):
				opts.append((start, end))
		return opts

	def update_time_available(self, minutes: int) -> None:
		"""Set owner's available minutes to the provided value."""
		self.daily_time_available = int(minutes)


@dataclass
class Pet:
	pet_id: str
	name: str
	species: str
	age_years: float
	activity_level: str
	health_notes: Optional[str] = None
	owner: Optional[Owner] = None
	tasks: List[Task] = field(default_factory=list)

	def add_task(self, task: Task) -> None:
		"""Add a task to this pet's task list."""
		self.tasks.append(task)

	def adjust_duration(self, task: Task) -> int:
		"""Return adjusted duration for a task based on pet age and activity."""
		factor = 1.0
		if self.age_years >= 8:
			factor *= 0.7
		if self.activity_level == "low":
			factor *= 0.8
		elif self.activity_level == "high":
			factor *= 1.1
		adjusted = max(1, int(task.duration * factor))
		return adjusted

	def is_task_recommended(self, task: Task) -> bool:
		"""Return whether this task is appropriate for this pet."""
		# Basic species/category rules
		if task.category == "walk":
			return self.species.lower() == "dog"
		# meds/grooming/feeding/enrichment allowed for all species by default
		return True

	def default_tasks(self) -> List[Task]:
		"""Return a small list of default tasks for this pet."""
		defaults: List[Task] = []
		# feed is default for all pets
		defaults.append(Task(task_id=f"{self.pet_id}-feed", name="Feed", category="feed", duration=10, priority=4))
		if self.species.lower() == "dog":
			defaults.append(Task(task_id=f"{self.pet_id}-walk", name="Walk", category="walk", duration=30, priority=5, preferred_window=(datetime.time(7,0), datetime.time(9,0))))
		return defaults


@dataclass
class Scheduler:
	strategy: str = "greedy"
	weights: Dict[str, float] = field(default_factory=lambda: {"priority": 1.0, "deadline": 1.5, "preference_fit": 0.5})
	explain: bool = False
	# simple in-memory score cache for a single planning run (keyed by task_id)
	score_cache: Dict[str, float] = field(default_factory=dict)

	def get_score_cached(self, task: Task, owner: Owner, pet: Pet) -> float:
		"""Return a cached numeric score for `task`, computing and caching if needed.

		The planner uses this method to avoid repeatedly calling potentially
		expensive scoring logic during a single planning run. The cache is keyed by
		`task.task_id` and is stored on the `Scheduler` instance for the duration
		of the planning operation.

		Args:
			task: Task to score.
			owner: Owner used to evaluate preferences/constraints.
			pet: Pet used to evaluate recommendations and adjustments.

		Returns:
			float: computed score (higher => more important to schedule).
		"""
		key = task.task_id
		if key in self.score_cache:
			return self.score_cache[key]
		s = task.score(owner, pet)
		self.score_cache[key] = s
		return s


	def rank_tasks(self, owner: Owner, pet: Pet, tasks: List[Task]) -> List[Task]:
		"""Rank the provided `tasks` by descending score using a per-run cache.

		Scores are retrieved via `get_score_cached`. This method returns a new list
		of tasks sorted from highest to lowest priority according to the computed
		score. It does not modify the input list.

		Args:
			owner: Owner context for scoring.
			pet: Pet context for scoring.
			tasks: List of tasks to rank.

		Returns:
			List[Task]: tasks sorted by descending score.
		"""
		# compute and sort by cached score (desc)
		scored = [(self.get_score_cached(t, owner, pet), t) for t in tasks]
		scored.sort(key=lambda x: x[0], reverse=True)
		return [t for _, t in scored]

	def sort_by_time(self, tasks: List[Task]) -> List[Task]:
		"""Return tasks sorted by a representative time used for time-based views.

		Representative time is chosen in this priority order: `deadline_time`,
		`preferred_window` start, otherwise midnight. This helper is intended for
		rendering or simple time-based ordering and does not perform placement or
		check availability.

		Args:
			tasks: tasks to sort.

		Returns:
			List[Task]: tasks ordered earliest-to-latest by representative time.
		"""
		def task_time(t: Task) -> Time:
			if t.deadline_time:
				return t.deadline_time
			if t.preferred_window:
				return t.preferred_window[0]
			return datetime.time(0, 0)

		return sorted(tasks, key=lambda t: task_time(t))

	def filter_tasks(self, tasks: List[Task], completed: Optional[bool] = None) -> List[Task]:
		"""Filter `tasks` by completion status.

		If `completed` is None, returns a shallow copy of the input list. Passing
	ture/False returns only tasks that match the completion predicate.

		Args:
			tasks: list of tasks to filter.
			completed: Optional bool indicating desired completion state.

		Returns:
			List[Task]: filtered list.
		"""
		if completed is None:
			return list(tasks)
		return [t for t in tasks if bool(t.completed) is bool(completed)]

	def filter_tasks_by_pet(self, pets: Dict[str, "Pet"], pet_name: Optional[str] = None, completed: Optional[bool] = None) -> List[Task]:
		"""Collect tasks from the provided `pets` mapping and optionally filter.

		If `pet_name` is provided the function returns tasks for that pet only;
		otherwise tasks from all pets in the mapping are aggregated.

		Args:
			pets: mapping of pet names to `Pet` objects.
			pet_name: optional key name to select a single pet.
			completed: Optional completion filter passed to `filter_tasks`.

		Returns:
			List[Task]: collected (and filtered) tasks.
		"""
		collected: List[Task] = []
		if pet_name:
			pet = pets.get(pet_name)
			if not pet:
				return []
			collected = list(pet.tasks)
		else:
			for pet in pets.values():
				collected.extend(pet.tasks)
		return self.filter_tasks(collected, completed=completed)

	def detect_conflicts(self, scheduled: List[Tuple[str, ScheduledTask]]) -> List[str]:
		"""Detect overlapping scheduled tasks and return human-readable warnings.

		This performs a simple pairwise comparison of scheduled intervals (assumed
		to be on the same day). Overlap is determined by the standard interval
		intersection test (start_a < end_b and start_b < end_a).

		Limitations:
		- Assumes all `ScheduledTask` times are on the same calendar day (today).
		- Does not attempt to resolve conflicts; only reports them.

		Args:
			scheduled: list of tuples (pet_name, ScheduledTask).

		Returns:
			List[str]: warning messages describing each detected overlap.
		"""
		warnings: List[str] = []
		# convert to events with datetimes for today
		events = []
		today = datetime.date.today()
		for pet_name, s in scheduled:
			start_dt = datetime.datetime.combine(today, s.start)
			end_dt = datetime.datetime.combine(today, s.end)
			events.append((pet_name, s.task, start_dt, end_dt))

		# compare pairs
		n = len(events)
		for i in range(n):
			pet_i, task_i, si, ei = events[i]
			for j in range(i + 1, n):
				pet_j, task_j, sj, ej = events[j]
				# overlap if start < other_end and other_start < end
				if (si < ej) and (sj < ei):
					msg = f"Conflict: {pet_i}:{task_i.name} ({si.time().strftime('%H:%M')}-{ei.time().strftime('%H:%M')}) overlaps {pet_j}:{task_j.name} ({sj.time().strftime('%H:%M')}-{ej.time().strftime('%H:%M')})"
					warnings.append(msg)
		return warnings

	def generate_plan(self, owner: Owner, pet: Pet, tasks: List[Task]) -> Dict[str, Any]:
		"""Generate a greedy schedule for `tasks` given `owner` and `pet` context.

		This is an intentionally lightweight, first-fit scheduler designed for
		interactive UIs and small task sets. It ranks tasks by score, then iterates
		over them selecting the highest-scoring feasible task that fits in the
		owner's remaining time and simple owner/pet constraints. For each selected
		task a `ScheduledTask` with a concrete start/end time is created using the
		first matching owner time window or a fallback time.

		Behavior notes:
		- The scheduler is greedy and does not perform global backtracking or
		  constraint solving. It's fast but may produce suboptimal placements.
		- Selected tasks reduce the local `remainder` time but do not persistently
		  modify the `Owner` object (caller may choose to persist changes).

		Args:
			owner: Owner providing available minutes and preferred windows.
			pet: Pet used for duration adjustments and recommendation checks.
			tasks: Candidate tasks to schedule.

		Returns:
			Dict[str, Any]: keys:
				- 'scheduled': List[ScheduledTask]
				- 'skipped': List[Tuple[Task, str]] (task and reason)
				- 'total_minutes': int minutes scheduled
				- 'explanation': List[str] (when `self.explain` is True)
		"""
		# simple greedy planning using durations and preferred windows
		plan_selected: List[ScheduledTask] = []
		skipped: List[Tuple[Task, str]] = []
		remainder = owner.available_minutes()
		ranked = self.rank_tasks(owner, pet, tasks)
		for task in ranked:
			if not task.enabled:
				skipped.append((task, "disabled"))
				continue
			if not owner.allows(task):
				skipped.append((task, "owner preference disallows"))
				continue
			if not pet.is_task_recommended(task):
				skipped.append((task, "not recommended for pet"))
				continue
			t_dur = pet.adjust_duration(task)
			if not task.is_feasible(remainder):
				skipped.append((task, "not enough time remaining"))
				continue
			# pick a window
			options = owner.window_options(task)
			start_time: Optional[Time] = None
			end_time: Optional[Time] = None
			if options:
				w = options[0]
				start_time = w[0]
				# compute end by adding minutes to start
				base_dt = datetime.datetime.combine(datetime.date.today(), start_time)
				end_dt = base_dt + datetime.timedelta(minutes=t_dur)
				end_time = end_dt.time()
			else:
				# fallback: schedule at 00:00
				base_dt = datetime.datetime.combine(datetime.date.today(), datetime.time(0,0))
				end_dt = base_dt + datetime.timedelta(minutes=t_dur)
				start_time = base_dt.time()
				end_time = end_dt.time()
			plan_selected.append(ScheduledTask(task=task, start=start_time, end=end_time))
			remainder -= t_dur
			# update owner available minutes (non-persistent here)
			# continue greedy
		# build explanations
		explanations = self.build_explanations([s.task for s in plan_selected], skipped) if self.explain else []
		return {"scheduled": plan_selected, "skipped": skipped, "total_minutes": owner.available_minutes() - remainder, "explanation": explanations}



	def select_tasks(self, owner: Owner, pet: Pet, ranked: List[Task]) -> Tuple[List[Task], List[Tuple[Task, str]]]:
		"""Select a subset of `ranked` tasks that fit within the owner's time.

		This convenience method performs feasibility checks similar to
		`generate_plan` but returns the selected `Task` objects rather than
		concrete `ScheduledTask` placements. It is useful for previews or when
		time-only filtering is required.

		Args:
			owner: Owner providing available minutes.
			pet: Pet providing duration adjustments and recommendations.
			ranked: tasks sorted by preference/score.

		Returns:
			Tuple[List[Task], List[Tuple[Task, str]]]: selected tasks and skipped
			(plus reasons).
		"""
		# Convenience wrapper for generating selected task list without times
		selected: List[Task] = []
		skipped: List[Tuple[Task, str]] = []
		remainder = owner.available_minutes()
		for task in ranked:
			if not task.enabled:
				skipped.append((task, "disabled"))
				continue
			if not owner.allows(task):
				skipped.append((task, "owner preference disallows"))
				continue
			if not pet.is_task_recommended(task):
				skipped.append((task, "not recommended for pet"))
				continue
			t_dur = pet.adjust_duration(task)
			if t_dur > remainder:
				skipped.append((task, "not enough time"))
				continue
			selected.append(task)
			remainder -= t_dur
		return selected, skipped

	def build_explanations(self, selected: List[Task], skipped: List[Tuple[Task, str]]) -> List[str]:
		"""Create human-readable explanation lines for a planning run.

		Used to provide debug or UI-facing explanations when `self.explain` is
		enabled. The output includes counts and brief itemized reasons for
		skipped tasks.

		Args:
			selected: list of selected Task objects.
			skipped: list of (Task, reason) tuples describing why tasks were
			skipped.

		Returns:
			List[str]: explanation lines suitable for display or logging.
		"""
		lines: List[str] = []
		lines.append(f"Selected {len(selected)} tasks")
		for t in selected:
			lines.append(f"- {t.name} ({t.task_id})")
		if skipped:
			lines.append(f"Skipped {len(skipped)} tasks:")
			for t, reason in skipped:
				lines.append(f"- {t.name} ({t.task_id}): {reason}")
		return lines


