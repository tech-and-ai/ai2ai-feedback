import unittest
from flask import Flask, jsonify, request
from src.utils.api_endpoints import register_routes
# Mock the database session and other dependencies here
class TestApiEndpoints(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        register_routes()
        self.app = app.test_client()
    def test_add_performance(self):
        response = self.app.post('/add_performance', json={'success_rate': 0.9})
        self.assertEqual(response.status_code, 201)
if __name__ == '__main__':
    unittest.main()