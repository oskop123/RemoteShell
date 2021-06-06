import socket
import os
import signal
import select

HOST = ""
PORT = 5000

signal.signal(signal.SIGCHLD, signal.SIG_IGN)

epoll = select.epoll()

listen_sockets = [
    socket.socket(socket.AF_INET6, socket.SOCK_STREAM),
    socket.socket(socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_SCTP)
]

for sock in listen_sockets:
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind((HOST, PORT))
    sock.listen()

    epoll.register(sock, select.EPOLLIN)

LISTEN_SOCKETS = {s.fileno(): s for s in listen_sockets}
CONN = {}

while True:
    descriptors_list = epoll.poll()
    for fd, event in descriptors_list:
        if fd in map(lambda sock: sock.fileno(), listen_sockets):
            conn, _ = LISTEN_SOCKETS[fd].accept()
            epoll.register(conn, select.EPOLLIN)
            CONN[conn.fileno()] = conn
        elif event & select.EPOLLIN:
            recv_data = CONN[fd].recv(100)

            if not recv_data:
                epoll.unregister(CONN[fd])
                CONN[fd].close()
                CONN.pop(fd)
                continue

            read_side, write_side = os.pipe()

            if os.fork():
                os.close(write_side)
                CONN[fd].send(os.read(read_side, 100))
                os.close(read_side)
                epoll.modify(CONN[fd], select.EPOLLIN)
            else:
                for i in listen_sockets:
                    i.close()
                os.close(read_side)
                os.dup2(write_side, 1)
                os.execl("/bin/sh", "sh", "-c", recv_data)
