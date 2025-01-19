"""No-IP Dynamic DNS provider."""
import base64
from typing import Dict, Any

from ..exceptions import AuthenticationError, DynamicDNSError
from ..models import NoIPConfig
from .base import BaseDynamicDNSProvider

class NoIPProvider(BaseDynamicDNSProvider):
    """No-IP provider implementation."""

    def __init__(self, config: NoIPConfig, http_client) -> None:
        """Initialize provider."""
        super().__init__(config, http_client)
        self._config: NoIPConfig = config
        auth = base64.b64encode(
            f"{config.username}:{config.password}".encode()
        ).decode()
        self._http_client.headers.update({
            "Authorization": f"Basic {auth}"
        })

    async def validate_connection(self) -> bool:
        """Test the connection and credentials."""
        try:
            status, text, _ = await self._http_client.get(
                f"https://dynupdate.no-ip.com/nic/update?hostname={self._config.hostname}"
            )
            if status == 401:
                raise AuthenticationError("Invalid No-IP credentials")
            if status != 200:
                raise DynamicDNSError(f"No-IP returned status {status}: {text}")
            return True
        except AuthenticationError:
            raise
        except Exception as err:
            raise DynamicDNSError(f"Failed to validate No-IP connection: {err}")

    async def update_record(self, ip_address: str) -> bool:
        """Update DNS record with new IP address."""
        try:
            params = {
                "hostname": self._config.hostname,
                "myip": ip_address
            }
            
            status, text, _ = await self._http_client.get(
                "https://dynupdate.no-ip.com/nic/update",
                params=params
            )

            if status != 200:
                raise DynamicDNSError(f"Failed to update No-IP record: HTTP {status}")
            
            if text.startswith("good") or text.startswith("nochg"):
                self._current_ip = ip_address
                return True
            
            raise DynamicDNSError(f"Failed to update No-IP record: {text}")

        except Exception as error:
            raise DynamicDNSError(f"Failed to update No-IP record: {error}")

    def domain_name(self) -> str:
        """Get the full domain name being managed."""
        return self._config.hostname

    def provider_name(self) -> str:
        """Get the name of the DNS provider."""
        return "No-IP"

    def extra_attributes(self) -> Dict[str, Any]:
        """Get provider-specific attributes."""
        return {
            "hostname": self._config.hostname,
        } 