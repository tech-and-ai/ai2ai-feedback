from flask import Flask, request, jsonify
from celery import Celery
import config
import uuid

app = Flask(__name__)
app.config.update(config.CELERY_CONFIG)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Mock database (replace with actual database implementation)
task_results = {}

@celery.task
def add(x, y, task_id):
    # Simulate task execution
    result = x + y
    task_results[task_id] = result
    return result

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    x = data['x']
    y = data['y']
    task_id = str(uuid.uuid4())
    task = add.apply_async(args=[x, y, task_id], task_id=task_id)
    return jsonify({'task_id': task.id}), 201

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = celery.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'result': task.info,
            'status': 'Success!'
        }
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
