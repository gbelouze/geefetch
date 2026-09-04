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
import threading
import time
from logging.handlers import QueueHandler
from multiprocessing.queues import Queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    LogQueue = Queue[logging.LogRecord]
else:
    LogQueue = Queue

log_queue: LogQueue | None = None


class PicklableQueueHandler(QueueHandler):
    """
    A QueueHandler that prepares records for multiprocessing by
    stringifying exceptions so they can be pickled.
    """

    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        record = super().prepare(record)

        if record.exc_info:
            # This turns the traceback object into a string and
            # stores it in record.exc_text
            record.exc_text = logging.Formatter().formatException(record.exc_info)
            record.exc_info = None  # Clear the unpicklable traceback

        return record


def init_log_queue_for_children(queue: LogQueue) -> None:
    from .progress import geefetch_debug

    # Clear any existing handlers to prevent duplicate output in the child
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)

    if not geefetch_debug():
        # Add the PicklableQueueHandler to the root
        # This catches ALL logs from ALL modules and sends them to the queue
        handler = PicklableQueueHandler(queue)
        root.addHandler(handler)
        root.setLevel(logging.INFO)

        # Ensure geefetch logs are not filtered too early
        logging.getLogger("geefetch").setLevel(logging.DEBUG)
        logging.getLogger("geefetch").propagate = True
    else:
        from .log import setup

        setup(logging.DEBUG)


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
                record = self.queue.get_nowait()
                record.msg = f"[PID={record.process}] {record.msg}"
                logging.getLogger(record.name).handle(record)
            except Exception:
                break
