from fastapi import APIRouter, BackgroundTasks, Request
from typing import Optional, Callable
from .schemas import TigoWebhookData

tigo_router = APIRouter()
_webhook_handler: Optional[Callable] = None

def set_tigo_webhook_handler(handler: Callable):
    """
    Registers a background task handler for incoming Tigo results.
    """
    global _webhook_handler
    _webhook_handler = handler

@tigo_router.post("/webhook")
async def tigo_webhook(
    data: TigoWebhookData,
    background_tasks: BackgroundTasks,
    request: Request
):
    """
    Handles Tigo Pesa webhooks.
    Responds immediately with HTTP 200, while running your handler in a background task.
    """
    if _webhook_handler is not None:
        background_tasks.add_task(_webhook_handler, data)
        
    return {"status": "success"}
