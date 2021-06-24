from posix import listdir
import socket
import select
import signal
import os
import sys
import argparse
import logging
import logging.handlers
from typing import Union
from utils import daemon_init, handle_request

def handle_sigterm():
	pass

def handle_sigkill():
    pass

def server(base_path, host: str, port: Union[str, int], damonize: bool, timeout: float = 5.0):

	# Handle signals
	signal.signal(signal.SIGCHLD, signal.SIG_IGN)

	logger = logging.getLogger('remshell_server_logger')
	formatter = logging.Formatter('%(asctime)s | %(name)s |  %(levelname)s: %(message)s')
	logger.setLevel(logging.INFO)

	# classic syslog
	sys_handler = logging.handlers.SysLogHandler(
		facility=logging.handlers.SysLogHandler.LOG_DAEMON,
		address='/dev/log'
	)
	sys_handler.setLevel(logging.ERROR)
	sys_handler.setFormatter(formatter)
	# daemon logging
	dameon_handler = logging.handlers.SysLogHandler(
		facility=logging.handlers.SysLogHandler.LOG_USER,
		address='/dev/log'
	)
	logger.addHandler(sys_handler)

	resolved_port = 0
	try:
		if isinstance(int(port), int):
			resolved_port = int(port)
		else:
			resolved_port = socket.getservbyname(port)
	except socket.gaierror as e:
		logger.error(f"getservbyname() error ({e.errno}): {e.strerror}")
		sys.exit(-2)

	except ValueError as e:
		logger.error(f"{str(e)}")
		sys.exit(-2)

	epoll = select.epoll()

	try:
		listen_sockets = [
			socket.socket(socket.AF_INET6, socket.SOCK_STREAM),
			socket.socket(socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_SCTP)
			]
	except OSError as e:
		logger.error(f'Unable to create one of the sockets ({e.errno}): {e.strerror}')
		sys.exit(-1)

	# If --daemonize is set -> daemonize the process | also run as non-root user to restrict priveleges
	if damonize:
		daemon_init(logger, 1000, 1000)

	for sock in listen_sockets:
		sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		sock.bind((host, resolved_port))
		sock.listen()

		epoll.register(sock, select.EPOLLIN)

	LISTEN_SOCKETS = { s.fileno(): s for s in listen_sockets }
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
					handle_request(base_path, recv_data, read_side, write_side)


if __name__ == "__main__":
	# Parsing entry arguments
	parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),
										description="Server for remote shell")
	parser.add_argument(
		'-D', '--daemonize',
		help="daemonize server program",
		action='store_true')
	parser.add_argument('--host',
						default='',
						help="server address or domain name")
	parser.add_argument('--port',
						default='5001',
						help="server port or service name")
	arguments = parser.parse_args()

	base_path = os.path.dirname(os.path.abspath(__name__))
	server(base_path, arguments.host, arguments.port, arguments.daemonize)