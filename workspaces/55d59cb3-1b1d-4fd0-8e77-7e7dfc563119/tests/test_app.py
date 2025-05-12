import unittest
import json
import app

class AppTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.app.test_client()
        self.app.testing = True

    def test_create_task(self):
        data = {"x": 5, "y": 10}
        response = self.app.post('/tasks', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertIn('task_id', response_data)

    def test_get_task_status(self):
        # First create a task
        data = {"x": 5, "y": 10}
        create_response = self.app.post('/tasks', data=json.dumps(data), content_type='application/json')
        create_data = json.loads(create_response.data.decode('utf-8'))
        task_id = create_data['task_id']

        # Then get the task status
        get_response = self.app.get(f'/tasks/{task_id}')
        self.assertEqual(get_response.status_code, 200)
        get_data = json.loads(get_response.data.decode('utf-8'))
        self.assertIn('state', get_data)

if __name__ == '__main__':
    unittest.main()
