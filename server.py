import socket
import os
import sys
import signal

HOST = ""
PORT = 5000

signal.signal(signal.SIGCHLD, signal.SIG_IGN)


def handle_client():
    read_side, write_side = os.pipe()
    recv_data = conn.recv(4096)

    pid2 = os.fork()
    if pid2:
        conn.send(os.read(read_side, 100))
    else:
        os.dup2(write_side, 1)
        os.execl("/bin/sh", "sh", "-c", recv_data)


try:
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind((HOST, PORT))
    s.listen()

    while True:
        conn, addr = s.accept()
        print('Connected by', addr)

        pid = os.fork()

        if pid:
            conn.close()
        else:
            s.close()
            handle_client()
            conn.close()
            sys.exit(0)

except OSError as e:
    print("Socket error({0}): {1}".format(e.errno, e.strerror))

except KeyboardInterrupt:
    print("Closing server")
    conn.close()
    s.close()
