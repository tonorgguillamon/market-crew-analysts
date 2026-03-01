import pika
import json
import os
from pika.exchange_type import ExchangeType
import asyncio
import aio_pika
import json
from src.agents.crew import MarketWarRoom

class RabbitMQManager:
    def __init__(self):
        self.connection = None
        self.channel = None
        self._user = os.getenv('RABBITMQ_USER')
        self._pass = os.getenv('RABBITMQ_PASS')

    def connect(self):
        credentials = pika.PlainCredentials(self._user, self._pass)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost', credentials=credentials)
        )
        self.channel = self.connection.channel()
        self.channel.confirm_delivery() # Ensure reliability
    
    def setup_infrastructure(self):
        """Declare Exchanges, Queues, and Bindings once."""
        self.channel.exchange_declare(
            exchange='market_pulse_topic', 
            exchange_type=ExchangeType.topic, 
            durable=True
        )
        self.channel.queue_declare(queue='main_analysis_queue', durable=True)
        self.channel.queue_bind(
            exchange='market_pulse_topic', 
            queue='main_analysis_queue', 
            routing_key='market.#'
        )

    def publish_event(self, routing_key: str, payload: dict):
        self.channel.basic_publish(
            exchange='market_pulse_topic',
            routing_key=routing_key,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def close(self):
        if self.connection:
            self.connection.close()


class MQConsumer:
    def __init__(self, amqp_url: str):
        self.amqp_url = amqp_url
        self.connection = None

    async def start(self):
        # Establish Async Connection
        self.connection = await aio_pika.connect_robust(self.amqp_url)
        channel = await self.connection.channel()

        # Set QoS: One event at a time per worker (Crucial for AI agents)
        await channel.set_qos(prefetch_count=1)

        # Declare the queue (idempotent)
        queue = await channel.declare_queue("main_analysis_queue", durable=True)

        print(" [*] AI Consumer waiting for market events...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process(): # Automatically 'Acks' when finished
                    payload = json.loads(message.body)
                    print(f" [x] New Event: {payload['ticker']}")

                    # Trigger the CrewAI Logic
                    # We await this so the worker doesn't take new jobs 
                    # until the agents finish the report
                    await MarketWarRoom.crew().kickoff_async(inputs=payload) 

    async def close(self):
        if self.connection:
            await self.connection.close()