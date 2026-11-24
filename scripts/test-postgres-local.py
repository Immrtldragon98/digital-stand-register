#!/usr/bin/env python3
"""Optional local test runner: pip install pgserver==0.1.4, then run this script.

Creates/stops/removes an isolated TCP-only PostgreSQL cluster in a temporary folder.
No production URL is read, copied, or changed. Server and tests share one process tree.
"""
from pathlib import Path
import os
import socket
import subprocess
import sys
import tempfile
import pgserver

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='dsr-pg-test-') as temporary:
    data = Path(temporary) / 'data'
    data.mkdir()
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    pgserver.initdb(['--auth=trust', '--encoding=UTF8', '-U', 'postgres'], pgdata=data)
    started = False
    try:
        pgserver.pg_ctl(['-w', '-o', f"-h 127.0.0.1 -p {port} -c unix_socket_directories=''", '-l', str(Path(temporary)/'postgres.log'), 'start'], pgdata=data)
        started = True
        pgserver.createdb(['-h', '127.0.0.1', '-p', str(port), '-U', 'postgres', 'dsr_release_test'])
        environment = dict(os.environ, DSR_TEST_DATABASE_URL=f'postgresql://postgres@127.0.0.1:{port}/dsr_release_test')
        result = subprocess.run([sys.executable, '-m', 'pytest', '-q', 'tests/postgres', *sys.argv[1:]], cwd=root/'backend', env=environment)
    finally:
        if started:
            pgserver.pg_ctl(['-w', '-m', 'fast', 'stop'], pgdata=data)
    raise SystemExit(result.returncode)
