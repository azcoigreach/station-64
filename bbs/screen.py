"""Screen control utilities for C64 BBS - clear screen, colors, cursor positioning."""
from typing import Optional, Union
from enum import IntEnum

# ConnectionType will be imported locally in functions to avoid circular import


class C64Color(IntEnum):
    """C64 color codes (0-15)."""
    BLACK = 0
    WHITE = 1
    RED = 2
    CYAN = 3
    PURPLE = 4
    GREEN = 5
    BLUE = 6
    YELLOW = 7
    ORANGE = 8
    BROWN = 9
    LIGHT_RED = 10
    DARK_GREY = 11
    GREY = 12
    LIGHT_GREEN = 13
    LIGHT_BLUE = 14
    LIGHT_GREY = 15


# ANSI color mapping for web terminal (approximate C64 colors)
ANSI_COLORS = {
    C64Color.BLACK: '\033[30m',      # Black
    C64Color.WHITE: '\033[37m',       # White
    C64Color.RED: '\033[31m',        # Red
    C64Color.CYAN: '\033[36m',       # Cyan
    C64Color.PURPLE: '\033[35m',     # Magenta (purple)
    C64Color.GREEN: '\033[32m',      # Green
    C64Color.BLUE: '\033[34m',       # Blue
    C64Color.YELLOW: '\033[33m',     # Yellow
    C64Color.ORANGE: '\033[38;5;208m',  # Orange (256-color)
    C64Color.BROWN: '\033[38;5;130m',   # Brown (256-color)
    C64Color.LIGHT_RED: '\033[91m',  # Bright red
    C64Color.DARK_GREY: '\033[90m',  # Dark grey
    C64Color.GREY: '\033[37m',       # Grey
    C64Color.LIGHT_GREEN: '\033[92m', # Bright green
    C64Color.LIGHT_BLUE: '\033[94m',  # Bright blue
    C64Color.LIGHT_GREY: '\033[97m',  # Bright white (light grey)
}

ANSI_RESET = '\033[0m'
ANSI_CLEAR_SCREEN = '\033[2J'  # Clear entire screen
ANSI_CLEAR_LINE = '\033[2K'    # Clear current line
ANSI_CURSOR_HOME = '\033[H'    # Move cursor to home position (0,0)
ANSI_REVERSE = '\033[7m'       # Reverse video
ANSI_BOLD = '\033[1m'          # Bold
ANSI_UNDERLINE = '\033[4m'     # Underline


def clear_screen(connection_type: Union['ConnectionType', str]) -> str:
    """Return clear screen command for the connection type.
    
    Reference: https://sta.c64.org/cbm64pet.html
    PETSCII code $93 (147 decimal) is the Clear screen command.
    """
    # Import locally to avoid circular import
    from bbs.core import ConnectionType
    
    if connection_type == ConnectionType.WEB or (isinstance(connection_type, str) and connection_type == "web"):
        # ANSI escape sequence for web terminal
        return ANSI_CLEAR_SCREEN + ANSI_CURSOR_HOME
    else:
        # For telnet/C64, use C64 clear screen code (CHR$(147))
        # This is PETSCII code 0x93 (Clear) - per official C64 PETSCII table
        return chr(0x93)


def set_color(connection_type: Union['ConnectionType', str], color: C64Color) -> str:
    """Set text color for the connection type."""
    # Import locally to avoid circular import
    from bbs.core import ConnectionType
    
    if connection_type == ConnectionType.WEB or (isinstance(connection_type, str) and connection_type == "web"):
        return ANSI_COLORS.get(color, '')
    else:
        # For C64, color codes are sent as control codes
        # C64 color codes: 0-15 (same as C64Color enum)
        # In PETSCII, colors are set using control codes
        # For telnet, we'll use ANSI codes as fallback since most C64 telnet clients support them
        return ANSI_COLORS.get(color, '')


def reset_color(connection_type: Union['ConnectionType', str]) -> str:
    """Reset color to default."""
    # Import locally to avoid circular import
    from bbs.core import ConnectionType
    
    if connection_type == ConnectionType.WEB or (isinstance(connection_type, str) and connection_type == "web"):
        return ANSI_RESET
    else:
        # For C64, reset to default color (usually white on black)
        return ANSI_RESET


