# Station-64 BBS

A modern BBS (Bulletin Board System) built in Python for the Commodore 64 and the retro computing community. This BBS provides both telnet access for authentic C64 hardware and a web-based terminal emulator for modern browsers.

## Features

- **Async Telnet Server**: Handles multiple concurrent C64 connections via Telnet
- **Web Terminal Emulator**: Browser-based terminal that emulates a C64 session
- **PETSCII Support**: Full PETSCII character set encoding/decoding
- **Extensible Architecture**: Modular design for easy feature additions
- **Docker Deployment**: Complete containerized setup with PostgreSQL

## Architecture

The system consists of three main components:

1. **Async Telnet Server** (`bbs/server.py`) - Handles C64 hardware connections
2. **FastAPI Web Server** (`bbs/web.py`) - Provides web UI with WebSocket terminal
3. **Shared BBS Core** (`bbs/core.py`) - Common logic for both connection types

Both servers share the same BBS session logic, ensuring a consistent experience whether connecting via C64 hardware or web browser.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Running with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd station-64
```

2. Create a `.env` file (copy from `.env.example` if needed):
```bash
DATABASE_URL=postgresql+asyncpg://bbs_user:bbs_password@postgres:5432/bbs_db
TELNET_HOST=0.0.0.0
TELNET_PORT=23
WEB_HOST=0.0.0.0
WEB_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

3. Start the services:
```bash
docker-compose up -d
```

4. Access the BBS:
   - **Web UI**: http://localhost:8000
   - **Telnet**: `telnet localhost 6400` (or use your C64 with a WiFi modem on port 6400)

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database (or use Docker):
```bash
docker-compose up -d postgres
```

3. Set environment variables (see `.env.example`)

4. Run the servers:
```bash
python -m bbs.main
```

Or run separately:
```bash
# Terminal 1: Telnet server
python -m bbs.server

# Terminal 2: Web server
python -m bbs.web
```

## Project Structure

```
station-64/
├── bbs/                  # BBS application code
│   ├── __init__.py
│   ├── main.py          # Main entry point (runs both servers)
│   ├── server.py        # Async telnet server
│   ├── web.py           # FastAPI web server
│   ├── core.py          # Core BBS logic (sessions, menus)
│   ├── petscii.py       # PETSCII encoding/decoding
│   ├── database.py      # Database models
│   └── config.py        # Configuration management
├── web/
│   └── static/          # Web UI files
│       ├── index.html   # Main web interface
│       ├── style.css    # Terminal styling
│       └── terminal.js  # WebSocket terminal client
├── docker/
│   └── Dockerfile       # Application container
├── docker-compose.yml   # Multi-container setup
├── requirements.txt     # Python dependencies
└── README.md
```

## Usage

### Connecting with a C64

1. Configure your C64 with a WiFi modem (e.g., WiModem232)
2. Set the modem to connect via Telnet
3. Connect to your BBS server on port 23
4. You'll see the PETSCII character set display and main menu

### Using the Web Interface

1. Open http://localhost:8000 in your browser
2. The terminal will automatically connect via WebSocket
3. Use the same commands as the telnet interface

### Available Commands

- `C` - View complete PETSCII character set
- `?` - Show help information
- `Q` - Quit and disconnect

## Configuration

Configuration is managed through environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `TELNET_HOST` - Telnet server bind address (default: 0.0.0.0)
- `TELNET_PORT` - Telnet server port (default: 23)
- `WEB_HOST` - Web server bind address (default: 0.0.0.0)
- `WEB_PORT` - Web server port (default: 8000)
- `DEBUG` - Enable debug mode (default: false)
- `LOG_LEVEL` - Logging level (default: INFO)

## Extending the BBS

The BBS is designed to be easily extensible:

1. **Add New Menus**: Create a class inheriting from `BBSMenu` in `bbs/core.py`
2. **Add Commands**: Register commands in your menu's `commands` dictionary
3. **Add Features**: Extend the `BBSCore` class or create new modules

Example:
```python
from bbs.core import BBSMenu, BBSSession

class MyMenu(BBSMenu):
    def __init__(self):
        super().__init__("mymenu", "My Custom Menu")
        self.commands = {
            "X": self.my_command,
        }
    
    async def my_command(self, session: BBSSession, cmd: str) -> str:
        return "Hello from my command!\n"
```

## Development

### Database Migrations

The project uses SQLAlchemy with async support. For database migrations, consider using Alembic (included in requirements).

### Testing

Run the servers locally for testing:
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Run BBS
python -m bbs.main
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! This is an open project for the Commodore 64 and retro computing community.

## Future Features

- User authentication and registration
- Message boards
- File downloads/uploads
- Door games
- Multi-node support
- ANSI/PETSCII art support
- And much more!
