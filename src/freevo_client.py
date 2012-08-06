import socket
import time

HOSTNAME = 'htpc'
PORT = 16311
MENU_DELAY = 0.3
MAX_MESSAGE_SIZE = 255


def send_command( command):
    sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOSTNAME,PORT))
    sock.send( command)
    sock.close()

def read_context():
    '''
    menu
    audio
    video
    '''
    sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOSTNAME,PORT))
    sock.send("xyzzy")
    ret = sock.recv(MAX_MESSAGE_SIZE)
    sock.close()
    return ret

def send_many( path_array):
    '''Send many commands in a row, allowing a small wait in between
       Particularly appropriate for navigating menus'''
    for element in path_array:
        send_command( element)
        time.sleep( MENU_DELAY)

def volume_up():
    send_many(["VOL+"]*5)

def volume_down():
    send_many(["VOL-"]*5)

def stop_playing():
    send_command("STOP")

def pause():
    send_command("PAUSE")

def play_radio_paradise():
    send_many([
        "MUSIC",
        "DOWN", "DOWN", "SELECT",
        "DOWN", "DOWN", "DOWN", "SELECT"
    ])

if __name__ == '__main__':
    print volume_down()