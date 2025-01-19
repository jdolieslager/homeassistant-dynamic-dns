"""DNSimple provider for Dynamic DNS."""
from typing import Optional, Dict, Any

from ..models import DNSimpleConfig
from ..services.http_client import HTTPClient
from ..exceptions import AuthenticationError, ConfigurationError, UpdateError
from .base import BaseDynamicDNSProvider

class DNSimpleProvider(BaseDynamicDNSProvider):
    """DNSimple provider implementation."""

    def __init__(
        self,
        config: DNSimpleConfig,
        http_client: HTTPClient
    ) -> None:
        """Initialize DNSimple provider."""
        super().__init__(config, http_client)
        self.config = config

    async def validate_connection(self) -> bool:
        """Test the connection and credentials."""
        try:
            # Verify token works by checking account access
            status, _, data = await self._http_client.get(
                f"https://api.dnsimple.com/v2/whoami"
            )
            
            if status != 200:
                raise AuthenticationError("Failed to authenticate with DNSimple")
            
            if str(data["data"]["account"]["id"]) != self.config.account_id:
                raise ConfigurationError("Account ID does not match the provided token")

            # Verify zone exists
            status, _, _ = await self._http_client.get(
                f"https://api.dnsimple.com/v2/{self.config.account_id}/zones/{self.config.zone}"
            )
            
            if status != 200:
                raise ConfigurationError("Zone not found or not accessible")

            return True

        except (AuthenticationError, ConfigurationError):
            raise
        except Exception as error:
            raise UpdateError(f"Failed to validate DNSimple connection: {error}")

    async def update_record(self, ip_address: str) -> bool:
        """Update DNS record with new IP address."""
        try:
            # Get existing records
            status, _, data = await self._http_client.get(
                f"https://api.dnsimple.com/v2/{self.config.account_id}/zones/{self.config.zone}/records"
            )
            
            if status != 200:
                raise UpdateError("Failed to get DNS records")

            # Find the A record
            record_id = None
            for record in data["data"]:
                if record["name"] == self.config.record_name and record["type"] == "A":
                    record_id = record["id"]
                    break

            if record_id:
                # Update existing record
                status, _, _ = await self._http_client.patch(
                    f"https://api.dnsimple.com/v2/{self.config.account_id}/zones/{self.config.zone}/records/{record_id}",
                    json={"content": ip_address}
                )
                
                if status != 200:
                    raise UpdateError("Failed to update DNS record")
            else:
                # Create new record
                status, _, _ = await self._http_client.post(
                    f"https://api.dnsimple.com/v2/{self.config.account_id}/zones/{self.config.zone}/records",
                    json={
                        "name": self.config.record_name,
                        "type": "A",
                        "content": ip_address
                    }
                )
                
                if status != 201:
                    raise UpdateError("Failed to create DNS record")

            self._current_ip = ip_address
            return True

        except Exception as error:
            raise UpdateError(f"Failed to update DNSimple record: {error}")

    def domain_name(self) -> str:
        """Get the full domain name being managed."""
        if self.config.record_name == "@":
            return self.config.zone
        return f"{self.config.record_name}.{self.config.zone}"

    def provider_name(self) -> str:
        """Get the name of the DNS provider."""
        return "DNSimple"

    def extra_attributes(self) -> Dict[str, Any]:
        """Get provider-specific attributes."""
        return {
            "zone": self.config.zone,
            "record_name": self.config.record_name,
        } 