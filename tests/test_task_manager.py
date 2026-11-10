import unittest

from sample_app.task_manager import TaskManager


class TaskManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = TaskManager()

    def test_add_task_trims_title(self):
        task = self.manager.add_task(1, "  Write tests  ")
        self.assertEqual(task.title, "Write tests")
        self.assertFalse(task.completed)

    def test_add_task_rejects_zero_id(self):
        with self.assertRaises(ValueError):
            self.manager.add_task(0, "Task")

    def test_add_task_rejects_negative_id(self):
        with self.assertRaises(ValueError):
            self.manager.add_task(-1, "Task")

    def test_add_task_rejects_boolean_id(self):
        with self.assertRaises(ValueError):
            self.manager.add_task(True, "Task")

    def test_add_task_rejects_blank_title(self):
        for title in ("", "   ", "\t\n"):
            with self.subTest(title=repr(title)):
                with self.assertRaises(ValueError):
                    self.manager.add_task(1, title)

    def test_add_task_rejects_non_string_title(self):
        with self.assertRaises(ValueError):
            self.manager.add_task(1, None)

    def test_duplicate_id_is_rejected(self):
        self.manager.add_task(1, "First")
        with self.assertRaises(ValueError):
            self.manager.add_task(1, "Second")

    def test_complete_task_changes_state(self):
        self.manager.add_task(7, "Review report")
        task = self.manager.complete_task(7)
        self.assertTrue(task.completed)
        self.assertTrue(self.manager.get_task(7).completed)

    def test_get_missing_task_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.manager.get_task(404)

    def test_complete_missing_task_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.manager.complete_task(404)

    def test_list_tasks_returns_all_tasks_in_insertion_order(self):
        self.manager.add_task(2, "Second")
        self.manager.add_task(1, "First")
        self.assertEqual([task.task_id for task in self.manager.list_tasks()], [2, 1])


if __name__ == "__main__":
    unittest.main()
