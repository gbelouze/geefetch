from collections.abc import Callable
from concurrent.futures import Executor, Future
from threading import Lock
from typing import ParamSpec, Self, TypeVar

_T = TypeVar("_T")
_P = ParamSpec("_P")

# Used by log and progress renderers in all of geefetch
global_console_lock = Lock()


class SequentialProcessPoolExecutor(Executor):
    """A fake process pool that runs tasks sequentially.

    Behaves like ProcessPoolExecutor for testing or debugging, but
    executes tasks in the calling thread. Ignores all pool arguments
    (initializer, initargs, max_workers, etc.).
    """

    def __init__(self, *_, **__):
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def map(self, fn, *iterables, timeout=None, chunksize=1):
        raise NotImplementedError

    def submit(self, fn: Callable[_P, _T], /, *args: _P.args, **kwargs: _P.kwargs) -> Future[_T]:
        """Execute the callable synchronously and return an already completed Future."""
        fut: Future[_T] = Future()
        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            fut.set_exception(e)
        else:
            fut.set_result(result)
        return fut

    def shutdown(self, wait: bool = True, *, cancel_futures: bool = False) -> None:
        """Compatibility no-op."""
        return None
