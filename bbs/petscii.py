"""PETSCII encoding/decoding utilities for C64 compatibility."""
from typing import Dict, Optional


# PETSCII to Unicode mapping (screen codes)
# Based on C64 character ROM
PETSCII_TO_UNICODE: Dict[int, str] = {
    # Control characters (0x00-0x1F)
    0x00: '\u0000',  # @ (null)
    0x01: 'A',
    0x02: 'B',
    0x03: 'C',
    0x04: 'D',
    0x05: 'E',
    0x06: 'F',
    0x07: 'G',
    0x08: 'H',
    0x09: 'I',
    0x0A: 'J',
    0x0B: 'K',
    0x0C: 'L',
    0x0D: '\r',  # Return
    0x0E: 'N',
    0x0F: 'O',
    0x10: 'P',
    0x11: 'Q',
    0x12: 'R',
    0x13: 'S',
    0x14: 'T',
    0x15: 'U',
    0x16: 'V',
    0x17: 'W',
    0x18: 'X',
    0x19: 'Y',
    0x1A: 'Z',
    0x1B: '[',  # ESC
    0x1C: '\\',
    0x1D: ']',
    0x1E: '^',
    0x1F: '_',
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
    # Graphics and special characters (0x60-0xFF)
    # Note: This is a simplified mapping. Full PETSCII includes
    # graphics characters, reverse video, etc.
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
    # Extended graphics (0x80-0xFF)
    # These are graphics characters unique to PETSCII
    # For now, we'll map common ones
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
    # Add more mappings as needed
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

