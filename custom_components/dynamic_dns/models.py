"""Data models for Dynamic DNS integration."""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from .exceptions import ConfigurationError

@dataclass
class UpdateInterval:
    """Update interval configuration."""
    interval: int = field(default=300)

    def validate(self) -> None:
        """Validate update interval."""
        if self.interval < 60:
            raise ConfigurationError("Update interval must be at least 60 seconds")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "interval": self.interval
        }

@dataclass
class DNSimpleConfig:
    """DNSimple configuration."""
    account_id: str
    token: str
    zone: str
    record_name: str
    update_interval: UpdateInterval = field(default_factory=lambda: UpdateInterval())

    def validate(self) -> None:
        """Validate configuration."""
        self.update_interval.validate()
        if not self.token:
            raise ConfigurationError("Token is required")
        if not self.account_id:
            raise ConfigurationError("Account ID is required")
        if not self.zone:
            raise ConfigurationError("Zone is required")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "account_id": self.account_id,
            "token": self.token,
            "zone": self.zone,
            "record_name": self.record_name,
            "update_interval": self.update_interval.interval,
        }

@dataclass
class NoIPConfig:
    """No-IP configuration."""
    username: str
    password: str
    hostname: str
    update_interval: UpdateInterval = field(default_factory=lambda: UpdateInterval())

    def validate(self) -> None:
        """Validate configuration."""
        self.update_interval.validate()
        if not self.username:
            raise ConfigurationError("Username is required")
        if not self.password:
            raise ConfigurationError("Password is required")
        if not self.hostname:
            raise ConfigurationError("Hostname is required")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "username": self.username,
            "password": "***",  # Don't expose password
            "hostname": self.hostname,
            "update_interval": self.update_interval.interval,
        }

@dataclass
class DuckDNSConfig:
    """DuckDNS configuration."""
    token: str
    domain: str
    update_interval: UpdateInterval = field(default_factory=lambda: UpdateInterval())

    def validate(self) -> None:
        """Validate configuration."""
        self.update_interval.validate()
        if not self.token:
            raise ConfigurationError("Token is required")
        if not self.domain:
            raise ConfigurationError("Domain is required")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "token": "***",  # Don't expose token
            "domain": self.domain,
            "update_interval": self.update_interval.interval,
        }

class UpdateStatus(Enum):
    """Update status enum."""
    SUCCESS = "success"
    FAILED = "failed"
    NO_UPDATE = "no_update_needed"
    ERROR = "error"

@dataclass
class UpdateResult:
    """Update result class."""
    status: UpdateStatus
    ip: Optional[str] = None
    record: Optional[str] = None
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "ip": self.ip,
            "dns_record": self.record,
            "last_update": self.status.value,
            "update_reason": self.reasons
        } 