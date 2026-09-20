from contextlib import contextmanager
import time
import os
import psutil
import logging
import resource

logger = logging.getLogger(__name__)

process = psutil.Process(os.getpid())

def memory_mb():
    return process.memory_info().rss / 1024 / 1024


@contextmanager
def performance_stage(name: str):
    memory_before = memory_mb()
    start = time.perf_counter()

    logger.info(
        "[PERF] START %s | memory=%.0f MiB",
        name,
        memory_before,
    )

    try:
        yield
    finally:
        duration = time.perf_counter() - start
        memory_after = memory_mb()

        logger.info(
            "[PERF] END %s | duration=%.3fs | "
            "memory=%.0f -> %.0f MiB | delta=%+.0f MiB",
            name,
            duration,
            memory_before,
            memory_after,
            memory_after - memory_before,
        )
   
def log_memory(label: str):
    current_memory_mb = memory_mb()
    
    # Linux reports ru_maxrss in KiB
    peak_memory_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

    logger.info("[MEMORY] %s current_rss=%.0f MiB | peak_rss=%.0f MiB", label, current_memory_mb, peak_memory_mb)