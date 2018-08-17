# logconf

[![Build Status](https://travis-ci.org/anlutro/logconf.py.svg?branch=master)](https://travis-ci.org/anlutro/logconf.py)
[![Latest version on PyPI](https://img.shields.io/pypi/v/logconf.svg?maxAge=2592000)](https://pypi.org/project/logconf)
[![Licence](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Setting up logging in Python is verbose and error prone. This library aims to fix that, without replacing the standard library logging entirely.

```python
import logging
from logconf import logconf

with logconf() as logger:
    # simple example:
    logger.log_to_console_if_interactive(level=logging.DEBUG)
    if os.getenv('LOG_DEST'):  # can be "stdout" or "stderr"
        logger.log_to_file(os.getenv('LOG_DEST'), level=os.getenv('LOG_LEVEL'))

    # more fine-grained control:
    logger.log_json_to_file('/var/log/myapp.jsonlog', level=logging.WARNING)
    logger.log_json_to_file('/var/log/myapp_debug.jsonlog', level=logging.DEBUG)

    # configure sub-loggers:
    with logger.logger('urllib3') as sublogger:
        sublogger.level = logging.WARNING
    with logger.logger('myapp.security') as sublogger:
        sublogger.log_to_file('/var/log/myapp.security.log', level=logging.INFO)
```
