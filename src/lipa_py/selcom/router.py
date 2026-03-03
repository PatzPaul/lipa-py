from fastapi import APIRouter, BackgroundTasks, Depends
from typing import Callable, Awaitable, Dict, Any, Optional
import inspect

from lipa_py.selcom.schemas import SelcomWebhookData

selcom_router = APIRouter(tags=["Selcom Webhooks"])

class SelcomWebhookRegistry:
    def __init__(self):
        self._handlers: Dict[str, Callable[[SelcomWebhookData], Awaitable[None]]] = {}

    def set_handler(self, event_type: str, handler: Callable[[SelcomWebhookData], Awaitable[None]]):
        self._handlers[event_type] = handler

    def get_handler(self, event_type: str) -> Optional[Callable[[SelcomWebhookData], Awaitable[None]]]:
        return self._handlers.get(event_type)

selcom_webhook_registry = SelcomWebhookRegistry()

def set_selcom_handler(handler: Callable[[SelcomWebhookData], Awaitable[None]], event_type: str = "default"):
    """
    Registers the async webhook handler for Selcom.
    """
    if not inspect.iscoroutinefunction(handler):
        raise ValueError("Webhook handler must be an async function")
        
    selcom_webhook_registry.set_handler(event_type, handler)

def get_selcom_handler_dependency(event_type: str = "default"):
    def dependency() -> Optional[Callable[[SelcomWebhookData], Awaitable[None]]]:
        return selcom_webhook_registry.get_handler(event_type)
    return dependency

@selcom_router.post("/webhook")
async def selcom_webhook(
    data: SelcomWebhookData, 
    background_tasks: BackgroundTasks,
    handler: Optional[Callable[[SelcomWebhookData], Awaitable[None]]] = Depends(get_selcom_handler_dependency("default"))
) -> Dict[str, Any]:
    """
    Selcom HTTP Post Callback to notify an integration about the successful or failed status
    of the initiated Checkout or payment.
    Requires background tasks so it responds back to Selcom with 200 Fast!.
    """
    if handler:
        background_tasks.add_task(handler, data)
        
    return {"result": "SUCCESS", "message": "Notification received successfully"}
