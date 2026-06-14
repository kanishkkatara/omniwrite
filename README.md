# omniwrite 🚀

> **Agentic multi-platform content generation** — Blog · Reddit · LinkedIn · LinkedIn Comment

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![LiteLLM](https://img.shields.io/badge/LLM-LiteLLM%20100%2B%20providers-green)](https://litellm.ai)
[![LangGraph](https://img.shields.io/badge/agents-LangGraph-orange)](https://langchain-ai.github.io/langgraph/)

Give it a topic. Get a long-form blog post, a platform-native Reddit writeup, a LinkedIn post, and the first comment — all tuned to your brand voice, powered by a multi-agent pipeline.

---

## ✨ Features

- **🤖 Agentic pipeline** — Research → Strategy → Outline → Parallel Writers → Editor
- **🔌 100+ LLM providers** via [LiteLLM](https://litellm.ai): OpenAI, Anthropic, Gemini, Groq, Ollama (local), Mistral, AWS Bedrock, and more
- **🧩 Plugin architecture** — add new platforms (Medium, Substack, Twitter) by dropping a single file
- **📝 External YAML prompts** — edit prompts without touching Python code
- **💬 Chat interface** — agent-led conversation with outline approval before writing
- **🏷️ Brand DNA** — voice, audience, perspective, avoid-lists injected into every generation
- **🚀 Auto-publish** — Ghost, Hashnode, WordPress, Dev.to, Notion out of the box
- **💰 Cost tracking** — per-generation token usage and USD cost breakdown
- **🖥️ CLI tool** — `omniwrite generate "topic"` scriptable from anywhere
- **🐳 One-command Docker** — self-host with `docker compose up -d`
- **🦙 Local LLM** — run fully offline with Ollama (zero API cost)
- **🌍 Multi-language** — generate in 7+ languages
- **📊 Observability** — OpenTelemetry, LangSmith tracing, Prometheus metrics

---

## 🚀 Quick Start

### Option 1 — Docker (Recommended)

```bash
git clone https://github.com/your-org/omniwrite
cd omniwrite
cp .env.example .env          # add your API keys
cp config.example.yaml config.yaml
docker compose up -d
open http://localhost:3000
```

### Option 2 — Local Development

```bash
# Prerequisites: Python 3.11+, Node 18+, uv

git clone https://github.com/your-org/omniwrite
cd omniwrite
cp .env.example .env
cp config.example.yaml config.yaml

# Backend
uv pip install -e ".[dev]"
uvicorn backend.main:app --reload

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

### Option 3 — CLI Only

```bash
pip install omniwrite

omniwrite generate "The rise of RAG pipelines in enterprise" \
  --platforms blog,reddit,linkedin \
  --model production
```

### Option 4 — Local LLM (zero API cost)

```bash
# Requires Docker + Ollama
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
# Pull a model
docker exec omniwrite-ollama-1 ollama pull llama3.3
open http://localhost:3000
```

---

## 🔧 Configuration

All settings live in `config.yaml`. Environment variables override YAML values.

### Minimal `.env` to get started

```env
# Pick at least one:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional (improves research quality):
TAVILY_API_KEY=tvly-...
```

### Switch models in `config.yaml`

```yaml
models:
  test:
    model: "gpt-4.1-nano"     # fast, cheap — default

  production:
    model: "claude-sonnet-4-5" # high quality

  # Local (free):
  local:
    model: "ollama/llama3.3"
    base_url: "http://localhost:11434"

default_mode: test   # or: production | local
```

See [`config.example.yaml`](config.example.yaml) for the full reference.

---

## 🧩 Supported LLM Providers

| Provider | Example Models | Needs Key |
|---|---|---|
| OpenAI | gpt-4.1-nano, gpt-4o, o3 | ✅ |
| Anthropic | claude-sonnet-4-5, claude-opus-4 | ✅ |
| Google | gemini-2.0-flash, gemini-2.5-pro | ✅ |
| Groq | llama-3.3-70b (ultra-fast) | ✅ |
| Mistral | mistral-large, codestral | ✅ |
| **Ollama** | llama3.3, qwen2.5, deepseek-r1 | ❌ Free |
| AWS Bedrock | Any Bedrock model | ✅ |
| Azure OpenAI | Any Azure deployment | ✅ |
| Hugging Face | Any inference endpoint | ✅ |

Any [LiteLLM-supported provider](https://docs.litellm.ai/docs/providers) works.

---

## 🚀 Supported Output Platforms

| Platform | Built-in |
|---|---|
| 📝 Blog Post (Markdown) | ✅ |
| 🤖 Reddit | ✅ |
| 💼 LinkedIn Post | ✅ |
| 💬 LinkedIn First Comment | ✅ |
| ✉️ Medium | Community plugin |
| 📰 Substack | Community plugin |
| 🐦 Twitter/X thread | Community plugin |

---

## 🔗 Publishing Integrations

| Platform | Status |
|---|---|
| Ghost CMS | ✅ Built-in |
| Hashnode | ✅ Built-in |
| WordPress | ✅ Built-in |
| Dev.to | ✅ Built-in |
| Notion | ✅ Built-in |

---

## 🧩 Writing a Platform Plugin

Drop a file in `backend/plugins/` — it's auto-discovered:

```python
# backend/plugins/medium_plugin.py
from backend.plugins.base import PlatformPlugin
from backend.models.state import AgentState

class MediumPlugin(PlatformPlugin):
    name = "medium"
    display_name = "Medium"
    icon = "✉️"
    max_words = 2000
    supports_publish = True

    def get_system_prompt(self, brand):
        return "Write in Medium's thoughtful, narrative style..."

    async def generate(self, state, settings):
        # Your generation logic here
        ...
```

See [Plugin Guide](docs/plugins/writing-a-platform-plugin.md) for the full API.

---

## 📊 CLI Reference

```bash
omniwrite generate "topic"              # Generate with defaults
omniwrite generate "topic" \
  --platforms blog,linkedin \
  --model production \
  --length long \
  --keywords "AI, SaaS" \
  --publish ghost,hashnode              # Auto-publish

omniwrite serve                         # Start web server
omniwrite brand create                  # Interactive brand setup
omniwrite brand list                    # List saved brands
omniwrite prompts list                  # List prompts
omniwrite prompts edit blog             # Edit blog prompt in $EDITOR
omniwrite config show                   # Show resolved config
```

---

## 🏗️ Architecture

```
User Input (Chat)
      │
      ▼
Brief Extractor Agent
      │
      ├──► Research Agent (web search — optional)
      │
      ├──► Strategy Agent (angle, tone, hooks)
      │
      └──► Outline Agent ──► [Human Approval]
                │
          ┌────┼────┐────────┐
          ▼    ▼    ▼        ▼
        Blog Reddit LinkedIn LI Comment   ← parallel
          └────┴────┘────────┘
                │
          Editor / QA Agent
                │
          Output Formatter
```

---

## 🤝 Contributing

We love contributions! See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for:
- Adding a new platform plugin
- Improving prompts (no Python needed!)
- Adding a publisher integration
- Adding a search provider

---

## 📄 License

MIT — see [LICENSE](LICENSE).
