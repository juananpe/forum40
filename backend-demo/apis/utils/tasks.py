from concurrent.futures import Future

import queue
from concurrent.futures.process import ProcessPoolExecutor
from threading import Lock
from types import SimpleNamespace
from typing import Any, Callable, Optional, List, Dict, Tuple

import classification
import embeddings


class Orchestrator:
    executor = ProcessPoolExecutor(1)

    def __init__(self, fn: Callable[..., Any]):
        self._fn = fn

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class ParallelOrchestrator(Orchestrator):
    def __call__(self, *args, **kwargs):
        obs = DoneObserver()
        fut = self.executor.submit(self._fn, *args, **kwargs)
        fut.add_done_callback(lambda _: obs.set_done())
        return obs


class SequentialOrchestrator(Orchestrator):
    def __init__(self, fn: Callable[..., Any]):
        super().__init__(fn)
        self._latest_future: Optional[Future] = None
        # queue of pending (DoneObserver, args, kwargs) entries
        self._call_queue: queue.Queue[Tuple[DoneObserver, List, Dict[str, Any]]] = queue.Queue()
        self._submit_lock = Lock()

    def __call__(self, *args, **kwargs):
        obs = DoneObserver()
        self._call_queue.put((obs, args, kwargs))
        self._maybe_start_next_call()
        return obs

    def _maybe_start_next_call(self):
        with self._submit_lock:
            try:
                if not self._latest_future or self._latest_future.done():
                    obs, args, kwargs = self._call_queue.get_nowait()
                    self._latest_future = self.executor.submit(self._fn, *args, **kwargs)
                    self._latest_future.add_done_callback(lambda _: self._maybe_start_next_call())
                    self._latest_future.add_done_callback(lambda _: obs.set_done())
            except queue.Empty:
                pass


async_tasks = SimpleNamespace(
    classification=SimpleNamespace(
        train=SequentialOrchestrator(classification.train),
        update=ParallelOrchestrator(classification.update),
    ),
    embeddings=SimpleNamespace(
        embed=SequentialOrchestrator(embeddings.embed),
        index=SequentialOrchestrator(embeddings.index),
        retrieve=SequentialOrchestrator(embeddings.retrieve),
    ),
)


class DoneObserver:
    def __init__(self):
        self._callbacks: List[Callable[[], Any]] = []
        self._is_done = False
        self._lock = Lock()

    def then(self, callback: Callable[[], Any]):
        with self._lock:
            if not self._is_done:
                self._callbacks.append(callback)
                return

        callback()

    def set_done(self):
        with self._lock:
            self._is_done = True
        for callback in self._callbacks:
            callback()
