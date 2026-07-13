import logging
import time
from typing import Callable, Tuple, Type

from phase2.interfaces.orchestrator_interface import IRetryManager, T
from phase2.exceptions.orchestration_exception import OrchestrationException

logger = logging.getLogger(__name__)

class RetryManager(IRetryManager):
    def __init__(self, retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)):
        self.retryable_exceptions = retryable_exceptions

    def execute_with_retry(self, max_retries: int, delay_ms: float, func: Callable[..., T], *args, **kwargs) -> T:
        attempts = 0
        last_exception = None

        while attempts <= max_retries:
            try:
                return func(*args, **kwargs)
            except self.retryable_exceptions as e:
                # Do not retry Timeout exceptions
                if e.__class__.__name__ == "TimeoutException":
                    raise e
                    
                last_exception = e
                attempts += 1
                if attempts > max_retries:
                    break
                
                sleep_sec = (delay_ms * (2 ** (attempts - 1))) / 1000.0
                logger.warning(f"Transient failure explicitly captured. Retrying ({attempts}/{max_retries}) natively after {sleep_sec}s: {e}")
                time.sleep(sleep_sec)
        
        if last_exception:
            raise last_exception
        raise OrchestrationException("Loop bound mapped empty securely natively.")
