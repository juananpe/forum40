from concurrent.futures import Future

from concurrent.futures.process import ProcessPoolExecutor
from threading import Lock
from types import SimpleNamespace
from typing import Any, Callable, Optional, List

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


class SingularOrchestrator(Orchestrator):
    # TODO: Enqueue repeated calls to be executed later
    # - add "key by" to e.g. allow one update per "source_id" parameter value
    #   (e.g. update source 1 and source 2 in parallel possible, but not source 1 twice)
    # - optionally only allow one in queue.
    #   E.g. 5 consecutive calls trigger once, enqueue one and omit the other three

    def __init__(self, fn: Callable[..., Any]):
        super().__init__(fn)
        self._latest_future: Optional[Future] = None
        self._submit_lock = Lock()

    def __call__(self, *args, **kwargs):
        with self._submit_lock:
            if not self._latest_future or self._latest_future.done():
                obs = DoneObserver()
                self._latest_future = self.executor.submit(self._fn, *args, **kwargs)
                self._latest_future.add_done_callback(lambda _: obs.set_done())
                return obs

        return None


async_tasks = SimpleNamespace(
    classification=SimpleNamespace(
        train=SingularOrchestrator(classification.train),
        update=ParallelOrchestrator(classification.update),
    ),
    embeddings=SimpleNamespace(
        embed=SingularOrchestrator(embeddings.embed),
        index=SingularOrchestrator(embeddings.index),
        retrieve=SingularOrchestrator(embeddings.retrieve),
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
