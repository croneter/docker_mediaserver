import sys
import os


MIN_PYTHON_VERSION = (3, 7, 0)


def sanity_checks():
    if sys.version_info < MIN_PYTHON_VERSION:
        raise RuntimeError('Need at least Python version {}, you got {}'
                           .format(MIN_PYTHON_VERSION, sys.version))
    try:
        if os.geteuid() == 0:
            raise RuntimeError('Do NOT run this script as root or with sudo!')
    except AttributeError:
        raise RuntimeError('Expected Unix-like operating system!')
