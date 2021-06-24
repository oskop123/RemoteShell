from posix import listdir
import socket
import select
import signal
import os
import sys
import argparse
import logging
from typing import Union

from utils import daemon_init, handle_request

def server(host: str, port: Union[str, int], damonize:bool, timeout: float = 5.0):

	# Handle signals
	signal.signal(signal.SIGCHLD, signal.SIG_IGN)

	logger = logging.getLogger('remshell_server_logger')
	logger.setLevel(logging.ERROR)
	handler = logging.handlers.SysLogHandler(facility=logging.handlers.SysLogHandler.LOG_DAEMON, address='/dev/log')
	logger.addHandler(handler)

	resolved_port = 0
	try:
		if isinstance(int(port), int):
			resolved_port = port
		else:
			resolved_port = socket.getservbyname(port)
	except socket.gaierror as e:
		logger.error(f"getservbyname() error ({e.errno}): {e.strerror}")

	except ValueError as e:
		logger.error(f"{e}")

	epoll = select.epoll()

	listen_sockets = [
		socket.socket(socket.AF_INET6, socket.SOCK_STREAM),
		socket.socket(socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_SCTP)
		]

	# If --daemonize is set -> daemonize the process
	if damonize:
		daemon_init(listen_sockets)
 
	for sock in listen_sockets:
			sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

			sock.bind((host, resolved_port))
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
						handle_request(recv_data, read_side, write_side)


if __name__ == "__main__":
    # Parsing entry arguments
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),
                                     description="Server for remote shell")
    parser.add_argument(
        '-D', '--daemonize',
        help="daemonize server program",
        action='store_true')
    parser.add_argument('host',
                        default='',
                        help="server address or domain name")
    parser.add_argument('port',
                        default='5001',
                        help="server port or service name")
    arguments = parser.parse_args()

    server(arguments.host, arguments.port, arguments.daemonize)