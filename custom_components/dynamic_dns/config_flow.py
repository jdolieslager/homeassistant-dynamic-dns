"""Config flow for Dynamic DNS integration."""
from typing import Any, Dict, Optional, cast
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_TOKEN
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ACCOUNT_ID,
    CONF_PROVIDER,
    CONF_ZONE,
    CONF_RECORD_NAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    PROVIDERS,
    PROVIDER_DNSIMPLE,
    PROVIDER_NOIP,
    PROVIDER_DUCKDNS,
    PROVIDER_REQUIREMENTS,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_HOSTNAME,
    CONF_DOMAIN,
)
from .models import (
    DNSimpleConfig,
    NoIPConfig,
    DuckDNSConfig,
    UpdateInterval,
)
from .exceptions import ConfigurationError
from .services.container import ServiceContainer
from .providers.dnsimple import DNSimpleProvider
from .providers.noip import NoIPProvider
from .providers.duckdns import DuckDNSProvider

import logging
_LOGGER = logging.getLogger(__name__)

class DynamicDNSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dynamic DNS."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._provider: Optional[str] = None
        self._data: Dict[str, Any] = {}
        self._services: Optional[ServiceContainer] = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle provider selection."""
        if user_input is not None:
            self._provider = cast(str, user_input[CONF_PROVIDER])
            return await self.async_step_provider()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_PROVIDER, default=PROVIDER_DNSIMPLE): vol.In(PROVIDERS),
            }),
        )

    async def async_step_provider(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle provider credentials."""
        errors = {}

        if user_input is not None:
            try:
                # Combine data from both steps
                self._data.update(user_input)
                self._data[CONF_PROVIDER] = self._provider

                # Initialize services if needed
                if not self._services:
                    self._services = ServiceContainer(self.hass)

                # Create update interval configuration
                update_interval = UpdateInterval(
                    interval=self._data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
                )

                # Create and validate provider configuration
                if self._provider == PROVIDER_DNSIMPLE:
                    config = DNSimpleConfig(
                        account_id=self._data[CONF_ACCOUNT_ID],
                        token=self._data[CONF_TOKEN],
                        zone=self._data[CONF_ZONE],
                        record_name=self._data[CONF_RECORD_NAME],
                        update_interval=update_interval
                    )
                    config.validate()
                    provider = DNSimpleProvider(
                        config=config,
                        http_client=self._services.get_http_client(
                            f"dnsimple_{config.account_id}",
                            headers={
                                "Authorization": f"Bearer {config.token}",
                                "Accept": "application/json",
                                "Content-Type": "application/json",
                            }
                        )
                    )
                elif self._provider == PROVIDER_NOIP:
                    config = NoIPConfig(
                        username=self._data[CONF_USERNAME],
                        password=self._data[CONF_PASSWORD],
                        hostname=self._data[CONF_HOSTNAME],
                        update_interval=update_interval
                    )
                    config.validate()
                    provider = NoIPProvider(
                        config=config,
                        http_client=self._services.get_http_client(
                            f"noip_{config.hostname}",
                            headers={
                                "User-Agent": "Home Assistant Dynamic DNS Client/1.0"
                            }
                        )
                    )
                elif self._provider == PROVIDER_DUCKDNS:
                    config = DuckDNSConfig(
                        token=self._data[CONF_TOKEN],
                        domain=self._data[CONF_DOMAIN],
                        update_interval=update_interval
                    )
                    config.validate()
                    provider = DuckDNSProvider(
                        config=config,
                        http_client=self._services.get_http_client(
                            f"duckdns_{config.domain}",
                            headers={
                                "User-Agent": "Home Assistant Dynamic DNS Client/1.0"
                            }
                        )
                    )

                if await provider.validate_connection():
                    await self.async_set_unique_id(
                        f"{self._provider}_{provider.domain_name()}"
                    )
                    self._abort_if_unique_id_configured()
                    
                    return self.async_create_entry(
                        title=provider.display_name(),
                        data=self._data,
                    )
                else:
                    errors["base"] = "cannot_connect"

            except ConfigurationError as err:
                errors["base"] = "invalid_config"
                _LOGGER.error("Configuration error: %s", err)
            except Exception as err:
                _LOGGER.exception("Unexpected error: %s", err)
                errors["base"] = "unknown"

            # Clean up services on error
            if self._services:
                await self._services.close()
                self._services = None

        # Build schema based on provider requirements
        schema = {}
        for field in PROVIDER_REQUIREMENTS.get(self._provider, []):
            schema[vol.Required(field)] = str

        schema[vol.Optional(
            CONF_UPDATE_INTERVAL,
            default=DEFAULT_UPDATE_INTERVAL
        )] = int

        return self.async_show_form(
            step_id="provider",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_import(self, import_config: dict) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_config)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.entry = entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_UPDATE_INTERVAL,
                default=self.entry.options.get(
                    CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                ),
            ): int,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options),
        ) 