// Terminal emulator for Station-64 BBS
class Terminal {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.terminalBody = document.getElementById('terminal-body');
        this.terminalInput = document.getElementById('terminal-input');
        this.status = document.getElementById('status');
        this.inputBuffer = '';
        this.cursorVisible = true;
        
        console.log('Terminal constructor called');
        console.log('Elements found:', {
            terminalBody: !!this.terminalBody,
            terminalInput: !!this.terminalInput,
            status: !!this.status
        });
        
        if (!this.terminalBody || !this.terminalInput || !this.status) {
            console.error('Required terminal elements not found!');
            return;
        }
        
        this.init();
    }
    
    init() {
        // Verify terminal elements exist
        if (!this.terminalBody || !this.terminalInput) {
            console.error('Terminal elements not found!');
            this.updateStatus('disconnected', 'Terminal Error');
            return;
        }
        
        // Check if WebSocket is supported
        if (typeof WebSocket === 'undefined') {
            console.error('WebSocket is not supported in this browser');
            this.updateStatus('disconnected', 'WebSocket Not Supported');
            return;
        }
        
        // Determine WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Use window.location.hostname and window.location.port explicitly
        const host = window.location.host || window.location.hostname + ':' + (window.location.port || (window.location.protocol === 'https:' ? '443' : '80'));
        const wsUrl = `${protocol}//${host}/ws`;
        
        console.log('=== Terminal Initialization ===');
        console.log('Window location href:', window.location.href);
        console.log('Window location host:', window.location.host);
        console.log('Window location hostname:', window.location.hostname);
        console.log('Window location port:', window.location.port);
        console.log('Window location protocol:', window.location.protocol);
        console.log('Calculated WebSocket URL:', wsUrl);
        console.log('WebSocket supported:', typeof WebSocket !== 'undefined');
        
        // Connect WebSocket
        this.connect(wsUrl);
        
        // Setup input handler
        this.terminalInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.terminalInput.addEventListener('input', (e) => this.handleInput(e));
        
        // Focus input
        this.terminalInput.focus();
        
        // Start cursor blink
        this.startCursorBlink();
    }
    
    connect(url) {
        try {
            console.log('=== WebSocket Connection Attempt ===');
            console.log('URL:', url);
            console.log('Window location:', window.location.href);
            console.log('Protocol:', window.location.protocol);
            console.log('Host:', window.location.host);
            console.log('Current readyState before connect:', this.ws ? this.ws.readyState : 'no ws object');
            
            this.updateStatus('connecting', 'Connecting...');
            
            // Close existing connection if any
            if (this.ws) {
                try {
                    console.log('Closing existing WebSocket connection');
                    this.ws.close();
                } catch (e) {
                    console.log('Error closing existing WebSocket:', e);
                }
            }
            
            console.log('Creating new WebSocket object...');
            this.ws = new WebSocket(url);
            console.log('WebSocket object created successfully');
            console.log('Initial readyState:', this.ws.readyState);
            console.log('WebSocket URL property:', this.ws.url);
            
            this.ws.onopen = (event) => {
                this.connected = true;
                this.updateStatus('connected', 'Connected');
                console.log('WebSocket connected successfully!', event);
            };
            
            this.ws.onmessage = (event) => {
                console.log('WebSocket message received, length:', event.data ? event.data.length : 0);
                try {
                    this.handleMessage(event.data);
                } catch (error) {
                    console.error('Error processing message:', error);
                    // Fallback: try to display as plain text
                    if (event.data) {
                        this.appendOutput(this.formatLine(event.data.replace(/\x1b\[[0-9;]*m/g, ''), '#00FF00'));
                    }
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error event:', error);
                console.error('WebSocket readyState:', this.ws ? this.ws.readyState : 'null');
                console.error('WebSocket URL:', this.ws ? this.ws.url : 'null');
                this.updateStatus('disconnected', 'Connection Error');
                this.connected = false;
            };
            
            this.ws.onclose = (event) => {
                this.connected = false;
                console.log('WebSocket closed. Code:', event.code, 'Reason:', event.reason || 'none', 'WasClean:', event.wasClean);
                this.updateStatus('disconnected', 'Disconnected');
                
                // Only attempt to reconnect if it wasn't a clean close
                if (!event.wasClean && event.code !== 1000) {
                    setTimeout(() => {
                        if (!this.connected) {
                            console.log('Attempting to reconnect...');
                            this.updateStatus('connecting', 'Reconnecting...');
                            this.connect(url);
                        }
                    }, 3000);
                }
            };
            
            // Check connection state after a short delay
            setTimeout(() => {
                console.log('WebSocket state after 100ms:', {
                    readyState: this.ws ? this.ws.readyState : 'null',
                    connected: this.connected,
                    url: this.ws ? this.ws.url : 'null'
                });
            }, 100);
            
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            console.error('Error stack:', error.stack);
            this.updateStatus('disconnected', 'Connection Failed');
        }
    }
    
    updateStatus(status, text) {
        if (this.status) {
            this.status.textContent = text;
            this.status.className = `status ${status}`;
            console.log('Status updated:', status, text);
        } else {
            console.error('Status element not found!');
        }
    }
    
    handleMessage(data) {
        // Process ANSI escape codes and append to terminal
        try {
            this.processAnsiOutput(data);
        } catch (error) {
            console.error('Error in handleMessage:', error, 'Data:', data);
            // Fallback: display as plain text
            if (data && data.trim().length > 0) {
                const plainText = data.replace(/\x1b\[[0-9;]*[mHJK]/g, '');
                if (plainText.trim().length > 0) {
                    this.appendOutput(this.formatLine(plainText, '#00FF00'));
                }
            }
        }
    }
    
    processAnsiOutput(text) {
        // Handle empty input
        if (!text) {
            return;
        }
        
        // Handle ANSI escape codes
        // Clear screen (ESC[2J)
        const shouldClear = text.includes('\x1b[2J');
        if (shouldClear) {
            this.terminalBody.innerHTML = '';
            // Remove clear screen code
            text = text.replace(/\x1b\[2J/g, '');
            // Handle cursor home (ESC[H)
            text = text.replace(/\x1b\[H/g, '');
        }
        
        // If text is empty after clearing, don't process
        if (!text || text.trim().length === 0) {
            return;
        }
        
        // Process color codes and other ANSI sequences
        let processed;
        try {
            processed = this.processAnsiCodes(text);
        } catch (error) {
            console.error('Error processing ANSI codes:', error, 'Text:', text.substring(0, 100));
            // Fallback: simple text display - split by lines and format each
            const lines = text.replace(/\x1b\[[0-9;]*[mHJK]/g, '').split('\n');
            processed = '';
            for (const line of lines) {
                if (line.trim().length > 0 || lines.length === 1) {
                    processed += this.formatLine(line.substring(0, 40), '#00FF00');
                }
            }
        }
        
        // Append the processed text (only if we have content)
        if (processed && processed.trim().length > 0) {
            this.appendOutput(processed);
        } else if (text.trim().length > 0) {
            // Fallback: if processing failed but we have text, display it
            const fallbackText = text.replace(/\x1b\[[0-9;]*[mHJK]/g, '');
            if (fallbackText.trim().length > 0) {
                const lines = fallbackText.split('\n');
                let fallbackOutput = '';
                for (const line of lines) {
                    fallbackOutput += this.formatLine(line.substring(0, 40), '#00FF00');
                }
                this.appendOutput(fallbackOutput);
            }
        }
    }
    
    processAnsiCodes(text) {
        // Handle empty or null text
        if (!text || text.length === 0) {
            return '';
        }
        
        // C64 8-bit color mapping (16 colors)
        // Using authentic C64 color palette
        const c64Colors = {
            // Standard ANSI codes
            '30': '#000000', // Black (C64 color 0)
            '31': '#880000', // Red (C64 color 2)
            '32': '#00AA00', // Green (C64 color 5)
            '33': '#AAAA00', // Yellow (C64 color 7)
            '34': '#0000AA', // Blue (C64 color 6)
            '35': '#AA00AA', // Purple (C64 color 4)
            '36': '#00AAAA', // Cyan (C64 color 3)
            '37': '#AAAAAA', // White/Grey (C64 color 1)
            // Extended colors (256-color mode for C64 colors)
            '38;5;208': '#FF8800', // Orange (C64 color 8)
            '38;5;130': '#AA5500', // Brown (C64 color 9)
            '90': '#555555', // Dark grey (C64 color 11)
            '91': '#FF5555', // Light red (C64 color 10)
            '92': '#55FF55', // Light green (C64 color 13)
            '94': '#5555FF', // Light blue (C64 color 14)
            '97': '#FFFFFF', // Light grey (C64 color 15)
        };
        
        // Process ANSI codes and wrap at 40 characters (C64 screen width)
        let output = '';
        let currentColor = '#00FF00'; // Default green (C64 color 5)
        let inEscape = false;
        let escapeSeq = '';
        let currentLine = '';
        
        for (let i = 0; i < text.length; i++) {
            const char = text[i];
            
            // Handle escape sequences
            // \x1b is the hex escape for ESC (same as \033 octal, but \033 is not allowed in strict mode)
            if (char === '\x1b') {
                inEscape = true;
                escapeSeq = '';
                continue;
            }
            
            if (inEscape) {
                if (char === '[') {
                    continue; // Start of CSI
                }
                if (char === 'm') {
                    // End of color code
                    inEscape = false;
                    const codes = escapeSeq.split(';');
                    const fullCode = escapeSeq;
                    
                    if (fullCode === '0' || codes[0] === '0') {
                        currentColor = '#00FF00'; // Reset to green
                    } else if (c64Colors[fullCode]) {
                        currentColor = c64Colors[fullCode];
                    } else if (c64Colors[codes[0]]) {
                        currentColor = c64Colors[codes[0]];
                    }
                    escapeSeq = '';
                    continue;
                }
                // Handle other escape sequences (like cursor positioning)
                if (char === 'H' || char === 'J' || char === 'K') {
                    // End of escape sequence we don't process
                    inEscape = false;
                    escapeSeq = '';
                    continue;
                }
                escapeSeq += char;
                continue;
            }
            
            // Handle regular characters with 40-column wrapping
            if (char === '\n') {
                // End of line - pad to 40 chars if needed, then add
                if (currentLine.length > 0) {
                    currentLine = this.padTo40(currentLine);
                    output += this.formatLine(currentLine, currentColor);
                    currentLine = '';
                } else {
                    // Empty line - still add it
                    output += this.formatLine('', currentColor);
                }
            } else if (char === '\r') {
                // Carriage return - ignore (handled by \n)
                continue;
            } else {
                currentLine += char;
                // Wrap at 40 characters (C64 screen width)
                if (currentLine.length >= 40) {
                    output += this.formatLine(currentLine.substring(0, 40), currentColor);
                    currentLine = currentLine.substring(40);
                }
            }
        }
        
        // Add remaining line
        if (currentLine.length > 0) {
            currentLine = this.padTo40(currentLine);
            output += this.formatLine(currentLine, currentColor);
        }
        
        return output;
    }
    
    padTo40(line) {
        // Pad line to exactly 40 characters (C64 screen width)
        if (line.length > 40) {
            return line.substring(0, 40);
        }
        return line + ' '.repeat(40 - line.length);
    }
    
    formatLine(line, color) {
        // Format a line with color, ensuring exactly 40 characters
        // Handle null/undefined
        if (line === null || line === undefined) {
            line = '';
        }
        // Ensure line is a string
        line = String(line);
        // Escape HTML
        const escaped = this.escapeHtml(line);
        return `<div class="terminal-line" style="color: ${color}">${escaped}</div>`;
    }
    
    escapeHtml(text) {
        if (text === null || text === undefined) {
            return '';
        }
        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML;
    }
    
    appendOutput(html) {
        // If no HTML, don't do anything
        if (!html || html.trim().length === 0) {
            return;
        }
        
        // Append HTML directly (already formatted as lines)
        // Use a temporary container to parse HTML safely
        const temp = document.createElement('div');
        temp.innerHTML = html;
        
        // Move all child nodes to terminal body
        while (temp.firstChild) {
            this.terminalBody.appendChild(temp.firstChild);
        }
        
        // Limit to 25 visible rows (C64 screen height)
        // Keep last 25 lines, remove older ones
        const lines = this.terminalBody.querySelectorAll('.terminal-line');
        if (lines.length > 25) {
            const toRemove = lines.length - 25;
            for (let i = 0; i < toRemove; i++) {
                lines[i].remove();
            }
        }
        
        // Auto-scroll to bottom
        this.terminalBody.scrollTop = this.terminalBody.scrollHeight;
    }
    
    handleKeyDown(e) {
        if (!this.connected) {
            e.preventDefault();
            return;
        }
        
        if (e.key === 'Enter') {
            e.preventDefault();
            const input = this.terminalInput.value;
            // Send full line to server (server will handle echoing)
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(input + '\r\n');
            }
            // Clear input field
            this.terminalInput.value = '';
            this.inputBuffer = '';
        } else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
            // Prevent default behavior for arrow keys (could implement command history later)
            e.preventDefault();
        }
        // Let other keys (including backspace) work normally in the input field
        // We don't send individual characters - only send complete lines on Enter
    }
    
    handleInput(e) {
        // Just update the buffer, don't send anything to server
        // We only send complete lines when Enter is pressed
        this.inputBuffer = e.target.value;
    }
    
    startCursorBlink() {
        setInterval(() => {
            this.cursorVisible = !this.cursorVisible;
        }, 500);
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(data);
        }
    }
}

// Initialize terminal when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('=== DOM Content Loaded ===');
    console.log('DOM loaded, initializing terminal...');
    console.log('Document ready state:', document.readyState);
    
    try {
        const terminal = new Terminal();
        console.log('Terminal initialized successfully:', terminal);
        
        // Set a timeout to check if WebSocket connected
        setTimeout(() => {
            if (!terminal.connected) {
                console.warn('WebSocket not connected after 2 seconds');
                console.warn('WebSocket state:', terminal.ws ? terminal.ws.readyState : 'null');
                console.warn('Connected flag:', terminal.connected);
            }
        }, 2000);
    } catch (error) {
        console.error('Failed to initialize terminal:', error);
        console.error('Error stack:', error.stack);
        
        // Show error to user
        const terminalBody = document.getElementById('terminal-body');
        if (terminalBody) {
            terminalBody.innerHTML = '<div style="color: red;">Error initializing terminal. Check console for details.</div>';
        }
    }
});

// Also try immediate initialization if DOM is already loaded
if (document.readyState === 'loading') {
    console.log('DOM is still loading, waiting for DOMContentLoaded...');
} else {
    console.log('DOM already loaded, initializing immediately...');
    try {
        const terminal = new Terminal();
        console.log('Terminal initialized (immediate):', terminal);
    } catch (error) {
        console.error('Failed to initialize terminal (immediate):', error);
    }
}

