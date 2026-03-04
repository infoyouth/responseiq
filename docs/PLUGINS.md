# ResponseIQ Plugin SDK

> **P5.2** — Ship custom log parsers without touching core ResponseIQ code.

---

## Overview

ResponseIQ's Plugin SDK lets you add support for any log format by writing a
single Python class.  Plugins are auto-discovered at startup — no registration
step, no monkey-patching.

---

## Built-in Parsers

Five parser plugins are shipped with ResponseIQ:

| Plugin | `log_format` | Detects |
|---|---|---|
| `DjangoParser` | Django | `django.request`, `ObjectDoesNotExist`, `django.core.exceptions` |
| `FastAPIParser` | FastAPI/Uvicorn | `uvicorn`, `fastapi`, `HTTPException`, `ValidationError` |
| `SpringParser` | Spring Boot | `org.springframework`, `BeanCreationException`, `Caused by:` chains |
| `NodejsParser` | Node.js/Express | `TypeError:`, `at …(.js:`, `UnhandledPromiseRejectionWarning` |
| `GoParser` | Go | `goroutine`, `panic:`, `runtime error:`, `SIGSEGV` |

---

## Writing a Custom Plugin

### 1. Create the file

Place your plugin in `src/responseiq/plugins/my_parser.py`:

```python
from responseiq.plugins.base import BasePlugin, PluginMetadata

class MyParser(BasePlugin):
    metadata = PluginMetadata(
        name="my_parser",
        version="1.0.0",
        author="you@example.com",
        log_format="my-framework",
        description="Parses MyFramework error logs.",
    )

    @classmethod
    def can_handle(cls, log_text: str) -> bool:
        return "MyFramework" in log_text

    def run(self, agent_state: dict) -> dict:
        messages = agent_state.get("messages", [])
        combined = "\n".join(messages)
        # … parse combined …
        return {
            "parsed_context": {
                "framework": "my-framework",
                "error": "...",      # extracted error type
                "stack_frames": [],  # list of {"file": ..., "line": ...}
            }
        }
```

### 2. That's it

`PluginRegistry` uses `pkgutil.iter_modules` to scan `src/responseiq/plugins/`
at import time.  Your parser is immediately available:

```python
from responseiq.plugin_registry import PluginRegistry

reg = PluginRegistry()
reg.list_plugins()        # ['django_parser', 'fastapi_parser', ..., 'my_parser']
cls = reg.get_plugin("my_parser")
instance = cls()
result = instance.run({"messages": ["MyFramework ERROR: something blew up"]})
```

---

## `BasePlugin` Contract

```
BasePlugin
├── metadata: PluginMetadata       ← required class attribute
│   ├── name: str                  ← unique snake_case identifier
│   ├── version: str               ← semver string
│   ├── author: str                ← email or GitHub handle
│   ├── log_format: str            ← human-readable framework name
│   └── description: str           ← one-line summary
│
├── can_handle(log_text: str) -> bool   ← class method, fast heuristic check
│
└── run(agent_state: dict) -> dict      ← returns a *delta* dict
    └── {"parsed_context": {...}}       ← merged into agent state by caller
```

### `run()` — delta pattern

`run()` returns only the keys it sets.  The caller merges the delta into the
existing `agent_state`.  A typical `parsed_context` structure:

```python
{
    "framework": "django",          # lowercase framework identifier
    "exception_type": "...",        # primary exception class name
    "traceback_frames": [           # ordered list, closest frame first
        {"file": "...", "line": "...", "function": "..."},
    ],
    "http_error": {                 # when applicable
        "method": "GET",
        "path": "/api/users/5/",
        "status_code": 500,
    },
}
```

---

## `can_handle()` — detection heuristics

`can_handle()` is called before `run()` to select the right parser.  Keep it
**fast** — a simple `any(sig in log_text for sig in SIGNATURES)` is ideal.
Avoid regex or I/O inside `can_handle()`.

---

## Testing your plugin

```python
def test_my_parser_detects_logs():
    assert MyParser.can_handle("MyFramework ERROR: boom")

def test_my_parser_extracts_error():
    result = MyParser().run({"messages": ["MyFramework ERROR: boom"]})
    assert result["parsed_context"]["framework"] == "my-framework"
```

Run with:

```bash
uv run pytest tests/unit/test_my_parser.py -v
```

---

## PluginRegistry API

```python
from responseiq.plugin_registry import PluginRegistry

reg = PluginRegistry()
reg.list_plugins()            # list[str]  — plugin name strings
reg.get_plugin("go_parser")   # Type[BasePlugin]
```
