"""
Multiprocessing-safe logging via a shared queue.

This module patches the Python logging system so that child processes can
forward log records to the main process. Workers emit logs as usual with
`logging.getLogger(...).info(...)`; the patch redirects them into a
multiprocessing queue. The parent process consumes the queue and replays
the messages through its own logging handlers.


Example
-------
>>> import multiprocessing as mp
>>> import logging
>>> from utils import LogQueueConsumer, init_log_queue_for_children
>>>
>>> logging.basicConfig(level=logging.INFO)
>>> log_queue = mp.Manager().Queue()
>>>
>>> def worker(x):
...     log = logging.getLogger(__name__)
...     log.info("processing %s", x)
...     return x * 2
>>>
>>> with LogQueueConsumer(log_queue), mp.Pool(
...     processes=2,
...     initializer=init_log_queue_for_children,
...     initargs=(log_queue,)
... ) as pool:
...     results = pool.map(worker, range(4))
>>> print(results)
[0, 2, 4, 6]
"""

import logging
import os
import threading
import time
from multiprocessing.queues import Queue
from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    LogQueue: TypeAlias = Queue[tuple[int, str, int, str]]  # pid, logger name, level, message
else:
    LogQueue: TypeAlias = Queue

# Global queue (set by init in child processes)
log_queue: LogQueue | None = None


class QueueLogger(logging.Logger):
    """
    A Logger subclass that forwards log messages to a multiprocessing queue
    if one is configured, otherwise falls back to normal logging.

    Intended for multiprocessing use: children push logs into the queue,
    the parent consumes and replays them.
    """

    def _log_to_queue_or_local(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        if log_queue is not None:
            log_queue.put((os.getpid(), self.name, level, msg % args if args else msg))
        else:
            super().log(level, msg, *args, **kwargs)

    # Override the standard log methods
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        self._log_to_queue_or_local(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        self._log_to_queue_or_local(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        self._log_to_queue_or_local(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        self._log_to_queue_or_local(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        self._log_to_queue_or_local(logging.CRITICAL, msg, *args, **kwargs)


def init_log_queue_for_children(queue: LogQueue) -> None:
    """
    Multiprocessing initializer: configure all future loggers to use QueueLogger
    and set the global log_queue for forwarding.
    """
    global log_queue
    log_queue = queue
    logging.setLoggerClass(QueueLogger)  # patch the logger class


class LogQueueConsumer:
    """
    Context manager that consumes log records from a multiprocessing queue
    in a background thread and replays them locally.
    """

    def __init__(self, queue: LogQueue, interval: float = 0.5):
        self.queue = queue
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._drain()

        # Only close if supported (i.e. non-manager queues)
        if hasattr(self.queue, "close"):
            self.queue.close()
        if hasattr(self.queue, "join_thread"):
            self.queue.join_thread()
        return False

    def _loop(self) -> None:
        while not self._stop.is_set():
            self._drain()
            time.sleep(self.interval)

    def _drain(self) -> None:
        while not self.queue.empty():
            try:
                process_pid, logger_name, level, msg = self.queue.get_nowait()
                logging.getLogger(logger_name).log(level, f"[PID={process_pid}] {msg}")
            except Exception:
                break
