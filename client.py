import socket
import sys
import time

HOST = 'localhost'
PORT = 5000

print(f"Connect to {HOST}:{PORT}")
print(sys.argv)

cmd = sys.argv[1] if len(sys.argv) > 1 else "ls"

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    time.sleep(5)
    s.send(bytes(cmd, 'utf-8'))
    data = s.recv(4096)
    print('Received:', repr(data))

    s.close()

except OSError as e:
    print("Socket error({0}): {1}".format(e.errno, e.strerror))
