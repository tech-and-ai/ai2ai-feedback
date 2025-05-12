import unittest
from unittest.mock import patch
from src.task_scheduler import TaskScheduler

class TestTaskScheduler(unittest.TestCase):

    @patch('src.task_scheduler.pika.BlockingConnection')
    def test_schedule_task(self, mock_connection):
        mock_channel = mock_connection.return_value.channel.return_value
        scheduler = TaskScheduler()
        task_definition = {'command': 'echo test'}
        task_id = scheduler.schedule_task(task_definition)

        self.assertIsNotNone(task_id)
        mock_channel.basic_publish.assert_called_once()

if __name__ == '__main__':
    unittest.main()
