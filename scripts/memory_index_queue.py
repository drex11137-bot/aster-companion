#!/usr/bin/env python3
"""
memory_index_queue.py - Single-Writer Index Queue and Control Plane.
Per Instruction.md Sections 31-34.

Responsibilities:
1. Durable queue at .agents/memory/index_queue.jsonl (Section 33).
2. Single-writer execution via file lease lock using scripts/lock_manager.py (Section 32).
3. Coalescing rapid sequential updates to the same file (Section 31).
4. Processing queued file indexing events into MemSearch backend (Section 21, 31).
5. Tracking index health state: HEALTHY, STALE, DEGRADED, REBUILDING, FAILED, MISSING (Section 34).
6. CLI commands: --enqueue, --drain, --rebuild, --health/--status, --list-queue.
"""

import os
import sys
import json
import time
import uuid
import hashlib
import logging
import argparse
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Import locking and atomic update mechanisms
try:
    from lock_manager import file_lock, safe_update_memory, atomic_write, LockTimeout
except ImportError:
    # Minimal fallback in case lock_manager is imported from alternate cwd
    from scripts.lock_manager import file_lock, safe_update_memory, atomic_write, LockTimeout

# Import MemSearch backend boundary
try:
    from memsearch_backend import get_backend, SemanticRetrievalBackend
except ImportError:
    try:
        from scripts.memsearch_backend import get_backend, SemanticRetrievalBackend
    except ImportError:
        get_backend = None
        SemanticRetrievalBackend = object

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("memory_index_queue")

WORKSPACE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_QUEUE_FILE = os.path.join(WORKSPACE_ROOT, ".agents", "memory", "index_queue.jsonl")
DEFAULT_HEALTH_FILE = os.path.join(WORKSPACE_ROOT, ".agents", "memory", "index_health.json")
DEFAULT_LEASE_FILE = os.path.join(WORKSPACE_ROOT, ".agents", "memory", "index_writer.lease")
DEFAULT_DLQ_FILE = os.path.join(WORKSPACE_ROOT, ".agents", "memory", "index_dead_letter.jsonl")


class IndexHealthState:
    HEALTHY = "HEALTHY"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    REBUILDING = "REBUILDING"
    FAILED = "FAILED"
    MISSING = "MISSING"


class SingleWriterConflictError(Exception):
    """Raised when another worker currently holds the single-writer index lease."""
    pass


