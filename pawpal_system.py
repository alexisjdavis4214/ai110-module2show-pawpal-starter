from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Any


@dataclass
class Task:
	task_id: str
	name: str
	category: str
	duration: int
	priority: int
	preferred_window: Optional[Tuple[str, str]] = None
	deadline_time: Optional[str] = None
	frequency: str = "daily"
	notes: Optional[str] = None
	enabled: bool = True

	def score(self, owner: "Owner", pet: "Pet") -> float:
		"""Compute a score for scheduling priority/urgency/preference fit."""
		raise NotImplementedError

	def is_feasible(self, remaining_minutes: int) -> bool:
		raise NotImplementedError

	def requires_exact_time(self) -> bool:
		raise NotImplementedError


@dataclass
class Owner:
	owner_id: str
	name: str
	daily_time_available: int  # minutes
	preferred_windows: List[Tuple[str, str]] = field(default_factory=list)
	preferences: Dict[str, Any] = field(default_factory=dict)

	def available_minutes(self) -> int:
		raise NotImplementedError

	def allows(self, task: Task) -> bool:
		raise NotImplementedError

	def window_options(self, task: Task) -> List[Tuple[str, str]]:
		raise NotImplementedError

	def update_time_available(self, minutes: int) -> None:
		raise NotImplementedError


@dataclass
class Pet:
	pet_id: str
	name: str
	species: str
	age_years: float
	activity_level: str
	health_notes: Optional[str] = None

	def adjust_duration(self, task: Task) -> int:
		raise NotImplementedError

	def is_task_recommended(self, task: Task) -> bool:
		raise NotImplementedError

	def default_tasks(self) -> List[Task]:
		raise NotImplementedError


@dataclass
class Scheduler:
	strategy: str = "greedy"
	weights: Dict[str, float] = field(default_factory=lambda: {"priority": 1.0, "deadline": 1.5, "preference_fit": 0.5})
	explain: bool = False

	def generate_plan(self, owner: Owner, pet: Pet, tasks: List[Task]) -> Dict[str, Any]:
		"""Return a plan dict with scheduled/skipped/explanation/total_minutes."""
		raise NotImplementedError

	def rank_tasks(self, owner: Owner, pet: Pet, tasks: List[Task]) -> List[Task]:
		raise NotImplementedError

	def select_tasks(self, owner: Owner, pet: Pet, ranked: List[Task]) -> Tuple[List[Task], List[Tuple[Task, str]]]:
		raise NotImplementedError

	def build_explanations(self, selected: List[Task], skipped: List[Tuple[Task, str]]) -> List[str]:
		raise NotImplementedError

