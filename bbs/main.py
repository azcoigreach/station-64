"""Main entry point - runs both telnet and web servers."""
import asyncio
import logging
import signal
import sys

from bbs.config import config
from bbs.server import TelnetServer
from bbs.web import app
import uvicorn

logger = logging.getLogger(__name__)


async def run_servers():
    """Run both telnet and web servers concurrently."""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create telnet server
    telnet_server = TelnetServer()
    
    # Start telnet server in background
    telnet_task = asyncio.create_task(telnet_server.start())
    
    # Start web server
    web_config = uvicorn.Config(
        app,
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        log_level=config.LOG_LEVEL.lower()
    )
    web_server = uvicorn.Server(web_config)
    web_task = asyncio.create_task(web_server.serve())
    
    logger.info("Starting Station-64 BBS servers...")
    logger.info(f"Telnet server: {config.TELNET_HOST}:{config.TELNET_PORT}")
    logger.info(f"Web server: http://{config.WEB_HOST}:{config.WEB_PORT}")
    
    try:
        # Run both servers
        await asyncio.gather(telnet_task, web_task, return_exceptions=True)
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        logger.info("Shutting down servers...")
        await telnet_server.stop()
        web_server.should_exit = True


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(run_servers())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)

