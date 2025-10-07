import socket
import time
import random
import threading
import sys
import getpass
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit.shortcuts import ProgressBar, input_dialog
from prompt_toolkit import Application
import queue
import asyncio

# --- Setup socket connection ---
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ip = input_dialog(title="Server IP", text="Enter the server IP:").run()
if not ip:
    exit("No IP provided!")

port = input_dialog(title="Server Port", text="Enter the server port:").run()
if not port:
    exit("No port provided!")

# --- Simulated connection loading bar ---
with ProgressBar() as pb:
    for i in pb(range(30)):
        time.sleep(random.uniform(0.01, 0.05))

# --- Connect ---
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

# --- INITIAL HANDSHAKE (001307 password request) ---
server.settimeout(1.0)
try:
    try:
        data = server.recv(4096)
    except socket.timeout:
        data = b""

    if data:
        initial_msg = data.decode(errors="ignore")
        if "001307" in initial_msg:
            passkey = input_dialog(
                title="Server Password",
                text="This room requires a password:",
                password=True
            ).run()
            if not passkey:
                print("No password entered. Disconnecting.")
                server.close()
                sys.exit(1)
            server.sendall(passkey.encode("utf-8"))

            try:
                server.settimeout(0.25)
                resp = server.recv(4096)
                if resp:
                    print(resp.decode(errors="ignore"))
            except socket.timeout:
                pass
finally:
    server.settimeout(None)

# --- Username ---
print("Sending join message...")
server.sendall("Receiving join data...".encode())
senderid = input("But wait!\nYou need a username!\n> ")
server.sendall(f"{senderid}306".encode())

# --- Queue for messages ---
msg_queue = queue.Queue()
running = True

# --- UI setup ---
output_field = TextArea(
    style="class:output-field",
    text="Connected.\n",
    scrollbar=True,
    wrap_lines=True,
    read_only=True
)

# --- Accept handler (Enter key) ---
def accept_handler(buff):
    text = buff.text.strip()
    if not text:
        buff.reset()
        return

    # Quit command
    if text.lower() == ":quit":
        msg_queue.put("\n[Disconnecting...]\n")
        global running
        running = False
        try:
            server.close()
        except:
            pass
        msg_queue.put("__EXIT__")
        buff.reset()
        return

    # Send to server
    try:
        server.sendall(f"{senderid}: {text}".encode("utf-8"))
        msg_queue.put(f"[You] {text}")  # echo locally
    except Exception as e:
        msg_queue.put(f"[Error sending: {e}]")

    buff.reset()


input_field = TextArea(
    height=1,
    prompt=f"[{senderid}] ",
    multiline=False,
    wrap_lines=False,
    accept_handler=accept_handler
)

root_container = HSplit([output_field, input_field])
layout = Layout(root_container, focused_element=input_field)

app = Application(layout=layout, full_screen=True)

# --- Thread to receive messages (unchanged, for passwords) ---
def receive_messages():
    while running:
        try:
            data = server.recv(4096)
            if not data:
                msg_queue.put("\n[Disconnected from server]")
                msg_queue.put("__EXIT__")
                break

            msg = data.decode(errors="ignore").strip()
            if not msg:
                continue

            # Handle password request marker
            if "001307" in msg:
                msg = msg.replace("001307", "")
                try:
                    passkey = app.run_in_terminal(lambda: getpass.getpass("Server requires password: "))
                except Exception:
                    passkey = input("Server requires password: ")

                if not passkey:
                    server.close()
                    msg_queue.put("\n[No password entered. Disconnecting...]")
                    msg_queue.put("__EXIT__")
                    break

                server.sendall(passkey.encode("utf-8"))
                if not msg.strip():
                    continue

            # Push received message to queue
            msg_queue.put(msg)

        except Exception as e:
            msg_queue.put(f"\n[Error receiving: {e}]")
            msg_queue.put("__EXIT__")
            break


threading.Thread(target=receive_messages, daemon=True).start()

# --- Message pump coroutine ---
async def message_pump():
    while True:
        try:
            msg = msg_queue.get_nowait()
        except queue.Empty:
            if not running and msg_queue.empty():
                break
            await asyncio.sleep(0.05)
            continue

        if msg == "__EXIT__":
            app.exit()
            break

        output_field.buffer.insert_text(msg + "\n")
        app.invalidate()
        await asyncio.sleep(0)

# --- Run the app ---
async def run():
    app.create_background_task(message_pump())
    await app.run_async()

asyncio.run(run())

