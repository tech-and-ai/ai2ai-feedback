import unittest
from unittest.mock import patch, MagicMock
from src.worker_node import WorkerNode
import json

class TestWorkerNode(unittest.TestCase):

    @patch('src.worker_node.pika.BlockingConnection')
    @patch('src.worker_node.subprocess.run')
    def test_process_task(self, mock_subprocess_run, mock_connection):
        mock_channel = mock_connection.return_value.channel.return_value
        worker = WorkerNode()

        # Mock task data
        task = {
            'task_id': '123',
            'definition': {'command': 'echo test'}
        }
        body = json.dumps(task).encode()

        # Mock subprocess result
        mock_subprocess_run.return_value.stdout = 'test output'
        mock_subprocess_run.return_value.stderr = ''
        mock_subprocess_run.return_value.returncode = 0

        # Mock channel, method, and properties
        mock_ch = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = 'delivery_tag'
        mock_properties = MagicMock()

        # Call process_task
        worker.process_task(mock_ch, mock_method, mock_properties, body)

        # Assertions
        mock_subprocess_run.assert_called_once_with('echo test', shell=True, capture_output=True, text=True, check=True)
        mock_channel.basic_publish.assert_called_once()
        mock_ch.basic_ack.assert_called_once_with(delivery_tag='delivery_tag')

if __name__ == '__main__':
    unittest.main()
