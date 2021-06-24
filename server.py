import socket
import select
import signal
import os
import pwd
import sys
import argparse
import logging
import logging.handlers
from typing import Union
from utils import daemon_init, handle_request


def server(name: str,
           host: str,
           port: Union[str, int],
		   commands_path: str,
           ipv4_only: bool = False,
           ipv6_only: bool = False,
           daemonize: bool = False,
           user: str = os.getlogin(),
):
	"""Main program to run server

	:param name: Name for the program in logs
	:type name: str
	:param host: To which address to bind to
	:type host: str
	:param port: On which port number to listen, can be also service name
	:type port: Union[str, int]
	:param commands_path: Path to file with allowed commands
	:type commands_path: str
	:param ipv4_only: To use only IPv4, defaults to False
	:type ipv4_only: bool, optional
	:param ipv6_only: To use only IPv6, defaults to False
	:type ipv6_only: bool, optional
	:param daemonize: To daemonize, defaults to False
	:type daemonize: bool, optional
	:param user: As which user run the daemonized program, defaults to os.getlogin()
	:type user: str, optional
	"""
	# Handle signals
	signal.signal(signal.SIGCHLD, signal.SIG_IGN)

	## logger setup
	logger = logging.getLogger(name)
	formatter = logging.Formatter('%(name)s [%(levelname)s]: %(message)s')
	logger.setLevel(logging.INFO)

	# classic syslog
	sys_handler = logging.handlers.SysLogHandler(
		facility=logging.handlers.SysLogHandler.LOG_DAEMON,
		address='/dev/log'
	)
	sys_handler.setLevel(logging.ERROR)
	sys_handler.setFormatter(formatter)
	
	# daemon logging
	daemon_handler = logging.handlers.SysLogHandler(
		facility=logging.handlers.SysLogHandler.LOG_USER,
		address='/dev/log'
	)
	daemon_handler.setLevel(logging.INFO)
	daemon_handler.setFormatter(formatter)

	logger.addHandler(sys_handler)
	logger.addHandler(daemon_handler)
	## end of logger setup

	## building sockets
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
		print(f"{str(e)}")
		sys.exit(-2)

	epoll = select.epoll()

	family = socket.AF_INET6
	if ipv4_only:
		family = socket.AF_INET

	try:
		listen_sockets = [
			socket.socket(family, socket.SOCK_STREAM),
			socket.socket(family, socket.SOCK_STREAM, socket.IPPROTO_SCTP)
			]
	except OSError as e:
		print(f'socket() error ({e.errno}): {e.strerror}')
		sys.exit(-1)
	
	for sock in listen_sockets:
		try:
			if not ipv4_only:
				if ipv6_only:
					sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
				else:
					sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		except OSError as e:
			logger.error(f'setsockopt() SO_REUSEADDR and/or IPV6_ONLY error ({e.errno}): {e.strerror}')
			sys.exit(-1)

		try:
			sock.bind((host, resolved_port))
		except OSError as e:
			logger.error(f'bind() error ({e.errno}): {e.strerror}')
			sys.exit(-1)

		try:
			sock.listen(2)
		except OSError as e:
			logger.error(f'listen() error ({e.errno}): {e.strerror}')
			sys.exit(-1)

		epoll.register(sock, select.EPOLLIN)

	LISTEN_SOCKETS = { s.fileno(): s for s in listen_sockets }
	CONN = {}
	## end of builing sockets

	# if --daemonize is set -> daemonize the process | also run as non-root user to restrict priveleges
	if daemonize:
		pwd_info = pwd.getpwnam(user)
		if daemon_init(logger, pwd_info[2], pwd_info[3]) < 0:
			logger.error(f'daemon_init() error: daemon not started')
			sys.exit(-4)

	try:
		# EPOLL process | event loop
		while True:
			descriptors_list = epoll.poll()
			for fd, event in descriptors_list:
				if fd in map(lambda sock: sock.fileno(), listen_sockets):
					conn, _ = LISTEN_SOCKETS[fd].accept()
					epoll.register(conn, select.EPOLLIN)
					CONN[conn.fileno()] = conn
				elif event & select.EPOLLIN:
					# when there is socket ready to read
					recv_data = CONN[fd].recv(100)

					# if recv_data empty
					if not recv_data:
						epoll.unregister(CONN[fd])
						CONN[fd].close()
						CONN.pop(fd)
						continue

					read_side, write_side = os.pipe()

					if os.fork():
						# parent closes pipe
						os.close(write_side)
						CONN[fd].send(os.read(read_side, 100))
						os.close(read_side)
						epoll.modify(CONN[fd], select.EPOLLIN)
					else:
						# close listening sockets
						for i in listen_sockets:
							i.close()
						# handling user command
						handle_request(logger, commands_path, recv_data, read_side, write_side)

	except OSError as e:
		_, _, tb = sys.exc_info()
		logger.error(f'epoll error: {e.strerror} ({e.errno}); line: {tb.tb_lineno}')
		sys.exit(-3)

	except ValueError as e:
		logger.error(f'epoll has error: {str(e)}')
		sys.exit(-3)

	except socket.gaierror as e:
		logger.error(f'epoll has error ({e.errno}): {e.strerror}')
		sys.exit(-3)


if __name__ == "__main__":
	# parsing entry arguments
	parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),
										description="Server for remote shell")
	parser.add_argument('-c', '--allowed-commands',
						default='',
                    	help='specify path to .txt file with allowed commands to execute; on default no restrictions for commands')
	parser.add_argument('-4', '--ipv4-only',
                    	help="run server only for IPv4",
						action='store_true')
	parser.add_argument('-6', '--ipv6-only',
                    	help="run server only for IPv6",
						action='store_true')
	parser.add_argument('-D', '--daemonize',
		help="daemonize server program",
		action='store_true')
	parser.add_argument('-u', '--as-user',
						default='student',
						help='run as user (UID, GID, EUID, EGID); only if daemonized; defaults to "student"')
	parser.add_argument('--host',
						default='',
						help='server address or domain name; defaults to ""')
	parser.add_argument('--port',
						default='5001',
						help='server port or service name; defaults to "5001"')
	arguments = parser.parse_args()

	base_path = os.path.dirname(os.path.abspath(__name__))
	
	server(
    	os.path.basename(sys.argv[0]),
        arguments.host,
        arguments.port,
        arguments.allowed_commands,
        arguments.ipv4_only,
        arguments.ipv6_only,
        arguments.daemonize,
        arguments.as_user
	)