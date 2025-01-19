"""Common test fixtures."""
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    client = Mock()
    client.get = AsyncMock(return_value=(200, "OK", {}))  # Return proper tuple format
    client.post = AsyncMock(return_value=(200, "OK", {}))
    client.patch = AsyncMock(return_value=(200, "OK", {}))
    return client 