"""IP address resolution service."""
import time
from abc import ABC, abstractmethod
import socket
import asyncio
import aiohttp
import dns.resolver
import dns.rdatatype
from typing import Optional, List, Dict, Tuple
from ..exceptions import ResolutionError

class CacheEntry:
    """Cache entry with timestamp."""
    
    def __init__(self, value: str, ttl: int = 300):
        """Initialize cache entry."""
        self.value = value
        self.timestamp = time.time()
        self.ttl = ttl

    def is_valid(self) -> bool:
        """Check if entry is still valid."""
        return time.time() - self.timestamp < self.ttl

class DNSCache:
    """DNS cache with TTL support."""
    
    def __init__(self):
        """Initialize cache."""
        self._cache: Dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[str]:
        """Get cached value if valid."""
        if key in self._cache and self._cache[key].is_valid():
            return self._cache[key].value
        return None

    def set(self, key: str, value: str, ttl: int = 300):
        """Set cache value with TTL."""
        self._cache[key] = CacheEntry(value, ttl)

class IPResolverStrategy(ABC):
    """Interface for IP resolution strategies."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the strategy."""
        pass
    
    @abstractmethod
    async def resolve(self) -> Optional[str]:
        """Resolve IP address."""
        pass

class AuthoritativeDNSResolver(IPResolverStrategy):
    """Resolver that queries authoritative DNS servers directly."""
    
    def __init__(self, hostname: str, cache: DNSCache) -> None:
        """Initialize DNS resolver."""
        self.hostname = hostname
        self._cache = cache
        self._resolver = None
        self._ns_cache: Dict[str, Tuple[List[str], float]] = {}

    async def initialize(self) -> None:
        """Initialize resolver asynchronously."""
        loop = asyncio.get_event_loop()
        self._resolver = await loop.run_in_executor(None, dns.resolver.Resolver)
        # Disable caching to always get fresh results
        self._resolver.cache = None
        self._resolver.lifetime = 10.0  # Timeout after 10 seconds

    async def resolve(self) -> Optional[str]:
        """Resolve IP using authoritative DNS servers."""
        if self._resolver is None:
            await self.initialize()
            
        try:
            # Remove cache check to always get fresh results
            domain = '.'.join(self.hostname.split('.')[-2:])
            ns_records = await self._get_nameservers(domain)
            
            if not ns_records:
                return None
            
            self._resolver.nameservers = ns_records
            
            loop = asyncio.get_event_loop()
            answer = await loop.run_in_executor(
                None,
                self._resolver.resolve,
                self.hostname,
                'A'
            )
            
            if answer and len(answer) > 0:
                return str(answer[0])  # Return IP without caching
            
            return None
            
        except Exception as err:
            raise ResolutionError(f"Failed to resolve {self.hostname}: {err}")

    async def _get_nameservers(self, domain: str) -> List[str]:
        """Get authoritative nameservers with caching."""
        now = time.time()
        if domain in self._ns_cache:
            servers, timestamp = self._ns_cache[domain]
            if now - timestamp < 3600:  # 1 hour cache
                return servers

        try:
            loop = asyncio.get_event_loop()
            # Create resolver in executor to avoid blocking
            resolver = await loop.run_in_executor(None, dns.resolver.Resolver)
            
            ns_answer = await loop.run_in_executor(
                None,
                resolver.resolve,
                domain,
                'NS'
            )
            
            nameservers = []
            for ns in ns_answer:
                a_answer = await loop.run_in_executor(
                    None,
                    resolver.resolve,
                    str(ns),
                    'A'
                )
                nameservers.extend(str(ip) for ip in a_answer)
            
            self._ns_cache[domain] = (nameservers, now)
            return nameservers
            
        except Exception as err:
            raise ResolutionError(f"Failed to get nameservers for {domain}: {err}")

class DNSResolver(IPResolverStrategy):
    """System DNS resolver."""
    
    def __init__(self, hostname: str, cache: DNSCache) -> None:
        """Initialize DNS resolver."""
        self.hostname = hostname
        self._cache = None
        self._resolver = None
    
    async def initialize(self) -> None:
        """Initialize resolver asynchronously."""
        loop = asyncio.get_event_loop()
        self._resolver = await loop.run_in_executor(None, dns.resolver.Resolver)
    
    async def resolve(self) -> Optional[str]:
        """Resolve IP using system DNS."""
        if self._resolver is None:
            await self.initialize()

        loop = asyncio.get_event_loop()
        try:
            # Always do fresh DNS lookup
            return await loop.run_in_executor(None, socket.gethostbyname, self.hostname)
        except socket.gaierror:
            return None

class IPifyResolver(IPResolverStrategy):
    """ipify.org-based IP resolver."""
    
    async def initialize(self) -> None:
        """Nothing to initialize."""
        pass
    
    async def resolve(self) -> Optional[str]:
        """Resolve IP using ipify.org."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.ipify.org', timeout=10) as response:
                    if response.status == 200:
                        return (await response.text()).strip()
        except Exception:
            return None
        return None

class IPResolver:
    """IP resolution service with fallback support."""
    
    def __init__(self, hostname: str) -> None:
        """Initialize with all strategies for given hostname."""
        self._cache = DNSCache()
        self.strategies = [
            AuthoritativeDNSResolver(hostname, self._cache),
            DNSResolver(hostname, self._cache),
            IPifyResolver()
        ]
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure all strategies are initialized."""
        if not self._initialized:
            await asyncio.gather(*(
                strategy.initialize() for strategy in self.strategies
            ))
            self._initialized = True
    
    async def get_ip(self) -> Optional[str]:
        """Try each strategy in order until one succeeds."""
        await self._ensure_initialized()
        
        last_error = None
        for strategy in self.strategies:
            try:
                if ip := await strategy.resolve():
                    return ip
            except ResolutionError as err:
                last_error = err
                continue
        if last_error:
            raise ResolutionError(f"All resolution strategies failed: {last_error}")
        return None

    async def get_current_ip(self) -> Optional[str]:
        """Get current public IP."""
        await self._ensure_initialized()
        return await self.strategies[-1].resolve()  # Use IPify 