"""Base provider for Dynamic DNS."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from ..models import UpdateInterval  # Only need UpdateInterval now
from ..services.http_client import HTTPClient
from ..exceptions import DynamicDNSError

class DNSRecordProvider(ABC):
    """Interface for DNS record operations."""
    
    @abstractmethod
    async def update_record(self, ip_address: str) -> bool:
        """Update DNS record."""
        pass

class ProviderMetadata(ABC):
    """Interface for provider metadata."""
    
    @abstractmethod
    def domain_name(self) -> str:
        """Get domain name."""
        pass
    
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
        pass
    
    @abstractmethod
    def extra_attributes(self) -> Dict[str, Any]:
        """Get provider attributes."""
        pass

class BaseDynamicDNSProvider(DNSRecordProvider, ProviderMetadata):
    """Base class combining all provider interfaces."""
    
    def __init__(
        self,
        config: Any,  # Type will be specific in child classes
        http_client: HTTPClient
    ) -> None:
        """Initialize provider with dependencies."""
        self.config = config
        self._http_client = http_client
        self._current_ip: Optional[str] = None

    @property
    def current_ip(self) -> Optional[str]:
        """Get current IP."""
        return self._current_ip

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Test the connection and credentials."""
        pass

    def display_name(self) -> str:
        """Get display name."""
        return f"{self.domain_name()} ({self.provider_name()})"

# ... rest of the existing base.py content ... 