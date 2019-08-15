import time
import logging
from functools import wraps

logger = logging.getLogger('todos')


def timer(func):
    """
    Simple decorator for time measuring
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        ret_val = func(*args, **kwargs)
        duration = time.time() - start_time

        logger.info(f'call function "{func.__qualname__}" from "{func.__module__}"'
                    f' with duration time {duration:.3f}s')
        return ret_val
    return wrapper
