# Make sure to import all the tasks here, so that they get registered with
# the server class (see ../server.py).

from .config import config                      # noqa
from .langid import run_langid                  # noqa
from .tasklist import tasklist                  # noqa
from .test import trivial_task                  # noqa
from .tokenize import tokenize                  # noqa
