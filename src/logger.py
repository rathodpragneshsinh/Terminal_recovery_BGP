"""
This module provides a general logging setup for recording events and messages.
"""
import gzip
import logging
import os
import shutil
from datetime import datetime
from logging import handlers
from pathlib import Path
import dotenv
dotenv.load_dotenv()
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
LOGFILE = Path(os.getenv("TERMINAL_LOG", default=f"/var/log/terminal/terminal_{timestamp}.log"))


def rotator(source, destination):
    with open(source, "rb") as f_in:
        with gzip.open(destination, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(source)

logger = logging.getLogger("Terminal_recovery")
logger.setLevel(logging.DEBUG)
date_format = "%Y-%m-%d %H:%M:%S"
fmt = logging.Formatter(
    "%(asctime)s :: %(levelname)-5s :: %(message)s", datefmt=date_format
)

# For debug purpose
handler = logging.StreamHandler()
handler.setLevel(logging.CRITICAL)
handler.setFormatter(fmt)
logger.addHandler(handler)

file_handler = handlers.TimedRotatingFileHandler(
    LOGFILE, when="midnight", backupCount=13, encoding="UTF-8"
)


file_handler.setLevel(logging.INFO)
file_handler.setFormatter(fmt)
file_handler.namer = lambda name: name.replace(".log", "") + ".gz"

file_handler.rotator = rotator
logger.addHandler(file_handler)