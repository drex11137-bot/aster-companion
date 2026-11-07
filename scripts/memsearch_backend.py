#!/usr/bin/env python3
"""
memsearch_backend.py - MemSearch Semantic Retrieval Adapter Boundary.
Per Instruction.md Section 21 & 35.

Provides a unified SemanticRetrievalBackend interface isolating the rest
of the system from vector database / embedding implementation details
(Milvus Lite, Milvus Server, Zilliz, or local fallback).
"""

import os
import sys
import json
import time
import shutil
import hashlib
import logging
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("memsearch_backend")

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_INDEX_DIR = os.path.join(WORKSPACE_ROOT, ".agents", "memory", ".memsearch")

# Ensure virtualenv site-packages are discoverable if present
_venv_candidates = [
    os.path.join(WORKSPACE_ROOT, ".venv-memsearch"),
    os.path.expanduser("~/.venv-memsearch"),
]
for _venv in _venv_candidates:
    if os.path.exists(_venv):
        import glob
        for _sp in glob.glob(os.path.join(_venv, "lib", "python*", "site-packages")):
            if _sp not in sys.path:
                sys.path.insert(0, _sp)


class SemanticRetrievalBackend:
    """Abstract interface for semantic retrieval per Instruction.md Section 21."""

    def index(self, file_path: str, content: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Indexes or updates a single file in the semantic retrieval backend."""
        raise NotImplementedError

    def delete(self, file_path: str) -> bool:
        """Removes a file and its indexed chunks from the semantic retrieval backend."""
        raise NotImplementedError

    def search(self, query: str, top_k: int = 5, score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Performs semantic search returning ranked chunks."""
        raise NotImplementedError

    def expand(self, chunk_id_or_path: str) -> Dict[str, Any]:
        """Expands a search match to inspect surrounding context."""
        raise NotImplementedError

    def health(self) -> Dict[str, Any]:
        """Returns health status of the semantic retrieval substrate."""
        raise NotImplementedError

    def rebuild(self, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Rebuilds the entire index from scratch for specified or discovered files."""
        raise NotImplementedError


class MemSearchBackend(SemanticRetrievalBackend):
    """
    Concrete adapter for MemSearch.
    Detects native CLI/library, with safe degraded fallback to prevent memory corruption.
    """

    def __init__(self, index_dir: str = DEFAULT_INDEX_DIR):
        self.index_dir = index_dir
        os.makedirs(self.index_dir, exist_ok=True)
        self.cli_path = shutil.which("memsearch")
        self.has_python_pkg = self._check_python_pkg()
        self.manifest_path = os.path.join(self.index_dir, "manifest.json")
        self._is_degraded = False
        self._degraded_reason = None
        self._load_manifest()

    def _purge_entities(self, abs_path: str) -> bool:
        """
        Purges indexed entities/chunks for the given file from the underlying Milvus Lite vector store.
        """
        # 1. Try in-process MilvusStore
        try:
            from memsearch.store import MilvusStore
            from memsearch.config import resolve_config
            cfg = resolve_config()
            with MilvusStore(uri=cfg.milvus.uri, collection=cfg.milvus.collection, dimension=None) as store:
                if store._client.has_collection(store._collection):
                    store.delete_by_source(abs_path)
                    logger.info(f"Purged entities for {abs_path} from MilvusStore (in-process)")
                    return True
                return True
        except Exception as e1:
            logger.debug(f"In-process MilvusStore purge unavailable/failed: {e1}")

        # 2. Try subprocess fallback using venv python
        venv_py = os.path.join(WORKSPACE_ROOT, ".venv-memsearch", "bin", "python3")
        if os.path.exists(venv_py):
            try:
                cmd = [
                    venv_py,
                    "-c",
                    (
                        "import sys\n"
                        "from memsearch.store import MilvusStore\n"
                        "from memsearch.config import resolve_config\n"
                        "cfg = resolve_config()\n"
                        "target = sys.argv[1]\n"
                        "with MilvusStore(uri=cfg.milvus.uri, collection=cfg.milvus.collection, dimension=None) as store:\n"
                        "    if store._client.has_collection(store._collection):\n"
                        "        store.delete_by_source(target)\n"
                    ),
                    abs_path,
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if res.returncode == 0:
                    logger.info(f"Purged entities for {abs_path} from MilvusStore (subprocess)")
                    return True
                else:
                    logger.warning(f"Subprocess MilvusStore purge returned non-zero ({res.returncode}): {res.stderr}")
            except Exception as e2:
                logger.warning(f"Error invoking MilvusStore purge subprocess for {abs_path}: {e2}")

        return False

    def _check_python_pkg(self) -> bool:
        try:
            import memsearch  # noqa: F401
            return True
        except ImportError:
            return False

    def _load_manifest(self):
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    self.manifest = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read manifest, creating new: {e}")
                self.manifest = {"indexed_files": {}, "last_updated": None}
        else:
            self.manifest = {"indexed_files": {}, "last_updated": None}

    def _save_manifest(self):
        try:
            temp_path = f"{self.manifest_path}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.manifest, f, indent=2)
            os.replace(temp_path, self.manifest_path)
        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")

    def index(self, file_path: str, content: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Indexes file_path into backend.
        """
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path) and content is None:
            logger.warning(f"Cannot index non-existent file: {abs_path}")
            return False

        if content is None:
            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Failed to read file {abs_path} for indexing: {e}")
                return False

        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Native CLI delegation if available
        if self.cli_path:
            for attempt in range(2):
                try:
                    self._purge_entities(abs_path)
                    res = subprocess.run(
                        [self.cli_path, "index", abs_path, "--provider", "onnx"],
                        capture_output=True,
                        text=True,
                        timeout=180
                    )
                    if res.returncode == 0:
                        break
                    elif "Could not open the local Milvus database" in (res.stderr or "") and attempt == 0:
                        time.sleep(0.3)
                        continue
                    else:
                        logger.warning(f"MemSearch CLI returned non-zero ({res.returncode}): {res.stderr}")
                except Exception as e:
                    logger.error(f"Error invoking MemSearch CLI for {abs_path}: {e}")

        # Update local manifest
        file_size = len(content.encode("utf-8"))
        self.manifest["indexed_files"][abs_path] = {
            "content_hash": content_hash,
            "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "size_bytes": file_size,
            "metadata": metadata or {}
        }
        self.manifest["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._save_manifest()
        logger.info(f"Indexed file into MemSearch backend: {abs_path} (hash: {content_hash[:8]})")
        return True

    def delete(self, file_path: str) -> bool:
        abs_path = os.path.abspath(file_path)

        # Entity purge from Milvus Lite / vector store
        try:
            self._purge_entities(abs_path)
        except Exception as e:
            logger.warning(f"Entity purge encountered exception for {abs_path}: {e}")

        # Manifest deletion
        manifest_deleted = False
        if abs_path in self.manifest.get("indexed_files", {}):
            del self.manifest["indexed_files"][abs_path]
            self.manifest["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            self._save_manifest()
            manifest_deleted = True
            logger.info(f"Deleted file from MemSearch manifest: {abs_path}")

        logger.info(f"Deletion completed for {abs_path} (manifest_deleted={manifest_deleted})")
        return True

    def search(self, query: str, top_k: int = 5, score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        results = []
        if self.cli_path:
            for attempt in range(2):
                try:
                    res = subprocess.run(
                        [self.cli_path, "search", "--top-k", str(top_k), "--provider", "onnx", "--json-output", "--", query],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        raw = res.stdout
                        # Locate the start of the JSON array ('['), stripping leading onnxruntime or device warnings
                        start_idx = raw.find('[')
                        parsed_chunks = None

                        # Probe occurrences of '[' to bypass any bracketed warning banners (e.g. [W:onnxruntime...])
                        search_pos = 0
                        while True:
                            idx = raw.find('[', search_pos)
                            if idx == -1:
                                break
                            chunk_str = raw[idx:].strip()
                            last_bracket = chunk_str.rfind(']')
                            candidate = chunk_str[:last_bracket + 1] if last_bracket != -1 else chunk_str
                            try:
                                val = json.loads(candidate)
                                if isinstance(val, list):
                                    parsed_chunks = val
                                    start_idx = idx
                                    break
                            except json.JSONDecodeError:
                                pass
                            search_pos = idx + 1

                        if parsed_chunks is not None:
                            if score_threshold > 0.0:
                                parsed_chunks = [c for c in parsed_chunks if c.get("score", 0.0) >= score_threshold]
                            return parsed_chunks[:top_k]
                        else:
                            # Parsing failed: remove silent swallow, log error, and set backend health to DEGRADED
                            target_snippet = raw[start_idx:] if start_idx != -1 else raw
                            try:
                                json.loads(target_snippet)
                            except json.JSONDecodeError as jde:
                                logger.error(f"Failed to parse MemSearch JSON output: {jde}. Raw stdout: {raw[:300]}")
                                self._is_degraded = True
                                self._degraded_reason = f"JSON decode error: {jde}"
                            break
                    elif res.returncode != 0:
                        if "Could not open the local Milvus database" in (res.stderr or "") and attempt == 0:
                            time.sleep(0.3)
                            continue
                        logger.error(f"MemSearch CLI search returned non-zero code {res.returncode}: {res.stderr}")
                        self._is_degraded = True
                        self._degraded_reason = f"CLI search returned code {res.returncode}"
                        break
                except Exception as e:
                    logger.error(f"CLI search failed: {e}")
                    self._is_degraded = True
                    self._degraded_reason = f"CLI search exception: {e}"
                    break

        # Fallback keyword match against indexed files in manifest
        query_terms = query.lower().split()
        for path, info in self.manifest.get("indexed_files", {}).items():
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read().lower()
                matches = sum(text.count(t) for t in query_terms)
                if matches > 0:
                    score = round(min(matches / 10.0, 1.0), 3)
                    if score >= score_threshold:
                        results.append({
                            "file_path": path,
                            "score": score,
                            "content_hash": info.get("content_hash"),
                            "indexed_at": info.get("indexed_at")
                        })
            except Exception as ex:
                logger.debug(f"Failed reading file {path} during fallback keyword search: {ex}")
                continue

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def expand(self, chunk_id_or_path: str) -> Dict[str, Any]:
        abs_path = os.path.abspath(chunk_id_or_path)
        if os.path.exists(abs_path):
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return {
                "file_path": abs_path,
                "content": content,
                "lines": len(content.splitlines())
            }

        # If not a file path on disk, try expanding via CLI as chunk hash
        if self.cli_path:
            try:
                res = subprocess.run(
                    [self.cli_path, "expand", chunk_id_or_path, "--json-output"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if res.returncode == 0 and res.stdout.strip():
                    raw = res.stdout
                    start_idx = raw.find('{')
                    if start_idx != -1:
                        end_idx = raw.rfind('}')
                        candidate = raw[start_idx:end_idx + 1] if end_idx != -1 else raw[start_idx:]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                logger.debug(f"CLI expand failed: {e}")

        return {"error": "Target not found", "target": chunk_id_or_path}

    def health(self) -> Dict[str, Any]:
        has_native = bool(self.cli_path or self.has_python_pkg)
        indexed_count = len(self.manifest.get("indexed_files", {}))
        status = "DEGRADED" if (self._is_degraded or not has_native) else "HEALTHY"
        info = {
            "status": status,
            "backend": "memsearch",
            "has_native_cli": bool(self.cli_path),
            "has_python_pkg": self.has_python_pkg,
            "mode": "native" if has_native and not self._is_degraded else "adapter_fallback",
            "indexed_files_count": indexed_count,
            "last_updated": self.manifest.get("last_updated"),
            "storage_path": self.index_dir
        }
        if self._is_degraded and self._degraded_reason:
            info["degraded_reason"] = self._degraded_reason
        return info

    def rebuild(self, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        logger.info("Starting rebuild of MemSearch index...")
        self.manifest = {"indexed_files": {}, "last_updated": None}
        if paths is None:
            # Default to canonical memory directories
            mem_dir = os.path.join(WORKSPACE_ROOT, ".agents", "memory")
            global_mem_dir = os.path.expanduser("~/.gemini/antigravity-cli/memory")
            paths = []
            for d in [mem_dir, global_mem_dir]:
                if os.path.exists(d):
                    for root, dirs, files in os.walk(d):
                        rel_root = os.path.relpath(root, d)
                        # Skip session archives, inbox staging, .memsearch, and hidden dirs
                        if any(part.startswith(".") or part in ("sessions", "inbox") for part in rel_root.split(os.sep) if part != "."):
                            continue
                        for f in files:
                            if f.endswith(".md"):
                                paths.append(os.path.join(root, f))

        success_count = 0
        failed_count = 0
        for p in paths:
            if self.index(p):
                success_count += 1
            else:
                failed_count += 1

        self.manifest["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._save_manifest()
        if failed_count > 0:
            self._is_degraded = True
            self._degraded_reason = f"Rebuild failed on {failed_count} files"
        else:
            self._is_degraded = False
            self._degraded_reason = None

        return {
            "status": "rebuilt",
            "indexed_count": success_count,
            "failed_count": failed_count,
            "timestamp": self.manifest["last_updated"]
        }


def get_backend() -> SemanticRetrievalBackend:
    return MemSearchBackend()
