from flask import Flask, request, jsonify
from src.task_scheduler import TaskScheduler
from src.result_aggregator import ResultAggregator

app = Flask(__name__)
scheduler = TaskScheduler()
aggregator = ResultAggregator()

@app.route('/tasks', methods=['POST'])
def create_task():
    task_definition = request.get_json()
    task_id = scheduler.schedule_task(task_definition)
    return jsonify({'task_id': task_id}), 201

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task_result(task_id):
    result = aggregator.get_result(task_id)
    if result:
        return jsonify(result), 200
    else:
        return jsonify({'message': 'Result not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
