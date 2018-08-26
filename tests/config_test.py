from collections import defaultdict
from unittest import mock
import logging
import sys

import pytest

from logconf import LoggerConfig


def test_level_is_normalized():
    lc = LoggerConfig()
    for v in ('debug', 'DEBUG', logging.DEBUG):
        lc.level = v
        assert lc.level == logging.DEBUG


def test_handler_level_is_normalized():
    lc = LoggerConfig()
    for v in ('debug', 'DEBUG', logging.DEBUG):
        lc.handler_level = v
        assert lc.handler_level == logging.DEBUG


def test_logconf_basic():
    loggers = defaultdict(mock.Mock)
    patch = mock.patch('logging.getLogger', side_effect=loggers.__getitem__)
    with patch as mock_getlogger,  LoggerConfig('test') as lc:
        lc.log_to_file('stderr', logging.DEBUG)
        lc.log_to_file('stdout', logging.INFO)
        lc.log_to_file('/tmp/test.log', logging.WARNING)

    assert mock_getlogger.call_args_list == [mock.call('test'), mock.call('logconf')]

    assert loggers['test'].setLevel.call_args_list == [mock.call(logging.NOTSET)]
    assert len(loggers['test'].handlers) == 3
    assert loggers['test'].handlers[0].stream == sys.stderr
    assert loggers['test'].handlers[1].stream == sys.stdout
    assert loggers['test'].handlers[2].baseFilename == '/tmp/test.log'

    args = [logging.INFO, 'setting up log handler %r to %s with level %s']
    assert loggers['logconf'].log.call_args_list == [
        mock.call(*args, loggers['test'].handlers[0], 'stderr', logging.DEBUG),
        mock.call(*args, loggers['test'].handlers[1], 'stdout', logging.INFO),
        mock.call(*args, loggers['test'].handlers[2], '/tmp/test.log', logging.WARNING),
    ]


def test_logconf_sublogger():
    loggers = defaultdict(mock.Mock)
    patch = mock.patch('logging.getLogger', side_effect=loggers.__getitem__)
    with patch, LoggerConfig('test') as lc:
        lc.log_to_file('stderr', logging.DEBUG)
        with lc.logger('sub') as sub_lc:
            sub_lc.log_to_file('/tmp/test.log', logging.WARNING)

    assert len(loggers['test'].handlers) == 1
    assert loggers['test'].handlers[0].stream == sys.stderr

    assert len(loggers['test.sub'].handlers) == 1
    assert loggers['test.sub'].handlers[0].baseFilename == '/tmp/test.log'
