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

	# Add tasks out of chronological order
	late_walk = Task(task_id="t4", name="Evening Walk", category="walk", duration=25, priority=4, preferred_window=(T(20,0), T(21,0)))
	quick_play = Task(task_id="t5", name="Playtime", category="enrichment", duration=15, priority=2, preferred_window=(T(12,0), T(12,30)))

	# conflict tasks (same time for dog and cat)
	conflict_dog = Task(task_id="t6", name="Vet Call", category="meds", duration=15, priority=5, preferred_window=(T(8,0), T(8,30)))
	conflict_cat = Task(task_id="t7", name="Mail Pickup", category="errand", duration=15, priority=3, preferred_window=(T(8,0), T(8,30)))

	# assign tasks to pets
	owner.tasks.extend([walk, feed_dog, cat_meds, late_walk, quick_play])
	dog.add_task(walk)
	dog.add_task(late_walk)
	dog.add_task(feed_dog)
	cat.add_task(cat_meds)
	cat.add_task(quick_play)

	# add conflicts to both pets
	dog.add_task(conflict_dog)
	cat.add_task(conflict_cat)

	# mark one complete out of order
	quick_play.mark_complete()

	scheduler = Scheduler(explain=True)

	# Demonstrate filtering and sorting
	pets = {dog.name: dog, cat.name: cat}

	print("All dog tasks (unsorted):", [t.name for t in dog.tasks])
	sorted_dog = scheduler.sort_by_time(dog.tasks)
	print("Dog tasks (sorted by time):", [t.name for t in sorted_dog])

	# filter completed tasks across all pets
	completed_tasks = scheduler.filter_tasks_by_pet(pets, completed=True)
	print("Completed tasks:", [t.name for t in completed_tasks])

	# generate per-pet plan to show scheduling still works
	plan_dog = scheduler.generate_plan(owner, dog, dog.tasks)
	plan_cat = scheduler.generate_plan(owner, cat, cat.tasks)

	# detect conflicts across pets
	combined = [(dog.name, s) for s in plan_dog.get("scheduled", [])] + [(cat.name, s) for s in plan_cat.get("scheduled", [])]
	warnings = scheduler.detect_conflicts(combined)
	if warnings:
		print("Warnings:")
		for w in warnings:
			print("-", w)

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

