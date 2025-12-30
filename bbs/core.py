"""Core BBS logic - sessions, menus, and screen rendering."""
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, Callable, Any, Awaitable, Tuple, List
from enum import Enum

from bbs.petscii import encode_petscii, decode_petscii, generate_petscii_charset_simple
from bbs.screen import (
    clear_screen, set_color, reset_color, C64Color, 
    center_text, create_header, create_status_bar, highlight_command_letter
)


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
        # Pagination state
        self.pagination_lines: Optional[List[str]] = None
        self.pagination_current_page: int = 0
        self.pagination_lines_per_page: int = 20  # C64 screen is 25 lines, leave room for prompt
        
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


def paginate_text(text: str, lines_per_page: int = 20) -> List[str]:
    """Split text into pages for pagination."""
    lines = text.split('\n')
    pages = []
    current_page = []
    
    for line in lines:
        current_page.append(line)
        if len(current_page) >= lines_per_page:
            pages.append('\n'.join(current_page))
            current_page = []
    
    if current_page:
        pages.append('\n'.join(current_page))
    
    return pages if pages else ['']


def format_pagination_page(content: str, current_page: int, total_pages: int, 
                          connection_type: ConnectionType) -> str:
    """Format a paginated page with navigation info."""
    result = [content]
    result.append("")
    result.append(f"Page {current_page + 1} of {total_pages}")
    if current_page < total_pages - 1:
        result.append("Press RETURN for next page, Q to quit")
    else:
        result.append("Press RETURN to continue")
    return '\n'.join(result)


class BBSMenu:
    """Base class for BBS menus."""
    
    def __init__(self, name: str, title: str):
        self.name = name
        self.title = title
        self.commands: Dict[str, Callable[[BBSSession, str], Awaitable[str]]] = {}
    
    async def display(self, session: BBSSession) -> str:
        """Display the menu screen."""
        # Clear screen and show menu
        output = clear_screen(session.connection_type)
        output += f"{self.title}\n" + "=" * 40 + "\n\n"
        return output
    
    async def handle_input(self, session: BBSSession, input_text: str) -> str:
        """Handle user input for this menu."""
        input_text = input_text.strip().upper()
        
        # Handle pagination
        if session.pagination_lines is not None:
            if input_text == "" or input_text == "\r":
                # Next page
                session.pagination_current_page += 1
                if session.pagination_current_page >= len(session.pagination_lines):
                    # Done with pagination
                    session.pagination_lines = None
                    session.pagination_current_page = 0
                    session.waiting_for_continue = False
                    return await self.display(session)
                else:
                    # Show next page
                    total_pages = len(session.pagination_lines)
                    page_content = session.pagination_lines[session.pagination_current_page]
                    return format_pagination_page(page_content, session.pagination_current_page, 
                                                 total_pages, session.connection_type)
            elif input_text == "Q":
                # Quit pagination
                session.pagination_lines = None
                session.pagination_current_page = 0
                session.waiting_for_continue = False
                return await self.display(session)
            else:
                # User entered something else - treat as command
                session.pagination_lines = None
                session.pagination_current_page = 0
        
        # Try exact match first
        if input_text in self.commands:
            return await self.commands[input_text](session, input_text)
        
        # Try common aliases
        aliases = {
            "QUIT": "Q",
            "EXIT": "Q",
            "HELP": "?",
            "H": "?",
            "LOGIN": "L",
            "REGISTER": "R",
            "GUEST": "G",
            "CHARSET": "C",
            "CHAR": "C",
        }
        
        if input_text in aliases and aliases[input_text] in self.commands:
            return await self.commands[aliases[input_text]](session, aliases[input_text])
        
        # Better error message with helpful hint
        output = set_color(session.connection_type, C64Color.RED)
        output += "\nInvalid command: "
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.YELLOW)
        output += f"'{input_text}'\n"
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.WHITE)
        output += "Type "
        output += set_color(session.connection_type, C64Color.YELLOW)
        output += "?"
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.WHITE)
        output += " for help or try a command from the menu above.\n"
        output += reset_color(session.connection_type)
        return output


