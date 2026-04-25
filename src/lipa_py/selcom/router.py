from fastapi import APIRouter, BackgroundTasks, Depends
from typing import Callable, Awaitable, Dict, Any, Optional

from lipa_py._base import WebhookRegistry
from lipa_py.selcom.schemas import SelcomWebhookData

selcom_router = APIRouter(tags=["Selcom Webhooks"])

selcom_webhook_registry: WebhookRegistry[SelcomWebhookData] = WebhookRegistry()


def set_selcom_handler(
    handler: Callable[[SelcomWebhookData], Awaitable[None]],
    event_type: str = "default",
) -> None:
    """Register an async handler invoked with the parsed Selcom webhook payload."""
    selcom_webhook_registry.set_handler(handler, event_type)


def _get_handler_dep(event_type: str = "default"):
    def dependency() -> Optional[Callable[[SelcomWebhookData], Awaitable[None]]]:
        return selcom_webhook_registry.get_handler(event_type)
    return dependency


@selcom_router.post("/webhook")
async def selcom_webhook(
    data: SelcomWebhookData,
    background_tasks: BackgroundTasks,
    handler: Optional[Callable[[SelcomWebhookData], Awaitable[None]]] = Depends(_get_handler_dep("default")),
) -> Dict[str, Any]:
    """
    Selcom webhook. Responds 200 immediately and runs the handler in a BackgroundTask.
    """
    if handler:
        background_tasks.add_task(handler, data)
    return {"result": "SUCCESS", "message": "Notification received successfully"}
