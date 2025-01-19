"""HTTP client service."""
from typing import Optional, Dict, Any, Tuple
import asyncio
from async_timeout import timeout
import aiohttp
from abc import ABC, abstractmethod

from ..exceptions import ConnectionError, DynamicDNSError

class HTTPClient(ABC):
    """Interface for HTTP operations."""
    
    @abstractmethod
    async def get(self, url: str, **kwargs) -> Tuple[int, str, Any]:
        """Perform GET request."""
        pass
    
    @abstractmethod
    async def post(self, url: str, **kwargs) -> Tuple[int, str, Any]:
        """Perform POST request."""
        pass

    @abstractmethod
    async def patch(self, url: str, **kwargs) -> Tuple[int, str, Any]:
        """Perform PATCH request."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the client."""
        pass

class AIOHTTPClient(HTTPClient):
    """aiohttp-based HTTP client."""
    
    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 3,
        timeout: int = 10,
        retry_delay: float = 1.0
    ) -> None:
        """Initialize client."""
        self.headers = headers or {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._retries = retries
        self._timeout = timeout
        self._retry_delay = retry_delay

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure session exists."""
        if self._session is None:
            self._session = aiohttp.ClientSession(headers=self.headers)
        return self._session

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Tuple[int, str, Any]:
        """Make HTTP request with retry logic."""
        session = await self._ensure_session()
        last_error = None

        for attempt in range(self._retries):
            try:
                async with timeout(self._timeout):
                    async with session.request(method, url, **kwargs) as response:
                        text = await response.text()
                        json_data = (
                            await response.json()
                            if response.content_type == 'application/json'
                            else None
                        )
                        return response.status, text, json_data

            except asyncio.TimeoutError as err:
                last_error = err
                if attempt == self._retries - 1:
                    raise ConnectionError(f"Timeout connecting to {url}")
                await asyncio.sleep(self._retry_delay * (attempt + 1))
            except Exception as err:
                last_error = err
                if attempt == self._retries - 1:
                    raise ConnectionError(f"Error connecting to {url}: {err}")
                await asyncio.sleep(self._retry_delay * (attempt + 1))

        raise ConnectionError(f"Failed to connect to {url} after {self._retries} attempts: {last_error}")

    async def get(self, url: str, **kwargs) -> Tuple[int, str, Any]:
        """Perform GET request."""
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> Tuple[int, str, Any]:
        """Perform POST request."""
        return await self._request("POST", url, **kwargs)

    async def patch(self, url: str, **kwargs) -> Tuple[int, str, Any]:
        """Perform PATCH request."""
        return await self._request("PATCH", url, **kwargs)

    async def close(self) -> None:
        """Close the client."""
        if self._session:
            await self._session.close()
            self._session = None

class MockHTTPClient(HTTPClient):
    """Mock HTTP client for testing."""
    
    def __init__(self) -> None:
        """Initialize mock client."""
        self._responses: Dict[str, Tuple[int, str, Any]] = {}

    def mock_response(self, url: str, status: int, text: str, json_data: Any = None) -> None:
        """Set mock response for URL."""
        self._responses[url] = (status, text, json_data)

    async def get(self, url: str, **kwargs) -> Tuple[int, str, Any]:
        """Return mock response."""
        if url not in self._responses:
            raise ConnectionError(f"No mock response for {url}")
        return self._responses[url]

    async def post(self, url: str, **kwargs) -> Tuple[int, str, Any]:
        """Return mock response."""
        if url not in self._responses:
            raise ConnectionError(f"No mock response for {url}")
        return self._responses[url]

    async def patch(self, url: str, **kwargs) -> Tuple[int, str, Any]:
        """Return mock response."""
        if url not in self._responses:
            raise ConnectionError(f"No mock response for {url}")
        return self._responses[url]

    async def close(self) -> None:
        """Mock close."""
        pass 