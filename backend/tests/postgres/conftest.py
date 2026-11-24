import os
from pathlib import Path
import subprocess
import sys
import uuid
from urllib.parse import quote
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


@pytest.fixture
def pg_engine():
    raw = os.environ.get('DSR_TEST_DATABASE_URL')
    if not raw:
        pytest.skip('DSR_TEST_DATABASE_URL is unset; PostgreSQL evidence must be run separately')
    url = make_url(raw)
    if not url.database or not url.database.endswith('_test'):
        pytest.fail('Refusing non-test database: database name must end in _test')
    schema = 'verify_' + uuid.uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA {schema}'))
    # A URL-encoded startup option also exercises Alembic percent handling.
    isolated = url.update_query_dict({'options': f'-csearch_path={schema}'})
    engine = create_engine(isolated, pool_pre_ping=True)
    try:
        environment = dict(os.environ, DATABASE_URL=isolated.render_as_string(hide_password=False))
        result = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=Path(__file__).parents[2], env=environment, text=True, capture_output=True)
        assert result.returncode == 0, result.stdout + result.stderr
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA {schema} CASCADE'))
        admin.dispose()
