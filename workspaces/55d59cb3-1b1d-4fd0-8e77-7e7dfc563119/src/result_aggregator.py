import pika
import json
from src.config import RABBITMQ_HOST, RESULT_QUEUE

class ResultAggregator:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=RESULT_QUEUE)
        self.results = {}

    def process_result(self, ch, method, properties, body):
        result = json.loads(body.decode())
        task_id = result['task_id']
        self.results[task_id] = result
        print(f"[x] Received result for task: {task_id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def start_consuming(self):
        self.channel.basic_consume(queue=RESULT_QUEUE, on_message_callback=self.process_result)
        print(' [x] Waiting for results. To exit press CTRL+C')
        self.channel.start_consuming()

    def get_result(self, task_id):
        return self.results.get(task_id)

    def close(self):
        self.connection.close()

if __name__ == '__main__':
    aggregator = ResultAggregator()
    aggregator.start_consuming()
