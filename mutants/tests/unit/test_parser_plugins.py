"""tests/unit/test_parser_plugins.py

Unit tests for the P5.2 built-in parser plugins.

Covers:
  - DjangoParser   — can_handle detection + structured extraction
  - FastAPIParser  — can_handle detection + structured extraction
  - SpringParser   — can_handle detection + structured extraction
  - NodejsParser   — can_handle detection + structured extraction
  - GoParser       — can_handle detection + structured extraction
  - PluginRegistry auto-discovery finds all 5 parsers
  - BasePlugin metadata contract
"""

from __future__ import annotations

import pytest

from responseiq.plugin_registry import PluginRegistry
from responseiq.plugins.base import BasePlugin, PluginMetadata
from responseiq.plugins.django_parser import DjangoParser
from responseiq.plugins.fastapi_parser import FastAPIParser
from responseiq.plugins.go_parser import GoParser
from responseiq.plugins.nodejs_parser import NodejsParser
from responseiq.plugins.spring_parser import SpringParser

# ── sample log fixtures ───────────────────────────────────────────────────────

_DJANGO_LOG = """\
2024-01-01 12:00:00,000 ERROR django.request Internal Server Error: /api/users/5/
Traceback (most recent call last):
  File "/app/venv/lib/python3.12/site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "/app/myapp/views.py", line 23, in user_detail
    user = User.objects.get(pk=user_id)
django.core.exceptions.ObjectDoesNotExist: User matching query does not exist.
"GET /api/users/5/ HTTP/1.1" 500 42
"""

_FASTAPI_LOG = """\
INFO:     127.0.0.1:52420 - "GET /users/99 HTTP/1.1" 404
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/app/routers/users.py", line 18, in get_user
    raise HTTPException(status_code=404, detail="User not found")
fastapi.exceptions.HTTPException: status_code=404, detail='User not found'
"""

_SPRING_LOG = """\
2024-01-01 10:00:00.123  ERROR 12345 --- [main] o.s.boot.SpringApplication               : Application run failed

org.springframework.beans.factory.BeanCreationException: Error creating bean 'dataSource'
\tat org.springframework.beans.factory.support.AbstractBeanFactory.getBean(AbstractBeanFactory.java:201)
\tat com.example.app.config.DatabaseConfig.dataSource(DatabaseConfig.java:45)
Caused by: java.sql.SQLException: Connection refused
\tat org.postgresql.Driver.connect(Driver.java:92)
"""

_NODE_LOG = """\
TypeError: Cannot read property 'id' of undefined
    at getUserById (src/services/userService.js:34:18)
    at Router.handle (node_modules/express/lib/router/index.js:284:10)
    at Layer.handle [as handle_request] (node_modules/express/lib/router/layer.js:95:5)
node_modules/.bin/node: error
UnhandledPromiseRejectionWarning: TypeError: Cannot read property 'id' of undefined
"""

_GO_LOG = """\
goroutine 1 [running]:
panic: runtime error: index out of range [1] with length 1

goroutine 1 [running]:
main.processRequest(0xc000142000)
\t/app/cmd/server/main.go:87 +0x1bc
net/http.(*ServeMux).ServeHTTP(0x1234560, {0x7f1234, 0xc00012}, 0xc000142000)
\t/usr/local/go/src/net/http/server.go:2316 +0x65
created by main.startServer
"""

_UNRELATED_LOG = "INFO: Application started successfully. All systems nominal."


# ── metadata contract ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "plugin_cls",
    [DjangoParser, FastAPIParser, SpringParser, NodejsParser, GoParser],
)
def test_plugin_has_metadata(plugin_cls: type) -> None:
    assert hasattr(plugin_cls, "metadata"), f"{plugin_cls.__name__} missing metadata"
    assert isinstance(plugin_cls.metadata, PluginMetadata)
    assert plugin_cls.metadata.name
    assert plugin_cls.metadata.version
    assert plugin_cls.metadata.log_format


@pytest.mark.parametrize(
    "plugin_cls",
    [DjangoParser, FastAPIParser, SpringParser, NodejsParser, GoParser],
)
def test_plugin_is_base_plugin_subclass(plugin_cls: type) -> None:
    assert issubclass(plugin_cls, BasePlugin)


# ── DjangoParser ──────────────────────────────────────────────────────────────


def test_django_can_handle_django_log() -> None:
    assert DjangoParser.can_handle(_DJANGO_LOG) is True


def test_django_cannot_handle_unrelated_log() -> None:
    assert DjangoParser.can_handle(_UNRELATED_LOG) is False


def test_django_extracts_framework_key() -> None:
    result = DjangoParser().run({"messages": [_DJANGO_LOG]})
    assert result["parsed_context"]["framework"] == "django"


def test_django_extracts_exception_type() -> None:
    result = DjangoParser().run({"messages": [_DJANGO_LOG]})
    assert result["parsed_context"]["exception_type"] is not None
    assert "ObjectDoesNotExist" in result["parsed_context"]["exception_type"]


def test_django_extracts_traceback_frames() -> None:
    result = DjangoParser().run({"messages": [_DJANGO_LOG]})
    frames = result["parsed_context"]["traceback_frames"]
    assert len(frames) > 0
    assert all("file" in f and "line" in f for f in frames)


def test_django_extracts_http_error() -> None:
    result = DjangoParser().run({"messages": [_DJANGO_LOG]})
    http_err = result["parsed_context"].get("http_error")
    assert http_err is not None
    assert http_err["status_code"] == 500


