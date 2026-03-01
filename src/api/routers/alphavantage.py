from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/webhooks/alphavantage", tags=["AlphaVantage"])

class AlphaVantageAlert(BaseModel):
    symbol: str
    price_change_percent: float
    # Add other fields specific to their API

@router.post("/")
async def handle_alphavantage(request: Request, alert: AlphaVantageAlert):
    mq = request.app.state.mq
    
    # NORMALIZE the data so the AI doesn't have to guess
    payload = {
        "source": "AlphaVantage",
        "ticker": alert.symbol,
        "intensity": alert.price_change_percent,
        "timestamp": "..." 
    }
    
    # Publish with a specific routing key
    mq.publish_event(
        routing_key=f"market.alphavantage.alert",
        payload=payload
    )
    
    return {"message": "Event queued for analysis"}