class FrontPageMenu(BBSMenu):
    """Front page menu with login/registration."""
    
    def __init__(self):
        super().__init__("frontpage", "STATION-64 BBS")
        self.commands = {
            "L": self.login,
            "R": self.register,
            "G": self.guest,
            "?": self.show_help,
        }
    
    async def display(self, session: BBSSession) -> str:
        """Display front page with PETSCII graphics."""
        from bbs.petscii import (
            PETSCII_BLOCK, PETSCII_HLINE, PETSCII_VLINE,
            PETSCII_TL_CORNER, PETSCII_TR_CORNER,
            PETSCII_BL_CORNER, PETSCII_BR_CORNER
        )
        
        output = clear_screen(session.connection_type)
        output += set_color(session.connection_type, C64Color.CYAN)
        
        # Clean PETSCII art banner - no meta labels, just pure retro art
        # Box with PETSCII block graphics and system status
        box_width = 38
        hline = PETSCII_HLINE * (box_width - 2)
        top_line = PETSCII_TL_CORNER + hline + PETSCII_TR_CORNER
        bottom_line = PETSCII_BL_CORNER + hline + PETSCII_BR_CORNER
        side_line = PETSCII_VLINE + " " * (box_width - 2) + PETSCII_VLINE
        
        # PETSCII block art - decorative pattern using block characters
        # Simple, clean design that fits C64 aesthetic
        banner_lines = [
            "",  # Empty line for spacing
            center_text(top_line, 40),
            center_text(side_line, 40),
            # Decorative PETSCII block pattern
            center_text(PETSCII_VLINE + " " * 4 + PETSCII_BLOCK * 6 + " " + PETSCII_BLOCK * 6 + " " + PETSCII_BLOCK * 6 + " " + PETSCII_BLOCK * 6 + " " * 5 + PETSCII_VLINE, 40),
            center_text(PETSCII_VLINE + " " * 4 + PETSCII_BLOCK + " " * 4 + PETSCII_BLOCK + " " + PETSCII_BLOCK + " " * 4 + PETSCII_BLOCK + " " + PETSCII_BLOCK + " " * 4 + PETSCII_BLOCK + " " + PETSCII_BLOCK + " " * 4 + PETSCII_BLOCK + " " * 5 + PETSCII_VLINE, 40),
            center_text(PETSCII_VLINE + " " * 4 + PETSCII_BLOCK * 6 + " " + PETSCII_BLOCK * 6 + " " + PETSCII_BLOCK * 6 + " " + PETSCII_BLOCK * 6 + " " * 5 + PETSCII_VLINE, 40),
            center_text(side_line, 40),
            # System identification - clean, diegetic text only
            center_text(PETSCII_VLINE + " " * 4 + "STATION-64 :: NODE ONLINE" + " " * 7 + PETSCII_VLINE, 40),
            center_text(side_line, 40),
            center_text(bottom_line, 40),
            "",  # Empty line for spacing
        ]
        
        output += '\n'.join(banner_lines)
        output += reset_color(session.connection_type)
        
        output += set_color(session.connection_type, C64Color.GREEN)
        output += center_text("Welcome to Station-64!", 40) + "\n"
        output += center_text("Modern BBS for Commodore 64", 40) + "\n\n"
        output += reset_color(session.connection_type)
        
        output += set_color(session.connection_type, C64Color.YELLOW)
        output += create_header("MAIN MENU", 40, "=") + "\n\n"
        output += reset_color(session.connection_type)
        
        # Commands with color-highlighted letters (like classic BBSes but better organized)
        output += set_color(session.connection_type, C64Color.WHITE)
        output += "  "
        output += set_color(session.connection_type, C64Color.GREEN)
        output += "L"
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.WHITE)
        output += " - Login to your account\n"
        
        output += "  "
        output += set_color(session.connection_type, C64Color.GREEN)
        output += "R"
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.WHITE)
        output += " - Register new account\n"
        
        output += "  "
        output += set_color(session.connection_type, C64Color.GREEN)
        output += "G"
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.WHITE)
        output += " - Enter as guest\n"
        
        output += "  "
        output += set_color(session.connection_type, C64Color.YELLOW)
        output += "?"
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.WHITE)
        output += " - Help (always available)\n"
        output += "\n"
        output += reset_color(session.connection_type)
        
        # Prompt with helpful hint
        output += set_color(session.connection_type, C64Color.CYAN)
        output += "Enter command"
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.GREY)
        output += " (or ? for help)"
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.CYAN)
        output += ": "
        output += reset_color(session.connection_type)
        
        return output
    
    async def login(self, session: BBSSession, cmd: str) -> str:
        """Handle login command."""
        session.waiting_for_continue = True
        output = set_color(session.connection_type, C64Color.YELLOW)
        output += "\n" + create_header("LOGIN", 40) + "\n\n"
        output += reset_color(session.connection_type)
        output += "Login functionality coming soon!\n"
        output += "For now, enter as guest (G) to explore.\n\n"
        output += "Press RETURN to continue..."
        return output
    
    async def register(self, session: BBSSession, cmd: str) -> str:
        """Handle registration command."""
        session.waiting_for_continue = True
        output = set_color(session.connection_type, C64Color.YELLOW)
        output += "\n" + create_header("REGISTRATION", 40) + "\n\n"
        output += reset_color(session.connection_type)
        output += "Registration functionality coming soon!\n"
        output += "For now, enter as guest (G) to explore.\n\n"
        output += "Press RETURN to continue..."
        return output
    
    async def guest(self, session: BBSSession, cmd: str) -> str:
        """Enter as guest - go to main menu."""
        session.is_authenticated = False
        session.username = "GUEST"
        session.current_menu = "main"
        return ""  # Will trigger menu display
    
    async def show_help(self, session: BBSSession, cmd: str) -> str:
        """Show help information."""
        session.waiting_for_continue = True
        output = set_color(session.connection_type, C64Color.CYAN)
        output += "\n" + create_header("HELP", 40) + "\n\n"
        output += reset_color(session.connection_type)
        output += "Station-64 BBS Help\n\n"
        output += "Commands:\n"
        output += "  L - Login to your account\n"
        output += "  R - Register a new account\n"
        output += "  G - Enter as guest (no login required)\n"
        output += "  ? - Show this help\n\n"
        output += "Press RETURN to continue..."
        return output