def test_django_run_empty_messages_is_safe() -> None:
    result = DjangoParser().run({"messages": []})
    assert "parsed_context" in result
    assert result["parsed_context"]["framework"] == "django"


# ── FastAPIParser ─────────────────────────────────────────────────────────────


def test_fastapi_can_handle_fastapi_log() -> None:
    assert FastAPIParser.can_handle(_FASTAPI_LOG) is True


def test_fastapi_cannot_handle_unrelated_log() -> None:
    assert FastAPIParser.can_handle(_UNRELATED_LOG) is False


def test_fastapi_extracts_framework_key() -> None:
    result = FastAPIParser().run({"messages": [_FASTAPI_LOG]})
    assert result["parsed_context"]["framework"] == "fastapi"


def test_fastapi_extracts_access_errors() -> None:
    result = FastAPIParser().run({"messages": [_FASTAPI_LOG]})
    access_errors = result["parsed_context"]["access_errors"]
    assert len(access_errors) >= 1
    assert access_errors[0]["status_code"] == 404


def test_fastapi_run_returns_dict_with_parsed_context() -> None:
    result = FastAPIParser().run({"messages": [_FASTAPI_LOG]})
    assert "parsed_context" in result


# ── SpringParser ──────────────────────────────────────────────────────────────


def test_spring_can_handle_spring_log() -> None:
    assert SpringParser.can_handle(_SPRING_LOG) is True


def test_spring_cannot_handle_unrelated_log() -> None:
    assert SpringParser.can_handle(_UNRELATED_LOG) is False


def test_spring_extracts_framework_key() -> None:
    result = SpringParser().run({"messages": [_SPRING_LOG]})
    assert result["parsed_context"]["framework"] == "spring_boot"


def test_spring_extracts_exception_chain() -> None:
    result = SpringParser().run({"messages": [_SPRING_LOG]})
    chain = result["parsed_context"]["exception_chain"]
    assert len(chain) >= 1
    assert any("BeanCreationException" in e for e in chain)


def test_spring_extracts_caused_by() -> None:
    result = SpringParser().run({"messages": [_SPRING_LOG]})
    chain = result["parsed_context"]["exception_chain"]
    assert any("SQLException" in e for e in chain)


def test_spring_extracts_error_log_lines() -> None:
    result = SpringParser().run({"messages": [_SPRING_LOG]})
    errors = result["parsed_context"]["error_log_lines"]
    assert len(errors) >= 1
    assert any("Application run failed" in e["message"] for e in errors)


# ── NodejsParser ──────────────────────────────────────────────────────────────


def test_nodejs_can_handle_node_log() -> None:
    assert NodejsParser.can_handle(_NODE_LOG) is True


def test_nodejs_cannot_handle_unrelated_log() -> None:
    assert NodejsParser.can_handle(_UNRELATED_LOG) is False


def test_nodejs_extracts_framework_key() -> None:
    result = NodejsParser().run({"messages": [_NODE_LOG]})
    assert result["parsed_context"]["framework"] == "nodejs"


def test_nodejs_extracts_error_types() -> None:
    result = NodejsParser().run({"messages": [_NODE_LOG]})
    error_types = result["parsed_context"]["error_types"]
    assert len(error_types) >= 1
    assert any("TypeError" in e["type"] for e in error_types)


def test_nodejs_extracts_stack_frames() -> None:
    result = NodejsParser().run({"messages": [_NODE_LOG]})
    frames = result["parsed_context"]["stack_frames"]
    assert len(frames) > 0
    assert all("file" in f and "line" in f for f in frames)


def test_nodejs_extracts_unhandled_promise() -> None:
    result = NodejsParser().run({"messages": [_NODE_LOG]})
    # The unhandled promise field should be populated
    assert result["parsed_context"]["unhandled_promise"] is not None


# ── GoParser ──────────────────────────────────────────────────────────────────


def test_go_can_handle_go_log() -> None:
    assert GoParser.can_handle(_GO_LOG) is True


def test_go_cannot_handle_unrelated_log() -> None:
    assert GoParser.can_handle(_UNRELATED_LOG) is False


def test_go_extracts_framework_key() -> None:
    result = GoParser().run({"messages": [_GO_LOG]})
    assert result["parsed_context"]["framework"] == "go"


def test_go_extracts_panic_message() -> None:
    result = GoParser().run({"messages": [_GO_LOG]})
    panic = result["parsed_context"]["panic_message"]
    assert panic is not None
    assert "index out of range" in panic


def test_go_extracts_goroutines() -> None:
    result = GoParser().run({"messages": [_GO_LOG]})
    goroutines = result["parsed_context"]["goroutines"]
    assert len(goroutines) >= 1
    assert goroutines[0]["state"] == "running"


def test_go_crash_type_is_panic() -> None:
    result = GoParser().run({"messages": [_GO_LOG]})
    assert result["parsed_context"]["crash_type"] == "panic"


# ── PluginRegistry auto-discovery ────────────────────────────────────────────


def test_registry_discovers_all_five_parsers() -> None:
    reg = PluginRegistry()
    names = reg.list_plugins()
    expected = {"django_parser", "fastapi_parser", "spring_parser", "nodejs_parser", "go_parser"}
    assert expected.issubset(set(names)), f"Missing parsers: {expected - set(names)}"


def test_registry_can_retrieve_django_parser() -> None:
    reg = PluginRegistry()
    cls = reg.get_plugin("django_parser")
    assert issubclass(cls, BasePlugin)
    assert cls.can_handle(_DJANGO_LOG)
