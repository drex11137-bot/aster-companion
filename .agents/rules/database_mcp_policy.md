# Database Tooling & Safe MCP Policy Rule

This rule governs database operations, database client tools, and MCP database adapters within the Antigravity agent workstation.

## 1. Tooling Requirements
- Client packages `sqlite3`, `postgresql-client`, `default-mysql-client`, and `redis-tools` are installed and available in `$PATH`.
- Local tests and fixtures must use SQLite or ephemeral test containers rather than persistent unmanaged daemon processes.

## 2. Safe MCP Access & Read-Only Governance
- MCP database adapters (`sqlite-safe`, `postgres-safe`) must have read-only mode explicitly configured (`DB_READONLY=true`, `PGREADONLY=true`).
- Never perform unrestricted production writes.
- For mutation-capable or DDL operations on non-fixture databases:
  ```text
  ASK / APPROVAL REQUIRED
  ```

## 3. Data Integrity & Credential Protection
- Never store plaintext credentials, production connection URIs, or tokens in `.agents/memory/`, rules, or code files.
- All database test fixtures must contain synthetic, non-PII test data only.
