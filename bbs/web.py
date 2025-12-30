"""FastAPI web server with WebSocket terminal emulation."""
import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from bbs.config import config
from bbs.core import BBSCore, ConnectionType, bbs_core
from bbs.petscii import decode_petscii, encode_petscii
from bbs.database import init_db

logger = logging.getLogger(__name__)

app = FastAPI(title="Station-64 BBS", version="0.1.0")
bbs = bbs_core

# Get the base directory (parent of bbs directory)
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "web" / "static"

# Mount static files (will be set up in startup if directory exists)
static_mounted = False


@app.on_event("startup")
async def startup_event():
    """Initialize database and static files on startup."""
    # Mount static files if directory exists
    global static_mounted
    if STATIC_DIR.exists() and not static_mounted:
        try:
            app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
            static_mounted = True
            logger.info(f"Static files mounted from {STATIC_DIR}")
        except Exception as e:
            logger.warning(f"Could not mount static files: {e}")
    else:
        logger.warning(f"Static directory not found at {STATIC_DIR}")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web UI."""
    try:
        index_file = STATIC_DIR / "index.html"
        if not index_file.exists():
            logger.error(f"index.html not found at {index_file}")
            return HTMLResponse(
                content=f"<h1>Station-64 BBS</h1><p>Web UI files not found at {index_file}. Please check installation.</p>",
                status_code=404
            )
        
        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error serving index.html: {e}", exc_info=True)
        return HTMLResponse(
            content=f"<h1>Station-64 BBS</h1><p>Error loading web UI: {e}</p>",
            status_code=500
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for terminal emulation."""
    await websocket.accept()
    
    remote_addr = websocket.client.host if websocket.client else "unknown"
    logger.info(f"New WebSocket connection from {remote_addr}")
    
    # Create BBS session
    session = bbs.create_session(ConnectionType.WEB, remote_addr)
    
    try:
        # Send initial screen
        initial_screen = await bbs.get_screen(session)
        await websocket.send_text(initial_screen)
        
        while True:
            try:
                # Receive input from client
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                
                if data:
                    # Remove line endings but keep the content
                    line = data.rstrip('\r\n')
                    line_stripped = line.strip()
                    
                    # Echo non-empty input
                    if line_stripped:
                        await websocket.send_text(f"\n{line}\n")
                    
                    # Process the command (always process, even if empty - needed for "waiting for continue")
                    response, should_show_menu = await bbs.process_input(session, line_stripped)
                    if response:
                        await websocket.send_text(response)
                    
                    # If quitting, break
                    if not session.is_active:
                        break
                    
                    # Only show menu again if process_input indicates we should (and not quitting)
                    # Commands that display info (like C, ?) set waiting_for_continue=True
                    # so we wait for the user to press RETURN before showing menu again
                    if session.is_active and should_show_menu:
                        screen = await bbs.get_screen(session)
                        await websocket.send_text(screen)
            
            except asyncio.TimeoutError:
                # Just continue waiting for input - don't do anything automatically
                continue
            
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket session: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info(f"WebSocket connection closed: {remote_addr}")
        bbs.remove_session(session.session_id)
        try:
            await websocket.close()
        except:
            pass


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        return {"status": "ok", "service": "station-64-bbs"}
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


async def main():
    """Main entry point for web server."""
    import uvicorn
    
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    uvicorn.run(
        app,
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        log_level=config.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    asyncio.run(main())