def set_reverse(connection_type: Union['ConnectionType', str], enable: bool = True) -> str:
    """Enable/disable reverse video."""
    # Import locally to avoid circular import
    from bbs.core import ConnectionType
    
    if connection_type == ConnectionType.WEB or (isinstance(connection_type, str) and connection_type == "web"):
        return ANSI_REVERSE if enable else ANSI_RESET
    else:
        # C64 reverse video code
        return ANSI_REVERSE if enable else ANSI_RESET


def set_bold(connection_type: Union['ConnectionType', str], enable: bool = True) -> str:
    """Enable/disable bold text."""
    # Import locally to avoid circular import
    from bbs.core import ConnectionType
    
    if connection_type == ConnectionType.WEB or (isinstance(connection_type, str) and connection_type == "web"):
        return ANSI_BOLD if enable else ANSI_RESET
    else:
        return ANSI_BOLD if enable else ANSI_RESET


def move_cursor(connection_type: Union['ConnectionType', str], row: int, col: int) -> str:
    """Move cursor to specified position (1-based)."""
    # Import locally to avoid circular import
    from bbs.core import ConnectionType
    
    if connection_type == ConnectionType.WEB or (isinstance(connection_type, str) and connection_type == "web"):
        return f'\033[{row};{col}H'
    else:
        # For C64, cursor positioning is more complex
        # Use ANSI as fallback
        return f'\033[{row};{col}H'


def center_text(text: str, width: int = 40) -> str:
    """Center text within a given width (default 40 for C64)."""
    text_len = len(text)
    if text_len >= width:
        return text[:width]
    padding = (width - text_len) // 2
    return ' ' * padding + text


def wrap_text(text: str, width: int = 40) -> str:
    """Wrap text to specified width (default 40 for C64 screen).
    
    Returns text with newlines inserted to respect column limit.
    """
    lines = []
    for line in text.split('\n'):
        if len(line) <= width:
            lines.append(line)
        else:
            # Wrap long lines
            for i in range(0, len(line), width):
                lines.append(line[i:i+width])
    return '\n'.join(lines)


def truncate_line(line: str, width: int = 40) -> str:
    """Truncate a line to specified width (default 40 for C64)."""
    if len(line) <= width:
        return line
    return line[:width]


def create_header(text: str, width: int = 40, char: str = '=') -> str:
    """Create a centered header with border."""
    centered = center_text(text, width)
    border = char * width
    return f"{border}\n{centered}\n{border}"


def create_separator(width: int = 40, char: str = '-') -> str:
    """Create a horizontal separator line."""
    return char * width


def format_screen(content: str, connection_type: Union['ConnectionType', str], 
                  clear: bool = True, color: Optional[C64Color] = None) -> str:
    """Format screen content with optional clearing and coloring."""
    result = []
    
    if clear:
        result.append(clear_screen(connection_type))
    
    if color is not None:
        result.append(set_color(connection_type, color))
    
    result.append(content)
    
    if color is not None:
        result.append(reset_color(connection_type))
    
    return ''.join(result)


def create_status_bar(left_text: str, right_text: str, width: int = 40,
                     connection_type: Union['ConnectionType', str] = None) -> str:
    """Create a status bar with left and right aligned text.
    
    Example: "User: GUEST                    Node: 1"
    """
    # Calculate spacing
    total_used = len(left_text) + len(right_text)
    if total_used >= width:
        # Truncate if too long
        available = width - len(right_text) - 1
        left_text = left_text[:available] if available > 0 else ""
        spacing = " "
    else:
        spacing = " " * (width - total_used)
    
    return left_text + spacing + right_text


def highlight_command_letter(text: str, letter: str, 
                             letter_color: C64Color = C64Color.GREEN,
                             text_color: C64Color = C64Color.WHITE,
                             connection_type: Union['ConnectionType', str] = None) -> str:
    """Highlight a command letter in a menu item.
    
    Example: "L - Login" where L is highlighted in green.
    """
    if letter.upper() not in text.upper():
        return text
    
    # Find the letter (case insensitive)
    text_upper = text.upper()
    letter_upper = letter.upper()
    idx = text_upper.find(letter_upper)
    
    if idx == -1:
        return text
    
    # Build highlighted version
    result = set_color(connection_type, text_color)
    result += text[:idx]
    result += set_color(connection_type, letter_color)
    result += text[idx]
    result += reset_color(connection_type)
    result += set_color(connection_type, text_color)
    result += text[idx + 1:]
    result += reset_color(connection_type)
    
    return result

