from flask import Flask, request, jsonify
import sqlite3
app = Flask(__name__)
# Database setup and schema
conn = sqlite3.connect('tools.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS tools (id INTEGER PRIMARY KEY, name TEXT, description TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS usage_log (id INTEGER PRIMARY KEY, tool_id INT, effectiveness REAL, last_used DATE)''')
conn.commit()
# API endpoints for managing the tool registry
@app.route('/tools', methods=['POST'])
def add_tool():
    data = request.get_json()
    with sqlite3.connect('tools.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tools (name, description) VALUES (?, ?)', (data['name'], data['description'])))
        conn.commit()
    return jsonify({'message': 'Tool added'}), 201
@app.route('/tools', methods=['GET'])
def get_tools():
    with sqlite3.connect('tools.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tools')
        rows = cursor.fetchall()
    return jsonify(rows), 200
if __name__ == '__main__':
    app.run(debug=True)
