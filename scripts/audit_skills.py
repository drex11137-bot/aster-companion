import os
import yaml
import re

skills_dir = "/workspaces/codespaces-blank/.agents/skills"
all_subdirs = sorted([d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))])

report = []
for name in all_subdirs:
    skill_path = os.path.join(skills_dir, name, "SKILL.md")
    if not os.path.exists(skill_path):
        continue
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()

    has_fm = content.startswith("---")
    fm_valid = False
    fm_data = {}
    body = content
    if has_fm:
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                fm_data = yaml.safe_load(parts[1])
                if isinstance(fm_data, dict) and "name" in fm_data and "description" in fm_data:
                    fm_valid = True
                body = parts[2]
            except Exception as e:
                fm_data = {"error": str(e)}
    
    # Let's check sections in content
    sections = {
        "frontmatter": fm_valid,
        "purpose": bool(re.search(r"(purpose|overview|description|principles|mission|objective)", content, re.I)),
        "triggers": bool(re.search(r"(trigger|activation|when to use|invoke|command)", content, re.I)),
        "prereqs": bool(re.search(r"(prereq|requirement|pre-flight|dependencies|environment|toolchain)", content, re.I)),
        "decision_tree": bool("mermaid" in content or "decision tree" in content.lower() or "flowchart" in content.lower() or "graph " in content),
        "workflows": bool(re.search(r"(workflow|procedure|step-by-step|actionable|instructions|execution)", content, re.I)),
        "verification": bool(re.search(r"(verif|test|assert|validate|evidence)", content, re.I)),
        "failure_recovery": bool(re.search(r"(failure|recovery|troubleshoot|remediation|fallback|error handling)", content, re.I)),
        "security": bool(re.search(r"(security|boundary|permission|guardrail|isolation|secret)", content, re.I))
    }
    
    tool_hallucinations = []
    for tool in ["read_file", "write_file", "edit_file", "modify_file", "run_cmd", "execute_command", "file_search", "read_url", "list_directory", "list_files", "grep_files"]:
        if re.search(r"\b" + tool + r"\b", content):
            tool_hallucinations.append(tool)
            
    report.append({
        "name": name,
        "sections": sections,
        "hallucinations": tool_hallucinations,
        "lines": len(content.splitlines()),
        "fm_data": fm_data
    })

print("| Skill | Frontmatter | Purpose | Triggers | Prereqs | Decision Tree | Workflows | Verification | Recovery | Security | Lines |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for r in report:
    s = r["sections"]
    def mark(b):
        return "✅" if b else "❌"
    print(f"| {r['name']} | {mark(s['frontmatter'])} | {mark(s['purpose'])} | {mark(s['triggers'])} | {mark(s['prereqs'])} | {mark(s['decision_tree'])} | {mark(s['workflows'])} | {mark(s['verification'])} | {mark(s['failure_recovery'])} | {mark(s['security'])} | {r['lines']} |")
