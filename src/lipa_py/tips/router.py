from fastapi import APIRouter, BackgroundTasks, Depends
from typing import Callable, Awaitable, Dict, Any, Optional

from lipa_py._base import WebhookRegistry
from .schemas import TIPSWebhookData

tips_router = APIRouter(tags=["TIPS Webhooks"])

tips_webhook_registry: WebhookRegistry[TIPSWebhookData] = WebhookRegistry()


def set_tips_webhook_handler(
    handler: Callable[[TIPSWebhookData], Awaitable[None]],
    event_type: str = "default",
) -> None:
    """Register an async handler invoked with the parsed TIPS webhook payload."""
    tips_webhook_registry.set_handler(handler, event_type)


def _get_handler_dep(event_type: str = "default"):
    def dependency() -> Optional[Callable[[TIPSWebhookData], Awaitable[None]]]:
        return tips_webhook_registry.get_handler(event_type)
    return dependency


@tips_router.post("/webhook")
async def tips_webhook(
    data: TIPSWebhookData,
    background_tasks: BackgroundTasks,
    handler: Optional[Callable[[TIPSWebhookData], Awaitable[None]]] = Depends(_get_handler_dep("default")),
) -> Dict[str, Any]:
    """
    TIPS webhook. Responds 200 immediately and runs the handler in a BackgroundTask.
    """
    if handler:
        background_tasks.add_task(handler, data)
    return {"status": "success"}
