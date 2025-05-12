from django.test import TestCase
from ..models import Task

class TaskModelTestCase(TestCase):
    def setUp(self):
        self.task1 = Task.objects.create(name='Task 1')
        self.task2 = Task.objects.create(name='Task 2')

    def test_str_representation(self):
        self.assertEqual(str(self.task1), 'Task 1')

    def test_circular_dependency(self):
        with self.assertRaises(Exception) as context:
            Task.objects.create(name='Circular', dependencies=[self.task1])
            self.task1.dependencies.add(self.task2)
            self.task2.dependencies.add(self.task1)
        self.assertTrue('Circular dependency detected' in str(context.exception))

    def test_invalid_status_update(self):
        with self.assertRaises(Exception) as context:
            self.task1.status = 'completed'
            self.task1.save()
        self.assertTrue('Invalid status transition' in str(context.exception))