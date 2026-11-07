import os
import fcntl
import time
import tempfile
import glob
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LockTimeout(Exception):
    pass

@contextmanager
def file_lock(filepath, timeout=5.0):
    lock_file = f"{filepath}.lock"
    # Ensure directory exists
    dirname = os.path.dirname(filepath)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
        
    fd = os.open(lock_file, os.O_RDWR | os.O_CREAT | os.O_TRUNC)
    start_time = time.time()
    
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.time() - start_time > timeout:
                os.close(fd)
                raise LockTimeout(f"Could not acquire lock on {lock_file} within {timeout} seconds")
            time.sleep(0.05)
            
    try:
        yield lock_file
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

def atomic_write(filepath, content):
    """
    Writes content to filepath atomically using a temporary file.
    """
    dirname = os.path.dirname(filepath)
    if not dirname:
        dirname = '.'
    os.makedirs(dirname, exist_ok=True)
    
    fd, tmp_path = tempfile.mkstemp(dir=dirname, prefix=os.path.basename(filepath)+".", suffix=".tmp")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, filepath)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise e

def safe_update_memory(filepath, update_fn, timeout=5.0):
    """
    Acquires lock, reads content, calls update_fn(content), writes atomically.
    """
    with file_lock(filepath, timeout):
        content = ""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
        
        new_content = update_fn(content)
        
        if new_content is not None:
            atomic_write(filepath, new_content)

def recover_and_cleanup(directory, max_age_seconds=3600):
    """
    Cleans up orphaned .tmp files and stale .lock files.
    """
    now = time.time()
    cleaned_tmp = 0
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith('.tmp'):
                try:
                    if now - os.path.getmtime(filepath) > max_age_seconds:
                        os.unlink(filepath)
                        logger.info(f"Cleaned up orphaned temp file: {filepath}")
                        cleaned_tmp += 1
                except OSError:
                    pass
    return cleaned_tmp
