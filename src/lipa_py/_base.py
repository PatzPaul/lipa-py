from dataclasses import dataclass
from typing import Callable, Awaitable, Dict, Generic, Optional, TypeVar
import inspect


@dataclass
class Environment:
    base_url: str


T = TypeVar("T")


class WebhookRegistry(Generic[T]):
    """
    Per-provider registry for async webhook handlers.
    Keyed by event_type so a single provider can fan out different
    payload shapes (e.g. "payment.success", "payment.failed") later.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[T], Awaitable[None]]] = {}

    def set_handler(
        self,
        handler: Callable[[T], Awaitable[None]],
        event_type: str = "default",
    ) -> None:
        if not inspect.iscoroutinefunction(handler):
            raise ValueError("Webhook handler must be an async function")
        self._handlers[event_type] = handler

    def get_handler(
        self, event_type: str = "default"
    ) -> Optional[Callable[[T], Awaitable[None]]]:
        return self._handlers.get(event_type)

    def clear(self) -> None:
        self._handlers.clear()
