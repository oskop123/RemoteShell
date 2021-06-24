import sys
import os
import argparse
import socket


def client(
    host: str,
	port: str,
	use_sctp: bool = False,
	ipv6: bool = False,
	buffer_size: int = 4096,
	timeout: float = 5.0
) -> int:
	"""Main program to run client for remote shell execution

	:param host: Server name or ip address
	:type host: str
	:param port: Port on which server listens, can be also name of the service
	:type port: str
	:param use_sctp: Use SCTP transport protocol or not, defaults to False
	:type use_sctp: bool, optional
	:param ipv6: Use IPv6 protocol, defaults to False
	:type ipv6: bool, optional
	:param buffer_size: Buffer size for recv and send 
	:type buffer_size: int, optional
	:param timeout: Timeout after which command is not more awaited, defaults to 5.0
	:type timeout: float, optional
	
	:return: Exit code
	:rtype: int
	"""
	buffer_size = 4096
	family = socket.AF_INET
	transport_protocol = socket.IPPROTO_TCP

	# Whether to use ipv6 or not
	if ipv6:
		family = socket.AF_INET6

	# Whether to use SCTP or not
	if use_sctp:
		transport_protocol = socket.IPPROTO_SCTP

	# Use DNS to get address and port of a server
	try:
		sockaddr = socket.getaddrinfo(
			host=host,
			port=port,
			family=family,
			proto=transport_protocol
		)[0][-1]
	except socket.gaierror as e:
		print(f"getaddrinfo() error ({e.errno}): {e.strerror}")
		return -1

	# Define socket
	try:
		sock = socket.socket(family, socket.SOCK_STREAM, transport_protocol)
		sock.setblocking(True)
		sock.settimeout(timeout)
	except OSError as e:
		print(f"socket() error ({e.errno}): {e.strerror}")
		return -2

	# Connect to a server
	try:
		sock.connect(sockaddr)
		print(f"Connected to {sockaddr[0]}:{sockaddr[1]}")
	except OSError as e:
		print(f"connect() error ({e.errno}): {e.strerror}")
		return -3

	print("Press: Ctrl+D to safely exit, Ctrl+C to interrupt")

	# Remote shell endless loop
	try:
		while True:
			cmd = input('> ')
			try:
				sock.sendall(bytes(cmd, 'utf-8'))
			except OSError as e:
				print(f"sendall() error ({e.errno}): {e.strerror}")
				return -3

			try:
				data = sock.recv(buffer_size)
				print(data.decode('utf-8').strip(' \n'))

			except socket.timeout as e:
				print("Request timeout..")
			
			except OSError as e:
				print(f"recv() error({e.errno}): {e.strerror}")
				return -3

				
	except KeyboardInterrupt:
		print(" Keyboard Interrupt")
		sock.close()
		return 255

	except EOFError:
		print("Safely Closing")
		sock.close()
		return 0

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),
                                     description="Client for remote shell")
    parser.add_argument(
        '-S', '--use-sctp',
        help='use SCTP as transport protocol',
        action='store_true')
    parser.add_argument(
        '-6', '--ipv6',
        help="use IPv6 address family",
        action='store_true')
    parser.add_argument(
		'-b', '--buffer-size',
		default=4096,
		help='define buffer size to read; defaults to 4096 bytes'
	)
    parser.add_argument(
		'-t', '--timeout',
		default=5.0,
		help='set timeout; defaults to 5.0 sec'
	)
    parser.add_argument('--host',
                        default='localhost',
                        help="server address or domain name")
    parser.add_argument('--port',
                        default='5001',
                        help="server port or service name")
    arguments = parser.parse_args()

    return_code = client(
        arguments.host,
		arguments.port,
		arguments.use_sctp,
		arguments.ipv6,
		arguments.buffer_size,
		arguments.timeout
	)
    sys.exit(return_code)
