"""PETSCII encoding/decoding utilities for C64 compatibility.

Reference: Official C64 PETSCII table - https://sta.c64.org/cbm64pet.html

Key points:
- Codes $00-$1F and $80-$9F are control codes (not printable characters)
- Code $93 (147 decimal) is the Clear screen command
- Codes $60-$7F and $E0-$FE are not used (they're copies of other ranges)
- Code $FF is the BASIC token for π (pi)
"""
from typing import Dict, Optional


# PETSCII to Unicode mapping (screen codes)
# Based on official C64 PETSCII table: https://sta.c64.org/cbm64pet.html
# Codes $00-$1F and $80-$9F are control codes (not printable characters)
PETSCII_TO_UNICODE: Dict[int, str] = {
    # Control characters (0x00-0x1F) - Control codes, not printable
    0x00: '\u0000',  # Null
    0x01: ' ',  # (control code)
    0x02: ' ',  # (control code)
    0x03: ' ',  # Stop
    0x04: ' ',  # (control code)
    0x05: ' ',  # White (color code)
    0x06: ' ',  # (control code)
    0x07: ' ',  # (control code)
    0x08: ' ',  # Disable C=-Shift
    0x09: ' ',  # Enable C=-Shift
    0x0A: ' ',  # (control code)
    0x0B: ' ',  # (control code)
    0x0C: ' ',  # (control code)
    0x0D: '\r',  # Return
    0x0E: ' ',  # lo/up charset
    0x0F: ' ',  # (control code)
    0x10: ' ',  # (control code)
    0x11: ' ',  # Cursor down
    0x12: ' ',  # Reverse on
    0x13: ' ',  # Home
    0x14: ' ',  # Delete
    0x15: ' ',  # (control code)
    0x16: ' ',  # (control code)
    0x17: ' ',  # (control code)
    0x18: ' ',  # (control code)
    0x19: ' ',  # (control code)
    0x1A: ' ',  # (control code)
    0x1B: '[',  # ESC / [
    0x1C: ' ',  # Red (color code)
    0x1D: ' ',  # Cursor right
    0x1E: ' ',  # Green (color code)
    0x1F: ' ',  # Blue (color code)
    # Printable characters (0x20-0x5F)
    0x20: ' ',
    0x21: '!',
    0x22: '"',
    0x23: '#',
    0x24: '$',
    0x25: '%',
    0x26: '&',
    0x27: "'",
    0x28: '(',
    0x29: ')',
    0x2A: '*',
    0x2B: '+',
    0x2C: ',',
    0x2D: '-',
    0x2E: '.',
    0x2F: '/',
    0x30: '0',
    0x31: '1',
    0x32: '2',
    0x33: '3',
    0x34: '4',
    0x35: '5',
    0x36: '6',
    0x37: '7',
    0x38: '8',
    0x39: '9',
    0x3A: ':',
    0x3B: ';',
    0x3C: '<',
    0x3D: '=',
    0x3E: '>',
    0x3F: '?',
    0x40: '@',
    0x41: 'A',
    0x42: 'B',
    0x43: 'C',
    0x44: 'D',
    0x45: 'E',
    0x46: 'F',
    0x47: 'G',
    0x48: 'H',
    0x49: 'I',
    0x4A: 'J',
    0x4B: 'K',
    0x4C: 'L',
    0x4D: 'M',
    0x4E: 'N',
    0x4F: 'O',
    0x50: 'P',
    0x51: 'Q',
    0x52: 'R',
    0x53: 'S',
    0x54: 'T',
    0x55: 'U',
    0x56: 'V',
    0x57: 'W',
    0x58: 'X',
    0x59: 'Y',
    0x5A: 'Z',
    0x5B: '[',
    0x5C: '\\',
    0x5D: ']',
    0x5E: '^',
    0x5F: '_',
    # Lowercase and graphics (0x60-0x7F)
    0x60: '`',
    0x61: 'a',
    0x62: 'b',
    0x63: 'c',
    0x64: 'd',
    0x65: 'e',
    0x66: 'f',
    0x67: 'g',
    0x68: 'h',
    0x69: 'i',
    0x6A: 'j',
    0x6B: 'k',
    0x6C: 'l',
    0x6D: 'm',
    0x6E: 'n',
    0x6F: 'o',
    0x70: 'p',
    0x71: 'q',
    0x72: 'r',
    0x73: 's',
    0x74: 't',
    0x75: 'u',
    0x76: 'v',
    0x77: 'w',
    0x78: 'x',
    0x79: 'y',
    0x7A: 'z',
    0x7B: '{',
    0x7C: '|',
    0x7D: '}',
    0x7E: '~',
    0x7F: '\u007F',  # DEL
    # Control codes (0x80-0x9F) - Control codes, not printable
    # Reference: https://sta.c64.org/cbm64pet.html
    0x80: ' ',  # (control code)
    0x81: ' ',  # Orange (color code)
    0x82: ' ',  # (control code)
    0x83: ' ',  # Run
    0x84: ' ',  # (control code)
    0x85: ' ',  # F1
    0x86: ' ',  # F3
    0x87: ' ',  # F5
    0x88: ' ',  # F7
    0x89: ' ',  # F2
    0x8A: ' ',  # F4
    0x8B: ' ',  # F6
    0x8C: ' ',  # F8
    0x8D: ' ',  # Shift-Return
    0x8E: ' ',  # up/gfx charset
    0x8F: ' ',  # (control code)
    0x90: ' ',  # Black (color code)
    0x91: ' ',  # Cursor up
    0x92: ' ',  # Reverse off
    0x93: ' ',  # Clear (screen clear) - CRITICAL CODE!
    0x94: ' ',  # Insert
    0x95: ' ',  # Brown (color code)
    0x96: ' ',  # Pink (color code)
    0x97: ' ',  # Dark grey (color code)
    0x98: ' ',  # Grey (color code)
    0x99: ' ',  # Light green (color code)
    0x9A: ' ',  # Light blue (color code)
    0x9B: ' ',  # Light grey (color code)
    0x9C: ' ',  # Purple (color code)
    0x9D: ' ',  # Cursor left
    0x9E: ' ',  # Yellow (color code)
    0x9F: ' ',  # Cyan (color code)
    # Full block and solid graphics
    0xA0: '\u2588',  # Full block (solid square)
    0xA1: '\u258C',  # Left half block
    0xA2: '\u2584',  # Lower half block
    0xA3: '\u2580',  # Upper half block
    0xA4: '\u2588',  # Full block
    0xA5: '\u2588',  # Full block
    0xA6: '\u2588',  # Full block
    0xA7: '\u2588',  # Full block
    0xA8: '\u2588',  # Full block
    0xA9: '\u2588',  # Full block
    0xAA: '\u2588',  # Full block
    0xAB: '\u2588',  # Full block
    0xAC: '\u2588',  # Full block
    0xAD: '\u2588',  # Full block
    0xAE: '\u2588',  # Full block
    0xAF: '\u2588',  # Full block
    # Right half block and quarter blocks
    0xB0: '\u2590',  # Right half block
    0xB1: '\u258C',  # Left half block
    0xB2: '\u2584',  # Lower half block
    0xB3: '\u2580',  # Upper half block
    0xB4: '\u2588',  # Full block
    0xB5: '\u2588',  # Full block
    0xB6: '\u2588',  # Full block
    0xB7: '\u2588',  # Full block
    0xB8: '\u2588',  # Full block
    0xB9: '\u2588',  # Full block
    0xBA: '\u2588',  # Full block
    0xBB: '\u2588',  # Full block
    0xBC: '\u2588',  # Full block
    0xBD: '\u2588',  # Full block
    0xBE: '\u2588',  # Full block
    0xBF: '\u2588',  # Full block
    # More graphics characters (0xC0-0xFE)
    # Note: Codes $E0-$FE are copies of $C0-$DE (not used per official table)
    0xC0: '\u2591',  # Light shade
    0xC1: '\u2592',  # Medium shade
    0xC2: '\u2593',  # Dark shade
    0xC3: '\u2588',  # Full block
    0xC4: '\u2500',  # Box drawing horizontal
    0xC5: '\u2502',  # Box drawing vertical
    0xC6: '\u250C',  # Box drawing top-left corner
    0xC7: '\u2510',  # Box drawing top-right corner
    0xC8: '\u2514',  # Box drawing bottom-left corner
    0xC9: '\u2518',  # Box drawing bottom-right corner
    0xCA: '\u251C',  # Box drawing left T
    0xCB: '\u2524',  # Box drawing right T
    0xCC: '\u252C',  # Box drawing top T
    0xCD: '\u2534',  # Box drawing bottom T
    0xCE: '\u253C',  # Box drawing cross
    0xCF: '\u2588',  # Full block
    0xD0: '\u2588',  # Full block
    0xD1: '\u2588',  # Full block
    0xD2: '\u2588',  # Full block
    0xD3: '\u2588',  # Full block
    0xD4: '\u2588',  # Full block
    0xD5: '\u2588',  # Full block
    0xD6: '\u2588',  # Full block
    0xD7: '\u2588',  # Full block
    0xD8: '\u2588',  # Full block
    0xD9: '\u2588',  # Full block
    0xDA: '\u2588',  # Full block
    0xDB: '\u2588',  # Full block
    0xDC: '\u2588',  # Full block
    0xDD: '\u2588',  # Full block
    0xDE: '\u2588',  # Full block
    0xDF: '\u2588',  # Full block
    0xE0: '\u2588',  # Full block
    0xE1: '\u2588',  # Full block
    0xE2: '\u2588',  # Full block
    0xE3: '\u2588',  # Full block
    0xE4: '\u2588',  # Full block
    0xE5: '\u2588',  # Full block
    0xE6: '\u2588',  # Full block
    0xE7: '\u2588',  # Full block
    0xE8: '\u2588',  # Full block
    0xE9: '\u2588',  # Full block
    0xEA: '\u2588',  # Full block
    0xEB: '\u2588',  # Full block
    0xEC: '\u2588',  # Full block
    0xED: '\u2588',  # Full block
    0xEE: '\u2588',  # Full block
    0xEF: '\u2588',  # Full block
    0xF0: '\u2588',  # Full block
    0xF1: '\u2588',  # Full block
    0xF2: '\u2588',  # Full block
    0xF3: '\u2588',  # Full block
    0xF4: '\u2588',  # Full block
    0xF5: '\u2588',  # Full block
    0xF6: '\u2588',  # Full block
    0xF7: '\u2588',  # Full block
    0xF8: '\u2588',  # Full block
    0xF9: '\u2588',  # Full block
    0xFA: '\u2588',  # Full block
    0xFB: '\u2588',  # Full block
    0xFC: '\u2588',  # Full block
    0xFD: '\u2588',  # Full block
    0xFE: '\u2588',  # Full block
    0xFF: '\u03C0',  # π (pi) - BASIC token, converts to $DE when printed
}

