import logging
import sys
from logging.handlers import RotatingFileHandler


def initialize_logger():
    """
    Инициализация и настройка логгера
    """

    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.INFO,
        handlers=[
            RotatingFileHandler("bot_errors.log", maxBytes=200000, backupCount=10),
            logging.StreamHandler(sys.stdout)
        ]
    )

    file_handler = logging.getLogger().handlers[0]
    file_handler.setLevel(logging.ERROR)

    stream_handler = logging.getLogger().handlers[1]
    stream_handler.setLevel(logging.INFO)
