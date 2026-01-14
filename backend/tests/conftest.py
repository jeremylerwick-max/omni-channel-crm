"""
pytest configuration - adds project root to sys.path and configures async fixtures
"""
import sys
from pathlib import Path
import logging
import pytest_asyncio

logger = logging.getLogger(__name__)

# Add the project root to sys.path so tests can import modules
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def cleanup_asyncpg_pool():
    """
    Cleanup asyncpg connection pool after each async test.
    This prevents 'Event loop is closed' errors in pytest-asyncio.
    """
    yield
    try:
        from modules.crm_core import close_pool
        await close_pool()
    except (ImportError, AttributeError):
        return
    except Exception as e:
        logger.exception("cleanup_asyncpg_pool failed", exc_info=e)
        raise