# Unicode to PETSCII reverse mapping
UNICODE_TO_PETSCII: Dict[str, int] = {v: k for k, v in PETSCII_TO_UNICODE.items() if v}


def petscii_to_unicode(byte: int) -> str:
    """Convert a PETSCII byte to Unicode character."""
    return PETSCII_TO_UNICODE.get(byte, chr(byte))


def unicode_to_petscii(char: str) -> int:
    """Convert a Unicode character to PETSCII byte."""
    if len(char) != 1:
        return ord('?')
    return UNICODE_TO_PETSCII.get(char, ord(char) if ord(char) < 256 else ord('?'))


def decode_petscii(data: bytes) -> str:
    """Decode PETSCII bytes to Unicode string."""
    return ''.join(petscii_to_unicode(b) for b in data)


def encode_petscii(text: str) -> bytes:
    """Encode Unicode string to PETSCII bytes."""
    return bytes(unicode_to_petscii(c) for c in text)


def generate_petscii_charset_display() -> str:
    """Generate a display showing the complete PETSCII character set."""
    lines = []
    lines.append("PETSCII CHARACTER SET")
    lines.append("=" * 40)
    lines.append("")
    
    # Display characters in rows
    for row_start in range(0, 256, 16):
        row_chars = []
        row_hex = []
        for i in range(16):
            byte_val = row_start + i
            char = petscii_to_unicode(byte_val)
            # Replace control characters with visible representation
            if ord(char) < 32 and char != '\r' and char != '\n':
                char = f"\\x{byte_val:02X}"
            row_chars.append(char if len(char) == 1 else '?')
            row_hex.append(f"{byte_val:02X}")
        
        lines.append(f"0x{row_start:02X}-0x{row_start+15:02X}: {' '.join(row_chars)}")
        lines.append(f"         Hex: {' '.join(row_hex)}")
        lines.append("")
    
    return '\n'.join(lines)


