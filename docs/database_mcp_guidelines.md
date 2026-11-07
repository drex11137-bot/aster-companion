# Safe Read-Only Database MCP Integration & Approval Policy

This document defines the operational standards, security controls, and approval policies for database tooling and Model Context Protocol (MCP) database integrations in the Antigravity engineering environment per **Sections 20 & 21 of `instruction.md`**.

---

## 1. Core Principles

1. **Read-Only by Default**: Database MCP integrations (`sqlite-safe`, `postgres-safe`) and database client tools MUST operate with read-only permissions by default when inspecting repositories, testing schemas, or running analytical queries.
2. **Zero Direct Production Writes**: Autonomous agents are strictly prohibited from performing write, update, delete, or schema-altering (DDL) operations on production or non-sandboxed shared databases without explicit, recorded user approval (`ASK / APPROVAL REQUIRED`).
3. **Zero Secrets Policy**: Database passwords, connection strings with embedded credentials, private tokens, or sensitive production connection URLs MUST NEVER be written to repository files, `.agents/memory/`, or logs.
4. **Client-First Tooling**: Prefer lightweight database client utilities (`sqlite3`, `postgresql-client`, `default-mysql-client`, `redis-tools`) and localized fixture databases over running heavy daemon background services unless explicitly mandated by project requirements.

---

## 2. Toolchain Inventory & Roles

| Database Tool / Client | Package / Binary | Primary Purpose | Safety Classification |
|---|---|---|---|
| **SQLite CLI** | `sqlite3` (`3.45.x+`) | Local file database inspection, migration verification, fixture testing | Sandboxed Local Read/Write |
| **PostgreSQL Client** | `psql` (`16.x+`) | Remote schema inspection, query execution, connection validation | Remote Network Client (Read-only by convention) |
| **MySQL Client** | `mysql` (`8.0.x+`) | Remote MySQL/MariaDB schema querying, status probing | Remote Network Client (Read-only by convention) |
| **Redis Tools** | `redis-cli` (`7.0.x+`) | In-memory cache inspection, TTL analysis, key scanning | Network Client (Non-destructive commands only) |
| **SQLite Safe MCP** | `@modelcontextprotocol/server-sqlite` | MCP-mediated local SQLite schema introspection & read queries | Enforced Read-Only (`DB_READONLY=true`) |
| **PostgreSQL Safe MCP** | `@modelcontextprotocol/server-postgres` | MCP-mediated PostgreSQL schema exploration & read queries | Enforced Read-Only (`PGREADONLY=true`) |

---

## 3. Safe MCP Database Server Configuration

Workspace-scoped database MCP servers are registered in `.agents/mcp_config.json`:

```json
{
  "mcpServers": {
    "sqlite-safe": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "/workspaces/codespaces-blank/fixtures/database/test.db"],
      "env": {
        "DB_READONLY": "true"
      },
      "description": "Safe read-only SQLite MCP server for local database schema inspection and queries."
    },
    "postgres-safe": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://readonly_user@localhost:5432/app_db"],
      "env": {
        "PGREADONLY": "true"
      },
      "description": "Safe read-only PostgreSQL MCP server for database schema inspection and analytical queries."
    }
  }
}
```

### Safety Controls for MCP Integrations
- **Environment Flag Enforcement**: The `DB_READONLY=true` and `PGREADONLY=true` variables instruct the server adapter to reject mutation queries (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`).
- **Connection Isolation**: Connection strings use dedicated read-only database roles without `GRANT ALL` or schema modification privileges.
- **Query Parameterization**: Dynamic queries must utilize parameterized SQL to prevent SQL injection vulnerabilities during automated agent evaluations.

---

## 4. Mutation & DDL Approval Policy (`ASK / APPROVAL REQUIRED`)

When a developer or agent workflow requires schema migrations, database seeding, or data modifications:

1. **Local Fixture Exception**: Local fixture databases (e.g., `/workspaces/codespaces-blank/fixtures/database/*.db`) and test containers created solely for automated unit testing are exempt from interactive prompts, provided they do not connect to external environments.
2. **External / Shared / Production Databases**:
   - Any execution of `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, `MIGRATE`, or `TRUNCATE` against remote database targets requires an explicit approval gate:
   ```text
   [SECURITY GATEKEEPER]
   Operation: Database Mutation / DDL Execution
   Target: postgresql://db.production.internal:5432/primary
   Statement: ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
   Policy: ASK / APPROVAL REQUIRED
   Status: Awaiting human confirmation before dispatch.
   ```
3. **Transaction Safety**: Approved migrations and mutation scripts must be wrapped in atomic transactions (`BEGIN ... COMMIT`) with verified rollback scripts (`DOWN` migrations).

---

## 5. Sanitization, Privacy & PII Handling

- **Test Fixture Datasets**: All test data stored in `fixtures/database/` must use synthetic, non-PII records (e.g., `alice@engineering.local`, mock SKU numbers, synthetic timestamps).
- **Production Data Dumps**: Production database dumps containing real customer PII or credential hashes must never be imported into local or Codespaces environments.

---

## 6. Verification & Health Probing

Database tooling health is verified using standard non-destructive commands:

```bash
# SQLite verification
sqlite3 fixtures/database/test.db ".tables"
sqlite3 fixtures/database/test.db "SELECT count(*) FROM users;"

# Client version inspection
sqlite3 --version
psql --version
mysql --version
redis-cli --version
```
