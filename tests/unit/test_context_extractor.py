import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from responseiq.utils.context_extractor import extract_context_from_log


@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.mark.asyncio
async def test_extract_context_semantic_scope(temp_workspace):
    """
    Test that extraction returns the full semantic scope (e.g., function definition)
    when using tree-sitter, rather than just a window of lines.
    """
    # Create a dummy python file with a function and a class
    file_content = """
class MyHelper:
    def __init__(self):
        self.value = 10

def complex_operation(x):
    y = x + 1
    # This is the target line
    if y > 10:
        return y * 2
    return y
"""
    file_path = temp_workspace / "semantic_test.py"
    file_path.write_text(file_content.strip())

    line_num = 7
    log_text = f'File "{file_path.name}", line {line_num}, in complex_operation'

    # Mock tree-sitter because the environment might have broken bindings
    with patch("responseiq.utils.context_extractor.tree_sitter_languages") as mock_ts:
        # Setup mocks
        mock_lang = MagicMock()
        mock_lang.name = "python"
        mock_ts.get_language.return_value = mock_lang

        mock_parser = MagicMock()
        mock_ts.get_parser.return_value = mock_parser

        mock_tree = MagicMock()
        mock_parser.parse.return_value = mock_tree

        mock_root = MagicMock()
        mock_tree.root_node = mock_root

        # Define the nodes
        # Target node at line 7 (index 6)
        mock_target_node = MagicMock()
        mock_target_node.type = "expression_statement"
        mock_target_node.start_point = (6, 4)
        mock_target_node.end_point = (6, 25)

        # Function node wrapping lines 5-9 (indices 4-8)
        mock_func_node = MagicMock()
        mock_func_node.type = "function_definition"
        mock_func_node.start_point = (4, 0)  # Line 5 (0-indexed 4)
        mock_func_node.end_point = (8, 12)  # Line 9 (0-indexed 8)

        # Link hierarchy
        mock_target_node.parent = mock_func_node
        mock_func_node.parent = MagicMock(type="module")  # Stop traversal

        # Configure lookup
        mock_root.descendant_for_point_range.return_value = mock_target_node

        context = await extract_context_from_log(log_text, root_path=temp_workspace)

        # Validation
        assert context is not None
        # It should include the function definition line
        assert "def complex_operation(x):" in context
        # It should include the return statement
        assert "return y" in context

        # It should NOT include the class definition (semantic scope)
        assert "class MyHelper:" not in context
        # It should NOT include lines outside scope
        assert "def __init__(self):" not in context


@pytest.mark.asyncio
async def test_fallback_behavior_non_supported_files(temp_workspace):
    """
    Verify fallback behavior for non-supported files (e.g., .txt).
    It should likely return a simple window of lines.
    """
    # Create a file with enough lines to test "window"
    lines = [f"line {i}" for i in range(1, 21)]
    file_content = "\n".join(lines)
    file_path = temp_workspace / "dummy.txt"
    file_path.write_text(file_content)

    line_num = 10
    log_text = f'File "{file_path.name}", line {line_num}'

    context = await extract_context_from_log(log_text, root_path=temp_workspace)

    assert context is not None
    # Should check if we got lines around line 10
    # context extractor uses ">> " marker for the current line
    assert ">> line 10" in context
    # Should check bounds (default context_lines=5)
    # line 5 to line 15 roughly
    assert "line 5" in context
    assert "line 15" in context


@pytest.mark.asyncio
async def test_missing_file_handling(temp_workspace):
    """
    Verify it handles missing files gracefully.
    """
    file_path = "non_existent.py"
    line_num = 5
    log_text = f'File "{file_path}", line {line_num}'

    # Should return empty string as per logic:
    # if not local_file or not local_file.exists(): continue
    # if not context_blocks: return ""

    context = await extract_context_from_log(log_text, root_path=temp_workspace)
    assert context == ""


@pytest.mark.asyncio
async def test_invalid_log_format(temp_workspace):
    """
    Verify it handles logs that don't match any pattern.
    """
    log_text = "Something went wrong but no file info here."
    context = await extract_context_from_log(log_text, root_path=temp_workspace)
    assert context == ""
