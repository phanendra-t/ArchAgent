# ArchAgent

**Agentic Code Review with Architectural Intent Understanding**

An AI code reviewer that catches architectural drift in PRs — cross-boundary dependencies, layer violations, and broken design contracts. Learns from your feedback to improve over time.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                                                                │
│  ┌──────────────┐   ┌────────────────┐   ┌──────────────┐   │
│  │  Engine      │   │  Dashboard     │   │  PostgreSQL  │   │
│  │  Port 8000   │   │  Port 3000     │   │  Port 5432   │   │
│  │              │   │                │   │              │   │
│  │  LLM Agents  │   │  Next.js UI    │   │  pgvector    │   │
│  │  Reward Model│   │  Feedback      │   │  Annotations │   │
│  │  Has API Key │   │  Metrics       │   │              │   │
│  └──────┬───────┘   └───────┬────────┘   └──────────────┘   │
│         └───────────────────┘                                 │
│                    ▲                                           │
└────────────────────┼──────────────────────────────────────────┘
                     │ HTTP
          ┌──────────┴──────────┐
          │   archagent CLI     │
          │   (bash script)     │
          │   No deps needed    │
          └─────────────────────┘
```

| Component | Docker Image | Purpose |
|-----------|-------------|---------|
| Engine | `phanitirumala/archagent-engine` | Multi-agent LLM review pipeline + reward model |
| Dashboard | `phanitirumala/archagent-dashboard` | Web UI for feedback, metrics, demos |
| CLI | [ArchagentCLI](https://github.com/phanendra-t/ArchagentCLI) | Bash script — talks to engine over HTTP |

---

## Quick Start

### 1. Install the CLI (one-time)

```bash
curl -fsSL https://raw.githubusercontent.com/phanendra-t/ArchagentCLI/main/install.sh | bash
```

The CLI lives in a separate public repo: [phanendra-t/ArchagentCLI](https://github.com/phanendra-t/ArchagentCLI)

### 2. Bootstrap a project

In any project where you want architectural review:

```bash
cd ~/my-project
archagent init
```

This creates:
- `docker-compose.yml` — pulls engine + dashboard + postgres
- `architecture-intent.yaml` — starter template to define your rules
- `.env` — place for your Anthropic API key
- `.gitignore` — excludes secrets and runtime data

### 3. Configure and start

```bash
# Add your API key
edit .env    # Set ANTHROPIC_API_KEY=sk-ant-...

# Start the stack
docker compose up -d
```

### 4. Review a PR

```bash
git diff HEAD~1 | archagent review --diff -

# Or from a file
archagent review --diff my-pr.diff
```

### 5. Open the Dashboard

```
http://localhost:3000
```

---

## How It Works

```
PR Diff + architecture-intent.yaml
          │
          ▼
┌─────────────────────────────────┐
│  1. Diff Parser                 │  Language-agnostic (TS, Py, Go, Java, Rust)
│  2. Rule Pre-Check              │  Catches obvious violations (path/import)
│  3. LLM Agents (parallel)       │  Context + Layer + Security reviewers
│  4. Synthesis                   │  Merge, deduplicate, rank
│  5. Defender Agent              │  Challenge findings, remove false positives
│  6. Reward Model (RLHF)        │  Score confidence from past feedback
└─────────────────────────────────┘
          │
          ▼
Findings with severity, evidence, impact, fix suggestions
```

### Feedback Loop (RLHF)

1. Review produces findings
2. You annotate: `archagent feedback <review-id> <finding-id> valid|false_positive`
3. After 20+ annotations, reward model activates
4. Future findings scored by confidence — false positives get suppressed
5. Run `archagent retrain` to update the model

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `archagent init` | Bootstrap project (docker-compose + intent + .env) |
| `archagent review --diff <file>` | Review a PR diff |
| `archagent feedback <r> <f> <label>` | Annotate a finding |
| `archagent stats` | Show model statistics |
| `archagent retrain` | Retrain reward model |
| `archagent validate <file>` | Validate intent file |

### Flags for `review`

```
--diff <file|->     Diff file or stdin (default: stdin)
--intent <file>     Override intent file (sends YAML to engine)
--format text|json  Output format (default: text)
--fail-on <sev>     Exit code 1 on findings of this severity or higher
--no-reward         Skip reward model scoring
--output <file>     Write to file
--quiet             Suppress progress messages
```

---

## Architecture Intent YAML

Define your architecture rules. ArchAgent reads this to know what's allowed.

> Full schema reference: [Architecture Intent YAML — Reference (v0.2.1)](https://github.com/phanendra-t/ArchagentCLI#architecture-intent-yaml--reference-v021) in the CLI repo.

```yaml
schema_version: "1.0"
system: "my-app"

bounded_contexts:
  - name: orders
    owns: ["src/orders/**"]
    forbidden_dependencies: [notifications, analytics]

layers:
  - name: controller
    pattern: "src/**/controllers/**"
    forbidden_imports_from: [repository]

communication_patterns:
  - between: [orders, notifications]
    allowed: event
    forbidden: direct

security_rules:
  - context: payments
    constraints:
      - "No logging of card numbers"
```

Run `archagent init --template full` for a comprehensive example.

---

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | — | Claude API key |
| `ARCHAGENT_ENGINE_PORT` | No | 8000 | Engine port |
| `ARCHAGENT_DASHBOARD_PORT` | No | 3000 | Dashboard port |
| `ARCHAGENT_SERVER` | No | localhost:8000 | CLI target (for remote engines) |

---

## Verified Results

| Metric | Target | Actual |
|--------|--------|--------|
| Recall | ≥70% | **100% (5/5)** |
| False positive rate | ≤20% | **0% (0/3)** |
| Latency | <30s | ~15-20s |
| Languages | Any | TS, Py, Go, Java, Rust, C# |

---

## Tech Stack

- **Engine:** Python 3.12, FastAPI, LangGraph, Anthropic Claude Sonnet 4
- **ML:** scikit-learn (MLP), sentence-transformers, pgvector
- **Dashboard:** Next.js 14, TypeScript, Tailwind, shadcn/ui, Recharts
- **Database:** PostgreSQL 16 + pgvector
- **CLI:** Bash (curl + jq)
- **Infra:** Docker, Docker Compose

---

## CI/CD Integration

See `examples/github-action/workflow.yml` and `examples/pre-commit/.pre-commit-config.yaml`.

---

## Development (From Source)

```bash
# Backend
cd backend
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install && npm run dev
```

---

## License

MIT
