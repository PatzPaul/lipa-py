from fastapi import APIRouter, BackgroundTasks, Depends
from typing import Callable, Awaitable, Dict, Any, Optional

from lipa_py._base import WebhookRegistry
from .schemas import SafaricomWebhookData

safaricom_router = APIRouter(tags=["Safaricom Webhooks"])

safaricom_webhook_registry: WebhookRegistry[SafaricomWebhookData] = WebhookRegistry()


def set_safaricom_webhook_handler(
    handler: Callable[[SafaricomWebhookData], Awaitable[None]],
    event_type: str = "default",
) -> None:
    """Register an async handler invoked with the parsed Safaricom Daraja webhook payload."""
    safaricom_webhook_registry.set_handler(handler, event_type)


def _get_handler_dep(event_type: str = "default"):
    def dependency() -> Optional[Callable[[SafaricomWebhookData], Awaitable[None]]]:
        return safaricom_webhook_registry.get_handler(event_type)
    return dependency


@safaricom_router.post("/webhook")
async def safaricom_webhook(
    data: SafaricomWebhookData,
    background_tasks: BackgroundTasks,
    handler: Optional[Callable[[SafaricomWebhookData], Awaitable[None]]] = Depends(_get_handler_dep("default")),
) -> Dict[str, Any]:
    """
    Safaricom Daraja STK Push webhook. Responds 200 immediately and runs the handler
    in a BackgroundTask.
    """
    if handler:
        background_tasks.add_task(handler, data)
    return {"status": "success"}
