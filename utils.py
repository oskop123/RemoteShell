import os
import sys
import signal


def daemon_init(sockets: list):
	# Terminate parent
	try:
		pid = os.fork()
		if pid:
			sys.exit(0)
	except OSError:
		return -1

	# Become session leader
	os.chdir("/")
	os.setsid()
	os.umask(0)

	# Terminate child process
	try:
		pid = os.fork()
		if pid:
			sys.exit(0)
	except OSError:
		return -1

	for i in range(socket.MAXFD)

	# Close STDIN, STDOUT, STDERR
	sys.stdout.flush()
	sys.stderr.flush()
	si = file('/dev/null', 'r')
	so = file('/dev/null', 'a+')
	se = file('/dev/null', 'a+', 0)
	os.dup2(si.fileno(), sys.stdin.fileno())
	os.dup2(so.fileno(), sys.stdout.fileno())
	os.dup2(se.fileno(), sys.stderr.fileno())


def handle_request(recv_data: str, read_side, write_side):
	os.close(read_side)
	os.dup2(write_side, 1)
	os.execl("/bin/sh", "sh", "-c", recv_data)


def check_requested_commands(path_of_origin: str, recv_data: str):
    with open(os.path.join(path_of_origin, 'allowed_commands.txt'), 'r') as acyml:
        