from responseiq.services.prompt_loader import render_prompt


def test_render_prompt_basic():
    template = "Hello, {{ name }}!"
    result = render_prompt(template, name="World")
    assert result == "Hello, World!"


def test_render_prompt_conditional():
    template = "{% if value %}Value: {{ value }}{% else %}No value{% endif %}"
    assert render_prompt(template, value=42) == "Value: 42"
    assert render_prompt(template, value=None) == "No value"
