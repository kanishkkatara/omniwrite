# Contributing to OmniWrite

Thank you for your interest in contributing! OmniWrite is designed to be highly extensible — you can add new platforms, improve prompts, or add publisher integrations without touching core code.

## Ways to Contribute

| Contribution Type | Difficulty | Impact |
|---|---|---|
| Improve a prompt YAML | Easy ⭐ | High — improves output quality |
| Add a platform plugin | Medium ⭐⭐ | High — new output platform |
| Add a publisher integration | Medium ⭐⭐ | High — auto-publish |
| Add a search provider | Medium ⭐⭐ | Medium — better research |
| Bug fix | Varies | High |
| New feature | Hard ⭐⭐⭐ | Varies |

---

## Development Setup

```bash
git clone https://github.com/your-org/omniwrite
cd omniwrite

# Python backend
pip install uv
uv pip install -e ".[dev]"
cp .env.example .env         # add at least OPENAI_API_KEY

# Frontend
cd frontend && npm install

# Pre-commit hooks
pre-commit install
```

Run tests:
```bash
pytest backend/tests/ -v
```

---

## Adding a Platform Plugin

The fastest way to contribute. Drop a file in `backend/plugins/` — it's auto-discovered.

```python
# backend/plugins/medium_plugin.py
"""Medium platform plugin for omniwrite."""
from __future__ import annotations

from backend.models.brand import BrandProfile
from backend.models.state import AgentState
from backend.plugins.base import PlatformPlugin
from backend.core.config import Settings
from backend.core.llm_factory import llm_call


class MediumPlugin(PlatformPlugin):
    name = "medium"
    display_name = "Medium"
    icon = "✉️"
    max_words = 2000
    supports_publish = True

    def get_system_prompt(self, brand: BrandProfile | None) -> str:
        brand_ctx = brand.to_prompt_context() if brand else ""
        return f"""You are an expert writer for Medium.
Write in Medium's thoughtful, narrative, story-driven style.
{brand_ctx}"""

    async def generate(self, state: AgentState, settings: Settings) -> str:
        messages = [
            {"role": "system", "content": self.get_system_prompt(state.brand)},
            {"role": "user", "content": f"Write a Medium article about: {state.brief.topic}"},
        ]
        content, *_ = await llm_call(messages, agent_name="medium_writer", settings=settings)
        return content
```

That's it. The plugin is automatically registered and available in the UI.

---

## Improving Prompts

No Python needed. Edit the YAML files in `backend/core/prompts/`:

```yaml
# backend/core/prompts/platforms/blog.yaml
name: blog_writer
version: "1.1.0"   # bump the version
system: |
  You are an expert content writer...
  # Your improvements here
```

Submit a PR with:
1. The edited YAML file
2. A brief explanation of what you changed and why
3. Before/after example output (optional but appreciated)

---

## Adding a Publisher Integration

```python
# backend/publishers/medium_publisher.py
from backend.publishers.base import PublisherPlugin

class MediumPublisher(PublisherPlugin):
    name = "medium"
    
    async def publish(self, content: str, credentials: dict) -> PublishResult:
        # Use Medium's Integration API
        ...
```

---

## Pull Request Guidelines

1. **One feature per PR** — keep it focused
2. **Tests required** for bug fixes and new features
3. **Update docs** if you're changing behavior
4. **Prompt PRs**: include before/after example outputs
5. Run `ruff check backend/ && mypy backend/` before submitting

## Code Style

- Python: `ruff` for formatting/linting, `mypy` for types
- `from __future__ import annotations` at top of every Python file
- Async/await throughout
- Type hints on all function signatures

## Questions?

Open a [Discussion](https://github.com/your-org/omniwrite/discussions) — we're friendly!
