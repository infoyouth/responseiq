import re
from pathlib import Path
from typing import Optional

import aiofiles
import tree_sitter_languages  # type: ignore

from responseiq.utils.logger import logger

# Regex patterns for common stack traces (Python, Node, Go, Java mostly)
# Captures: 1=File Path, 2=Line Number
PATTERNS = [
    # Python: File "src/main.py", line 10 in <module>
    r'File\s+"([^"]+)",\s+line\s+(\d+)',
    # Node/JS: at Object.<anonymous> (/app/src/index.js:15:12)
    r"\((/[^:]+|[\w\-\./\\]+\.\w+):(\d+):\d+\)",
    # Go: /path/to/file.go:12 +0x4
    r"\s+([\w\-\./\\]+\.go):(\d+)",
    # Java: at com.example.Main.main(Main.java:14) -> tough to map to file without package scan
    # skipping for now
]


def _get_tree_sitter_language(file_path: Path):
    """Detects parser language from file extension."""
    suffix = file_path.suffix.lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".rs": "rust",
    }
    lang_name = mapping.get(suffix)
    if not lang_name:
        return None
    try:
        return tree_sitter_languages.get_language(lang_name)
    except Exception:
        return None  # Fallback to lines if parser not found


def _find_semantic_scope(node, target_line):
    """
    Traverses up the syntax tree to find the smallest 'scope' (Function/Class)
    that contains the target line.
    """
    current = node
    # Walk up the tree
    while current:
        # Check if this node covers the line
        if current.start_point[0] <= target_line and current.end_point[0] >= target_line:
            # Check for interesting node types
            if current.type in [
                "function_definition",
                "class_definition",
                "method_definition",
                "arrow_function",
                "function_declaration",
            ]:
                return current
        current = current.parent
    return None  # If no function scope found (e.g. top level), return None


async def extract_context_from_log(log_text: str, root_path: Path = Path(".")) -> str:
    """
    Scans log text for file references, reads the local source code around those lines,
    and returns a formatted context block for the AI.
    """
    context_blocks = []
    seen_refs = set()

    for pattern in PATTERNS:
        matches = re.finditer(pattern, log_text)
        for match in matches:
            file_path_str = match.group(1)
            line_num = int(match.group(2))

            # Normalize path
            # Some logs have absolute paths "/app/src/..." that map to local "src/..."
            try:
                # Naive stripping of common prefixes if file not found
                local_file = resolve_local_path(file_path_str, root_path)

                if not local_file or not local_file.exists():
                    continue

                ref_key = f"{local_file}:{line_num}"
                if ref_key in seen_refs:
                    continue
                seen_refs.add(ref_key)

                # Read distinct block (Async I/O for speed)
                code_snippet = await read_code_around_line(local_file, line_num)
                if code_snippet:
                    context_blocks.append(f"--- Source: {local_file} (Line {line_num}) ---\n" f"{code_snippet}\n")
            except Exception as e:
                logger.debug(f"Failed to extract context for {file_path_str}: {e}")

    if not context_blocks:
        return ""

    return "\nDETECTED SOURCE CODE CONTEXT:\n" + "\n".join(context_blocks) + "\n"


def resolve_local_path(path_str: str, root: Path) -> Optional[Path]:
    """
    Attempts to map a log path to a real local file.
    Handles relative paths and stripping docker/cloud absolute prefixes.
    """
    # 1. Try direct
    p = Path(path_str)
    if (root / p).exists():
        return root / p

    # 2. Try stripping leading slash or common prefixes like /app/ or /workspace/
    parts = p.parts
    # Iterate parts to find a suffix match in root
    # e.g. /app/src/main.py -> src/main.py
    for i in range(len(parts)):
        sub_path = Path(*parts[i:])
        candidate = root / sub_path
        if candidate.exists() and candidate.is_file():
            return candidate

    return None


async def read_code_around_line(file_path: Path, line_num: int, context_lines: int = 5) -> Optional[str]:
    """
    Reads file using Tree-sitter for semantic scope extraction.
    Fallbacks to simple line-window if parsing fails.
    """
    # Read full content
    try:
        async with aiofiles.open(file_path, mode="r", encoding="utf-8", errors="ignore") as f:
            content = await f.read()
    except Exception:
        return None

    if not content:
        return None

    # Tree-sitter Logic
    try:
        language = _get_tree_sitter_language(file_path)
        if language:
            parser = tree_sitter_languages.get_parser(language.name)
            tree = parser.parse(bytes(content, "utf8"))
            root_node = tree.root_node

            # Find node at specific line/column (approximate column 0)
            target_node = root_node.descendant_for_point_range((line_num - 1, 0), (line_num - 1, 100))

            # Find semantic scope (Function or Class)
            scope_node = _find_semantic_scope(target_node, line_num - 1)

            if scope_node:
                # Extract the full scope content
                start_line = scope_node.start_point[0]
                end_line = scope_node.end_point[0]

                # Add a few lines buffer for context inside function if it's huge?
                # For now, return the WHOLE function to ensure "Surgical Fix" has full context.
                lines = content.splitlines()

                # Ensure we don't go out of bounds
                start_line = max(0, start_line)
                end_line = min(len(lines) - 1, end_line)

                formatted_lines = []
                for i in range(start_line, end_line + 1):
                    marker = ">> " if (i + 1) == line_num else "   "
                    formatted_lines.append(f"{i + 1:4d} | {marker}{lines[i]}")

                return "\n".join(formatted_lines)

    except Exception as e:
        logger.debug(f"Tree-sitter parsing failed for {file_path}: {e}")
        # Fallback to default logic
        pass

    # Fallback Logic (Simple Window)
    start = max(1, line_num - context_lines)
    end = line_num + context_lines

    file_lines = content.splitlines()
    lines_out = []

    display_start = max(0, start - 1)
    display_end = min(len(file_lines), end)

    for i in range(display_start, display_end):
        marker = ">> " if (i + 1) == line_num else "   "
        lines_out.append(f"{i + 1:4d} | {marker}{file_lines[i]}")

    return "\n".join(lines_out)
