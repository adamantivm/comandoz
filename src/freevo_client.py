import socket
import time

HOSTNAME = 'htpc'
PORT = 16311
MENU_DELAY = 0.3

def send_command( command):
    sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOSTNAME,PORT))
    sock.send( command)
    sock.close()
    
def navigate_menu( path_array):
    for element in path_array:
        send_command( element)
        time.sleep( MENU_DELAY)
        
def stop_playing():
    send_command("STOP")

def play_radio_paradise():
    navigate_menu([
        "MUSIC",
        "DOWN", "DOWN", "SELECT",
        "DOWN", "DOWN", "DOWN", "SELECT"
    ])
