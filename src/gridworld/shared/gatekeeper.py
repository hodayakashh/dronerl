"""API Gatekeeper — centralised external-call manager.

This project has no external API calls. The gatekeeper is provided as an
architectural placeholder to satisfy the SDK layer contract and to make future
integration (e.g. logging to a remote service) straightforward.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class ApiGatekeeper:
    """Centralised pass-through for all external calls.

    Logs every call. Extend this class to add rate-limiting or retries
    when real external APIs are introduced.
    """

    def execute(self, api_call: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute a callable through the gatekeeper.

        Args:
            api_call: The function to call.
            *args: Positional arguments forwarded to api_call.
            **kwargs: Keyword arguments forwarded to api_call.

        Returns:
            Whatever api_call returns.
        """
        logger.debug("Gatekeeper executing: %s", getattr(api_call, "__name__", repr(api_call)))
        return api_call(*args, **kwargs)
