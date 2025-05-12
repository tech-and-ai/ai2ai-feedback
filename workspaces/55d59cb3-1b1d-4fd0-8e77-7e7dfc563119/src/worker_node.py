import pika
import json
import subprocess
from src.config import RABBITMQ_HOST, RABBITMQ_QUEUE, RESULT_QUEUE

class WorkerNode:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        self.channel.queue_declare(queue=RESULT_QUEUE)

    def process_task(self, ch, method, properties, body):
        task = json.loads(body.decode())
        task_id = task['task_id']
        definition = task['definition']
        print(f"[x] Received task: {task_id}")

        try:
            result = subprocess.run(definition['command'], shell=True, capture_output=True, text=True, check=True)
            output = result.stdout
            status = 'success'
            log = result.stderr
        except subprocess.CalledProcessError as e:
            output = e.stdout
            status = 'failure'
            log = e.stderr

        result = {
            'task_id': task_id,
            'status': status,
            'output': output,
            'log': log
        }

        self.channel.basic_publish(exchange='', routing_key=RESULT_QUEUE, body=json.dumps(result))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[x] Task {task_id} processed. Result sent.")

    def start_consuming(self):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=self.process_task)
        print(' [x] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

    def close(self):
        self.connection.close()

if __name__ == '__main__':
    worker = WorkerNode()
    worker.start_consuming()
