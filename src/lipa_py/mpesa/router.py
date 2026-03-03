from fastapi import APIRouter, BackgroundTasks, Depends
from typing import Callable, Awaitable, Dict, Any, Optional
import inspect

from lipa_py.mpesa.schemas import MpesaWebhookData

mpesa_router = APIRouter(tags=["M-Pesa Webhooks"])

# We allow developers to set their custom webhook logic here
class WebhookRegistry:
    def __init__(self):
        self._handlers: Dict[str, Callable[[MpesaWebhookData], Awaitable[None]]] = {}

    def set_handler(self, event_type: str, handler: Callable[[MpesaWebhookData], Awaitable[None]]):
        self._handlers[event_type] = handler

    def get_handler(self, event_type: str) -> Optional[Callable[[MpesaWebhookData], Awaitable[None]]]:
        return self._handlers.get(event_type)

webhook_registry = WebhookRegistry()

def set_webhook_handler(handler: Callable[[MpesaWebhookData], Awaitable[None]], event_type: str = "default"):
    """
    Allows developers to set an async function that handles verified webhook data.
    """
    if not inspect.iscoroutinefunction(handler):
        raise ValueError("Webhook handler must be an async function")
        
    webhook_registry.set_handler(event_type, handler)

# We use dependency injection for handlers to be easily overridden or mocked if needed
def get_webhook_handler_dependency(event_type: str = "default"):
    def dependency() -> Optional[Callable[[MpesaWebhookData], Awaitable[None]]]:
        return webhook_registry.get_handler(event_type)
    return dependency

@mpesa_router.post("/webhook")
async def mpesa_webhook(
    data: MpesaWebhookData, 
    background_tasks: BackgroundTasks,
    handler: Optional[Callable[[MpesaWebhookData], Awaitable[None]]] = Depends(get_webhook_handler_dependency("default"))
) -> Dict[str, Any]:
    """
    Handles M-Pesa webhook callbacks.
    Parses incoming data and optionally fires an async handler cleanly in the background
    to return a quick 200 response to Vodacom as required by standard protocols.
    """
    
    if handler:
        # Avoid blocking the M-Pesa API response back to MNO
        background_tasks.add_task(handler, data)
        
    return {"status": "success", "message": "Webhook received"}
