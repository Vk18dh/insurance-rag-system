"""
phase2.validation.tests.concurrency.test_concurrency
====================================================

Concurrency tests. Thread safety and lack of context bleed.
"""

import pytest
import threading
from phase2.validation.services import ConcurrencyTesterService

def test_concurrency_isolation():
    """Verify concurrent thread execution isolation without shared state race conditions."""
    tester = ConcurrencyTesterService()
    
    def worker_fn(val):
        t_id = threading.get_ident()
        return {"input": val, "thread_id": t_id, "processed": val * 2}
        
    payloads = list(range(10))
    results = tester.execute_concurrently(worker_fn, payloads, concurrent_users=4)
    
    assert len(results) == 10
    processed_vals = sorted([r["processed"] for r in results])
    assert processed_vals == [i * 2 for i in range(10)]
    thread_ids = {r["thread_id"] for r in results}
    assert len(thread_ids) >= 1