def generate_petscii_charset_simple() -> str:
    """Generate a simpler display of PETSCII characters (printable only)."""
    lines = []
    lines.append("PETSCII CHARACTER SET")
    lines.append("=" * 40)
    lines.append("")
    
    # Show printable characters in a grid
    for row_start in range(32, 256, 16):
        row = []
        for i in range(16):
            byte_val = row_start + i
            if byte_val < 256:
                char = petscii_to_unicode(byte_val)
                # Only show printable characters
                if 32 <= ord(char) < 127 or char in ['\u2588', '\u258C', '\u2584', '\u2580']:
                    row.append(char)
                else:
                    row.append('.')
        if any(c != '.' for c in row):
            lines.append(f"0x{row_start:02X}: {' '.join(row)}")
    
    return '\n'.join(lines)


# PETSCII Graphics Character Constants
PETSCII_BLOCK = '\u2588'  # Full block (0xA0)
PETSCII_LEFT_HALF = '\u258C'  # Left half block (0xA1)
PETSCII_LOWER_HALF = '\u2584'  # Lower half block (0xA2)
PETSCII_UPPER_HALF = '\u2580'  # Upper half block (0xA3)
PETSCII_RIGHT_HALF = '\u2590'  # Right half block (0xB0)
PETSCII_LIGHT_SHADE = '\u2591'  # Light shade (0xC0)
PETSCII_MEDIUM_SHADE = '\u2592'  # Medium shade (0xC1)
PETSCII_DARK_SHADE = '\u2593'  # Dark shade (0xC2)

