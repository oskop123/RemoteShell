import socket
import sys

HOST = 'localhost'
PORT = 5000
SCTP = True

print(f"Connect to {HOST}:{PORT}")
print(sys.argv)

try:
    if SCTP:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_SCTP)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    while True:
        cmd = input('CMD: ')
        s.sendall(bytes(cmd, 'utf-8'))
        data = s.recv(4096)
        print(data.decode('utf-8'), end='')

except OSError as e:
    print("Socket error({0}): {1}".format(e.errno, e.strerror))

except KeyboardInterrupt as e:
    s.close()
