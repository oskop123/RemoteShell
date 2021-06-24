import os
import sys
import signal


def daemon_init(
    logger: object,
    uid: int,
    gid: int
) -> int:
	"""Function to make daemon out of program

	:param logger: Logger object to log errors and infos
	:type logger: object
	:param uid: UID to pass priviledges tos
	:type uid: int
	:param gid: GID to pass priviledges to
	:type gid: int
	:return: Return code
	:rtype: int
	"""
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
		if gid is not None:
			os.setregid(gid, gid)
		if uid is not None:
			os.setreuid(uid, uid)
	except OSError as e:
		logger.error(f'Unable to run as user: {uid}, group: {gid}. Msg: {e.strerror} ({e.errno})')
	logger.info(f'Process {os.path.basename(sys.argv[0])} started as a daemon. Old PID: {opid}, new PID: {os.getpid()}. Running as UID: {os.getuid()}, EUID: {os.geteuid()}, GID: {os.getgid()}, EGID: {os.getegid()}')
	return 0


def handle_request(
    logger: object,
    path_to_check: str,
    recv_data: str,
    read_side: int,
    write_side: int
):
	"""Function to handle requested commands

	:param logger: Logger object to log errors and infos
	:type logger: object
	:param path_to_check: Path to file with allowed commands
	:type path_to_check: str
	:param recv_data: Received data buffer from client
	:type recv_data: str
	:param read_side: Read side of the pipe
	:type read_side: int
	:param write_side: Write side of the pipe
	:type write_side: int
	"""
	os.close(read_side)
	permit = True
	if path_to_check != '':
		permit = check_requested_commands(path_to_check, recv_data)

	if permit:
		try:
			os.dup2(write_side, 1)
			os.execl("/bin/sh", "sh", "-c", recv_data)
		except OSError as e:
			logger.error(f'os.execl() error ({e.errno}): {e.strerror}')
			os.write(write_side, b'Error during execution')
	else:
		os.write(write_side, b'Illegal input!')
	


def check_requested_commands(
    path_to_check: str,
	recv_data: str
) -> bool:
	"""Function to check if command requested to execute are permited on the server

	:param path_to_check: Path to file
	:type path_to_check: str
	:param recv_data: Received data buffer from client
	:type recv_data: str
	:return: If data contains illegal not alllowed commands or words return False
	:rtype: bool
	"""
	busted_files = [path_to_check,
                	'/etc/passwd',
            		'/etc/shadow']

	with open(path_to_check, 'r') as actxt:
		ac = actxt.readlines()
  
	ac = [ x.strip().replace('\n', '') for x in ac ]
	print(recv_data)
	print(ac)

	permit = True
	for command in recv_data.decode('utf-8').strip().split('|'):
		words = command.strip().split()
		print(words)
		if words[0] not in ac:
			permit = False
		for word in words:
			if word in busted_files:
				permit = False
  
	return permit