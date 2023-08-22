from functools import partial
import logging
import os
import shutil
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from multiprocessing.synchronize import Lock

logger = logging.getLogger(__name__)

CUSTOM_BUCKETS = [0.0005, 0.001, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05, 0.06, 0.07, 0.08, 0.09,
                  0.1, 0.125, 0.15, 0.175, 0.2, 0.225, 0.25, 0.275, 0.3, 0.325, 0.35, 0.375, 0.4, 0.425, 0.45, 0.475,
                  0.5, 0.525, 0.55, 0.575, 0.6, 0.7, 0.8, 0.9, 1.0, 1.25, 1.5, 2, 2.5, 5.0, 10.0, 30.0, 60.0, 180.0,
                  360.0]

class PrometheusClient:
    def __init__(
        self,
        *,
        namespace: str = "",
        multiproc: bool = True,
        multiproc_lock: Optional["Lock"] = None,
        multiproc_dir: Optional[str] = None,
    ):
        """
        Set up multiproc_dir for prometheus to work in multiprocess mode,
        which is required when working with Gunicorn server

        Warning: for this to work, prometheus_client library must be imported after
        this function is called. It relies on the os.environ['prometheus_multiproc_dir']
        to properly setup for multiprocess mode
        """
        self.multiproc = multiproc
        self.namespace = namespace
        self._registry = None

        if multiproc:
            assert multiproc_dir is not None, "multiproc_dir must be provided"
            if multiproc_lock is not None:
                multiproc_lock.acquire()
            try:
                logger.debug("Setting up prometheus_multiproc_dir: %s", multiproc_dir)
                # Wipe prometheus metrics directory between runs
                # https://github.com/prometheus/client_python#multiprocess-mode-gunicorn
                # Ignore errors so it does not fail when directory does not exist
                shutil.rmtree(multiproc_dir, ignore_errors=True)
                os.makedirs(multiproc_dir, exist_ok=True)

                os.environ['prometheus_multiproc_dir'] = multiproc_dir
            finally:
                if multiproc_lock is not None:
                    multiproc_lock.release()

    @property
    def registry(self):
        if self._registry is None:
            from prometheus_client import (
                CollectorRegistry,
                multiprocess,
            )

            registry = CollectorRegistry()
            if self.multiproc:
                multiprocess.MultiProcessCollector(registry)
            self._registry = registry
        return self._registry

    @staticmethod
    def mark_process_dead(pid: int) -> None:
        from prometheus_client import multiprocess

        multiprocess.mark_process_dead(pid)

    def start_http_server(self, port: int, addr: str = "") -> None:
        from prometheus_client import start_http_server

        start_http_server(port=port, addr=addr, registry=self.registry)

    def generate_latest(self):
        from prometheus_client import generate_latest

        return generate_latest(self.registry)

    @property
    def CONTENT_TYPE_LATEST(self) -> str:
        from prometheus_client import CONTENT_TYPE_LATEST

        return CONTENT_TYPE_LATEST

    @property
    def Histogram(self):
        from prometheus_client import Histogram as Operator
        return partial(Operator, namespace=self.namespace, registry=self.registry, buckets=CUSTOM_BUCKETS)

    @property
    def Counter(self):
        from prometheus_client import Counter as Operator

        return partial(Operator, namespace=self.namespace, registry=self.registry)

    @property
    def Summary(self):
        from prometheus_client import Summary as Operator

        return partial(Operator, namespace=self.namespace, registry=self.registry)

    @property
    def Gauge(self):
        from prometheus_client import Gauge as Operator

        return partial(Operator, namespace=self.namespace, registry=self.registry)
