"""DuckDNS Dynamic DNS provider."""
from typing import Dict, Any

from ..exceptions import AuthenticationError, DynamicDNSError
from ..models import DuckDNSConfig
from .base import BaseDynamicDNSProvider

class DuckDNSProvider(BaseDynamicDNSProvider):
    """DuckDNS provider implementation."""

    def __init__(self, config: DuckDNSConfig, http_client) -> None:
        """Initialize provider."""
        super().__init__(config, http_client)
        # Strip .duckdns.org suffix if present
        domain = config.domain.lower()
        if domain.endswith('.duckdns.org'):
            domain = domain[:-12]  # Remove .duckdns.org
        self._config = DuckDNSConfig(
            token=config.token,
            domain=domain,
            update_interval=config.update_interval
        )

    async def validate_connection(self) -> bool:
        """Test the connection and credentials."""
        try:
            status, text, _ = await self._http_client.get(
                f"https://www.duckdns.org/update"
                f"?domains={self._config.domain}"
                f"&token={self._config.token}"
                f"&verbose=true"
            )
            if status != 200:
                raise DynamicDNSError(f"DuckDNS returned status {status}: {text}")
            if "KO" in text:
                raise AuthenticationError("Invalid DuckDNS token")
            if "OK" not in text:
                raise DynamicDNSError(f"Unexpected DuckDNS response: {text}")
            return True
        except AuthenticationError:
            raise
        except Exception as err:
            raise DynamicDNSError(f"Failed to validate DuckDNS connection: {err}")

    async def update_record(self, ip_address: str) -> bool:
        """Update DNS record."""
        try:
            status, text, _ = await self._http_client.get(
                f"https://www.duckdns.org/update"
                f"?domains={self._config.domain}"
                f"&token={self._config.token}"
                f"&ip={ip_address}"
            )
            return status == 200 and "OK" in text
        except Exception as err:
            raise DynamicDNSError(f"Failed to update DuckDNS record: {err}")

    def domain_name(self) -> str:
        """Get domain name."""
        return f"{self._config.domain}.duckdns.org"

    def provider_name(self) -> str:
        """Get provider name."""
        return "DuckDNS"

    def extra_attributes(self) -> Dict[str, Any]:
        """Get provider attributes."""
        return {
            "domain": self._config.domain
        } 