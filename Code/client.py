import socket
import time
import random
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit import Application
import threading
import sys
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ip = input("Select an IP to join:")
port = input("Select a port to join:")
with ProgressBar() as pb:
    for i in pb(range(30)):
        randy = random.uniform(0, 1.20)
        time.sleep(int(randy))
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
server.sendall("Recieving join data...".encode())
senderid = input("But wait!\nYou need a username!\n> ")