class IndexQueueManager:
    """
    Manages durable index queue, single-writer lease execution, event coalescing,
    MemSearch backend synchronization, and derived index health tracking.
    """

    def __init__(
        self,
        queue_file: str = DEFAULT_QUEUE_FILE,
        health_file: str = DEFAULT_HEALTH_FILE,
        lease_file: str = DEFAULT_LEASE_FILE,
        dlq_file: Optional[str] = None,
        backend: Optional[Any] = None,
        max_attempts: int = 3
    ):
        self.queue_file = os.path.abspath(queue_file)
        self.health_file = os.path.abspath(health_file)
        self.lease_file = os.path.abspath(lease_file)
        self.dlq_file = os.path.abspath(dlq_file) if dlq_file else os.path.join(os.path.dirname(self.queue_file), "index_dead_letter.jsonl")
        self.max_attempts = max_attempts

        # Ensure parent directories exist
        os.makedirs(os.path.dirname(self.queue_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.health_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.lease_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.dlq_file), exist_ok=True)

        if backend is not None:
            self.backend = backend
        elif get_backend is not None:
            self.backend = get_backend()
        else:
            self.backend = None

    def _read_all_dead_letter_jobs(self) -> List[Dict[str, Any]]:
        """Reads all dead-letter jobs from dlq_file."""
        if not os.path.exists(self.dlq_file):
            return []
        jobs = []
        try:
            with open(self.dlq_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        jobs.append(json.loads(line))
                    except json.JSONDecodeError as err:
                        logger.warning(f"Corrupt JSON line in DLQ skipped: {err}")
        except Exception as e:
            logger.error(f"Error reading DLQ file {self.dlq_file}: {e}")
        return jobs

    def _write_all_dead_letter_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """Atomically writes all dead-letter jobs to dlq_file."""
        lines = [json.dumps(job) for job in jobs]
        content = "\n".join(lines) + ("\n" if lines else "")
        atomic_write(self.dlq_file, content)

    def _record_dead_letter(self, job: Dict[str, Any]) -> None:
        """Records a permanently failed job to the Dead-Letter Queue."""
        with file_lock(self.dlq_file, timeout=5.0):
            dlq_jobs = self._read_all_dead_letter_jobs()
            existing_ids = {j.get("job_id") for j in dlq_jobs}
            if job.get("job_id") not in existing_ids:
                dlq_entry = dict(job)
                dlq_entry["dead_letter"] = True
                dlq_entry["dead_letter_recorded_at"] = self._utc_now()
                dlq_jobs.append(dlq_entry)
                self._write_all_dead_letter_jobs(dlq_jobs)
                logger.warning(f"Job {job.get('job_id')} for {job.get('source_path')} moved to Dead-Letter Queue.")

    def list_dead_letter(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns recent entries from the Dead-Letter Queue."""
        jobs = self._read_all_dead_letter_jobs()
        return jobs[-limit:]

    def requeue_dead_letter(self, job_id: Optional[str] = None) -> int:
        """
        Moves dead-letter jobs back to the active queue for retry.
        If job_id is provided, requeues only that specific job; otherwise requeues all.
        """
        requeued_count = 0
        with file_lock(self.dlq_file, timeout=5.0):
            dlq_jobs = self._read_all_dead_letter_jobs()
            remaining_dlq = []
            jobs_to_requeue = []

            for j in dlq_jobs:
                if job_id is None or j.get("job_id") == job_id:
                    requeued_job = dict(j)
                    requeued_job["status"] = "pending"
                    requeued_job["attempts"] = 0
                    requeued_job["error"] = None
                    requeued_job["last_attempt"] = None
                    requeued_job["requeued_at"] = self._utc_now()
                    requeued_job.pop("dead_letter", None)
                    requeued_job.pop("dead_letter_recorded_at", None)
                    jobs_to_requeue.append(requeued_job)
                    requeued_count += 1
                else:
                    remaining_dlq.append(j)

            if jobs_to_requeue:
                with file_lock(self.queue_file, timeout=5.0):
                    current_jobs = self._read_all_jobs()
                    existing_map = {item.get("job_id"): idx for idx, item in enumerate(current_jobs)}
                    for rj in jobs_to_requeue:
                        rid = rj.get("job_id")
                        if rid in existing_map:
                            current_jobs[existing_map[rid]] = rj
                        else:
                            current_jobs.append(rj)
                    self._write_all_jobs(current_jobs)
                self._write_all_dead_letter_jobs(remaining_dlq)
                self._update_health_on_enqueue()
                logger.info(f"Requeued {requeued_count} dead-letter jobs back to active index queue.")
        return requeued_count

    def _utc_now(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _read_all_jobs(self) -> List[Dict[str, Any]]:
        """Reads all jobs from index_queue.jsonl."""
        if not os.path.exists(self.queue_file):
            return []
        jobs = []
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        jobs.append(json.loads(line))
                    except json.JSONDecodeError as err:
                        logger.warning(f"Corrupt JSON line in queue skipped: {err}")
        except Exception as e:
            logger.error(f"Error reading queue file {self.queue_file}: {e}")
        return jobs

    def _write_all_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """Atomically writes all jobs to index_queue.jsonl."""
        lines = [json.dumps(job) for job in jobs]
        content = "\n".join(lines) + ("\n" if lines else "")
        atomic_write(self.queue_file, content)

    def compute_file_hash(self, file_path: str, content: Optional[str] = None) -> str:
        """Computes SHA256 hash of file content."""
        if content is not None:
            return hashlib.sha256(content.encode("utf-8")).hexdigest()
        if os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    return hashlib.sha256(f.read()).hexdigest()
            except Exception as e:
                logger.warning(f"Failed to read file {file_path} for hash: {e}")
                return ""
        return ""

    def compute_canonical_revision(self) -> str:
        """
        Computes composite revision hash across canonical markdown files in memory directory.
        Used to detect if canonical memory has changed relative to indexed state.
        """
        mem_dir = os.path.join(WORKSPACE_ROOT, ".agents", "memory")
        if not os.path.exists(mem_dir):
            return "empty"

        hasher = hashlib.sha256()
        canonical_files = []
        for root, dirs, files in os.walk(mem_dir):
            # Exclude non-canonical runtime artifacts and internal cache
            if ".memsearch" in root or "inbox" in root:
                continue
            for f in sorted(files):
                if f.endswith(".md"):
                    canonical_files.append(os.path.join(root, f))

        for path in sorted(canonical_files):
            rel_path = os.path.relpath(path, WORKSPACE_ROOT)
            try:
                mtime = os.path.getmtime(path)
                size = os.path.getsize(path)
                hasher.update(f"{rel_path}:{mtime}:{size}".encode("utf-8"))
            except OSError:
                continue

        return hasher.hexdigest()[:16]

    def get_canonical_files(self) -> List[str]:
        """Discovers all canonical memory markdown files in workspace and global memory."""
        search_dirs = [
            os.path.join(WORKSPACE_ROOT, ".agents", "memory"),
            os.path.expanduser("~/.gemini/antigravity-cli/memory")
        ]
        discovered = []
        for s_dir in search_dirs:
            if not os.path.exists(s_dir):
                continue
            for root, dirs, files in os.walk(s_dir):
                if ".memsearch" in root or "inbox" in root:
                    continue
                for f in sorted(files):
                    if f.endswith(".md"):
                        discovered.append(os.path.abspath(os.path.join(root, f)))
        return sorted(list(set(discovered)))

    def detect_dirty_canonical_files(self) -> List[Dict[str, Any]]:
        """
        Detects canonical files that have unsynchronized modifications or deletions.
        Compares disk state against the backend manifest.
        Per Section 15 & 53.
        """
        dirty = []
        manifest_files = {}
        if self.backend and hasattr(self.backend, "manifest") and isinstance(self.backend.manifest, dict):
            manifest_files = self.backend.manifest.get("indexed_files", {})

        canonical_files = self.get_canonical_files()
        canonical_set = set(canonical_files)

        # Check existing canonical files on disk against manifest
        for path in canonical_files:
            disk_hash = self.compute_file_hash(path)
            indexed_entry = manifest_files.get(path)
            if not indexed_entry:
                dirty.append({
                    "source_path": path,
                    "event_type": "upsert",
                    "disk_hash": disk_hash,
                    "indexed_hash": None,
                    "reason": "unindexed"
                })
            elif indexed_entry.get("content_hash") != disk_hash:
                dirty.append({
                    "source_path": path,
                    "event_type": "upsert",
                    "disk_hash": disk_hash,
                    "indexed_hash": indexed_entry.get("content_hash"),
                    "reason": "hash_mismatch"
                })

        # Check for deleted canonical files still tracked in manifest
        mem_dir = os.path.join(WORKSPACE_ROOT, ".agents", "memory")
        for indexed_path in manifest_files.keys():
            if indexed_path.startswith(mem_dir) and indexed_path not in canonical_set and not os.path.exists(indexed_path):
                dirty.append({
                    "source_path": indexed_path,
                    "event_type": "delete",
                    "disk_hash": "",
                    "indexed_hash": manifest_files[indexed_path].get("content_hash"),
                    "reason": "deleted_on_disk"
                })

        return dirty

    def sync_dirty_canonical_files(self) -> List[Dict[str, Any]]:
        """
        Enqueues all dirty canonical files that do not currently have an identical pending queue job.
        Returns list of enqueued jobs.
        """
        dirty_items = self.detect_dirty_canonical_files()
        enqueued_jobs = []
        for item in dirty_items:
            path = item["source_path"]
            event = item["event_type"]
            job = self.enqueue(path, event_type=event, priority=10)
            enqueued_jobs.append(job)
        if enqueued_jobs:
            logger.info(f"Synchronized {len(enqueued_jobs)} dirty canonical files into index queue.")
        return enqueued_jobs

    def enqueue(
        self,
        source_path: Optional[str] = None,
        event_type: str = "upsert",
        priority: int = 10,
        content: Optional[str] = None,
        operation: Optional[str] = None,
        target_path: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Enqueues a file change event with atomic locking and coalescing of rapid successive updates.
        Per Section 31 & 33. Supports operation= and target_path= for DEF-009 compatibility.
        """
        if source_path is None and target_path is not None:
            source_path = target_path
        if operation is not None:
            event_type = operation
        if not source_path:
            raise ValueError("source_path or target_path must be provided to enqueue()")
        abs_path = os.path.abspath(source_path)
        content_hash = self.compute_file_hash(abs_path, content=content)

        # Detect deletion if file does not exist on disk
        if not os.path.exists(abs_path) and content is None:
            event_type = "delete"
            content_hash = ""

        # Acquire lock on the queue file for atomic mutation
        with file_lock(self.queue_file, timeout=5.0):
            jobs = self._read_all_jobs()
            now_iso = self._utc_now()

            # Coalesce rapid sequential updates for the same file
            coalesced_earlier = False
            for existing in jobs:
                if existing.get("source_path") == abs_path and existing.get("status") == "pending":
                    # If pending job has identical hash and event, no new job needed
                    if existing.get("content_hash") == content_hash and existing.get("event_type") == event_type:
                        logger.info(f"Deduplicated event for {abs_path} (hash: {content_hash[:8] or 'deleted'})")
                        return existing

                    # If pending job has different hash/event, mark earlier pending job as coalesced
                    existing["status"] = "coalesced"
                    existing["last_attempt"] = now_iso
                    existing["error"] = "Coalesced into newer sequential update"
                    coalesced_earlier = True

            new_job = {
                "job_id": f"job_{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}",
                "source_path": abs_path,
                "content_hash": content_hash,
                "event_type": event_type,
                "created_at": now_iso,
                "attempts": 0,
                "last_attempt": None,
                "status": "pending",
                "error": None,
                "priority": priority
            }

            jobs.append(new_job)
            self._write_all_jobs(jobs)

        if coalesced_earlier:
            logger.info(f"Coalesced rapid updates for {abs_path} into job {new_job['job_id']}")
        else:
            logger.info(f"Enqueued index job {new_job['job_id']} for {abs_path}")

        # Update health to STALE if currently HEALTHY (canonical changed, index pending)
        self._update_health_on_enqueue()
        return new_job

    def _coalesce_pending_jobs(self, pending_jobs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Groups pending jobs by source_path and selects only the latest job per path.
        Returns (jobs_to_execute, jobs_to_mark_coalesced).
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for job in pending_jobs:
            path = job["source_path"]
            grouped.setdefault(path, []).append(job)

        jobs_to_execute = []
        jobs_to_coalesce = []

        for path, job_list in grouped.items():
            # Sort by created_at or job_id
            job_list.sort(key=lambda j: j["created_at"])
            # The last job is the current target state
            target_job = job_list[-1]
            jobs_to_execute.append(target_job)
            for earlier in job_list[:-1]:
                jobs_to_coalesce.append(earlier)

        return jobs_to_execute, jobs_to_coalesce

    def drain(
        self,
        max_batch_size: Optional[int] = None,
        lease_timeout: float = 10.0,
        sync_dirty: bool = False
    ) -> Dict[str, Any]:
        """
        Processes pending jobs from the queue into the MemSearch backend.
        Enforces single-writer execution using file lease lock (Section 32).
        Coalesces sequential updates before executing indexing (Section 31).
        """
        if sync_dirty:
            self.sync_dirty_canonical_files()

        # Enforce single-writer execution via file lease lock
        try:
            with file_lock(self.lease_file, timeout=lease_timeout):
                return self._drain_under_lease(max_batch_size=max_batch_size)
        except LockTimeout:
            msg = f"Single-writer lease lock on {self.lease_file} held by another indexing process. Aborting concurrent run."
            logger.warning(msg)
            return {
                "status": "busy",
                "error": msg,
                "processed": 0,
                "coalesced": 0,
                "failed": 0
            }

    def _drain_under_lease(self, max_batch_size: Optional[int] = None) -> Dict[str, Any]:
        """Internal drain logic executed strictly under single-writer lease lock."""
        now_iso = self._utc_now()
        start_time = time.time()

        with file_lock(self.queue_file, timeout=5.0):
            jobs = self._read_all_jobs()
            job_map = {j["job_id"]: j for j in jobs}

            pending = [j for j in jobs if j.get("status") == "pending"]
            if not pending:
                logger.info("Index queue is empty. No pending jobs to drain.")
                self.check_and_refresh_health()
                return {
                    "status": "empty",
                    "processed": 0,
                    "coalesced": 0,
                    "failed": 0,
                    "duration_seconds": round(time.time() - start_time, 3)
                }

            # Coalesce pending jobs for the same source_path
            jobs_to_execute, jobs_to_coalesce = self._coalesce_pending_jobs(pending)

            # Mark coalesced jobs
            for c_job in jobs_to_coalesce:
                c_job["status"] = "coalesced"
                c_job["last_attempt"] = now_iso
                c_job["error"] = None

            # Sort jobs to execute by priority (lower number = higher priority), then creation time
            jobs_to_execute.sort(key=lambda j: (j.get("priority", 10), j["created_at"]))

            if max_batch_size and max_batch_size > 0:
                jobs_to_execute = jobs_to_execute[:max_batch_size]

            # Save initial coalesced status
            self._write_all_jobs(jobs)

        processed_count = 0
        failed_count = 0
        failed_sources = []

        # Process jobs through MemSearch backend
        for job in jobs_to_execute:
            job_id = job["job_id"]
            source_path = job["source_path"]
            event_type = job["event_type"]

            job["status"] = "processing"
            job["attempts"] += 1
            job["last_attempt"] = self._utc_now()

            success = False
            error_msg = None

            try:
                if self.backend is None:
                    # Backend missing; simulate safe intake and record warning
                    logger.warning(f"No MemSearch backend configured. Dry-run indexing for {source_path}")
                    success = True
                else:
                    if event_type in ("upsert", "modify"):
                        if os.path.exists(source_path):
                            # Re-compute current hash from disk to capture latest live state
                            current_hash = self.compute_file_hash(source_path)
                            job["content_hash"] = current_hash
                            success = bool(self.backend.index(source_path))
                        else:
                            # File removed before indexing executed
                            logger.info(f"File removed prior to indexing; deleting from backend: {source_path}")
                            job["event_type"] = "delete"
                            success = bool(self.backend.delete(source_path))
                    elif event_type == "delete":
                        success = bool(self.backend.delete(source_path))
                    else:
                        success = bool(self.backend.index(source_path))

                if not success:
                    error_msg = f"Backend indexing operation failed for {source_path}"
            except Exception as ex:
                error_msg = f"Exception during indexing {source_path}: {str(ex)}"
                logger.error(error_msg)
                success = False

            if success:
                job["status"] = "completed"
                job["error"] = None
                processed_count += 1
                logger.info(f"Successfully processed job {job_id} for {source_path}")
            else:
                job["error"] = error_msg
                if job["attempts"] >= self.max_attempts:
                    job["status"] = "failed"
                    job["dead_letter"] = True
                    self._record_dead_letter(job)
                    failed_count += 1
                    failed_sources.append(source_path)
                    logger.error(f"Job {job_id} for {source_path} failed permanently after {job['attempts']} attempts.")
                else:
                    job["status"] = "pending"  # Will retry on next drain
                    logger.warning(f"Job {job_id} for {source_path} failed attempt {job['attempts']}; scheduled for retry.")

        # Persist final job statuses under lock
        with file_lock(self.queue_file, timeout=5.0):
            current_jobs = self._read_all_jobs()
            updated_lookup = {j["job_id"]: j for j in jobs_to_execute}
            updated_lookup.update({j["job_id"]: j for j in jobs_to_coalesce})
            for idx, item in enumerate(current_jobs):
                if item["job_id"] in updated_lookup:
                    current_jobs[idx] = updated_lookup[item["job_id"]]
            self._write_all_jobs(current_jobs)
            remaining_pending = [j for j in current_jobs if j.get("status") == "pending"]

        # Update index health
        drain_succeeded = (failed_count == 0 and len(remaining_pending) == 0)
        health = self.check_and_refresh_health(recent_failures=failed_sources, drain_succeeded=drain_succeeded)

        duration = round(time.time() - start_time, 3)
        return {
            "status": "completed",
            "processed": processed_count,
            "coalesced": len(jobs_to_coalesce),
            "failed": failed_count,
            "duration_seconds": duration,
            "health_status": health.get("status")
        }

    # Alias for drain per interface conventions
    drain_queue = drain

    def rebuild(
        self,
        target_dir: Optional[str] = None,
        lease_timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Performs full or targeted rebuild of semantic index under single-writer lease lock.
        Sets health state to REBUILDING during operation (Section 34).
        """
        try:
            with file_lock(self.lease_file, timeout=lease_timeout):
                return self._rebuild_under_lease(target_dir=target_dir)
        except LockTimeout:
            msg = f"Cannot rebuild: single-writer lease held on {self.lease_file} by another worker."
            logger.error(msg)
            return {"status": "busy", "error": msg}

    def _rebuild_under_lease(self, target_dir: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"Starting index rebuild for target: {target_dir or 'all canonical memory'}...")

        # Set status to REBUILDING
        self._write_health({
            "status": IndexHealthState.REBUILDING,
            "canonical_revision": self.compute_canonical_revision(),
            "indexed_revision": None,
            "pending_jobs_count": 0,
            "total_processed_jobs": 0,
            "failed_jobs_count": 0,
            "last_success": None,
            "last_failure": None,
            "failed_sources": [],
            "embedding_provider": "onnx-bge-m3" if (self.backend and getattr(self.backend, "cli_path", None)) else "adapter-fallback",
            "embedding_model": "bge-m3",
            "schema_version": "1.0.0",
            "last_updated": self._utc_now()
        })

        search_dirs = []
        if target_dir:
            search_dirs.append(os.path.abspath(target_dir))
        else:
            search_dirs.append(os.path.join(WORKSPACE_ROOT, ".agents", "memory"))
            global_mem = os.path.expanduser("~/.gemini/antigravity-cli/memory")
            if os.path.exists(global_mem):
                search_dirs.append(global_mem)

        discovered_files = []
        for s_dir in search_dirs:
            if not os.path.exists(s_dir):
                continue
            for root, dirs, files in os.walk(s_dir):
                if ".memsearch" in root:
                    continue
                for f in sorted(files):
                    if f.endswith(".md"):
                        discovered_files.append(os.path.abspath(os.path.join(root, f)))

        logger.info(f"Discovered {len(discovered_files)} canonical memory files for rebuild.")

        rebuild_res = {}
        if self.backend is not None:
            rebuild_res = self.backend.rebuild(paths=discovered_files)
        else:
            rebuild_res = {"status": "rebuilt", "indexed_count": len(discovered_files), "failed_count": 0}

        # Clear or mark existing queue jobs for rebuilt files as completed
        with file_lock(self.queue_file, timeout=5.0):
            jobs = self._read_all_jobs()
            rebuilt_set = set(discovered_files)
            now_iso = self._utc_now()
            for j in jobs:
                if j.get("source_path") in rebuilt_set and j.get("status") in ("pending", "failed"):
                    j["status"] = "completed"
                    j["last_attempt"] = now_iso
                    j["error"] = "Resolved and completed via full rebuild"
            self._write_all_jobs(jobs)

        canonical_rev = self.compute_canonical_revision()
        failed_count = rebuild_res.get("failed_count", 0)
        final_status = IndexHealthState.HEALTHY if failed_count == 0 else IndexHealthState.DEGRADED

        health_data = {
            "status": final_status,
            "canonical_revision": canonical_rev,
            "indexed_revision": canonical_rev,
            "pending_jobs_count": 0,
            "total_processed_jobs": rebuild_res.get("indexed_count", len(discovered_files)),
            "failed_jobs_count": failed_count,
            "last_success": self._utc_now(),
            "last_failure": None if failed_count == 0 else self._utc_now(),
            "failed_sources": [],
            "embedding_provider": "onnx-bge-m3" if (self.backend and getattr(self.backend, "cli_path", None)) else "adapter-fallback",
            "embedding_model": "bge-m3",
            "schema_version": "1.0.0",
            "last_updated": self._utc_now()
        }
        self._write_health(health_data)

        duration = round(time.time() - start_time, 3)
        return {
            "status": final_status,
            "indexed_files": rebuild_res.get("indexed_count", len(discovered_files)),
            "failed_files": failed_count,
            "canonical_revision": canonical_rev,
            "duration_seconds": duration
        }

    def _read_health(self) -> Dict[str, Any]:
        if os.path.exists(self.health_file):
            try:
                with open(self.health_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to parse health file: {e}")
        return {
            "status": IndexHealthState.MISSING,
            "canonical_revision": self.compute_canonical_revision(),
            "indexed_revision": None,
            "pending_jobs_count": 0,
            "total_processed_jobs": 0,
            "failed_jobs_count": 0,
            "last_success": None,
            "last_failure": None,
            "failed_sources": [],
            "embedding_provider": "onnx-bge-m3" if (self.backend and getattr(self.backend, "cli_path", None)) else "adapter-fallback",
            "embedding_model": "bge-m3",
            "schema_version": "1.0.0",
            "last_updated": self._utc_now()
        }

    def _write_health(self, health_data: Dict[str, Any]) -> None:
        try:
            atomic_write(self.health_file, json.dumps(health_data, indent=2))
        except Exception as e:
            logger.error(f"Failed to persist index health file {self.health_file}: {e}")

    def _update_health_on_enqueue(self) -> None:
        """Transitions index health to STALE if canonical memory has new pending changes."""
        health = self._read_health()
        if health.get("status") in (IndexHealthState.HEALTHY, IndexHealthState.MISSING):
            health["status"] = IndexHealthState.STALE
            health["pending_jobs_count"] = health.get("pending_jobs_count", 0) + 1
            health["canonical_revision"] = self.compute_canonical_revision()
            health["last_updated"] = self._utc_now()
            self._write_health(health)

    def verify_index_integrity(self) -> Dict[str, Any]:
        """
        Diagnoses index corruption, wrong dimensions, missing collections,
        stale chunks, deleted source files, and embedding migrations.
        Per Instruction.md Sections 53, 98, and 99.
        """
        diagnostics = []
        issues = []
        is_corrupt = False

        # 1. Manifest readability and corruption (Section 99)
        manifest_data = None
        manifest_path = getattr(self.backend, "manifest_path", None)
        if manifest_path and os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
            except Exception as e:
                is_corrupt = True
                diag = f"Corrupt index manifest at {manifest_path}: {e}"
                diagnostics.append(diag)
                issues.append({"type": "corrupt_index", "detail": diag})

        # 2. Embedding model and migration state (Section 98)
        configured_model = "bge-m3"
        configured_provider = "onnx"
        expected_dimension = 1024
        migration_state = "CURRENT"

        config_path = os.path.expanduser("~/.memsearch/config.toml")
        if os.path.exists(config_path):
            try:
                import tomllib
                with open(config_path, "rb") as cf:
                    cfg_data = tomllib.load(cf)
                configured_model = cfg_data.get("embedding", {}).get("model", configured_model)
                configured_provider = cfg_data.get("embedding", {}).get("provider", configured_provider)
            except Exception:
                pass

        if os.path.exists(self.health_file):
            try:
                with open(self.health_file, "r", encoding="utf-8") as f:
                    rec = json.load(f)
                rec_model = rec.get("embedding_model")
                if rec_model and rec_model != configured_model:
                    migration_state = "MIGRATION_REQUIRED"
                    diag = f"Embedding model migration required: old='{rec_model}', new='{configured_model}'"
                    diagnostics.append(diag)
                    issues.append({"type": "model_migration_required", "detail": diag})
            except Exception:
                pass

        # 3. Half-built index detection (Section 99)
        jobs = self._read_all_jobs()
        half_built = [j for j in jobs if j.get("status") == "processing"]
        if half_built:
            diag = f"Half-built index: {len(half_built)} jobs interrupted in 'processing' state."
            diagnostics.append(diag)
            issues.append({"type": "half_built_index", "detail": diag})

        # 4. Deleted source files still present in manifest (Section 99)
        if manifest_data and isinstance(manifest_data, dict) and "indexed_files" in manifest_data:
            for sp in manifest_data["indexed_files"]:
                if not os.path.exists(sp):
                    diag = f"Deleted source file still present in index: {sp}"
                    diagnostics.append(diag)
                    issues.append({"type": "deleted_source_file", "detail": diag})

        # 5. Stale chunks (dirty files with hash mismatches)
        dirty = self.detect_dirty_canonical_files()
        stale = [d for d in dirty if d.get("reason") == "hash_mismatch"]
        if stale:
            diag = f"Stale chunks: {len(stale)} files have content hashes differing from index."
            diagnostics.append(diag)
            issues.append({"type": "stale_chunks", "detail": diag})

        # 6. Backend health state
        if self.backend and hasattr(self.backend, "health"):
            try:
                bh = self.backend.health()
                if bh.get("status") in ("DEGRADED", "FAILED"):
                    diag = f"Backend substrate {bh.get('status')}: {bh.get('degraded_reason', 'Unhealthy')}"
                    diagnostics.append(diag)
                    issues.append({"type": "backend_degraded", "detail": diag})
            except Exception as ex:
                diag = f"Backend health check exception: {ex}"
                diagnostics.append(diag)
                issues.append({"type": "backend_error", "detail": diag})

        status = IndexHealthState.HEALTHY
        if is_corrupt:
            status = IndexHealthState.FAILED
        elif any(i["type"] in ("missing_collection", "model_migration_required", "backend_degraded", "backend_error") for i in issues):
            status = IndexHealthState.DEGRADED
        elif any(i["type"] in ("stale_chunks", "deleted_source_file", "half_built_index") for i in issues):
            status = IndexHealthState.STALE

        return {
            "status": status,
            "is_corrupt": is_corrupt,
            "migration_state": migration_state,
            "issues": issues,
            "diagnostics": diagnostics,
            "configured_model": configured_model,
            "configured_provider": configured_provider,
            "expected_dimension": expected_dimension
        }

    def check_and_refresh_health(
        self,
        recent_failures: Optional[List[str]] = None,
        drain_succeeded: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates and records derived health state:
        HEALTHY, STALE, DEGRADED, REBUILDING, FAILED, MISSING.
        Per Section 34, 53, 98, and 99.
        """
        jobs = self._read_all_jobs()
        pending = [j for j in jobs if j.get("status") == "pending"]
        failed = [j for j in jobs if j.get("status") == "failed"]
        completed = [j for j in jobs if j.get("status") == "completed"]

        canonical_rev = self.compute_canonical_revision()
        current_health = self._read_health()
        indexed_rev = current_health.get("indexed_revision")

        if drain_succeeded and len(failed) == 0 and len(pending) == 0:
            indexed_rev = canonical_rev

        failed_sources = []
        for f in failed:
            sp = f.get("source_path")
            if sp and sp not in failed_sources:
                failed_sources.append(sp)
        if recent_failures:
            for rf in recent_failures:
                if rf not in failed_sources:
                    failed_sources.append(rf)

        integrity = self.verify_index_integrity()

        # Determine health status
        if current_health.get("status") == IndexHealthState.REBUILDING:
            status = IndexHealthState.REBUILDING
        elif integrity.get("is_corrupt"):
            status = IndexHealthState.FAILED
        elif failed_sources or len(failed) > 0:
            status = IndexHealthState.DEGRADED
        elif integrity.get("status") == IndexHealthState.DEGRADED:
            status = IndexHealthState.DEGRADED
        elif len(pending) > 0 or (indexed_rev and indexed_rev != canonical_rev):
            status = IndexHealthState.STALE
        elif len(completed) == 0 and not os.path.exists(self.health_file):
            status = IndexHealthState.MISSING
        else:
            status = IndexHealthState.HEALTHY
            indexed_rev = canonical_rev

        updated_health = {
            "status": status,
            "canonical_revision": canonical_rev,
            "indexed_revision": indexed_rev,
            "pending_jobs_count": len(pending),
            "total_processed_jobs": len(completed),
            "failed_jobs_count": len(failed_sources),
            "dead_letter_jobs_count": len(self.list_dead_letter(limit=1000)),
            "last_success": current_health.get("last_success") or (self._utc_now() if status == IndexHealthState.HEALTHY else None),
            "last_failure": self._utc_now() if (status == IndexHealthState.DEGRADED and recent_failures) else current_health.get("last_failure"),
            "failed_sources": failed_sources,
            "embedding_provider": integrity.get("configured_provider", "onnx"),
            "embedding_model": integrity.get("configured_model", "bge-m3"),
            "embedding_dimension": integrity.get("expected_dimension", 1024),
            "migration_state": integrity.get("migration_state", "CURRENT"),
            "diagnostics": integrity.get("diagnostics", []),
            "schema_version": "1.0.0",
            "last_updated": self._utc_now()
        }

        self._write_health(updated_health)
        return updated_health

    def get_health(self) -> Dict[str, Any]:
        """Returns the current index health record."""
        return self.check_and_refresh_health()

    def list_queue(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the most recent queue entries."""
        jobs = self._read_all_jobs()
        return jobs[-limit:]

    def clear_completed(self) -> int:
        """Prunes completed and coalesced jobs to keep queue compact."""
        with file_lock(self.queue_file, timeout=5.0):
            jobs = self._read_all_jobs()
            remaining = [j for j in jobs if j.get("status") in ("pending", "processing", "failed")]
            pruned_count = len(jobs) - len(remaining)
            self._write_all_jobs(remaining)
        logger.info(f"Pruned {pruned_count} completed/coalesced jobs from queue.")
        return pruned_count


def drain_queue(
    queue_file: str = DEFAULT_QUEUE_FILE,
    health_file: str = DEFAULT_HEALTH_FILE,
    lease_file: str = DEFAULT_LEASE_FILE,
    dlq_file: Optional[str] = None,
    backend: Optional[Any] = None,
    max_batch_size: Optional[int] = None,
    lease_timeout: float = 10.0,
    sync_dirty: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to drain and synchronize the memory index queue into Milvus Lite.
    Per Instruction.md Sections 15, 31-34, 52, 53, 98, 99.
    """
    manager = IndexQueueManager(
        queue_file=queue_file,
        health_file=health_file,
        lease_file=lease_file,
        dlq_file=dlq_file,
        backend=backend
    )
    if sync_dirty:
        manager.sync_dirty_canonical_files()
    return manager.drain(max_batch_size=max_batch_size, lease_timeout=lease_timeout)


def parse_args():
    parser = argparse.ArgumentParser(
        description="IndexQueueManager CLI - Single-Writer Memory Index Control Plane."
    )
    parser.add_argument("--enqueue", type=str, help="Path to canonical memory file to enqueue for indexing.")
    parser.add_argument("--event-type", type=str, default="upsert", choices=["upsert", "modify", "delete"], help="Event type.")
    parser.add_argument("--priority", type=int, default=10, help="Job priority (lower number = higher priority).")
    parser.add_argument("--drain", action="store_true", help="Process and drain all pending indexing jobs.")
    parser.add_argument("--sync-dirty", action="store_true", help="Synchronize dirty canonical files into index queue before drain.")
    parser.add_argument("--batch-size", type=int, default=None, help="Maximum number of jobs to process during drain.")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild semantic index from canonical memory files.")
    parser.add_argument("--target-dir", type=str, default=None, help="Target directory for index rebuild.")
    parser.add_argument("--health", "--status", dest="show_health", action="store_true", help="Show index health state and statistics.")
    parser.add_argument("--list-queue", action="store_true", help="List recent jobs in durable index queue.")
    parser.add_argument("--list-dead-letter", action="store_true", help="List failed jobs in dead-letter queue.")
    parser.add_argument("--requeue-dead-letter", type=str, nargs="?", const="ALL", help="Requeue dead-letter jobs back to active index queue.")
    parser.add_argument("--verify-integrity", action="store_true", help="Diagnose index corruption, dimension mismatch, and stale chunks.")
    parser.add_argument("--clear-completed", action="store_true", help="Prune completed and coalesced jobs from queue.")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Output results in JSON format.")
    return parser.parse_args()


def main():
    args = parse_args()
    manager = IndexQueueManager()

    if args.enqueue:
        job = manager.enqueue(args.enqueue, event_type=args.event_type, priority=args.priority)
        if args.as_json:
            print(json.dumps(job, indent=2))
        else:
            print(f"[ENQUEUED] Job ID: {job['job_id']}")
            print(f"  Target: {job['source_path']}")
            print(f"  Event:  {job['event_type']}")
            print(f"  Status: {job['status']}")
            print(f"  Hash:   {job['content_hash'][:8] or 'None'}")
        return

    if args.drain:
        result = manager.drain(max_batch_size=args.batch_size, sync_dirty=args.sync_dirty)
        if args.as_json:
            print(json.dumps(result, indent=2))
        else:
            print("==================================================")
            print("        INDEX QUEUE DRAIN SUMMARY                 ")
            print("==================================================")
            print(f"Status:             {result.get('status')}")
            print(f"Processed Jobs:     {result.get('processed', 0)}")
            print(f"Coalesced Updates:  {result.get('coalesced', 0)}")
            print(f"Failed Jobs:        {result.get('failed', 0)}")
            print(f"Duration:           {result.get('duration_seconds', 0)}s")
            print(f"Derived Health:     {result.get('health_status', 'UNKNOWN')}")
            print("==================================================")
        return

    if args.rebuild:
        result = manager.rebuild(target_dir=args.target_dir)
        if args.as_json:
            print(json.dumps(result, indent=2))
        else:
            print("==================================================")
            print("        INDEX REBUILD SUMMARY                     ")
            print("==================================================")
            print(f"Status:             {result.get('status')}")
            print(f"Indexed Files:      {result.get('indexed_files', 0)}")
            print(f"Failed Files:       {result.get('failed_files', 0)}")
            print(f"Canonical Revision: {result.get('canonical_revision')}")
            print(f"Duration:           {result.get('duration_seconds', 0)}s")
            print("==================================================")
        return

    if args.show_health:
        health = manager.get_health()
        if args.as_json:
            print(json.dumps(health, indent=2))
        else:
            print("==================================================")
            print("        SEMANTIC INDEX HEALTH STATUS              ")
            print("==================================================")
            print(f"State:              {health.get('status')}")
            print(f"Canonical Revision: {health.get('canonical_revision')}")
            print(f"Indexed Revision:   {health.get('indexed_revision')}")
            print(f"Pending Jobs:       {health.get('pending_jobs_count')}")
            print(f"Total Processed:    {health.get('total_processed_jobs')}")
            print(f"Failed Sources:     {len(health.get('failed_sources', []))}")
            print(f"Dead-Letter Jobs:   {health.get('dead_letter_jobs_count', 0)}")
            print(f"Embedding Provider: {health.get('embedding_provider')}")
            print(f"Embedding Model:    {health.get('embedding_model')}")
            print(f"Last Updated:       {health.get('last_updated')}")
            print("==================================================")
        return

    if args.verify_integrity:
        integrity = manager.verify_index_integrity()
        if args.as_json:
            print(json.dumps(integrity, indent=2))
        else:
            print("==================================================")
            print("        INDEX INTEGRITY VERIFICATION              ")
            print("==================================================")
            print(f"Status:             {integrity.get('status')}")
            print(f"Is Corrupt:         {integrity.get('is_corrupt')}")
            print(f"Migration State:    {integrity.get('migration_state')}")
            print(f"Configured Model:   {integrity.get('configured_model')}")
            print(f"Expected Dimension: {integrity.get('expected_dimension')}")
            print(f"Total Issues:       {len(integrity.get('issues', []))}")
            for iss in integrity.get("issues", []):
                print(f"  - [{iss.get('type')}] {iss.get('detail')}")
            print("==================================================")
        return

    if args.list_queue:
        jobs = manager.list_queue()
        if args.as_json:
            print(json.dumps(jobs, indent=2))
        else:
            print(f"Total Queue Entries: {len(jobs)}")
            for j in jobs:
                print(f"[{j.get('status').upper():10}] {j.get('job_id')} | {j.get('event_type'):6} | {os.path.basename(j.get('source_path'))}")
        return

    if args.list_dead_letter:
        dlq_jobs = manager.list_dead_letter()
        if args.as_json:
            print(json.dumps(dlq_jobs, indent=2))
        else:
            print(f"Total Dead-Letter Entries: {len(dlq_jobs)}")
            for j in dlq_jobs:
                print(f"[DEAD_LETTER] {j.get('job_id')} | {os.path.basename(j.get('source_path'))} | Attempts: {j.get('attempts')} | Error: {j.get('error')}")
        return

    if args.requeue_dead_letter:
        target_id = None if args.requeue_dead_letter == "ALL" else args.requeue_dead_letter
        requeued = manager.requeue_dead_letter(job_id=target_id)
        print(f"Requeued {requeued} dead-letter jobs back to active index queue.")
        return

    if args.clear_completed:
        pruned = manager.clear_completed()
        print(f"Pruned {pruned} completed/coalesced jobs.")
        return

    # Default: print health status
    health = manager.get_health()
    print(f"Index Health Status: {health.get('status')} (Pending Jobs: {health.get('pending_jobs_count')})")
    print("Use --help to see all available commands.")


if __name__ == "__main__":
    main()
