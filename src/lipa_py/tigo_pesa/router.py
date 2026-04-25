from fastapi import APIRouter, BackgroundTasks, Depends
from typing import Callable, Awaitable, Dict, Any, Optional

from lipa_py._base import WebhookRegistry
from .schemas import TigoWebhookData

tigo_router = APIRouter(tags=["Tigo Pesa Webhooks"])

tigo_webhook_registry: WebhookRegistry[TigoWebhookData] = WebhookRegistry()


def set_tigo_webhook_handler(
    handler: Callable[[TigoWebhookData], Awaitable[None]],
    event_type: str = "default",
) -> None:
    """Register an async handler invoked with the parsed Tigo Pesa webhook payload."""
    tigo_webhook_registry.set_handler(handler, event_type)


def _get_handler_dep(event_type: str = "default"):
    def dependency() -> Optional[Callable[[TigoWebhookData], Awaitable[None]]]:
        return tigo_webhook_registry.get_handler(event_type)
    return dependency


@tigo_router.post("/webhook")
async def tigo_webhook(
    data: TigoWebhookData,
    background_tasks: BackgroundTasks,
    handler: Optional[Callable[[TigoWebhookData], Awaitable[None]]] = Depends(_get_handler_dep("default")),
) -> Dict[str, Any]:
    """
    Tigo Pesa webhook. Responds 200 immediately and runs the handler in a BackgroundTask.
    """
    if handler:
        background_tasks.add_task(handler, data)
    return {"status": "success"}