# Box drawing characters
PETSCII_HLINE = '\u2500'  # Horizontal line (0xC4)
PETSCII_VLINE = '\u2502'  # Vertical line (0xC5)
PETSCII_TL_CORNER = '\u250C'  # Top-left corner (0xC6)
PETSCII_TR_CORNER = '\u2510'  # Top-right corner (0xC7)
PETSCII_BL_CORNER = '\u2514'  # Bottom-left corner (0xC8)
PETSCII_BR_CORNER = '\u2518'  # Bottom-right corner (0xC9)
PETSCII_LEFT_T = '\u251C'  # Left T (0xCA)
PETSCII_RIGHT_T = '\u2524'  # Right T (0xCB)
PETSCII_TOP_T = '\u252C'  # Top T (0xCC)
PETSCII_BOTTOM_T = '\u2534'  # Bottom T (0xCD)
PETSCII_CROSS = '\u253C'  # Cross (0xCE)


def get_petscii_char(byte_val: int) -> str:
    """Get PETSCII character by byte value."""
    return petscii_to_unicode(byte_val)


def create_box(width: int, height: int, double: bool = False) -> str:
    """Create a box using PETSCII box drawing characters."""
    if double:
        hline = '\u2550'  # Double horizontal
        vline = '\u2551'  # Double vertical
        tl = '\u2554'  # Double top-left
        tr = '\u2557'  # Double top-right
        bl = '\u255A'  # Double bottom-left
        br = '\u255D'  # Double bottom-right
    else:
        hline = PETSCII_HLINE
        vline = PETSCII_VLINE
        tl = PETSCII_TL_CORNER
        tr = PETSCII_TR_CORNER
        bl = PETSCII_BL_CORNER
        br = PETSCII_BR_CORNER
    
    lines = []
    # Top border
    lines.append(tl + hline * (width - 2) + tr)
    # Middle lines
    for _ in range(height - 2):
        lines.append(vline + ' ' * (width - 2) + vline)
    # Bottom border
    if height > 1:
        lines.append(bl + hline * (width - 2) + br)
    
    return '\n'.join(lines)

