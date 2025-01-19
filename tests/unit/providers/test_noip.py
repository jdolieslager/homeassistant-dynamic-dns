"""Test the NoIP provider."""
from unittest.mock import Mock, patch, AsyncMock
import pytest
import aiohttp
import base64

from custom_components.dynamic_dns.exceptions import DynamicDNSError
from custom_components.dynamic_dns.providers.noip import NoIPProvider, NoIPConfig

@pytest.fixture
def config():
    """Create a test config."""
    return NoIPConfig(
        hostname="test.ddns.net",
        username="testuser",
        password="testpass"
    )

@pytest.fixture
def mock_response():
    """Create a mock response."""
    response = Mock()
    response.status = 200
    response.text = Mock(return_value="good 1.2.3.4")
    return response

@pytest.fixture
def mock_session():
    """Create a mock session."""
    session = Mock()
    session.headers = {}
    return session

@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    client = Mock()
    client.get = AsyncMock(return_value=(200, "OK", None))
    client.post = AsyncMock(return_value=(200, "OK", None))
    client.patch = AsyncMock(return_value=(200, "OK", None))
    return client

@pytest.fixture
def provider(config, mock_http_client):
    """Create a test provider."""
    return NoIPProvider(config=config, http_client=mock_http_client)

async def test_update_record_success(provider, mock_response):
    """Test successful record update."""
    mock_response.text = AsyncMock(return_value="good 1.2.3.4")
    
    with patch.object(provider._http_client, "get") as mock_get:
        mock_get.return_value = (200, "good 1.2.3.4", {})
        result = await provider.update_record("1.2.3.4")
        assert result is True
        mock_get.assert_called_once_with(
            "https://dynupdate.no-ip.com/nic/update",
            params={"hostname": "test.ddns.net", "myip": "1.2.3.4"}
        )

async def test_update_record_failure(provider):
    """Test failed record update."""
    mock_response = Mock()
    mock_response.text = AsyncMock(return_value="nohost")
    mock_response.status = 200
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        with pytest.raises(DynamicDNSError):
            await provider.update_record("1.2.3.4")

async def test_validate_connection_success(provider):
    """Test successful connection validation."""
    mock_response = Mock()
    mock_response.status = 200
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        result = await provider.validate_connection()
        assert result is True

async def test_validate_connection_failure(provider):
    """Test failed connection validation."""
    with patch.object(provider._http_client, "get") as mock_get:
        mock_get.return_value = (401, "Unauthorized", {})
        with pytest.raises(DynamicDNSError):
            await provider.validate_connection() 