# Index Health & Substrate Audit Report

**Component**: Memory Index Queue Control Plane & Milvus Lite Vector Substrate  
**Maintainer**: Agent 14 (Index Queue Engineer)  
**Date**: September 4, 2026  
**Status**: **HEALTHY**  
**Canonical Revision**: `bb05313ae179ebb0`  
**Indexed Revision**: `bb05313ae179ebb0`  

---

## 1. Executive Summary

The memory index queue control plane ([`scripts/memory_index_queue.py`](file:///workspaces/codespaces-blank/scripts/memory_index_queue.py)) has been fully verified, hardened, and synchronized with the underlying Milvus Lite vector store at `~/.memsearch/milvus.db`. All dirty canonical markdown files in the workspace have been drained, coalesced, and indexed into the semantic retrieval substrate.

### Substrate Health Matrix
| Metric / Component | Status / Value | Audit Finding |
| :--- | :--- | :--- |
| **System Health State** | `HEALTHY` | Canonical and vector revisions are in exact alignment. |
| **Active Queue** | `.agents/memory/index_queue.jsonl` | 0 pending jobs, 0 failed jobs, 34 completed jobs. |
| **Dead-Letter Queue** | `.agents/memory/index_dead_letter.jsonl` | 0 dead-letter jobs. |
| **Advisory Lease Lock** | `.agents/memory/index_writer.lease.lock` | Enforces single-writer execution via POSIX `flock`. |
| **Vector Engine** | Milvus Lite (`~/.memsearch/milvus.db`) | 236 entities, 106 unique sources; 13 canonical files verified. |
| **Embedding Substrate** | `onnx-bge-m3` (Dimension: 1024) | `MIGRATION_REQUIRED: False` (Migration state: `CURRENT`). |
| **Test Verification** | `tests/test_memory_index_queue.py` | 10 / 10 tests passing (100% pass rate). |

---

## 2. Specification Compliance Matrix

### Section 15: Single-Writer / Queued Indexing
- **Architecture**: Canonical writes do not trigger uncoordinated semantic indexing inside hooks. Instead, updates are atomically enqueued into `.agents/memory/index_queue.jsonl`.
- **Failure Non-Suppression**: Never hides indexing failures (rejecting `memsearch index || true`). If backend indexing fails after canonical storage succeeds, the job enters retry state and index health transitions immediately to `DEGRADED`.
- **Single-Writer Serialization**: Background indexing jobs run strictly serialized under an advisory lease lock.

### Section 52: File Locking & Concurrency
- **Advisory Lease**: Managed through [`scripts/lock_manager.py`](file:///workspaces/codespaces-blank/scripts/lock_manager.py) via `index_writer.lease.lock`.
- **Atomic Operations**: All queue mutations use atomic file writes (`atomic_write` using temporary files and atomic rename).
- **Contention Handling**: Concurrent writers encountering a held lease timeout gracefully without corrupting the queue, returning `status: busy`.

### Section 53: Index / Canonical Consistency
- **Consistency Verification**:
  - When `canonical_revision != indexed_revision`, health is diagnosed as `STALE`.
  - When backend index or manifest is corrupted / unreadable, health is diagnosed as `FAILED` or `DEGRADED`.
  - Upon successful queue drain of all pending canonical updates, `indexed_revision` is updated to match `canonical_revision` and state transitions to `HEALTHY`.

### Section 98: Index Migration & Vector Space Compatibility
- **Vector Space Protection**: Embedding model (`bge-m3`), provider (`onnx`), and dimension (`1024`) are strictly tracked.
- **Migration Trigger**: Any deviation between configured embedding models in `~/.memsearch/config.toml` and historical index metadata triggers `MIGRATION_REQUIRED` diagnostics, preventing silent mixing of incompatible vector spaces.

### Section 99: Index Corruption Diagnostics
The system implements comprehensive anomaly detection across the 6 failure scenarios:
1. **Corrupt Index**: Validates JSON syntax of `manifest.json`.
2. **Wrong Dimension**: Detects collection embedding dimension mismatches.
3. **Missing Collection**: Verifies presence of `memsearch_chunks` collection.
4. **Half-Built Index**: Identifies interrupted queue jobs left in `processing` state.
5. **Stale Chunks**: Identifies hash discrepancies between disk files and indexed chunks.
6. **Deleted Source Files**: Identifies chunks remaining in vector store after file deletion and purges them.

---

## 3. Queue Coalescing and Dead-Letter Queue (DLQ) Mechanics

### Queue Coalescing
When multiple successive edits occur on the same canonical file before indexing completes:
1. Identical successive writes (same content hash) are deduplicated immediately at `enqueue()` time.
2. Rapid sequential edits with differing hashes are marked as `status: "coalesced"`, and only the latest snapshot is dispatched to the backend during `drain()`, collapsing $N$ writes into 1 upsert.

### Retry & Dead-Letter Queue (DLQ)
- **Retry Budget**: Configurable via `max_attempts` (default: 3).
- **Transient Failures**: Intermittent backend errors remain `status: "pending"` with incremented `attempts`.
- **Permanent Failures**: Once `attempts >= max_attempts`, the job is marked `failed` and atomically recorded to `.agents/memory/index_dead_letter.jsonl`.
- **Operator Remediation**:
  - `python3 scripts/memory_index_queue.py --list-dead-letter`
  - `python3 scripts/memory_index_queue.py --requeue-dead-letter`

---

## 4. Milvus Lite Index Synchronization Evidence

### Queue Drain Invocation
```bash
python3 -c "from scripts.memory_index_queue import drain_queue; drain_queue(sync_dirty=True)"
```

**Execution Log Excerpt**:
```text
INFO:memory_index_queue:Synchronized 4 dirty canonical files into index queue.
INFO:milvus_lite.server_manager:MilvusLite server started for /home/codespace/.memsearch/milvus.db on port 39547
INFO:memsearch_backend:Purged entities for /workspaces/codespaces-blank/.agents/memory/sessions/2026-09-01-1546.md from MilvusStore (in-process)
INFO:memsearch_backend:Indexed file into MemSearch backend: .../sessions/2026-09-01-1546.md (hash: 7fe9917b)
INFO:memory_index_queue:Successfully processed job job_... for .../sessions/2026-09-01-1546.md
...
Drain result: {
  "status": "completed",
  "processed": 4,
  "coalesced": 0,
  "failed": 0,
  "duration_seconds": 36.138,
  "health_status": "HEALTHY"
}
```

### Verified Canonical Files in Milvus Lite
```text
Milvus Store Collection: memsearch_chunks (URI: ~/.memsearch/milvus.db)
Total Entities: 236 | Total Unique Sources: 106

Canonical Files Synchronized:
  ✓ /workspaces/codespaces-blank/.agents/memory/ARCHITECTURE.md
  ✓ /workspaces/codespaces-blank/.agents/memory/CURRENT.md
  ✓ /workspaces/codespaces-blank/.agents/memory/DECISIONS.md
  ✓ /workspaces/codespaces-blank/.agents/memory/GOTCHAS.md
  ✓ /workspaces/codespaces-blank/.agents/memory/INDEX.md
  ✓ /workspaces/codespaces-blank/.agents/memory/PROCEDURES.md
  ✓ /workspaces/codespaces-blank/.agents/memory/inbox/procedures/INDEX.md
  ✓ /workspaces/codespaces-blank/.agents/memory/inbox/procedures/proc-20260903-python3-01.md
  ✓ /workspaces/codespaces-blank/.agents/memory/inbox/procedures/proc-20260903-session-memory-audit.md
  ✓ /workspaces/codespaces-blank/.agents/memory/sessions/2026-09-01-1546.md
  ✓ /workspaces/codespaces-blank/.agents/memory/sessions/2026-09-01-1617.md
  ✓ /workspaces/codespaces-blank/.agents/memory/sessions/2026-09-02-1015.md
  ✓ /workspaces/codespaces-blank/.agents/memory/sessions/2026-09-02-1430.md
```

---

## 5. Automated Verification Test Suite

**Test Execution**: `pytest tests/test_memory_index_queue.py -v`

```text
============================= test session starts ==============================
platform linux -- Python 3.12.1, pytest-9.1.1, pluggy-1.6.0
rootdir: /workspaces/codespaces-blank
plugins: anyio-4.12.1
collected 10 items

tests/test_memory_index_queue.py::test_durable_queue_enqueue PASSED      [ 10%]
tests/test_memory_index_queue.py::test_coalescing_rapid_sequential_updates PASSED [ 20%]
tests/test_memory_index_queue.py::test_duplicate_event_deduplication PASSED [ 30%]
tests/test_memory_index_queue.py::test_single_writer_lease_lock_enforcement PASSED [ 40%]
tests/test_memory_index_queue.py::test_index_health_state_transitions PASSED [ 50%]
tests/test_memory_index_queue.py::test_cli_commands PASSED               [ 60%]
tests/test_memory_index_queue.py::test_dead_letter_queue_mechanics PASSED [ 70%]
tests/test_memory_index_queue.py::test_drain_queue_convenience_function PASSED [ 80%]
tests/test_memory_index_queue.py::test_section_99_corruption_diagnostics PASSED [ 90%]
tests/test_memory_index_queue.py::test_section_53_consistency_stale_and_degraded PASSED [100%]

============================= 10 passed in 33.62s ==============================
```
