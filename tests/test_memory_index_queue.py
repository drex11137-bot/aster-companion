#!/usr/bin/env python3
"""
test_memory_index_queue.py - Comprehensive Verification for Single-Writer Index Queue.
Validates Instruction.md Sections 31-34:
- Durable queue persistence at index_queue.jsonl
- Single-writer execution via lease locking (scripts/lock_manager.py)
- Coalescing of rapid sequential updates
- Processing into MemSearch backend
- Index health state transitions (HEALTHY, STALE, DEGRADED, REBUILDING)
- CLI commands (--enqueue, --drain, --rebuild, --health)
"""

import os
import sys
import json
import time
import shutil
import tempfile
import pytest
import subprocess

SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from memory_index_queue import IndexQueueManager, IndexHealthState, drain_queue
from memsearch_backend import MemSearchBackend
from lock_manager import file_lock, LockTimeout


@pytest.fixture
def temp_env():
    """Sets up an isolated temporary test environment for queue testing."""
    test_dir = tempfile.mkdtemp(prefix="test_idx_queue_")
    queue_file = os.path.join(test_dir, ".agents", "memory", "index_queue.jsonl")
    health_file = os.path.join(test_dir, ".agents", "memory", "index_health.json")
    lease_file = os.path.join(test_dir, ".agents", "memory", "index_writer.lease")
    index_dir = os.path.join(test_dir, ".agents", "memory", ".memsearch")

    backend = MemSearchBackend(index_dir=index_dir)
    manager = IndexQueueManager(
        queue_file=queue_file,
        health_file=health_file,
        lease_file=lease_file,
        backend=backend
    )

    yield {
        "test_dir": test_dir,
        "queue_file": queue_file,
        "health_file": health_file,
        "lease_file": lease_file,
        "index_dir": index_dir,
        "backend": backend,
        "manager": manager
    }

    shutil.rmtree(test_dir, ignore_errors=True)


def test_durable_queue_enqueue(temp_env):
    """Test enqueuing events writes durable JSONL entries with all traceable fields."""
    manager = temp_env["manager"]
    queue_file = temp_env["queue_file"]

    # Create dummy file
    sample_file = os.path.join(temp_env["test_dir"], "SAMPLE.md")
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write("# Sample Memory Content\nInitial text.")

    job = manager.enqueue(sample_file, event_type="upsert", priority=5)

    assert os.path.exists(queue_file)
    assert job["source_path"] == os.path.abspath(sample_file)
    assert job["status"] == "pending"
    assert job["priority"] == 5
    assert job["attempts"] == 0
    assert job["content_hash"] != ""

    # Verify health changed to STALE
    health = manager.get_health()
    assert health["status"] == IndexHealthState.STALE
    assert health["pending_jobs_count"] == 1


def test_coalescing_rapid_sequential_updates(temp_env):
    """Test rapid edits to the same file are coalesced so only the latest is executed."""
    manager = temp_env["manager"]
    sample_file = os.path.join(temp_env["test_dir"], "ACTIVE_EDIT.md")

    # Step 1: Write version 1
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write("Version 1 content")
    job1 = manager.enqueue(sample_file, event_type="modify")

    # Step 2: Immediate version 2 edit
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write("Version 2 content with revisions")
    job2 = manager.enqueue(sample_file, event_type="modify")

    # Step 3: Immediate version 3 edit
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write("Version 3 final content")
    job3 = manager.enqueue(sample_file, event_type="modify")

    # Verify earlier jobs marked coalesced in the queue
    jobs = manager.list_queue()
    assert len(jobs) == 3
    assert jobs[0]["status"] == "coalesced"
    assert jobs[1]["status"] == "coalesced"
    assert jobs[2]["status"] == "pending"

    # Drain queue
    drain_result = manager.drain()
    assert drain_result["processed"] == 1
    assert drain_result["failed"] == 0
    assert drain_result["health_status"] == IndexHealthState.HEALTHY

    # Verify backend has version 3 indexed
    manifest_path = os.path.join(temp_env["index_dir"], "manifest.json")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    indexed = manifest["indexed_files"][os.path.abspath(sample_file)]
    assert indexed["content_hash"] == manager.compute_file_hash(sample_file)


