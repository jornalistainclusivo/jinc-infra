# Antigravity Agent Configurations (v1.2.1)

## 🛡️ Core Permissions & Script Authorization

- **Python Execution:** Full authorization granted for Python interpreters to execute scripts within `.agent/scripts/` and general workspace automation.
- **Node.js/NPM:** Explicit permission for `npm` commands, dependency audits, and build processes.
- **Filesystem Access:** Direct read/write access authorized for `src/`, `lib/`, `types/`, and configuration files within the workspace scope.
- **Scripting Freedom:** Agents are authorized to generate, modify, and execute temporary shell/python scripts for task automation without path rejection.

## 🧩 Skill Mapping & Environment

- **Terminal Integration:** Active (Enabled via v1.18.3+ protocol).
- **Execution Shell:** PowerShell (Windows 11) or Bash (WSL/Linux) via the `Bash` tool.
- **Trust Level:** High (Workspace Trusted).

## 🛠️ Tool Authorizations (The "Bash" Power-Grid)

- **`Bash` Tool:** Full invocation rights granted to the following specialist personas:
  - `orchestrator`, `seo-specialist`, `backend-specialist`, `database-architect`,
  - `debugger`, `devops-engineer`, `qa-automation-engineer`, `project-planner`,
  - `product-owner`, `product-manager`, `performance-optimizer`, `penetration-tester`,
  - `mobile-developer`, `game-developer`, `frontend-specialist`, `explorer-agent`,
  - `documentation-writer`, `security-auditor`, and `test-engineer`.
- **Constraint:** Operations must remain within the `jinc-cms` and `jinc-frontend` directories.

## 🚦 Security & Operational Protocol

- **NPM Guard:** Confirmation is mandatory before `npm install` if `package-lock.json` is modified.
- **Integrity Gate:** Running `python .agent/scripts/checklist.py .` is a hard requirement (Mandatory) before any merge or commit to the `main` branch.
- **Error Handling:** If a command fails due to permission, the agent must automatically check `AGENTS.md` and request a re-validation of "Workspace Trust" instead of aborting.
