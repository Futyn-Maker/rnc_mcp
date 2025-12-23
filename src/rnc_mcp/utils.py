import time
import functools


def measure_time(func):
    """
    Async decorator that measures execution time and logs it to FastMCP Context.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start_time
            msg = f"Operation '{func.__name__}' completed in {elapsed:.4f}s"

            # Try to find 'ctx' in keyword arguments
            ctx = kwargs.get('ctx')

            # If not found, look in positional args (duck typing)
            if not ctx:
                for arg in args:
                    if hasattr(arg, 'debug') and hasattr(arg, 'info'):
                        ctx = arg
                        break

            # Log to context
            if ctx:
                await ctx.debug(msg)

    return wrapper
