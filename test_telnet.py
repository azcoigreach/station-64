#!/usr/bin/env python3
"""Simple telnet test script for Station-64 BBS."""
import socket
import time
import sys

def test_telnet(host='localhost', port=6400):
    """Test telnet connection to BBS."""
    try:
        print(f"Connecting to {host}:{port}...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((host, port))
        print("Connected!\n")
        
        # Receive initial data
        data = s.recv(4096)
        print("=== Initial Menu ===")
        print(data.decode('utf-8', errors='replace'))
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            print(f"\n=== Sending command: '{command}' ===")
            s.send(f"{command}\r\n".encode())
            time.sleep(0.5)
            
            data = s.recv(4096)
            print("=== Response ===")
            print(data.decode('utf-8', errors='replace')[:1000])
        else:
            print("\nTo test a command, run: python3 test_telnet.py <command>")
            print("Example: python3 test_telnet.py C")
        
        s.close()
        print("\n=== Connection test completed ===")
        return True
        
    except ConnectionRefusedError:
        print(f"Error: Connection refused. Is the server running on {host}:{port}?")
        return False
    except socket.timeout:
        print("Error: Connection timeout")
        return False
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    host = sys.argv[2] if len(sys.argv) > 2 else 'localhost'
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 2323
    success = test_telnet(host, port)
    sys.exit(0 if success else 1)



