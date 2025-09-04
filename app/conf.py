import logging.config
import time
import os
from typing import Self
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


def setup_logging(env="development"):
    """Configure logging based on the environment."""

    # Base config for all environments
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "standard",
                "filename": "app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
            },
        },
        "loggers": {
            "": {"handlers": ["console"], "level": "INFO"},  # Root logger
            "app": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
        },
    }

    # Environment-specific overrides
    if env == "development":
        log_config["loggers"]["app"]["level"] = "DEBUG"
        log_config["loggers"]["uvicorn"]["level"] = "DEBUG"
    elif env == "production":
        log_config["loggers"]["app"]["handlers"].append("file")
        log_config["loggers"]["uvicorn"]["handlers"].append("file")
        log_config["handlers"]["console"]["level"] = "INFO"

    # Apply configuration
    logging.config.dictConfig(log_config)


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, *, logger: logging.Logger) -> None:
        self._logger = logger
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request info
        self._logger.info(
            f"Request from {request.client.host if request.client else '?'} started: {request.method} {request.url}"
        )

        # Process the request
        try:
            response: Response = await call_next(request)

            process_time = time.time() - start_time
            self._logger.info(
                f"Request completed: {request.method} {request.url} {request.headers}- Status: {response.status_code} - Time: {process_time:.3f}s"
            )

            return response
        except Exception as e:
            self._logger.error(
                f"Request failed: {request.method} {request.url} - Error: {str(e)}"
            )
            raise

class PrimitiveAuthorizationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, *, logger: logging.Logger) -> None:
        self._logger = logger
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        self._logger.debug(os.getenv('LEADERBOARD_API_KEY', 'set_key'))
        if request.headers['authorization'] == os.getenv('LEADERBOARD_API_KEY', 'set_key'):
            response: Response = await call_next(request)
            return response
        else:
            self._logger.warning('Unauthorized request')
            return JSONResponse(
                status_code=401,
                headers={"WWW-Authenticate": "Prmtv realm='Poorly secured leaderboard'"},
                content={"details": "Unauthorized"},
    )