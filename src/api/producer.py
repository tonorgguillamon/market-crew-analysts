from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.routers import alphavantage, finazon, twelvedata
from src.api.rabbitmq import RabbitMQManager

mq_manager = RabbitMQManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    mq_manager.connect()
    mq_manager.setup_infrastructure()
    
    # Attach to app state so it's globally accessible
    app.state.mq = mq_manager
    
    yield # App is running
    
    # SHUTDOWN
    mq_manager.close()

app = FastAPI(lifespan=lifespan, title="Api Producer")

# Include all the individual brokers
app.include_router(alphavantage.router)
app.include_router(finazon.router)
app.include_router(twelvedata.router)

@app.get("/")
def health_check():
    return {"status": "Market Pulse Producer is Online"}

