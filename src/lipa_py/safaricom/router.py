from fastapi import APIRouter, BackgroundTasks, Request
from typing import Optional, Callable
from .schemas import SafaricomWebhookData

safaricom_router = APIRouter()
_webhook_handler: Optional[Callable] = None

def set_safaricom_webhook_handler(handler: Callable):
    """
    Registers a background task handler for incoming Safaricom STK Push results.
    """
    global _webhook_handler
    _webhook_handler = handler

@safaricom_router.post("/webhook")
async def safaricom_webhook(
    data: SafaricomWebhookData,
    background_tasks: BackgroundTasks,
    request: Request
):
    """
    Handles Safaricom Daraja STK Push webhooks.
    Responds immediately with HTTP 200, while running your handler in a background task.
    """
    if _webhook_handler is not None:
        background_tasks.add_task(_webhook_handler, data)
        
    return {"status": "success"}
