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
print(f"serving on {ip}:8081")
print(f"Make sure to send ':stop' to exit, and not the x button to close.")
print(f"As the server host pf {ip}:8081, your messages will appear as '[SERVER] Message'.")
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

kb = KeyBindings()

input_field = TextArea(
    height=1,
    prompt="[SERVER] ",
    multiline=False,
)

output_field = output_field = TextArea(
    text=f"Server running at {ip}:{port}\nType ':stop' to exit.\n\n",
    read_only=True,
    scrollbar=True,
    wrap_lines=True,
)
running = True

@kb.add("enter")
def _(event):
    text = input_field.text.strip()
    if text:
        if text == ":stop":
            server.close()
            event.app.exit()
    server.sendall(f"[SERVER] {text}".encode())
def recv_forever():
    """Continuously accept clients and receive messages while the app runs."""
    server.listen(5)
    while running:
        try:
            conn, addr = server.accept()
            output_field.buffer.insert_text(f"[+] Connection from {addr}\n")

            # Each client gets its own thread for receiving data
            threading.Thread(
                target=client_recv_loop,
                args=(conn, addr),
                daemon=True
            ).start()
        except OSError:
            break

def client_recv_loop(conn, addr):
    """Receive data from one client in a loop."""
    while running:
        try:
            data = conn.recv(1024)
            if not data:
                break
            message = data.decode(errors="ignore").strip()
            output_field.buffer.insert_text(f"{message}\n")
            conn.sendall(message.encode())
        except ConnectionResetError:
            print("CONN RESET. PLEASE SEND :stop")
        except OSError:
            print("OSERROR, PLEASE SEND :stop")
    output_field.buffer.insert_text(f"[-] Disconnected: {addr}\n")
    conn.close()


root_container = HSplit([
    output_field,
    input_field,
])

app = Application(
    layout=Layout(root_container, focused_element=input_field),
    key_bindings=kb,
    full_screen=True,
)
threading.Thread(target=recv_forever, daemon=True).start()
app.run()