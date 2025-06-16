import functools
import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def log_execution(name: str = None):
    def decorator(func: Callable):
        func_name = name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger.info(f"[START] {func_name} args={args} kwargs={kwargs}")
            start_time = time.perf_counter()

            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                logger.info(f"[END] {func_name} -> {result} (took {duration:.3f}s)")
                return result
            except Exception as e:
                logger.exception(f"[ERROR] {func_name} raised: {e}")
                raise

        return wrapper

    return decorator
