import socket

HOST = 'localhost'
PORT = 5000

print(f"Connect to {HOST}:{PORT}")

try:
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.send(b'Hello, world')
    data = s.recv(1024)
    print('Received:', repr(data))

    s.close()

except socket.error as e:
    print("Socket error({0}): {1}".format(e.errno, e.strerror))
