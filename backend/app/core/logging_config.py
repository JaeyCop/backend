import logging
import sys

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "pathname": record.pathname,
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return self.json_dumps(log_record)

    def json_dumps(self, obj):
        # This can be replaced with a more robust JSON library like ujson or orjson
        # if performance is critical and they are installed.
        import json
        return json.dumps(obj)

def configure_logging(log_level: str = "INFO"):
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers to prevent duplicate logs
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)

    # Optionally, add file handler for persistent logs
    # file_handler = logging.FileHandler("app.log")
    # file_handler.setFormatter(JsonFormatter())
    # logger.addHandler(file_handler)

    # Suppress noisy loggers
    logging.getLogger("uvicorn").propagate = False
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("sqlalchemy").propagate = False
    logging.getLogger("alembic").propagate = False
