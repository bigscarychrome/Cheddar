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

# --- REPLACE EVERYTHING BELOW THIS LINE (the "# app" line) ---

import asyncio
import queue

server.bind((ip, int(port)))
server.listen(5)
clients = []
running = True

# Thread-safe queue for messages coming from socket threads.
msg_queue = queue.Queue()

# --- UI setup ---
output_field = TextArea(
    text=f"Server running at {ip}:{port}\nType ':stop' to exit.\n\n",
    read_only=False,   # ← changed!
    scrollbar=True,
    wrap_lines=True,
)

# Use accept_handler instead of a global "enter" keybinding.
# This is the reliable way to handle "Enter" for a TextArea with multiline=False.
def accept_handler(buffer):
    """
    Called by TextArea when Enter is pressed (multiline=False).
    buffer is the prompt_toolkit Buffer for input_field.
    """
    global running
    text = buffer.text.strip()
    if not text:
        buffer.reset()
        return

    # Stop command
    if text.lower() == ":stop":
        msg_queue.put("\nServer shutting down...\n")
        broadcast("[SERVER] Server is shutting down.\n")
        running = False
        try:
            server.close()
        except Exception:
            pass
        # Use a sentinel so the message pump (running in the app loop) can exit the app.
        msg_queue.put("__EXIT__")
        return

    # Normal server message
    message = f"[SERVER] {text}\n"
    msg_queue.put(message)
    broadcast(message)
    buffer.reset()


input_field = TextArea(
    height=1,
    prompt="[SERVER] ",
    multiline=False,
    accept_handler=accept_handler,  # <- critical: handle enter here
)

root_container = HSplit([output_field, input_field])

# --- Networking functions (unchanged logic, but they place messages into msg_queue) ---
def broadcast(message: str):
    """Send message to all connected clients."""
    for c in clients[:]:
        try:
            c.sendall(message.encode("utf-8"))
        except OSError:
            try:
                clients.remove(c)
            except ValueError:
                pass

def handle_client(conn, addr):
    """Handle messages from one client (runs in worker thread)."""
    msg_queue.put(f"[+] Client connected: {addr}\n")

    # Store display names per IP
    if not hasattr(handle_client, "names"):
        handle_client.names = {}  # {ip: display_name}

    while running:
        try:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode("utf-8", errors="ignore").strip()

            # --- NEW FEATURE ---
            # If message ends with "306", set this IP's display name
            if msg.endswith("306"):
                display_name = msg[:-3].strip()
                if display_name:
                    handle_client.names[addr[0]] = display_name
                    msg_queue.put(f"[SERVER] {addr[0]} is now known as {display_name}\n")
                    broadcast(f"[SERVER] {addr[0]} is now known as {display_name}\n")
                continue
            # -------------------

            # Determine display name if exists
            name = handle_client.names.get(addr[0], addr[0])
            msg_queue.put(f"[{name}] {msg}\n")
            broadcast(f"[{name}] {msg}\n")

        except (OSError, ConnectionResetError):
            break

    msg_queue.put(f"[-] Client disconnected: {addr}\n")
    try:
        clients.remove(conn)
    except ValueError:
        pass
    try:
        conn.close()
    except Exception:
        pass

def accept_clients():
    """Accept clients continuously in background (worker thread)."""
    while running:
        try:
            conn, addr = server.accept()
            clients.append(conn)
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except OSError:
            break

# --- Coroutine that runs inside the Application event loop and updates the UI ---
async def message_pump():
    """
    Pull messages from msg_queue and safely update the prompt_toolkit UI.
    This runs inside the Application's asyncio loop (scheduled as a background task).
    """
    while True:
        try:
            msg = msg_queue.get_nowait()
        except queue.Empty:
            # If server stopped and nothing left to process, exit.
            if not running and msg_queue.empty():
                break
            await asyncio.sleep(0.05)
            continue

        # Special sentinel to request app exit from inside the loop
        if msg == "__EXIT__":
            # exit the app from its own event loop (safe)
            app.exit()
            break

        # Insert into output buffer and request redraw
        output_field.buffer.insert_text(msg)
        app.invalidate()
        # give control back to the loop
        await asyncio.sleep(0)

# --- Build the Application (no enter keybinding; using accept_handler instead) ---
app = Application(
    layout=Layout(root_container, focused_element=input_field),
    full_screen=True,
)

# Start accepting clients in a background thread
threading.Thread(target=accept_clients, daemon=True).start()

# Schedule the message_pump coroutine to run inside the app's event loop.
# create_background_task is safe to call before run(); it schedules the coroutine
# on the application's loop once it starts.
# Run the UI and start the message pump once the loop is ready.
async def run():
    app.create_background_task(message_pump())
    await app.run_async()

import asyncio
asyncio.run(run())

