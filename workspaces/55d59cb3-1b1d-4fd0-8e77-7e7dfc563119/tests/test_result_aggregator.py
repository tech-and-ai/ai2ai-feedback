import unittest
from unittest.mock import patch, MagicMock
from src.result_aggregator import ResultAggregator
import json

class TestResultAggregator(unittest.TestCase):

    @patch('src.result_aggregator.pika.BlockingConnection')
    def test_process_result(self, mock_connection):
        aggregator = ResultAggregator()

        # Mock result data
        result = {
            'task_id': '123',
            'status': 'success',
            'output': 'test output'
        }
        body = json.dumps(result).encode()

        # Mock channel, method, and properties
        mock_ch = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = 'delivery_tag'
        mock_properties = MagicMock()

        # Call process_result
        aggregator.process_result(mock_ch, mock_method, mock_properties, body)

        # Assertions
        self.assertEqual(aggregator.get_result('123'), result)
        mock_ch.basic_ack.assert_called_once_with(delivery_tag='delivery_tag')

if __name__ == '__main__':
    unittest.main()
