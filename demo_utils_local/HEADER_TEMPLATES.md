# Python File Header Templates — Choose Your Style

> Pick ONE style and apply it consistently across all production files.  
> Templates are ordered from minimal to most structured.

---

## Option A — Minimal

**Best for:** utility files, small helpers, internal modules  
**Characters:** ~3 lines  

```python
"""responseiq.utils.k8s_patcher — Comment-preserving Kubernetes YAML patcher."""
```

Or with two lines when you also want to document an important behaviour:

```python
"""responseiq.utils.k8s_patcher — Comment-preserving Kubernetes YAML patcher.

Uses ruamel.yaml to preserve inline comments and quote styles during edits.
"""
```

**Pros:** No noise, always current, works with every docstring renderer  
**Cons:** No extended context for a new contributor

---

## Option B — Standard Module Docstring  ← Recommended for this project

**Best for:** services, plugins, core utilities — anywhere a new engineer lands and needs orientation  
**Lines:** ~12-20  

```python
"""responseiq.services.watchdog_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Post-apply error-rate monitor with automatic rollback trigger.

After a guarded_apply, WatchdogService polls a configurable metrics callback
(or falls back to a /health probe).  If the error rate exceeds the threshold
within the monitoring window, it executes the pre-generated rollback script.

Typical usage::

    svc = WatchdogService()
    result = await svc.monitor_post_apply(
        incident_id="INC-42",
        rollback_script_path=Path("rollbacks/rollback_INC-42.py"),
    )

Feature-gated via ``settings.watchdog_enabled`` (default: False).
"""
```

**Pros:** Self-contained, renders cleanly in Sphinx/MkDocs, easy to scan  
**Cons:** Needs a minute of thought to write well

*Formatting rules for this style:*
- First line: `package.module.name` (no `src/`) then a tilde underline matching its exact length
- Blank line, then one sentence "what it does"
- Blank line, then a short paragraph on how it works / key design decision
- Optional `Typical usage::` block (use `::` not `:`)
- Optional single-line notes (feature gates, external deps, etc.)

---

## Option C — Sphinx / reStructuredText  

**Best for:** public-facing packages, auto-generated API docs  
**Lines:** ~15-25  

```python
"""
:module: responseiq.plugins.go_parser
:synopsis: Go runtime panic and error log parser.
:since: v2.20.0
:author: responseiq-core

Detects and extracts structured context from Go logs:

* Runtime panics (goroutine dumps)
* ``panic: <message>`` lines
* Standard Go stack frames (``pkg/file.go:line``)
* Signal-based crashes (SIGSEGV, SIGABRT)
* ``log.Fatal`` / ``log.Panic`` / ``zap`` / ``logrus`` output

.. note::
   This parser is loaded via ``PluginRegistry`` dynamic discovery.
   It is not auto-dispatched from ``--mode scan``; call ``GoParser.run()``
   directly for log enrichment.
"""
```

**Pros:** Auto-renders in Sphinx HTML docs, structured metadata  
**Cons:** Verbose, `:since:` / `:author:` drift unless you enforce via CI

---

## Option D — Google Style

**Best for:** teams already using Google-style docstrings throughout  
**Lines:** ~18-28  

```python
"""Comment-preserving Kubernetes Deployment YAML patcher.

Uses ruamel.yaml to read, modify, and write Kubernetes manifests while
preserving inline comments, quote styles, and indentation — so the
diff stays readable in code review.

Example::

    patcher = KubernetesPatcher()
    patcher.update_memory_limit(
        Path("k8s/deployment.yaml"),
        container_name="api",
        new_limit="1Gi",
    )

Note:
    Only ``update_memory_limit`` is currently implemented.
    Image, replica, and environment variable patching are not yet supported.

Attributes:
    yaml: The configured ``ruamel.yaml.YAML`` instance (quote-preserving).
"""
```

**Pros:** Consistent with Google-style function/class docstrings, clean in IDEs  
**Cons:** `Attributes:` section gets stale if class fields change

---

## Comparison Table

| Style | Length | Auto-docs | IDE hover | Effort | Best fit |
|-------|--------|-----------|-----------|--------|----------|
| A — Minimal | 1-3 lines | ✅ | ✅ | Low | helpers, __init__.py |
| B — Standard (recommended) | 12-20 lines | ✅ | ✅ | Medium | services, plugins, utils |
| C — Sphinx rST | 15-25 lines | ✅✅ | ✅ | High | public API surface |
| D — Google | 18-28 lines | ✅ | ✅✅ | Medium | Google-style codebases |

---

## Decision: What to use in ResponseIQ

**Recommended: Mix of A + B**

| File type | Style |
|-----------|-------|
| `__init__.py`, `__version__.py`, `db.py`, `cli.py` | A — one line is enough |
| All `services/`, `plugins/`, `utils/` files | B — standard module docstring |
| Any file with no header today | B (add immediately when touching the file) |

**Non-negotiables regardless of style chosen:**
1. First line is always the module path + short description (no leading blank line before the `"""`-open)
2. No `TODO`, `FIXME`, `HACK` in headers — move those to inline comments or GitHub Issues
3. No author or date in headers — git blame owns that
4. Keep class/function docstrings separate from the module header

---

## Quick fill-in template (Option B)

Copy-paste, fill the `[brackets]`:

```python
"""responseiq.[package].[module]
[tilde underline matching length of first line exactly]
[One sentence: what this module does.]

[One paragraph (2-4 sentences): HOW it works, key design choice, or what to
watch out for. Mention external dependencies here if any.]

[Optional: Typical usage:: block]

[Optional: single-line notes — feature flags, deprecations, related modules]
"""
```
