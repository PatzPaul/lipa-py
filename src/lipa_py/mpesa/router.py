from fastapi import APIRouter, BackgroundTasks, Depends
from typing import Callable, Awaitable, Dict, Any, Optional

from lipa_py._base import WebhookRegistry
from lipa_py.mpesa.schemas import MpesaWebhookData

mpesa_router = APIRouter(tags=["M-Pesa Webhooks"])

webhook_registry: WebhookRegistry[MpesaWebhookData] = WebhookRegistry()


def set_webhook_handler(
    handler: Callable[[MpesaWebhookData], Awaitable[None]],
    event_type: str = "default",
) -> None:
    """Register an async handler invoked with the parsed M-Pesa webhook payload."""
    webhook_registry.set_handler(handler, event_type)


def _get_handler_dep(event_type: str = "default"):
    def dependency() -> Optional[Callable[[MpesaWebhookData], Awaitable[None]]]:
        return webhook_registry.get_handler(event_type)
    return dependency


@mpesa_router.post("/webhook")
async def mpesa_webhook(
    data: MpesaWebhookData,
    background_tasks: BackgroundTasks,
    handler: Optional[Callable[[MpesaWebhookData], Awaitable[None]]] = Depends(_get_handler_dep("default")),
) -> Dict[str, Any]:
    """
    M-Pesa webhook. Responds 200 immediately and runs the handler in a BackgroundTask
    so Vodacom doesn't time out.
    """
    if handler:
        background_tasks.add_task(handler, data)
    return {"status": "success", "message": "Webhook received"}