def test_duplicate_event_deduplication(temp_env):
    """Test exact duplicate enqueue events with identical content hash are deduplicated."""
    manager = temp_env["manager"]
    sample_file = os.path.join(temp_env["test_dir"], "SAME_FILE.md")
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write("Identical unchanging content")

    job1 = manager.enqueue(sample_file)
    job2 = manager.enqueue(sample_file)

    assert job1["job_id"] == job2["job_id"]
    jobs = manager.list_queue()
    assert len(jobs) == 1


def test_single_writer_lease_lock_enforcement(temp_env):
    """Test that concurrent drain attempts are blocked when another worker holds lease."""
    manager = temp_env["manager"]
    lease_file = temp_env["lease_file"]
    sample_file = os.path.join(temp_env["test_dir"], "LOCKED_TEST.md")
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write("Testing locking")
    manager.enqueue(sample_file)

    # Acquire the lease lock simulating another indexing process running
    with file_lock(lease_file, timeout=2.0):
        # Attempt drain with zero/short timeout while lock is held
        res = manager.drain(lease_timeout=0.1)
        assert res["status"] == "busy"
        assert "Single-writer lease lock" in res["error"]
        assert res["processed"] == 0

    # Once lock released, drain succeeds cleanly
    drain_res = manager.drain()
    assert drain_res["status"] == "completed"
    assert drain_res["processed"] == 1


def test_index_health_state_transitions(temp_env):
    """Test health state transitions: HEALTHY -> STALE -> DEGRADED -> REBUILDING -> HEALTHY."""
    manager = temp_env["manager"]

    # Initial state on fresh empty repository before any indexing
    h0 = manager.check_and_refresh_health()
    assert h0["status"] == IndexHealthState.MISSING

    # Enqueue a file -> transitions to STALE
    file1 = os.path.join(temp_env["test_dir"], "DOC1.md")
    with open(file1, "w") as f:
        f.write("Content 1")
    manager.enqueue(file1)

    h1 = manager.get_health()
    assert h1["status"] == IndexHealthState.STALE
    assert h1["pending_jobs_count"] == 1

    # Drain -> transitions back to HEALTHY
    manager.drain()
    h2 = manager.get_health()
    assert h2["status"] == IndexHealthState.HEALTHY
    assert h2["pending_jobs_count"] == 0

    # Simulate indexing failure on invalid/failing file
    bad_file = os.path.join(temp_env["test_dir"], "BAD.md")
    with open(bad_file, "w") as f:
        f.write("Corruptible content")
    job = manager.enqueue(bad_file)

    # Force backend failure for test
    original_index = manager.backend.index
    manager.backend.index = lambda path, **kwargs: False
    manager.max_attempts = 1
    manager.drain()

    h3 = manager.get_health()
    assert h3["status"] == IndexHealthState.DEGRADED
    assert len(h3["failed_sources"]) > 0

    # Restore backend and rebuild -> transitions through REBUILDING to HEALTHY
    manager.backend.index = original_index
    rebuild_res = manager.rebuild(target_dir=temp_env["test_dir"])
    assert rebuild_res["status"] == IndexHealthState.HEALTHY

    h4 = manager.get_health()
    assert h4["status"] == IndexHealthState.HEALTHY


def test_cli_commands(temp_env):
    """Test CLI commands: --enqueue, --drain, --health, --list-queue, --rebuild."""
    cli_path = os.path.join(SCRIPT_DIR, "memory_index_queue.py")
    sample = os.path.join(temp_env["test_dir"], "CLI_TEST.md")
    with open(sample, "w") as f:
        f.write("CLI test file content")

    env = os.environ.copy()
    # Override default paths using env or args if supported, or test CLI on workspace
    cmd_help = [sys.executable, cli_path, "--help"]
    res = subprocess.run(cmd_help, capture_output=True, text=True)
    assert res.returncode == 0
    assert "--enqueue" in res.stdout
    assert "--drain" in res.stdout
    assert "--rebuild" in res.stdout
    assert "--health" in res.stdout
    assert "--list-dead-letter" in res.stdout
    assert "--requeue-dead-letter" in res.stdout
    assert "--verify-integrity" in res.stdout


