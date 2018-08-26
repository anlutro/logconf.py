import json
import logging

from logconf import JsonFormatter


def test_basic_format():
    fmt = JsonFormatter()
    rec = logging.makeLogRecord(dict(
        levelname='DEBUG', name='name', msg='msg'
    ))
    data = json.loads(fmt.format(rec))
    assert data['level'] == 'DEBUG'
    assert data['name'] == 'name'
    assert data['msg'] == 'msg'
