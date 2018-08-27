from json import dumps as json_dumps
import contextlib
import logging
import logging.handlers
import sys
import time

__all__ = ('global_logconf', 'LoggerConfig')


class JsonFormatter(logging.Formatter):
    """
    Formatter for writing line-delimited JSON logs.
    """
    separators = (',', ':')

    def __init__(self, fields=None, datefmt=None):
        super(JsonFormatter, self).__init__(datefmt=datefmt)
        self.fields = set(fields) if fields else set()

    # pass json_dumps as arg for performance
    def format(self, record, json_dumps=json_dumps):
        record.message = record.getMessage()

        data = {
            'level': record.levelname,
            'name': record.name,
            'msg': self.formatMessage(record),
            'time': time.strftime(
                '%Y-%m-%dT%H:%M:%S%z',
                self.converter(record.created),
            ),
        }

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            data['exc_info'] = record.exc_text

        if record.stack_info and 'stack_info' in self.fields:
            data['stack_info'] = self.formatStack(record.stack_info)

        for key in self.fields - data.keys():
            data[key] = getattr(record, key)

        return json_dumps(data, separators=self.separators)

    def __repr__(self):
        return 'JsonFormatter(keys=[%s])' % ','.join(self.fields)


def get_formatter(colors, shortened_levels=True):
    level_len = 5 if shortened_levels else 8
    if colors:
        level_len += 11
        fmt = ('\033[37m%(asctime)s %(levelname_colored)' + str(level_len) +
               's\033[37m %(name)s \033[0m%(message)s')
    else:
        fmt = ('%(asctime)s [%(levelname)' + str(level_len) +
               's] [%(name)s] %(message)s')
    return logging.Formatter(fmt)


class ColorLogRecord(logging.LogRecord):
    RESET = '\033[0m'
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = (
        '\033[1;%dm' % (i + 30) for i in range(8)
    )

    COLORS = {
        logging.DEBUG: GREEN,
        logging.INFO: BLUE,
        logging.WARNING: MAGENTA,
        logging.ERROR: YELLOW,
        logging.CRITICAL: RED,
    }

    def __init__(self, *args, **kwargs):
        super(ColorLogRecord, self).__init__(*args, **kwargs)
        self.levelname_colored = ''.join((
            self.COLORS[self.levelno],
            self.levelname,
            self.RESET,
        ))


def shorten_levels_globally():
    logging._levelToName[logging.WARNING] = 'WARN'
    logging._nameToLevel['WARN'] = logging.WARNING
    logging._levelToName[logging.CRITICAL] = 'CRIT'
    logging._nameToLevel['CRIT'] = logging.CRITICAL


def normalize_level(level):
    if level is None:
        return logging.NOTSET
    if isinstance(level, str):
        return logging.getLevelName(level.upper())
    return level


class LoggerConfig:
    colors = False
    shorten_levels = False

    def __init__(self, name='', level=logging.NOTSET, *,
                 handler_level=logging.NOTSET, propagate=False,
                 exclusive=True):
        """
        Args:
          name: Name of the logger to start configuring at.
          level: Which level to set on the root logger. If this is set, levels
            lower than this will be ignored even if set on individual handlers,
            so it's usually a good idea to leave this at NOTSET.
          handler_level: Which level to set for handlers by default.
          propagate: Whether logs should propagate to the parent logger.
            Only applies if not configuring a root logger.
          exclusive: Whether to overwrite existing handlers.
        """
        self.name = name
        self.level = level
        self.is_root = name == ''
        self.handler_level = handler_level
        self.propagate = propagate
        self.exclusive = exclusive

        self._startup_messages = []
        self._handlers = []

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, level):
        self._level = normalize_level(level)

    @property
    def handler_level(self):
        return self._handler_level

    @handler_level.setter
    def handler_level(self, level):
        self._handler_level = normalize_level(level)

    def add_startup_message(self, level, message, *args):
        """
        Add a line to be logged once logging has been set up.
        """
        self._startup_messages.append((level, message) + args)

    def log_to_file(self, file, level=None, json=False, json_fields=None):
        """
        Log to a file.
        """
        if isinstance(file, str) and file.lower() in ('stderr', 'stdout'):
            handler = logging.StreamHandler(getattr(sys, file.lower()))
        else:
            handler = logging.handlers.WatchedFileHandler(file)

        if json:
            formatter = JsonFormatter(fields=json_fields)
        else:
            is_interactive = handler.stream and handler.stream.isatty()
            formatter = get_formatter(
                colors=self.colors and is_interactive,
                shortened_levels=self.shorten_levels,
            )
        handler.setFormatter(formatter)

        if level is None:
            level = self.handler_level
        else:
            level = normalize_level(level)
        handler.setLevel(level)

        self.add_startup_message(
            logging.INFO,
            'setting up log handler %r to %s with level %s',
            handler, file, level,
        )
        self.add_handler(handler)

    def log_json_to_file(self, file, level=None, fields=None):
        """
        Log in JSON format to a file.
        """
        self.log_to_file(file, level=level, json=True, json_fields=fields)

    def log_to_console_if_interactive(self, level=None):
        """
        If running in an interactive terminal, log to it.
        """
        if sys.__stderr__.isatty():
            self.log_to_file('stderr', level=level)

    def add_handler(self, handler):
        """
        Add a handler to the logger.
        """
        self._handlers.append(handler)

    def finish(self):
        """
        Complete logging setup.
        """
        root = logging.getLogger(self.name)
        root.setLevel(self.level)

        root.propagate = bool(self._handlers if self.propagate is None
                              else self.propagate)

        if self.exclusive:
            root.handlers = self._handlers[:]
        else:
            root.handlers.extend(self._handlers)

        logger = logging.getLogger(__name__)
        for line in self._startup_messages:
            level, message = line[:2]
            args = line[2:]
            logger.log(level, message, *args)

    @contextlib.contextmanager
    def logger(self, logger_name):
        assert logger_name, 'must provide logger_name'
        logger_name = '.'.join(n for n in (self.name, logger_name) if n)
        lc = type(self)(logger_name)
        yield lc
        lc.finish()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.finish()


@contextlib.contextmanager
def global_logconf(*, shorten_levels=False, colors=False, **kwargs):
    logger_config = LoggerConfig(**kwargs)

    if shorten_levels:
        LoggerConfig.shorten_levels = True
        shorten_levels_globally()

    if colors:
        LoggerConfig.colors = True
        logging.setLogRecordFactory(ColorLogRecord)

    yield logger_config

    logger_config.finish()
