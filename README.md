# RemoteShell
Remote Shell in Python

<img src='https://img.shields.io/badge/license-MIT-brightgreen'></a>
<p>
    <img src='https://img.shields.io/badge/system-UNIX-brightgreen'></a>
    <img src='https://img.shields.io/badge/system-Windows-darkred'></a>
</p>
<p>
    <img src='https://img.shields.io/badge/protocol-TCP-brightgreen'></a>
    <img src='https://img.shields.io/badge/protocol-SCTP-brightgreen'></a>
    <img src='https://img.shields.io/badge/protocol-UDP-darkred'></a>
</p>

## Usage

There are two scripts that allow for communication:
- `server.py`
- `client.py`

### `server.py`

Default `HOST` and `PORT` values, that server is bound to, are:

- `HOST`: `''` => `0.0.0.0` for IPv4 or `*` for IPv6
- `PORT`: `5001`

```
usage: server.py [-h] [-c ALLOWED_COMMANDS] [-4] [-6] [-D] [-u AS_USER]
                 [--host HOST] [--port PORT]

Server for remote shell

optional arguments:
  -h, --help            show this help message and exit
  -c ALLOWED_COMMANDS, --allowed-commands ALLOWED_COMMANDS
                        specify path to .txt file with allowed commands to
                        execute; on default no restrictions for commands
  -4, --ipv4-only       run server only for IPv4
  -6, --ipv6-only       run server only for IPv6
  -D, --daemonize       daemonize server program
  -u AS_USER, --as-user AS_USER
                        run as user (UID, GID, EUID, EGID); only if
                        daemonized; defaults to "student"
  --host HOST           server address or domain name; defaults to ""
  --port PORT           server port or service name; defaults to "5001"
```

### `client.py`

```
usage: client.py [-h] [-S] [-6] [--host HOST] [--port PORT]

Client for remote shell

optional arguments:
  -h, --help      show this help message and exit
  -S, --use-sctp  use SCTP as transport protocol
  -6, --ipv6      use IPv6 address family
  --host HOST     server address or domain name
  --port PORT     server port or service name
```

## Important

On default there is no allowed commands, but the file can be added like this:

> name_of_the_file.txt
```
cat
ls
touch
rm
wc
grep
echo
pwd
```

Also main program (`server.py`) if daemonized will try to move `uid, gid, euid, egid` to user specified by `-u` flag. On default it is set to `student`. The change is needed if you try to run it without user `student` on your system. 
