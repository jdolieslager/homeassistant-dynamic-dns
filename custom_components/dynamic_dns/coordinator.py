"""Data update coordinator for Dynamic DNS."""
from datetime import timedelta, datetime
import logging
from typing import Optional, TYPE_CHECKING, Dict, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .models import UpdateStatus, UpdateResult
from .exceptions import DynamicDNSError, ResolutionError
from .services.container import ServiceContainer

if TYPE_CHECKING:
    from .providers.base import BaseDynamicDNSProvider

_LOGGER = logging.getLogger(__name__)

class DNSUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching DNS data."""

    def __init__(
        self,
        hass: HomeAssistant,
        provider: "BaseDynamicDNSProvider",
        services: ServiceContainer,
    ) -> None:
        """Initialize."""
        self.provider = provider
        self._services = services
        self._ip_resolver = services.get_ip_resolver(provider.domain_name())
        
        _LOGGER.debug(
            "Initializing coordinator for %s with update interval: %d seconds",
            provider.domain_name(),
            provider.config.update_interval.interval
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=provider.config.update_interval.interval),
        )

    async def async_start(self):
        """Start the coordinator."""
        _LOGGER.debug("Starting coordinator for %s", self.provider.domain_name())
        await self.async_refresh()
        _LOGGER.debug("Initial refresh completed for %s", self.provider.domain_name())

    async def async_stop(self):
        """Stop the coordinator."""
        _LOGGER.debug("Stopping coordinator for %s", self.provider.domain_name())
        await self.async_shutdown()
        _LOGGER.debug("Coordinator stopped for %s", self.provider.domain_name())

    async def _async_update_data(self):
        """Update DNS records if IP has changed."""
        now = datetime.now()
        if isinstance(self.last_update_success, datetime):  # Check if we have a previous update
            time_since_update = (now - self.last_update_success).total_seconds()
            _LOGGER.debug(
                "%s: Time since last update: %d seconds (interval: %d seconds)",
                self.provider.domain_name(),
                time_since_update,
                self.provider.config.update_interval.interval
            )

        _LOGGER.debug("%s: Starting update at %s", self.provider.domain_name(), now.isoformat())

        try:
            # Get current DNS record from authoritative servers
            current_record = await self._ip_resolver.get_ip()
            _LOGGER.debug("%s: Current DNS record: %s", self.provider.domain_name(), current_record)

            # Get current public IP
            current_ip = await self._ip_resolver.get_current_ip()
            _LOGGER.debug("%s: Current public IP: %s", self.provider.domain_name(), current_ip)

            if not current_ip:
                raise ResolutionError("Failed to determine current IP address")

            # Compare both current record and stored IP
            needs_update = False
            update_reasons = []

            if current_ip != self.provider.current_ip:
                update_reasons.append("local IP cache mismatch")
                needs_update = True

            if current_record and current_ip != current_record:
                update_reasons.append("DNS record mismatch")
                needs_update = True

            if needs_update:
                _LOGGER.debug(
                    "%s: Update needed - Current IP: %s, DNS Record: %s, Stored IP: %s, Reasons: %s",
                    self.provider.domain_name(),
                    current_ip,
                    current_record,
                    self.provider.current_ip,
                    ", ".join(update_reasons)
                )
                success = await self.provider.update_record(current_ip)
                if success:
                    _LOGGER.info(
                        "%s: Successfully updated DNS record to %s",
                        self.provider.domain_name(),
                        current_ip
                    )
                    return UpdateResult(
                        status=UpdateStatus.SUCCESS,
                        ip=current_ip,
                        record=current_record,
                        reasons=update_reasons
                    ).to_dict()

                _LOGGER.warning("%s: Failed to update DNS record", self.provider.domain_name())
                return UpdateResult(
                    status=UpdateStatus.FAILED,
                    ip=current_ip,
                    record=current_record,
                    reasons=update_reasons
                ).to_dict()
            
            _LOGGER.debug("%s: No update needed - IP and DNS record match", self.provider.domain_name())
            return UpdateResult(
                status=UpdateStatus.NO_UPDATE,
                ip=current_ip,
                record=current_record,
                reasons=["no update needed"]
            ).to_dict()

        except DynamicDNSError as error:
            _LOGGER.error("%s: %s", self.provider.domain_name(), str(error))
            return UpdateResult(
                status=UpdateStatus.ERROR,
                reasons=[str(error)]
            ).to_dict()
        except Exception as error:
            _LOGGER.exception("%s: Unexpected error: %s", self.provider.domain_name(), error)
            return UpdateResult(
                status=UpdateStatus.ERROR,
                reasons=[f"Unexpected error: {str(error)}"]
            ).to_dict() 