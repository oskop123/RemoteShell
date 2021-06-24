import sys
import os
import argparse
import socket


def client(host: str, port: str, use_sctp: bool = False, ipv6: bool = False, timeout: float = 5.0) -> int:

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

	# Remote shell endless loop
	try:
		while True:
			cmd = input('> ')
			try:
				sock.sendall(bytes(cmd, 'utf-8'))
			except OSError as e:
				print(f"sendall() error ({e.errno}): {e.strerror}")
				return -3

			data = ''
			while True:
				try:
					data = sock.recv(buffer_size)
					if len(data) == 0:
						break
					print(data.decode('utf-8'))

				except OSError as e:
					print(f"sendall() error({e.errno}): {e.strerror}")
					return -3

				except socket.timeout as e:
					print("Command execution timeout")
					break
				
	except KeyboardInterrupt as e:
		sock.close()
		return 0


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),
                                     description="Client for remote shell")
    parser.add_argument(
        '-S', '--use-sctp',
        help="use SCTP as transport protocol",
        action='store_true')
    parser.add_argument(
        '-6', '--ipv6',
        help="use IPv6 address family",
        action='store_true')
    parser.add_argument('host',
                        default='localhost',
                        help="server address or domain name")
    parser.add_argument('port',
                        default='5001',
                        help="server port or service name")
    arguments = parser.parse_args()

    return_code = client(arguments.host, arguments.port,
                         arguments.use_sctp, arguments.ipv6)
    sys.exit(return_code)
