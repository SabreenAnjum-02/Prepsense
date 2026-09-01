import logging
import sys
from loguru import logger

class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages and route them to Loguru.
    This ensures that all third-party libraries (FastAPI, SQLAlchemy, etc.) 
    use the same structured JSON logging format as the main application.
    """
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_production_logging():
    """Configure Loguru for production JSON output and intercept standard logs."""
    # Remove standard loguru handlers
    logger.remove()

    # Add JSON formatted handler for stdout
    logger.add(
        sys.stdout, 
        serialize=True, 
        format="{time:YYYY-MM-DDTHH:mm:ssZ} | {level} | {name}:{function}:{line} | {message}",
        level="INFO"
    )

    # Intercept all standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Specific third-party logger adjustments
    for name in ["uvicorn.access", "uvicorn.error", "fastapi"]:
        target_logger = logging.getLogger(name)
        target_logger.handlers = [InterceptHandler()]
        target_logger.propagate = False

    logger.info("Production structured logging initialized.")
