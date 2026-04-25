from fastapi import APIRouter, BackgroundTasks, Depends
from typing import Callable, Awaitable, Dict, Any, Optional

from lipa_py._base import WebhookRegistry
from .schemas import AirtelWebhookData

airtel_router = APIRouter(tags=["Airtel Money Webhooks"])

airtel_webhook_registry: WebhookRegistry[AirtelWebhookData] = WebhookRegistry()


def set_airtel_webhook_handler(
    handler: Callable[[AirtelWebhookData], Awaitable[None]],
    event_type: str = "default",
) -> None:
    """Register an async handler invoked with the parsed Airtel Money webhook payload."""
    airtel_webhook_registry.set_handler(handler, event_type)


def _get_handler_dep(event_type: str = "default"):
    def dependency() -> Optional[Callable[[AirtelWebhookData], Awaitable[None]]]:
        return airtel_webhook_registry.get_handler(event_type)
    return dependency


@airtel_router.post("/webhook")
async def airtel_webhook(
    data: AirtelWebhookData,
    background_tasks: BackgroundTasks,
    handler: Optional[Callable[[AirtelWebhookData], Awaitable[None]]] = Depends(_get_handler_dep("default")),
) -> Dict[str, Any]:
    """
    Airtel Money webhook. Responds 200 immediately and runs the handler
    in a BackgroundTask.
    """
    if handler:
        background_tasks.add_task(handler, data)
    return {"status": "success"}
