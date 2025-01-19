"""Support for Dynamic DNS sensors."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DNSUpdateCoordinator
from .models import UpdateStatus

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dynamic DNS sensor."""
    coordinator = hass.data[DOMAIN]["coordinators"][entry.entry_id]
    async_add_entities([DynamicDNSSensor(coordinator)], True)

class DynamicDNSSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Dynamic DNS sensor."""

    def __init__(self, coordinator: DNSUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.provider.domain_name()}_status"
        self._attr_name = coordinator.provider.display_name()

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("ip")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the sensor."""
        attrs = {
            "provider": self.coordinator.provider.provider_name(),
            "domain": self.coordinator.provider.domain_name(),
            "update_interval": self.coordinator.provider.config.update_interval.interval,
        }

        # Add provider-specific attributes
        attrs.update(self.coordinator.provider.extra_attributes())

        if self.coordinator.data:
            # Add status information
            attrs["last_update"] = self.coordinator.data.get("last_update", "unknown")
            attrs["dns_record"] = self.coordinator.data.get("dns_record")
            attrs["update_reason"] = self.coordinator.data.get("update_reason", [])

            # Add last successful update timestamp if available
            if self.coordinator.data.get("last_update") == UpdateStatus.SUCCESS.value:
                attrs["last_update_success"] = datetime.now().isoformat()

        return attrs

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        return self.coordinator.data is not None

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if not self.coordinator.data:
            return "mdi:dns-outline"
        
        status = self.coordinator.data.get("last_update")
        if status == UpdateStatus.SUCCESS.value:
            return "mdi:dns"
        elif status == UpdateStatus.NO_UPDATE.value:
            return "mdi:dns-outline"
        elif status in [UpdateStatus.FAILED.value, UpdateStatus.ERROR.value]:
            return "mdi:dns-off"
        return "mdi:dns-outline" 