from src.db import get_session, init_db


def test_db_init():
    init_db()
    s = get_session()
    assert s is not None
