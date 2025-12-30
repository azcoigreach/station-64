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
        
        this.init();
    }
    
    init() {
        // Determine WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
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
            this.ws = new WebSocket(url);
            
            this.ws.onopen = () => {
                this.connected = true;
                this.updateStatus('connected', 'Connected');
                console.log('WebSocket connected');
            };
            
            this.ws.onmessage = (event) => {
                this.handleMessage(event.data);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('disconnected', 'Connection Error');
            };
            
            this.ws.onclose = () => {
                this.connected = false;
                this.updateStatus('disconnected', 'Disconnected');
                console.log('WebSocket closed');
                
                // Attempt to reconnect after 3 seconds
                setTimeout(() => {
                    if (!this.connected) {
                        this.updateStatus('connecting', 'Reconnecting...');
                        this.connect(url);
                    }
                }, 3000);
            };
        } catch (error) {
            console.error('Failed to connect:', error);
            this.updateStatus('disconnected', 'Connection Failed');
        }
    }
    
    updateStatus(status, text) {
        this.status.textContent = text;
        this.status.className = `status ${status}`;
    }
    
    handleMessage(data) {
        // Append received data to terminal
        // Remove any existing prompt from input area by checking if we're at the end
        this.appendOutput(data);
    }
    
    appendOutput(text) {
        // Create a text node and append
        const lines = text.split('\n');
        lines.forEach((line, index) => {
            if (line || index < lines.length - 1) {
                const lineDiv = document.createElement('div');
                lineDiv.className = 'terminal-line';
                lineDiv.textContent = line;
                this.terminalBody.appendChild(lineDiv);
            }
        });
        
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
    new Terminal();
});

