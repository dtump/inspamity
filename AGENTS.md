# Inspamity — Agent Guidelines

AI-powered spam detection tool that integrates with rspamd using AI providers (Anthropic Claude, OpenAI).

## Project Structure

```
├── email_ai_interface.py          # Main entry point (stdin/file → AI → JSON)
├── cli_toolbox.py                 # CLI tool for testing emails
├── email_utils/
│   ├── config.py                  # Shared config loader (system/local)
│   ├── prompts.py                 # Shared SYSTEM_PROMPT constant
│   ├── ai_spam_check.py           # Provider dispatcher (check_spam_with_ai)
│   ├── anthropic_spam_check.py    # Anthropic provider implementation
│   └── openai_spam_check.py       # OpenAI provider implementation
│   └── process_email.py           # Email parsing and formatting
├── rspamd/
│   └── external_ai_test.lua       # rspamd Lua plugin
├── tests/                         # pytest test suite
├── config.ini.default             # Configuration template
└── pyproject.toml                 # Project metadata and dependencies
```

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Code Standards

- **Python ≥ 3.10** — use modern syntax (`str | None`, `dict[str, Any]`)
- **Formatting/linting**: ruff — run `ruff check .` and `ruff format .` before committing
- **Type hints** on all public function signatures
- **Line length**: 100 characters max
- **Quotes**: double quotes (enforced by ruff)
- **Imports**: sorted by ruff (`I` rule), stdlib → third-party → local

## Before Submitting a PR

- Run `ruff check . && ruff format --check . && pytest` — all must pass
- Check if `README.md` needs updates to reflect your changes (new features, changed config, updated commands)

## Testing

- **Framework**: pytest 9.0.3
- **Run tests**: `pytest -v`
- **All changes must pass**: `ruff check . && ruff format --check . && pytest`
- Tests live in `tests/` and mirror the module structure
- Mock external APIs — never make real API calls in tests. Use `unittest.mock.patch` for API clients and `monkeypatch` for config paths
- Use `tmp_path` for temporary files, `monkeypatch` for config isolation

## Architecture Notes

- **Provider dispatch**: `ai_spam_check.py` reads the `provider` setting from config and dispatches to the appropriate provider module. Provider imports are lazy (inside if/elif branches) so only the selected SDK is loaded.
- **Adding a new provider**: Create `email_utils/<provider>_spam_check.py` with a `check_spam_with_<provider>(email_content: str) -> dict[str, Any]` function, add an elif branch in `ai_spam_check.py`, and add the config section.
- **System prompt** is shared across providers via `email_utils/prompts.py`. Do not duplicate it in provider modules.
- **Config loading** is centralized in `email_utils/config.py`. Don't duplicate config logic elsewhere. Config is read from `/etc/inspamity/config.ini` (system) or `config.ini` in the project root (local), in that priority order.
- **Entry points** (`email_ai_interface.py`, `cli_toolbox.py`) live at the project root because the rspamd Lua plugin references them by absolute path (`/usr/local/inspamity/`). Do not move them into a package.
- **Production deployment** uses a venv at `/usr/local/inspamity/.venv/` — the Lua script calls that venv's Python directly.
- The **temperature** parameter is only passed to the API when explicitly set in config. Do not hardcode it.
- All provider functions must always return a dict with `is_spam`, `confidence`, and `reason` keys, even on error.
