from fastapi import APIRouter, BackgroundTasks, Request
from typing import Optional, Callable
from .schemas import AirtelWebhookData

airtel_router = APIRouter()
_webhook_handler: Optional[Callable] = None

def set_airtel_webhook_handler(handler: Callable):
    """
    Registers a background task handler for incoming Airtel results.
    """
    global _webhook_handler
    _webhook_handler = handler

@airtel_router.post("/webhook")
async def airtel_webhook(
    data: AirtelWebhookData,
    background_tasks: BackgroundTasks,
    request: Request
):
    """
    Handles Airtel Money webhooks.
    Responds immediately with HTTP 200, while running your handler in a background task.
    """
    if _webhook_handler is not None:
        background_tasks.add_task(_webhook_handler, data)
        
    return {"status": "success"}
