import os
import sys
import unittest

# ensure project root is on path for imports when running tests directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pawpal_system import Task, Pet

class TestPawPal(unittest.TestCase):

    def test_task_mark_complete(self):
        t = Task(task_id="tt1", name="Test", category="feed", duration=5, priority=1)
        self.assertFalse(t.completed)
        t.mark_complete()
        self.assertTrue(t.completed)

    def test_pet_add_task_increases_count(self):
        p = Pet(pet_id="p100", name="Buddy", species="dog", age_years=2.0, activity_level="med")
        initial = len(p.tasks)
        t = Task(task_id="tt2", name="Walk", category="walk", duration=15, priority=3)
        p.add_task(t)
        self.assertEqual(len(p.tasks), initial + 1)

if __name__ == "__main__":
    unittest.main()
