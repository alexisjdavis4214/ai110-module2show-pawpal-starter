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

	def mark_complete(self) -> None:
		"""Mark this task as completed."""
		self.completed = True

	def requires_exact_time(self) -> bool:
		"""Return True when the task requires an exact time (has a deadline)."""
		return bool(self.deadline_time)

	def expand_occurrences(self, base_date: Optional[datetime.date] = None) -> List[TimeRange]:
		"""Expand frequency into concrete time ranges for planning (sketch)."""
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
		"""Return a cached score for a task or compute and cache it."""
		key = task.task_id
		if key in self.score_cache:
			return self.score_cache[key]
		s = task.score(owner, pet)
		self.score_cache[key] = s
		return s


	def rank_tasks(self, owner: Owner, pet: Pet, tasks: List[Task]) -> List[Task]:
		"""Rank tasks by cached score (descending)."""
		# compute and sort by cached score (desc)
		scored = [(self.get_score_cached(t, owner, pet), t) for t in tasks]
		scored.sort(key=lambda x: x[0], reverse=True)
		return [t for _, t in scored]

	def generate_plan(self, owner: Owner, pet: Pet, tasks: List[Task]) -> Dict[str, Any]:
		"""Generate a greedy schedule plan for the given owner, pet, and tasks."""
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
		"""Select feasible tasks from a ranked list given owner's available time."""
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
		"""Return human-readable explanations for selected and skipped tasks."""
		lines: List[str] = []
		lines.append(f"Selected {len(selected)} tasks")
		for t in selected:
			lines.append(f"- {t.name} ({t.task_id})")
		if skipped:
			lines.append(f"Skipped {len(skipped)} tasks:")
			for t, reason in skipped:
				lines.append(f"- {t.name} ({t.task_id}): {reason}")
		return lines


