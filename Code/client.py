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

