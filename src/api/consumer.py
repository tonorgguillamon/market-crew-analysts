import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.rabbitmq import MQConsumer
from dotenv import load_dotenv
import os

load_dotenv()

# Configuration
rabbitmq_user = os.getenv("RABBITMQ_USER")
rabbitmq_pass = os.getenv("RABBITMQ_PASS")

RABBITMQ_URL = f"amqp://{rabbitmq_user}:{rabbitmq_pass}@localhost/"
consumer = MQConsumer(RABBITMQ_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Start the consumer in the background
    # asyncio.create_task ensures it doesn't block the API from starting
    loop = asyncio.get_running_loop()
    task = loop.create_task(consumer.start())
    
    yield # App is handling Webhooks now
    
    # SHUTDOWN: Clean up
    task.cancel()
    await consumer.close()

app = FastAPI(lifespan=lifespan)