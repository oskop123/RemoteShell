import os
import sys
import signal


def daemon_init(logger, uid: int, gid: int):
	print('Daemonizing..')
	opid = os.getpid()
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

	# Close STDIN, STDOUT, STDERR
	sys.stdout.flush()
	sys.stderr.flush()
	si = open('/dev/null', 'r')
	so = open('/dev/null', 'a+')
	se = open('/dev/null', 'a+')
	os.dup2(si.fileno(), sys.stdin.fileno())
	os.dup2(so.fileno(), sys.stdout.fileno())
	os.dup2(se.fileno(), sys.stderr.fileno())
 
	try:
		os.setregid(gid, gid)
		os.setreuid(uid, uid)
	except OSError as e:
		logger.error(f'Unable to run as user: {uid}, group: {gid}. Msg: {e.strerror} ({e.errno})')
	logger.info(f'Process {os.path.basename(sys.argv[0])} started as a daemon. Old PID: {opid}, new PID: {os.getpid()}. Running as UID: {os.getuid()}, EUID: {os.geteuid()}, GID: {os.getgid()}, EGID: {os.getegid()}')


def handle_request(path_of_origin: str, recv_data: str, read_side, write_side):
	os.close(read_side)
	permit = check_requested_commands(path_of_origin, recv_data)
	if permit:
		os.dup2(write_side, 1)
		os.execl("/bin/sh", "sh", "-c", recv_data)
	else:
		write_side.write("Illegal input!")


def check_requested_commands(path_of_origin: str, recv_data: str):
	busted_files = [os.path.join(path_of_origin, 'allowed_commands.txt'),
                	'/etc/passwd',
            		'/etc/shadow']

	with open(os.path.join(path_of_origin, 'allowed_commands.txt'), 'r') as actxt:
		ac = actxt.readlines().strip()

	permit = True
	for command in recv_data.strip().split('|'):
		words = command.strip().split()
		if words[0] not in ac:
			permit = False
		for word in words:
			if word in busted_files:
				permit = False
  
	return permit