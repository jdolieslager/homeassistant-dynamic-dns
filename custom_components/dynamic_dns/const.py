"""Constants for the Dynamic DNS integration."""
from typing import Final, Dict, List

DOMAIN: Final = "dynamic_dns"

# Services
SERVICE_DIAGNOSTICS = "diagnostics"

# Providers
PROVIDER_DNSIMPLE = "dnsimple"
PROVIDER_NOIP = "noip"
PROVIDER_DUCKDNS = "duckdns"
# Add more providers later:
# PROVIDER_NAMECHEAP = "namecheap"

PROVIDERS = [
    PROVIDER_DNSIMPLE,
    PROVIDER_NOIP,
    PROVIDER_DUCKDNS,
]

# Configuration keys
CONF_PROVIDER = "provider"
CONF_ACCOUNT_ID = "account_id"
CONF_TOKEN = "token"
CONF_ZONE = "zone"
CONF_RECORD_NAME = "record_name"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_HOSTNAME = "hostname"
CONF_DOMAIN = "domain"

DEFAULT_UPDATE_INTERVAL = 300  # 5 minutes

# Provider specific requirements
PROVIDER_REQUIREMENTS: Dict[str, List[str]] = {
    PROVIDER_DNSIMPLE: [
        CONF_ACCOUNT_ID,
        CONF_TOKEN,
        CONF_ZONE,
        CONF_RECORD_NAME,
    ],
    PROVIDER_NOIP: [
        CONF_USERNAME,
        CONF_PASSWORD,
        CONF_HOSTNAME,
    ],
    PROVIDER_DUCKDNS: [
        CONF_TOKEN,
        CONF_DOMAIN,
    ],
    # Add more provider requirements later:
    # PROVIDER_NAMECHEAP: [CONF_USERNAME, CONF_TOKEN, CONF_DOMAIN],
} 