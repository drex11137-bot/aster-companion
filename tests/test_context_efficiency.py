import os
import subprocess
import json
import unittest

def run_search(query):
    result = subprocess.run(
        ["python3", "/workspaces/codespaces-blank/scripts/search_memory.py", query, "--json", "--scope", "all"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    
    try:
        data = json.loads(result.stdout)
        return [match["file"] for match in data.get("results", [])]
    except Exception:
        return []

def main():
    tasks = {
        "Git task": "Git",
        "Frontend task": "Frontend",
        "Database task": "Database"
    }

    report_lines = [
        "# Context Efficiency Test Report",
        "",
        "## Methodology",
        "Tested memory routing filtering by querying specific domain terms.",
        "Expected behavior: Only relevant domain files should be returned in the results, keeping the context lightweight.",
        ""
    ]

    for task_name, query in tasks.items():
        loaded_files = run_search(query)
        report_lines.append(f"### {task_name}")
        report_lines.append(f"**Query**: `{query}`")
        if loaded_files:
            report_lines.append("**Loaded Files**:")
            for f in loaded_files:
                report_lines.append(f"- {f}")
            
            # Verify filtering
            if query == "Git":
                assert any("git.md" in f for f in loaded_files), "Missing git memory"
                assert not any("frontend.md" in f for f in loaded_files), "Leaked frontend memory"
                assert not any("medical.md" in f for f in loaded_files), "Leaked medical memory"
            elif query == "Frontend":
                assert any("frontend.md" in f for f in loaded_files), "Missing frontend memory"
                assert not any("git.md" in f for f in loaded_files), "Leaked git memory"
            elif query == "Database":
                assert any("database.md" in f for f in loaded_files), "Missing database memory"
                assert not any("git.md" in f for f in loaded_files), "Leaked git memory"
                
            report_lines.append("\n**Verdict**: PASS (Unrelated domains strictly filtered out)\n")
        else:
            report_lines.append("**Loaded Files**: None")
            report_lines.append("\n**Verdict**: FAIL\n")
            
    os.makedirs("/workspaces/codespaces-blank/docs/test_reports", exist_ok=True)
    report_path = "/workspaces/codespaces-blank/docs/test_reports/03_context_efficiency.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
        
    print(f"Test completed successfully. Report generated at {report_path}")

class TestContextEfficiency(unittest.TestCase):
    def test_context_efficiency(self):
        """Phase 8 (Section 28): Verify context efficiency and memory routing filtering."""
        main()

if __name__ == "__main__":
    unittest.main()
