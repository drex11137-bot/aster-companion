import os
import multiprocessing
import time
import random
import tempfile
from lock_manager import safe_update_memory, recover_and_cleanup, atomic_write

TEST_DIR = os.path.join(tempfile.gettempdir(), "memory_test") # nosec B108
TEST_FILE = os.path.join(TEST_DIR, "concurrent_mem.md")

def worker(worker_id, num_updates):
    for i in range(num_updates):
        def update_fn(content):
            # simulate reading and processing
            time.sleep(random.uniform(0.01, 0.03))
            lines = content.split('\n') if content else []
            lines.append(f"Worker {worker_id} update {i}")
            return '\n'.join(lines)
        
        try:
            safe_update_memory(TEST_FILE, update_fn)
        except Exception as e:
            print(f"Worker {worker_id} failed: {e}")

def simulate_crash():
    print("Simulating crash during write...")
    # Create a stale tmp file
    os.makedirs(TEST_DIR, exist_ok=True)
    stale_tmp = os.path.join(TEST_DIR, "concurrent_mem.md.stale123.tmp")
    with open(stale_tmp, 'w') as f:
        f.write("partial write content")
    
    # modify mtime to simulate age
    old_time = time.time() - 4000
    os.utime(stale_tmp, (old_time, old_time))
    
    print("Crash simulation ready.")
    return stale_tmp

def main():
    print("Running Crash Recovery Test...")
    stale_tmp = simulate_crash()
    assert os.path.exists(stale_tmp)
    
    cleaned = recover_and_cleanup(TEST_DIR, max_age_seconds=3600)
    print(f"Cleaned up {cleaned} files.")
    assert not os.path.exists(stale_tmp), "Stale tmp file was not cleaned up!"
    
    print("\nRunning Concurrency Test...")
    if os.path.exists(TEST_FILE):
        os.unlink(TEST_FILE)
        
    num_workers = 5
    updates_per_worker = 10
    
    processes = []
    for i in range(num_workers):
        p = multiprocessing.Process(target=worker, args=(i, updates_per_worker))
        processes.append(p)
        p.start()
        
    for p in processes:
        p.join()
        
    with open(TEST_FILE, 'r') as f:
        content = f.read()
        
    lines = [l for l in content.split('\n') if l.strip()]
    expected_lines = num_workers * updates_per_worker
    
    print(f"Expected lines: {expected_lines}")
    print(f"Actual lines: {len(lines)}")
    
    assert len(lines) == expected_lines, "Concurrency bug: lost updates!"
    print("Concurrency test PASSED.")

if __name__ == '__main__':
    main()
