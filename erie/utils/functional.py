from typing import TypeVar, Callable, Iterable
import logging

T = TypeVar("T")
logger = logging.getLogger(__name__)


def attempt(action: Callable[[], T], label: str) -> T | None:
    """Run a side-effecting call, log and swallow any exception."""
    try:
        return action()
    except Exception:
        logger.exception("Error in: %s", label)
        return None


def attempt_all(actions: Iterable[Callable[[], None]]) -> None:
    """Run every action, never let one failure abort the rest."""
    for action in actions:
        attempt(action, label=action.__qualname__)
