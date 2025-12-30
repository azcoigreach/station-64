"""Async telnet server for C64 hardware connections."""
import asyncio
import logging
from typing import Optional

from bbs.config import config
from bbs.core import BBSCore, ConnectionType, bbs_core
from bbs.petscii import decode_petscii, encode_petscii

logger = logging.getLogger(__name__)


class TelnetServer:
    """Async telnet server for C64 connections."""
    
    def __init__(self):
        self.host = config.TELNET_HOST
        self.port = config.TELNET_PORT
        self.server: Optional[asyncio.Server] = None
        self.bbs = bbs_core
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a telnet client connection."""
        remote_addr = writer.get_extra_info('peername')
        logger.info(f"New telnet connection from {remote_addr}")
        
        # Create BBS session
        session = self.bbs.create_session(ConnectionType.TELNET, str(remote_addr))
        
        try:
            # Send initial screen
            initial_screen = await self.bbs.get_screen(session)
            writer.write(encode_petscii(initial_screen))
            await writer.drain()
            
            # Input buffer
            input_buffer = b""
            
            while True:
                # Check for input
                try:
                    data = await asyncio.wait_for(reader.read(1024), timeout=0.1)
                    if not data:
                        break
                    
                    input_buffer += data
                    
                    # Filter out telnet protocol negotiation bytes (IAC commands)
                    # IAC is 255 (0xFF). Simple approach: skip IAC and next byte(s)
                    # This handles most telnet negotiation for basic C64 connections
                    filtered_buffer = b""
                    i = 0
                    while i < len(input_buffer):
                        if input_buffer[i] == 0xFF:  # IAC byte
                            # Skip IAC byte
                            i += 1
                            if i < len(input_buffer):
                                cmd = input_buffer[i]
                                i += 1  # Skip command byte
                                # If SB (subnegotiation), skip until SE
                                if cmd == 0xFA:  # SB
                                    while i < len(input_buffer):
                                        if input_buffer[i] == 0xFF and i + 1 < len(input_buffer) and input_buffer[i+1] == 0xF0:
                                            i += 2  # Skip IAC SE
                                            break
                                        i += 1
                        else:
                            filtered_buffer += bytes([input_buffer[i]])
                            i += 1
                    input_buffer = filtered_buffer
                    
                    # Process complete lines
                    while b'\r' in input_buffer or b'\n' in input_buffer:
                        # Find line ending
                        if b'\r' in input_buffer:
                            line_end = input_buffer.find(b'\r')
                        elif b'\n' in input_buffer:
                            line_end = input_buffer.find(b'\n')
                        else:
                            break
                        
                        # Extract line
                        line_bytes = input_buffer[:line_end]
                        input_buffer = input_buffer[line_end + 1:]
                        
                        # Decode PETSCII to process
                        line_text = decode_petscii(line_bytes).strip()
                        
                        # Process input (always process, even if empty - needed for "waiting for continue")
                        # Echo the input if non-empty (telnet clients usually echo, but we do it for consistency)
                        if line_text:
                            writer.write(encode_petscii(f"{line_text}\r\n"))
                            await writer.drain()
                        
                        response, should_show_menu = await self.bbs.process_input(session, line_text)
                        if response:
                            writer.write(encode_petscii(response))
                            await writer.drain()
                        
                        # If quitting, break
                        if not session.is_active:
                            break
                        
                        # Only show menu again if process_input indicates we should (and not quitting)
                        if session.is_active and should_show_menu:
                            screen = await self.bbs.get_screen(session)
                            writer.write(encode_petscii(screen))
                            await writer.drain()
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error handling input: {e}")
                    break
        
        except Exception as e:
            logger.error(f"Error in telnet session: {e}")
        finally:
            logger.info(f"Telnet connection closed: {remote_addr}")
            self.bbs.remove_session(session.session_id)
            writer.close()
            await writer.wait_closed()
    
    async def start(self):
        """Start the telnet server."""
        try:
            self.server = await asyncio.start_server(
                self.handle_client,
                self.host,
                self.port
            )
            logger.info(f"Telnet server started on {self.host}:{self.port}")
            
            async with self.server:
                await self.server.serve_forever()
        except PermissionError:
            logger.error(f"Permission denied: Cannot bind to port {self.port}. Port 23 requires root privileges.")
            logger.error(f"Consider using a different port (e.g., 2323) or running with appropriate permissions.")
            raise
        except OSError as e:
            logger.error(f"Error starting telnet server: {e}")
            raise
    
    async def stop(self):
        """Stop the telnet server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Telnet server stopped")


async def main():
    """Main entry point for telnet server."""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = TelnetServer()
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down telnet server...")
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())

