#! /usr/bin/env python
"""This module simply gives a logging functionality for all other modules to use."""
from __future__ import absolute_import

import logging

from mozci.utils.transfer import path_to_file

LOG = None


def setup_logging(level=logging.INFO, datefmt='%I:%M:%S', show_timestamps=True,
                  show_name_level=False):
    """
    Save every message (including debug ones) to ~/.mozilla/mozci/mozci-debug.log.

    Log messages of level equal or greater then 'level' to the terminal.

    As seen in:
    https://docs.python.org/2/howto/logging-cookbook.html#logging-to-multiple-destinations
    """
    global LOG
    if LOG:
        return LOG

    # We need to set the root logger or we will not see messages from dependent
    # modules
    LOG = logging.getLogger()

    format = ''
    if show_timestamps:
        format += '%(asctime)s '

    format += '%(name)s'

    if show_name_level:
        format += ' %(levelname)s" '

    format += '\t%(message)s'

    # Handler 1 - Store all debug messages in a specific file
    logging.basicConfig(level=logging.DEBUG,
                        format=format,
                        datefmt=datefmt,
                        filename=path_to_file('mozci-debug.log'),
                        filemode='w')

    # Handler 2 - Console output
    console = logging.StreamHandler()
    console.setLevel(level)
    # console does not use the same formatter specified in basicConfig
    # we have to set it again
    formatter = logging.Formatter(format, datefmt=datefmt)
    console.setFormatter(formatter)
    LOG.addHandler(console)
    LOG.info("Setting %s level" % logging.getLevelName(level))

    if level != logging.DEBUG:
        # requests is too noisy and adds no value
        logging.getLogger("requests").setLevel(logging.WARNING)

    return LOG
