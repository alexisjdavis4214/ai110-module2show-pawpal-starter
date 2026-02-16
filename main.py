from pawpal_system import Owner, Pet, Task, Scheduler
import datetime


def main() -> None:
	T = datetime.time

	owner = Owner(
		owner_id="o1",
		name="Alex",
		daily_time_available=120,
		preferred_windows=[(T(7, 0), T(9, 0)), (T(17, 0), T(21, 0))],
		preferences={"avoid_late_walks": True, "no_grooming_weekdays": True},
	)

	dog = Pet(pet_id="p1", name="Rex", species="dog", age_years=5.0, activity_level="high", owner=owner)
	cat = Pet(pet_id="p2", name="Mittens", species="cat", age_years=3.0, activity_level="low", owner=owner)

	# Tasks for dog
	walk = Task(
		task_id="t1",
		name="Morning Walk",
		category="walk",
		duration=30,
		priority=5,
		preferred_window=(T(7, 30), T(8, 30)),
	)

	feed_dog = Task(
		task_id="t2",
		name="Feed Dog",
		category="feed",
		duration=10,
		priority=4,
		preferred_window=(T(7, 0), T(9, 0)),
	)

	# Tasks for cat
	cat_meds = Task(
		task_id="t3",
		name="Cat Meds",
		category="meds",
		duration=5,
		priority=5,
		deadline_time=T(9, 0),
	)

	# Assign tasks to owner (and implicitly available to pets)
	owner.tasks.extend([walk, feed_dog, cat_meds])

	scheduler = Scheduler(explain=True)

	# Generate per-pet plans
	plan_dog = scheduler.generate_plan(owner, dog, [walk, feed_dog])
	plan_cat = scheduler.generate_plan(owner, cat, [cat_meds])

	print("Today's Schedule:\n")

	def print_plan(plan, pet):
		scheduled = plan.get("scheduled", [])
		skipped = plan.get("skipped", [])
		if scheduled:
			for s in scheduled:
				start = s.start.strftime("%H:%M")
				end = s.end.strftime("%H:%M")
				print(f"- {pet.name}: {s.task.name} ({s.task.category}) {start} - {end}")
		if skipped:
			for t, reason in skipped:
				print(f"- {pet.name}: SKIPPED {t.name} ({reason})")

	print_plan(plan_dog, dog)
	print_plan(plan_cat, cat)


if __name__ == "__main__":
	main()

