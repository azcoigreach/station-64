"""Core BBS logic - sessions, menus, and screen rendering."""
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, Callable, Any, Awaitable, Tuple
from enum import Enum

from bbs.petscii import encode_petscii, decode_petscii, generate_petscii_charset_simple


class ConnectionType(Enum):
    """Connection type enumeration."""
    TELNET = "telnet"
    WEB = "web"


class BBSSession:
    """Represents a BBS session for a connected user."""
    
    def __init__(self, session_id: str, connection_type: ConnectionType, remote_addr: Optional[str] = None):
        self.session_id = session_id
        self.connection_type = connection_type
        self.remote_addr = remote_addr
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.user_id: Optional[int] = None
        self.username: Optional[str] = None
        self.is_authenticated = False
        self.current_menu: Optional[str] = None
        self.buffer: str = ""
        self._output_queue: asyncio.Queue[str] = asyncio.Queue()
        self._input_buffer: str = ""
        self.waiting_for_continue: bool = False
        self.is_active: bool = True
        
    async def send(self, data: str):
        """Send data to the client (PETSCII encoded)."""
        await self._output_queue.put(data)
    
    async def receive(self) -> Optional[str]:
        """Receive data from the output queue."""
        try:
            return await asyncio.wait_for(self._output_queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()


class BBSMenu:
    """Base class for BBS menus."""
    
    def __init__(self, name: str, title: str):
        self.name = name
        self.title = title
        self.commands: Dict[str, Callable[[BBSSession, str], Awaitable[str]]] = {}
    
    async def display(self, session: BBSSession) -> str:
        """Display the menu screen."""
        return f"{self.title}\n" + "=" * 40 + "\n\n"
    
    async def handle_input(self, session: BBSSession, input_text: str) -> str:
        """Handle user input for this menu."""
        input_text = input_text.strip().upper()
        
        if input_text in self.commands:
            return await self.commands[input_text](session, input_text)
        
        return "Invalid command. Type ? for help.\n"


class MainMenu(BBSMenu):
    """Main BBS menu."""
    
    def __init__(self):
        super().__init__("main", "STATION-64 BBS")
        self.commands = {
            "C": self.show_charset,
            "?": self.show_help,
            "Q": self.quit,
        }
    
    async def display(self, session: BBSSession) -> str:
        """Display main menu."""
        output = []
        output.append("")
        output.append("")
        output.append(" " * 10 + "STATION-64 BBS")
        output.append(" " * 8 + "=" * 24)
        output.append("")
        output.append("Welcome to Station-64!")
        output.append("")
        output.append("Commands:")
        output.append("  C - View PETSCII Character Set")
        output.append("  ? - Show Help")
        output.append("  Q - Quit")
        output.append("")
        output.append("Enter command: ")
        return "\n".join(output)
    
    async def show_charset(self, session: BBSSession, cmd: str) -> str:
        """Show PETSCII character set."""
        session.waiting_for_continue = True
        output = []
        output.append("")
        output.append(generate_petscii_charset_simple())
        output.append("")
        output.append("Press RETURN to return to main menu...")
        output.append("")
        return "\n".join(output)
    
    async def show_help(self, session: BBSSession, cmd: str) -> str:
        """Show help information."""
        session.waiting_for_continue = True
        output = []
        output.append("\n")
        output.append("STATION-64 BBS HELP")
        output.append("=" * 40)
        output.append("")
        output.append("This is a modern BBS for the Commodore 64.")
        output.append("")
        output.append("Available commands:")
        output.append("  C - View complete PETSCII character set")
        output.append("  ? - Show this help message")
        output.append("  Q - Quit and disconnect")
        output.append("")
        output.append("Press RETURN to continue...")
        return "\n".join(output)
    
    async def quit(self, session: BBSSession, cmd: str) -> str:
        """Quit the BBS."""
        return "\n\nThank you for calling Station-64!\n\nGoodbye!\n"


class BBSCore:
    """Core BBS engine managing sessions and menus."""
    
    def __init__(self):
        self.sessions: Dict[str, BBSSession] = {}
        self.menus: Dict[str, BBSMenu] = {}
        self._register_default_menus()
    
    def _register_default_menus(self):
        """Register default menus."""
        main_menu = MainMenu()
        self.menus["main"] = main_menu
    
    def create_session(self, connection_type: ConnectionType, remote_addr: Optional[str] = None) -> BBSSession:
        """Create a new BBS session."""
        session_id = str(uuid.uuid4())
        session = BBSSession(session_id, connection_type, remote_addr)
        session.current_menu = "main"
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[BBSSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def remove_session(self, session_id: str):
        """Remove a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    async def process_input(self, session: BBSSession, input_text: str) -> Tuple[str, bool]:
        """Process user input and return (response, should_show_menu_after).
        
        Returns:
            tuple: (response_string, should_show_menu_after)
            should_show_menu_after is True if menu should be shown after this response,
            False if response already contains the menu or we're waiting for continue.
        """
        session.update_activity()
        
        # If waiting for continue and input is empty/just RETURN, show menu again
        if session.waiting_for_continue:
            if not input_text or input_text.strip() == "":
                session.waiting_for_continue = False
                # Return menu screen and indicate we should NOT show menu again (it's in the response)
                return (await self.get_screen(session), False)
            else:
                # User entered something while waiting for continue - treat as new command
                session.waiting_for_continue = False
        
        if not session.current_menu or session.current_menu not in self.menus:
            session.current_menu = "main"
        
        menu = self.menus[session.current_menu]
        response = await menu.handle_input(session, input_text)
        
        # If quitting, mark session for removal
        if "Goodbye" in response:
            session.is_active = False
        
        # If waiting for continue was set by the command, don't show menu after
        should_show_menu = not session.waiting_for_continue
        return (response, should_show_menu)
    
    async def get_screen(self, session: BBSSession) -> str:
        """Get the current screen for a session."""
        if not session.current_menu or session.current_menu not in self.menus:
            session.current_menu = "main"
        
        menu = self.menus[session.current_menu]
        return await menu.display(session)
    
    def register_menu(self, menu: BBSMenu):
        """Register a new menu (for extensibility)."""
        self.menus[menu.name] = menu


# Global BBS core instance
bbs_core = BBSCore()