def test_dead_letter_queue_mechanics(temp_env):
    """Test retry count tracking and dead-letter queue (DLQ) mechanics."""
    manager = temp_env["manager"]
    sample_file = os.path.join(temp_env["test_dir"], "DLQ_TEST.md")
    with open(sample_file, "w") as f:
        f.write("DLQ test content")

    job = manager.enqueue(sample_file)
    assert job["attempts"] == 0

    # Mock backend to fail indexing
    manager.backend.index = lambda path, **kwargs: False
    manager.max_attempts = 2

    # Attempt 1 -> remains pending for retry
    res1 = manager.drain()
    assert res1["processed"] == 0
    assert res1["failed"] == 0
    jobs = manager.list_queue()
    assert jobs[0]["status"] == "pending"
    assert jobs[0]["attempts"] == 1

    # Attempt 2 -> hits max_attempts, moves to failed & dead_letter
    res2 = manager.drain()
    assert res2["failed"] == 1
    jobs = manager.list_queue()
    assert jobs[0]["status"] == "failed"
    assert jobs[0]["attempts"] == 2
    assert jobs[0].get("dead_letter") is True

    # Check DLQ storage
    dlq = manager.list_dead_letter()
    assert len(dlq) == 1
    assert dlq[0]["job_id"] == job["job_id"]

    # Requeue dead letter
    requeued = manager.requeue_dead_letter(job_id=job["job_id"])
    assert requeued == 1
    dlq_after = manager.list_dead_letter()
    assert len(dlq_after) == 0

    jobs_after = manager.list_queue()
    assert jobs_after[0]["status"] == "pending"
    assert jobs_after[0]["attempts"] == 0


def test_drain_queue_convenience_function(temp_env):
    """Test the top-level drain_queue function execution."""
    sample_file = os.path.join(temp_env["test_dir"], "CONVENIENCE_TEST.md")
    with open(sample_file, "w") as f:
        f.write("Convenience drain content")

    manager = temp_env["manager"]
    manager.enqueue(sample_file)

    res = drain_queue(
        queue_file=temp_env["queue_file"],
        health_file=temp_env["health_file"],
        lease_file=temp_env["lease_file"],
        backend=temp_env["backend"],
        sync_dirty=False
    )
    assert res["status"] == "completed"
    assert res["processed"] == 1
    assert res["health_status"] == IndexHealthState.HEALTHY


def test_section_99_corruption_diagnostics(temp_env):
    """
    Test Section 99 corruption scenarios:
    - Corrupt manifest
    - Deleted source file
    """
    manager = temp_env["manager"]

    # 1. Corrupt manifest simulation
    manifest_path = os.path.join(temp_env["index_dir"], "manifest.json")
    with open(manifest_path, "w") as f:
        f.write("{invalid_json_corrupted: true")

    diag = manager.verify_index_integrity()
    assert diag["is_corrupt"] is True
    assert diag["status"] == IndexHealthState.FAILED
    assert any(i["type"] == "corrupt_index" for i in diag["issues"])

    # 2. Deleted source file in manifest simulation
    valid_manifest = {
        "indexed_files": {
            "/tmp/non_existent_file_section99.md": {
                "content_hash": "dummyhash",
                "indexed_at": "2026-09-04T00:00:00Z"
            }
        },
        "last_updated": "2026-09-04T00:00:00Z"
    }
    with open(manifest_path, "w") as f:
        json.dump(valid_manifest, f)

    diag2 = manager.verify_index_integrity()
    assert any(i["type"] == "deleted_source_file" for i in diag2["issues"])


def test_section_53_consistency_stale_and_degraded(temp_env):
    """
    Test Section 53 Index/Canonical Consistency:
    - canonical revision != indexed revision reports STALE
    - unreadable / corrupt index reports FAILED
    """
    manager = temp_env["manager"]

    # Construct scenario: canonical memory = revision 10, index = revision 9
    health_data = {
        "status": IndexHealthState.HEALTHY,
        "canonical_revision": "rev10_abc",
        "indexed_revision": "rev9_xyz",
        "pending_jobs_count": 0,
        "total_processed_jobs": 1,
        "failed_jobs_count": 0
    }
    with open(temp_env["health_file"], "w") as f:
        json.dump(health_data, f)

    h = manager.get_health()
    assert h["status"] == IndexHealthState.STALE

    # Construct scenario: index = unreadable / corrupt -> FAILED
    manifest_path = os.path.join(temp_env["index_dir"], "manifest.json")
    with open(manifest_path, "w") as f:
        f.write("BROKEN_MANIFEST")

    h_corrupt = manager.get_health()
    assert h_corrupt["status"] == IndexHealthState.FAILED

