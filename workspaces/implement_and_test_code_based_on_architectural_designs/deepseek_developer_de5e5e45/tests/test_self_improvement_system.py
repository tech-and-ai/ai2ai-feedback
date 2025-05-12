import unittest
from flask import Flask, request, jsonify
import sqlite3
from src.self_improvement_system import app as tested_app
class TestSelfImprovementSystem(unittest.TestCase):
    def setUp(self):
        self.app = tested_app.test_client()
        with sqlite3.connect('self_improve.db') as conn:
            cursor = conn.cursor()
            cursor.execute('DROP TABLE IF EXISTS metrics')
            cursor.execute('''CREATE TABLE metrics (id INTEGER PRIMARY KEY, agent TEXT, performance REAL, lessons TEXT)''')
    def test_add_metric(self):
        response = self.app.post('/metrics', json={'agent': 'AI Agent 1', 'performance': 0.95, 'lessons': 'Initial setup'}))
        self.assertEqual(response.status_code, 201)
    def test_get_metrics(self):
        self.app.post('/metrics', json={'agent': 'AI Agent 1', 'performance': 0.95, 'lessons': 'Initial setup'}))
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)
if __name__ == '__main__':
    unittest.main()