class MainMenu(BBSMenu):
    """Main BBS menu (after login/guest entry)."""
    
    def __init__(self):
        super().__init__("main", "STATION-64 BBS")
        self.commands = {
            "C": self.show_charset,
            "?": self.show_help,
            "Q": self.quit,
        }
    
    async def display(self, session: BBSSession) -> str:
        """Display main menu with PETSCII graphics."""
        from bbs.petscii import (
            PETSCII_BLOCK, PETSCII_HLINE, PETSCII_VLINE,
            PETSCII_TL_CORNER, PETSCII_TR_CORNER,
            PETSCII_BL_CORNER, PETSCII_BR_CORNER
        )
        
        output = clear_screen(session.connection_type)
        output += set_color(session.connection_type, C64Color.GREEN)
        
        # Header with box using PETSCII characters
        box_width = 38
        hline = PETSCII_HLINE * (box_width - 2)
        top_line = PETSCII_TL_CORNER + hline + PETSCII_TR_CORNER
        bottom_line = PETSCII_BL_CORNER + hline + PETSCII_BR_CORNER
        title_line = PETSCII_VLINE + " " * 6 + "STATION-64 BBS MAIN MENU" + " " * 7 + PETSCII_VLINE
        
        header_box = [
            "",
            center_text(top_line, 40),
            center_text(title_line, 40),
            center_text(bottom_line, 40),
            "",
        ]
        output += '\n'.join(header_box)
        output += reset_color(session.connection_type)
        
        # Status bar with user info
        username = session.username or "GUEST"
        status_text = create_status_bar(
            f"User: {username}",
            "Type ? for help",
            width=40,
            connection_type=session.connection_type
        )
        output += set_color(session.connection_type, C64Color.GREY)
        output += status_text + "\n"
        output += reset_color(session.connection_type)
        output += "\n"
        
        # Welcome message
        output += set_color(session.connection_type, C64Color.CYAN)
        output += f"Welcome, {username}!\n\n"
        output += reset_color(session.connection_type)
        
        # Menu options organized in sections with color-highlighted commands
        output += set_color(session.connection_type, C64Color.YELLOW)
        output += create_header("AVAILABLE COMMANDS", 40, "-") + "\n\n"
        output += reset_color(session.connection_type)
        
        # Commands section with highlighted letters
        output += set_color(session.connection_type, C64Color.WHITE)
        output += "  "
        output += set_color(session.connection_type, C64Color.CYAN)
        output += "C"
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.WHITE)
        output += " - View PETSCII Character Set\n"
        
        output += "  "
        output += set_color(session.connection_type, C64Color.YELLOW)
        output += "?"
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.WHITE)
        output += " - Show Help\n"
        
        output += "  "
        output += set_color(session.connection_type, C64Color.RED)
        output += "Q"
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.WHITE)
        output += " - Quit and disconnect\n"
        output += "\n"
        output += reset_color(session.connection_type)
        
        # Helpful prompt
        output += set_color(session.connection_type, C64Color.GREEN)
        output += "Enter command"
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.GREY)
        output += " (or ? for help)"
        output += reset_color(session.connection_type)
        output += set_color(session.connection_type, C64Color.GREEN)
        output += ": "
        output += reset_color(session.connection_type)
        
        return output
    
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
        frontpage_menu = FrontPageMenu()
        self.menus["frontpage"] = frontpage_menu
        main_menu = MainMenu()
        self.menus["main"] = main_menu
    
    def create_session(self, connection_type: ConnectionType, remote_addr: Optional[str] = None) -> BBSSession:
        """Create a new BBS session."""
        session_id = str(uuid.uuid4())
        session = BBSSession(session_id, connection_type, remote_addr)
        session.current_menu = "frontpage"  # Start at front page
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
            session.current_menu = "frontpage"
        
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
            session.current_menu = "frontpage"
        
        menu = self.menus[session.current_menu]
        return await menu.display(session)
    
    def register_menu(self, menu: BBSMenu):
        """Register a new menu (for extensibility)."""
        self.menus[menu.name] = menu


# Global BBS core instance
bbs_core = BBSCore()

