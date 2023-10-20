from __future__ import annotations

import os


def cleanup():
    """
    Every time the Config class is instantiated the os.environ['PATH']
    value keeps having values appended to it.

    This cleanup method avoids getting the following exception
      ValueError: the environment variable is longer than 32767 characters
    """
    os.environ['PATH'] = os.pathsep.join(item for item in set(os.environ['PATH'].split(os.pathsep)))
