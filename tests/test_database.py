"""
Verification test suite for Database Tooling & Safe MCP Integration.
Verifies Section 20 & 21 compliance:
- Client tools: sqlite3, postgresql-client (psql), mysql-client (mysql), redis-tools (redis-cli)
- SQLite test database fixtures and schemas (users, products, orders, order_items)
- Relational integrity and query execution
- MCP database configuration checks
"""

import os
import sqlite3
import subprocess
import json
import unittest
from pathlib import Path

FIXTURE_DB = Path("/workspaces/codespaces-blank/fixtures/database/test.db")
MCP_CONFIG = Path("/workspaces/codespaces-blank/.agents/mcp_config.json")
GUIDELINES_DOC = Path("/workspaces/codespaces-blank/docs/database_mcp_guidelines.md")


class TestDatabaseToolingAndMCP(unittest.TestCase):
    def test_client_binaries_installed(self):
        """Verify that sqlite3, psql, mysql, and redis-cli binaries are in PATH and functional."""
        binaries = [
            ("sqlite3", ["sqlite3", "--version"]),
            ("psql", ["psql", "--version"]),
            ("mysql", ["mysql", "--version"]),
            ("redis-cli", ["redis-cli", "--version"]),
        ]
        for name, cmd in binaries:
            with self.subTest(binary=name):
                res = subprocess.run(cmd, capture_output=True, text=True)
                self.assertEqual(
                    res.returncode, 0, f"{name} failed execution: {res.stderr}"
                )
                output = res.stdout.strip() or res.stderr.strip()
                self.assertTrue(len(output) > 0, f"{name} produced empty version output")

    def test_sqlite_fixture_database_exists(self):
        """Verify the SQLite test database exists and is accessible."""
        self.assertTrue(FIXTURE_DB.exists(), f"Missing fixture DB at {FIXTURE_DB}")
        self.assertGreater(FIXTURE_DB.stat().st_size, 0, "Fixture DB is empty")

    def test_sqlite_schema_tables(self):
        """Verify the test database contains users, products, orders, and order_items tables."""
        conn = sqlite3.connect(FIXTURE_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected_tables = {"users", "products", "orders", "order_items"}
        self.assertTrue(
            expected_tables.issubset(tables),
            f"Expected tables {expected_tables} missing from {tables}",
        )

    def test_sqlite_relational_queries(self):
        """Verify data integrity and join queries across users, orders, and products."""
        conn = sqlite3.connect(FIXTURE_DB)
        cursor = conn.cursor()

        # Check users count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        self.assertGreaterEqual(user_count, 4, "Users table should have at least 4 rows")

        # Check products count
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        self.assertGreaterEqual(product_count, 4, "Products table should have at least 4 rows")

        # Check orders count
        cursor.execute("SELECT COUNT(*) FROM orders")
        order_count = cursor.fetchone()[0]
        self.assertGreaterEqual(order_count, 4, "Orders table should have at least 4 rows")

        # Test relational join query
        query = """
        SELECT u.username, o.id, o.status, p.name, oi.quantity, oi.unit_price, o.total_amount
        FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN order_items oi ON oi.order_id = o.id
        JOIN products p ON oi.product_id = p.id
        ORDER BY o.id, oi.id
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        self.assertGreaterEqual(len(rows), 6, "Relational join query should return >= 6 items")
        conn.close()

    def test_mcp_config_database_servers(self):
        """Verify that .agents/mcp_config.json contains safe database MCP configurations."""
        self.assertTrue(MCP_CONFIG.exists(), f"Missing MCP config at {MCP_CONFIG}")
        with open(MCP_CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)

        servers = config.get("mcpServers", {})
        self.assertIn("sqlite-safe", servers, "sqlite-safe server missing from mcp_config.json")
        self.assertIn("postgres-safe", servers, "postgres-safe server missing from mcp_config.json")

        sqlite_cfg = servers["sqlite-safe"]
        self.assertEqual(sqlite_cfg.get("env", {}).get("DB_READONLY"), "true")

        postgres_cfg = servers["postgres-safe"]
        self.assertEqual(postgres_cfg.get("env", {}).get("PGREADONLY"), "true")

    def test_guidelines_documentation_exists(self):
        """Verify database guidelines and approval policy documentation exists."""
        self.assertTrue(
            GUIDELINES_DOC.exists(),
            f"Missing database MCP guidelines at {GUIDELINES_DOC}",
        )
        content = GUIDELINES_DOC.read_text(encoding="utf-8")
        self.assertIn("ASK / APPROVAL REQUIRED", content)
        self.assertIn("sqlite-safe", content)
        self.assertIn("postgres-safe", content)


if __name__ == "__main__":
    unittest.main()
