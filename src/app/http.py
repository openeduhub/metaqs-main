from typing import Union

from httpx import AsyncClient, Timeout

from app.core.logging import logger

_client: Union[AsyncClient, None] = None


async def get_client():
    global _client
    if not _client:
        logger.debug("httpx: Opening client")
        _client = AsyncClient(
            timeout=Timeout(connect=10.0, read=30.0, write=30.0, pool=5.0)
        )
        logger.debug("httpx: Opened client")
    return _client


async def close_client():
    global _client
    if _client:
        logger.debug("httpx: Closing client")
        await _client.aclose()
        logger.debug("httpx: Closed client")
