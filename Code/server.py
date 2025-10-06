import socket
import time
import random
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit import Application
import threading

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip = input("Select an IP (For all, use 0.0.0.0, or simply dont type anything then hit enter):")
port = input("Select a port (Try a number that is 8000-65535, dont type anything for a random port):")
if ip == "":
    ip = "0.0.0.0"
if port == "":
    port = random.randint(8000, 65535)
rand = random.randint(1, 15)
print(f"serving on {ip}:{port}")
print(f"Make sure to send ':stop' to exit, and not the x button to close.")
print(f"As the server host of {ip}:{port}, your messages will appear as '[SERVER] Message'.")
print(f"The capacity for users is how many the server can handle!")
print(f"Please wait while we start your server...")
print(f"", end="\r")
for null in range(rand):
    print("/ ", end="\r")
    time.sleep(0.1)
    print("| ", end="\r")
    time.sleep(0.1)
    print(f"\ ", end="\r")
    time.sleep(0.1)
    print("- ", end="\r")
    time.sleep(0.1)
print("Joining as SERVER...")
with ProgressBar() as pb:
    for i in pb(range(100)):
        randy = random.uniform(0, 1)
        time.sleep(int(randy))


print("Server started on {ip}:{port}")
# app

server.bind((ip, int(port)))
server.listen(5)
clients = []
running = True

# --- UI setup ---
output_field = TextArea(
    text=f"Server running at {ip}:{port}\nType ':stop' to exit.\n\n",
    read_only=True,
    scrollbar=True,
    wrap_lines=True,
)

input_field = TextArea(
    height=1,
    prompt="[SERVER] ",
    multiline=False,
)

root_container = HSplit([output_field, input_field])
kb = KeyBindings()

# --- Networking functions ---

def broadcast(message: str):
    """Send message to all connected clients."""
    for c in clients[:]:
        try:
            c.sendall(message.encode("utf-8"))
        except OSError:
            clients.remove(c)

def handle_client(conn, addr):
    """Handle messages from one client."""
    output_field.buffer.insert_text(f"[+] Client connected: {addr}\n")
    while running:
        try:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode("utf-8").strip()
            app.invalidate()  # update UI
            output_field.buffer.insert_text(f"[{addr[0]}] {msg}\n")
            broadcast(f"[{addr[0]}] {msg}")
        except OSError:
            break
    output_field.buffer.insert_text(f"[-] Client disconnected: {addr}\n")
    try:
        clients.remove(conn)
    except ValueError:
        pass
    conn.close()
    app.invalidate()

def accept_clients():
    """Accept clients continuously in background."""
    while running:
        try:
            conn, addr = server.accept()
            clients.append(conn)
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except OSError:
            break

# --- Key binding for Enter ---
@kb.add("enter")
def _(event):
    global running
    text = input_field.text.strip()
    if not text:
        return

    if text.lower() == ":stop":
        output_field.buffer.insert_text("\nServer shutting down...\n")
        broadcast("[SERVER] Server is shutting down.\n")
        running = False
        server.close()
        time.sleep(0.5)
        event.app.exit()
        return

    message = f"[SERVER] {text}\n"
    output_field.buffer.insert_text(message)
    broadcast(message)
    input_field.buffer.reset()
    app.invalidate()

# --- Build and run app ---
app = Application(
    layout=Layout(root_container, focused_element=input_field),
    key_bindings=kb,
    full_screen=True,
)

# Background thread for accepting clients
threading.Thread(target=accept_clients, daemon=True).start()

app.run()
