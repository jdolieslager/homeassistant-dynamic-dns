"""The Dynamic DNS integration."""
import logging
from typing import Any, Dict

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant, ServiceCall, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform

from .const import (
    CONF_ACCOUNT_ID,
    CONF_ZONE,
    CONF_RECORD_NAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    SERVICE_DIAGNOSTICS,
    PROVIDER_DNSIMPLE,
    PROVIDER_NOIP,
    CONF_PROVIDER,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_HOSTNAME,
    CONF_DOMAIN,
    PROVIDER_DUCKDNS,
)
from .coordinator import DNSUpdateCoordinator
from .providers.dnsimple import DNSimpleProvider
from .providers.noip import NoIPProvider
from .providers.duckdns import DuckDNSProvider
from .services.container import ServiceContainer
from .models import (
    DNSimpleConfig,
    NoIPConfig,
    DuckDNSConfig,
    UpdateInterval,
)
from .exceptions import ConfigurationError

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.removed(DOMAIN, raise_if_present=False)

PLATFORMS = [Platform.SENSOR]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Dynamic DNS component."""
    hass.data[DOMAIN] = {
        "services": ServiceContainer(hass),
        "coordinators": {},
    }

    async def handle_diagnostics(call: ServiceCall) -> None:
        """Handle the diagnostics service call."""
        try:
            diagnostics = []
            last_coordinator = None
            
            for entry_id, coordinator in hass.data[DOMAIN]["coordinators"].items():
                last_coordinator = coordinator
                last_update = coordinator.data.get("last_update", "unknown") if coordinator.data else "unknown"
                current_ip = coordinator.data.get("ip", "unknown") if coordinator.data else "unknown"
                
                entry = hass.config_entries.async_get_entry(entry_id)
                if not entry:
                    continue

                diagnostics.append({
                    "domain": coordinator.provider.domain_name(),
                    "provider": coordinator.provider.provider_name(),
                    "update_interval": coordinator.provider.config.update_interval.interval,
                    "current_ip": current_ip,
                    "last_update": last_update,
                })

            hass.states.async_set(f"{DOMAIN}.diagnostics", "active", {
                "entries": diagnostics,
                "last_updated": last_coordinator.last_update_success.isoformat() if last_coordinator and last_coordinator.last_update_success else "never"
            })
        except Exception as err:
            _LOGGER.error("Error in diagnostics service: %s", err)

    hass.services.async_register(DOMAIN, SERVICE_DIAGNOSTICS, handle_diagnostics)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dynamic DNS from a config entry."""
    services = hass.data[DOMAIN]["services"]
    provider_type = entry.data[CONF_PROVIDER]
    
    try:
        if provider_type == PROVIDER_DNSIMPLE:
            config = DNSimpleConfig(
                account_id=entry.data[CONF_ACCOUNT_ID],
                token=entry.data[CONF_TOKEN],
                zone=entry.data[CONF_ZONE],
                record_name=entry.data[CONF_RECORD_NAME],
                update_interval=UpdateInterval(
                    interval=entry.options.get(
                        CONF_UPDATE_INTERVAL,
                        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
                    )
                )
            )
            config.validate()
            provider = DNSimpleProvider(
                config=config,
                http_client=services.get_http_client(
                    f"dnsimple_{config.account_id}",
                    headers={
                        "Authorization": f"Bearer {config.token}",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    }
                )
            )
        elif provider_type == PROVIDER_NOIP:
            config = NoIPConfig(
                username=entry.data[CONF_USERNAME],
                password=entry.data[CONF_PASSWORD],
                hostname=entry.data[CONF_HOSTNAME],
                update_interval=UpdateInterval(
                    interval=entry.options.get(
                        CONF_UPDATE_INTERVAL,
                        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
                    )
                ),
            )
            config.validate()
            provider = NoIPProvider(
                config=config,
                http_client=services.get_http_client(
                    f"noip_{config.hostname}",
                    headers={
                        "User-Agent": "Home Assistant Dynamic DNS Client/1.0"
                    }
                )
            )
        elif provider_type == PROVIDER_DUCKDNS:
            config = DuckDNSConfig(
                token=entry.data[CONF_TOKEN],
                domain=entry.data[CONF_DOMAIN],
                update_interval=UpdateInterval(
                    interval=entry.options.get(
                        CONF_UPDATE_INTERVAL,
                        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
                    )
                ),
            )
            config.validate()
            provider = DuckDNSProvider(
                config=config,
                http_client=services.get_http_client(
                    f"duckdns_{config.domain}",
                    headers={
                        "User-Agent": "Home Assistant Dynamic DNS Client/1.0"
                    }
                )
            )
        else:
            _LOGGER.error("Unsupported provider: %s", provider_type)
            return False

    except ConfigurationError as error:
        _LOGGER.error("Configuration error: %s", error)
        return False

    coordinator = DNSUpdateCoordinator(
        hass,
        provider=provider,
        services=services,
    )

    # Start the coordinator
    await coordinator.async_start()

    hass.data[DOMAIN]["coordinators"][entry.entry_id] = coordinator

    # Handle options update
    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN]["coordinators"].pop(entry.entry_id)
        await coordinator.async_stop()

    if not hass.data[DOMAIN]["coordinators"]:
        # Close all services if no coordinators left
        await hass.data[DOMAIN]["services"].close()
        hass.data.pop(DOMAIN)

    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id) 