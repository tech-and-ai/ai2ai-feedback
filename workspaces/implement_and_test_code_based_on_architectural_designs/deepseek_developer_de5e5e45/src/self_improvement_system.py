from flask import Flask, request, jsonify
import sqlite3
import logging
app = Flask(__name__)
# Database setup and schema
conn = sqlite3.connect('self_improve.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS metrics (id INTEGER PRIMARY KEY, agent TEXT, performance REAL, lessons TEXT)''')
conn.commit()
logger = logging.getLogger(__name__)
# API endpoints for managing self-improvement data
@app.route('/metrics', methods=['POST'])
def add_metric():
    data = request.get_json()
    with sqlite3.connect('self_improve.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO metrics (agent, performance, lessons) VALUES (?, ?, ?)', (data['agent'], data['performance'], data['lessons'])))
        conn.commit()
    return jsonify({'message': 'Metric added'}), 201
@app.route('/metrics', methods=['GET'])
def get_metrics():
    with sqlite3.connect('self_improve.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM metrics')
        rows = cursor.fetchall()
    return jsonify(rows), 200
if __name__ == '__main__':
    app.run(debug=True)
