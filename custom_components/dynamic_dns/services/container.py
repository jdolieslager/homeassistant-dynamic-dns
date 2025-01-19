"""Service container for Dynamic DNS integration."""
from typing import Dict, Optional, TYPE_CHECKING
from homeassistant.core import HomeAssistant

if TYPE_CHECKING:
    from .http_client import HTTPClient
    from .ip_resolver import IPResolver
else:
    from .http_client import AIOHTTPClient
    from .ip_resolver import IPResolver

from ..exceptions import ConfigurationError

class ServiceContainer:
    """Container for shared services."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize service container."""
        self._hass = hass
        self._http_clients: Dict[str, "HTTPClient"] = {}
        self._ip_resolvers: Dict[str, "IPResolver"] = {}

    def get_http_client(self, identifier: str, headers: Optional[Dict[str, str]] = None) -> "HTTPClient":
        """Get or create HTTP client."""
        if identifier not in self._http_clients:
            self._http_clients[identifier] = AIOHTTPClient(headers=headers)
        return self._http_clients[identifier]

    def get_ip_resolver(self, hostname: str) -> "IPResolver":
        """Get or create IP resolver."""
        if hostname not in self._ip_resolvers:
            self._ip_resolvers[hostname] = IPResolver(hostname)
        return self._ip_resolvers[hostname]

    async def close(self) -> None:
        """Close all services."""
        for client in self._http_clients.values():
            await client.close()
        self._http_clients.clear()
        self._ip_resolvers.clear() 