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

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            host="localhost",
            login=self._user,
            password=self._pass,
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)
    
    async def setup_infrastructure(self):
        exchange = await self.channel.declare_exchange(
            "market_pulse_topic",
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        queue = await self.channel.declare_queue("main_analysis_queue", durable=True)
        await queue.bind(exchange, routing_key="market.#")

    async def publish_event(self, routing_key: str, payload: dict):
        exchange = await self.channel.get_exchange("market_pulse_topic")
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )

    async def close(self):
        if self.connection:
            await self.connection.close()


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

class MarketBatchConsumer:
    def __init__(self, amqp_url: str, threshold=100):
        self.url = amqp_url
        self.connection = None
        self.threshold = threshold
        self.buffer = []
        self.messages_to_ack = [] # To acknowledge them all at once later

    async def start(self):
        # 1. Connect to RabbitMQ
        self.connection = await aio_pika.connect_robust(self.url)
        channel = await self.connection.channel()

        # 2. Set Prefetch: Allow the worker to pull 100+ messages into its local memory
        await channel.set_qos(prefetch_count=self.threshold + 10)
        
        queue = await channel.declare_queue("market_data_queue", durable=True)

        print(f"[*] Waiting for {self.threshold} data points...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                # message to buffer, but NOT 'ack' yet
                payload = json.loads(message.body)
                self.buffer.append(payload)
                self.messages_to_ack.append(message)

                print(f"Buffer: {len(self.buffer)}/{self.threshold}")

                if len(self.buffer) >= self.threshold:
                    await self.trigger_analysis()

    async def trigger_analysis(self):
        print("All data collected. Handing over to CrewAI...")
        # New messages will now go into the fresh empty lists
        batch = self.buffer[:]
        msgs = self.messages_to_ack[:]
        self.buffer = []
        self.messages_to_ack = []

        try:
            # Pass the list of 100 events to the Crew
            await MarketWarRoom().crew().kickoff_async(inputs={"market_data": self.buffer})
            
            # SUCCESS: Ack all 100 messages at once
            for msg in self.messages_to_ack:
                await msg.ack()
            
            print("Analysis finished and messages acknowledged.")
        except Exception as e:
            print(f"CrewAI Failed: {e}. Messages will stay in queue.")
            for msg in msgs:
                await msg.nack(requeue=True)

    async def close(self):
        if self.connection:
            await self.connection.close()