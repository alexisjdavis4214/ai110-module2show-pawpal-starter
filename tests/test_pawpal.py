import os
import sys
import unittest
import datetime

# ensure project root is on path for imports when running tests directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pawpal_system import Task, Pet, Owner, Scheduler, ScheduledTask


class TestPawPal(unittest.TestCase):

    def test_task_mark_complete(self):
        t = Task(task_id="tt1", name="Test", category="feed", duration=5, priority=1)
        self.assertFalse(t.completed)
        t.mark_complete(create_next=False)
        self.assertTrue(t.completed)

    def test_pet_add_task_increases_count(self):
        p = Pet(pet_id="p100", name="Buddy", species="dog", age_years=2.0, activity_level="med")
        initial = len(p.tasks)
        t = Task(task_id="tt2", name="Walk", category="walk", duration=15, priority=3)
        p.add_task(t)
        self.assertEqual(len(p.tasks), initial + 1)

    def test_sort_by_time_orders_tasks_chronologically(self):
        # midnight (no time) should come first, then preferred window start, then deadline
        t_mid = Task(task_id="t_mid", name="Mid", category="feed", duration=5, priority=1)
        t_pref = Task(task_id="t_pref", name="Pref", category="walk", duration=10, priority=2, preferred_window=(datetime.time(8,0), datetime.time(9,0)))
        t_dead = Task(task_id="t_dead", name="Dead", category="feed", duration=5, priority=3, deadline_time=datetime.time(9,0))
        scheduler = Scheduler()
        ordered = scheduler.sort_by_time([t_dead, t_pref, t_mid])
        self.assertEqual([t.task_id for t in ordered], ["t_mid", "t_pref", "t_dead"])

    def test_recurrence_creates_next_daily_task(self):
        owner = Owner(owner_id="o1", name="Alex", daily_time_available=60)
        pet = Pet(pet_id="p1", name="Buddy", species="dog", age_years=2.0, activity_level="med", owner=owner)
        task = Task(task_id="daily1", name="DailyFeed", category="feed", duration=10, priority=4, frequency="daily")
        pet.add_task(task)
        owner.tasks.append(task)

        new_task = task.mark_complete(owner=owner, pet=pet, create_next=True)
        self.assertTrue(task.completed)
        self.assertIsNotNone(new_task)
        expected_date = datetime.date.today() + datetime.timedelta(days=1)
        self.assertEqual(new_task.due_date, expected_date)
        self.assertIn(new_task, pet.tasks)
        self.assertIn(new_task, owner.tasks)

    def test_detect_conflicts_flags_overlaps(self):
        scheduler = Scheduler()
        t1 = Task(task_id="c1", name="Brush", category="grooming", duration=30, priority=1)
        t2 = Task(task_id="c2", name="Walk", category="walk", duration=60, priority=2)
        s1 = ScheduledTask(task=t1, start=datetime.time(9,0), end=datetime.time(10,0))
        s2 = ScheduledTask(task=t2, start=datetime.time(9,30), end=datetime.time(10,30))
        warnings = scheduler.detect_conflicts([("petA", s1), ("petB", s2)])
        self.assertTrue(len(warnings) >= 1)
        self.assertIn("overlaps", warnings[0])


if __name__ == "__main__":
    unittest.main()
