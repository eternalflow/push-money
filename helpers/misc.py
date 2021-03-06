import logging
from functools import wraps
from logging.handlers import TimedRotatingFileHandler
from time import sleep
from typing import Union, Iterable, Callable
import math

from shortuuid import uuid as _uuid

from config import LOG_LEVEL


def retry(
        exceptions: Union[Exception, Iterable[Exception]], logger: Callable = print, tries=4, delay=3, backoff=2,
        default=None):
    """
    Retry calling the decorated function using an exponential backoff.

    :param exceptions: an exception (or iterable) to check  of exceptions)
    :param logger: <Callable> logger to use ('print' by default)
    :param tries: <int> number of times to try (not retry) before giving up
    :param delay: <int, float> initial delay between retries in seconds
    :param backoff: <int, float> backoff multiplier. For example, backoff=2 will make the delay x2 for each retry
    """
    exceptions = (exceptions, ) if not isinstance(exceptions, tuple) else exceptions
    logger_fn = logger if callable(logger) \
        else logger.info if isinstance(logger, logging.Logger) \
        else print

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            f_tries, f_delay = tries, delay
            while f_tries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    msg = f"{str(e)}, Retrying in {f_delay} seconds. fn: {f.__name__}\nargs: {args},\nkwargs: {kwargs}"
                    logger_fn(msg)
                    sleep(f_delay)
                    f_tries -= 1
                    f_delay *= backoff
            return default if default is not None else f(*args, **kwargs)
        return f_retry
    return deco_retry


def setup_logging():
    config = dict(
        force=True,
        level=getattr(logging, LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            TimedRotatingFileHandler("debug.log", when='midnight', utc=True, backupCount=7)
        ])
    logging.basicConfig(**config)


def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper


def uuid(unique_for_model=None, model_param=None, length=6):
    if not unique_for_model:
        return _uuid()[:length]
    if unique_for_model and not model_param:
        raise RuntimeError('Model param not specified')

    while True:
        link_id = _uuid()[:length]
        if unique_for_model.get_or_none(**{model_param: link_id}):
            continue
        return link_id
