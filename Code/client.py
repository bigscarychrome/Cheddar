import socket
import time
import random
import threading
import sys
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit import Application
from prompt_toolkit.shortcuts import ProgressBar, input_dialog

server_dict = {
    "001307"
}
def passwd():
    passkey = input_dialog(
        title="login name",
        text="This room requires a password.",
        password=True
    ).run()
    if not passkey:
        exit("NO PASSKEY")

# --- Setup socket connection ---
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ip = input_dialog(title="Server IP", text="Enter the server IP:").run()
if not ip:
    exit("No IP provided!")

# Prompt for Port second
port = input_dialog(title="Server Port", text="Enter the server port:").run()
if not port:
    exit("No port provided!")

# Simulated connection loading bar
with ProgressBar() as pb:
    for i in pb(range(30)):
        time.sleep(random.uniform(0.01, 0.05))

try:
    server.connect((ip, int(port)))
except ConnectionRefusedError as e:
    print("\033[31;7mCONNECTION REFUSED ERROR\033[0;0m")
    print(e)
    sys.exit(1)
except TimeoutError as e:
    print("\033[31;7mTIMED OUT\033[0;0m")
    print(e)
    sys.exit(1)

print("Sending join message...")
server.sendall("Receiving join data...".encode())

senderid = input("But wait!\nYou need a username!\n> ")
server.sendall(f"{senderid}306".encode())

# --- Prompt Toolkit chat interface setup ---
output_field = TextArea(style="class:output-field", text="Connected.\n", scrollbar=True, wrap_lines=True, read_only=True)
input_field = TextArea(height=1, prompt="> ", multiline=False)

kb = KeyBindings()

@kb.add("enter")
def _(event):
    """Send message when Enter is pressed"""
    message = input_field.text.strip()
    if message:
        try:
            server.sendall(f"{senderid}: {message}".encode())
        except Exception as e:
            output_field.text += f"\n[Error sending message: {e}]"
        input_field.text = ""
    event.app.invalidate()

root_container = HSplit([
    output_field,
    input_field
])

layout = Layout(root_container)
app = Application(layout=layout, key_bindings=kb, full_screen=True)

# --- Thread to receive messages ---
def receive_messages():
    while True:
        try:
            data = server.recv(1024)
            if not data:
                output_field.text += "\n[Disconnected from server]"
                break
            msg = data.decode(errors="ignore")
            output_field.text += f"\n{msg}"
            app.invalidate()
        except Exception as e:
            output_field.text += f"\n[Error receiving: {e}]"
            break

recv_thread = threading.Thread(target=receive_messages, daemon=True)
recv_thread.start()

# --- Run the chat UI ---
try:
    app.run()
except KeyboardInterrupt:
    print("\nClosing...")
    server.close()
