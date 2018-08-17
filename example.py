#!/usr/bin/env python
from logconf import logconf
import argparse
import logging
log = logging.getLogger('scripts.log')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--colors', action='store_true')
    parser.add_argument('-f', '--log-file')
    parser.add_argument('--file-level')
    parser.add_argument('--console-level')
    parser.add_argument('-j', '--json', action='store_true')
    parser.add_argument('-l', '--long-levels', action='store_true')
    parser.add_argument('-t', '--tree', action='store_true')
    args = parser.parse_args()

    with logconf(shorten_levels=not args.long_levels, colors=args.colors) as cfg:
        if args.log_file:
            cfg.log_to_file(args.log_file, args.file_level, json=args.json)
        cfg.log_to_console_if_interactive(args.console_level)

    log.debug('debug test msg with extra', extra=dict(foo='bar'))
    log.debug('debug test msg')
    log.info('info test msg')
    log.warning('warning test msg')
    log.error('error test msg')
    log.critical('critical test msg')
    try:
        raise Exception('test exception')
    except:
        log.exception('exception test msg')

    if args.tree:
        import logging_tree
        print()
        logging_tree.printout()

if __name__ == '__main__':
    main()
