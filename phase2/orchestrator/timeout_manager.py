import logging
import concurrent.futures
from typing import Callable

from phase2.interfaces.orchestrator_interface import ITimeoutManager, T
from phase2.exceptions.orchestration_exception import TimeoutException

logger = logging.getLogger(__name__)

class TimeoutManager(ITimeoutManager):
    def execute_with_timeout(self, timeout_ms: float, func: Callable[..., T], *args, **kwargs) -> T:
        timeout_sec = timeout_ms / 1000.0
        if timeout_sec <= 0:
            return func(*args, **kwargs)
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout_sec)
            except concurrent.futures.TimeoutError:
                logger.error(f"Execution exceeded timeout limit natively: {timeout_sec}s")
                raise TimeoutException(f"Execution bound forcefully terminated securely after {timeout_ms}ms")
