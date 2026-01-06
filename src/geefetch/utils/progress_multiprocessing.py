import logging
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from multiprocessing.queues import Queue
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

from rich.progress import Progress, TaskID

from geefetch.utils.multiprocessing import global_console_lock

log = logging.getLogger(__name__)


class ProgressProtocol(Protocol):
    """Protocol for objects exposing a Rich-like progress API."""

    def add_task(self, description: str, total: float | None = None, **kwargs: Any) -> Any: ...

    def update(self, task_id: Any, **kwargs: Any) -> None: ...

    def advance(self, task_id: Any, advance: float = 1.0) -> None: ...

    def refresh(self) -> None: ...

    def remove_task(self, task_id: Any) -> None: ...


if TYPE_CHECKING:
    ProgressQueue: TypeAlias = Queue[tuple[str, str, dict[str, Any]]]  # task_id, command, kwargs
else:
    ProgressQueue: TypeAlias = Queue


class QueuedProgress:
    """
    Proxy for rich.progress.Progress usable in multiprocessing.
    Enqueues commands so the main thread can safely handle progress updates.

    Parameters
    ----------
    q : ProgressQueue
        Queue shared with the main process.
    """

    def __init__(self, q: ProgressQueue):
        self.q = q

    def add_task(self, description: str, total: float | None = None, **kwargs: Any) -> str:
        """
        Mimics Progress.add_task but only enqueues the request.

        Parameters
        ----------
        description : str
            Task description.
        total : float | None
            Total number of steps. Defaults to None.
        **kwargs : Any
            Additional arguments to be passed to progress.add_task

        Returns
        -------
        str
            Task identifier (a UUID string suitable as dict key).
        """
        import uuid

        task_id = str(uuid.uuid4())
        self.q.put(("add_task", task_id, dict(description=description, total=total, **kwargs)))
        return task_id

    def update(self, task_id: str, **kwargs: Any) -> None:
        """Queue an update for the specified task."""
        self.q.put(("update", task_id, kwargs))

    def advance(self, task_id: str, advance: float = 1.0) -> None:
        """Queue an advance for the specified task."""
        self.q.put(("advance", task_id, {"advance": advance}))

    def remove_task(self, task_id: str) -> None:
        """Queue a task removal if it exists."""
        self.q.put(("remove_task", task_id, {}))

    def refresh(self) -> None:
        pass


class ProgressQueueConsumer:
    """
    Context manager that consumes progress updates from a multiprocessing queue
    in a background thread and updates a live rich.progress.Progress instance.

    Parameters
    ----------
    queue : ProgressQueue
        Queue to consume progress updates from.
    progress : Progress
        Rich progress object to update.
    interval : float
        Time between queue drain iterations. Defaults to 0.1.
    """

    def __init__(self, queue: ProgressQueue, progress: Progress, interval: float = 0.1):
        self.queue = queue
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._progress = progress
        self._task_map: dict[str, int] = {}

    def __enter__(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._drain()

        # Only close if supported (non-manager queues)
        if hasattr(self.queue, "close"):
            self.queue.close()
        if hasattr(self.queue, "join_thread"):
            self.queue.join_thread()
        return False

    def _loop(self) -> None:
        """Background loop that drains the queue periodically."""
        while not self._stop.is_set():
            self._drain()
            time.sleep(self.interval)

    def _drain(self) -> None:
        """Consume all pending messages from the queue."""
        while not self.queue.empty():
            try:
                cmd, task_id, data = self.queue.get_nowait()
                with global_console_lock:
                    if cmd == "add_task":
                        self._task_map[task_id] = self._progress.add_task(**data)
                    elif cmd == "update":
                        self._progress.update(self._task_map[task_id], **data)
                    elif cmd == "advance":
                        self._progress.advance(self._task_map[task_id], **data)
                    elif cmd == "remove_task":
                        self._progress.remove_task(self._task_map[task_id])
            except Exception as e:
                log.error(f"Exception consuming progress queue : {e}")
                break


@contextmanager
def add_task_finally_remove(progress: Progress, *args: Any, **kwargs: Any) -> Iterator[TaskID]:
    """
    Context manager that adds a progress task and ensures it is removed
    when the context exits, regardless of success or failure.

    Parameters
    ----------
    progress : Progress
        A `rich.progress.Progress` instance managing the tasks.
    *args : Any
        Positional arguments passed to `progress.add_task`.
    **kwargs : Any
        Keyword arguments passed to `progress.add_task`.

    Yields
    ------
    TaskID
        The task ID returned by `progress.add_task`.

    Notes
    -----
    - The task is first hidden (`visible=False`) and then removed from
      the progress display when the context exits.
    - Any exception raised within the context is propagated after
      cleanup.

    Examples
    --------
    >>> from rich.progress import Progress
    >>> progress = Progress()
    >>> with progress:
    ...     with add_task_finally_remove(progress, "Processing", total=100) as task:
    ...         for i in range(100):
    ...             progress.update(task, advance=1)
    """
    try:
        task = progress.add_task(*args, **kwargs)
        yield task
    finally:
        progress.update(task, visible=False)
        progress.remove_task(task)
