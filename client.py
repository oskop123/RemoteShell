import socket

HOST = 'localhost'
PORT = 5000

print(f"Connect to {HOST}:{PORT}")

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.send(b'ls')
    data = s.recv(4096)
    print('Received:', repr(data))

    s.close()

except OSError as e:
    print("Socket error({0}): {1}".format(e.errno, e.strerror))
