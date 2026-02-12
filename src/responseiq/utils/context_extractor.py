import re
from pathlib import Path
from typing import Optional

import aiofiles

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
    Reads file effectively using async I/O and extracts a window around the line.
    """
    start = max(1, line_num - context_lines)
    end = line_num + context_lines

    lines = []
    try:
        async with aiofiles.open(file_path, mode="r", encoding="utf-8", errors="ignore") as f:
            # We have to read lines to find the range.
            # Optimization: If file is huge, this is slow. But source files are usually
            # small (<1MB).
            # For massive files, we'd want seek(), but text lines are variable length.
            # Since source code files are small, reading all content into memory is
            # reliable and fast enough.
            content = await f.readlines()

            if len(content) < 1:
                return None

            # Python lists are 0-indexed, lines are 1-indexed
            display_start = max(0, start - 1)
            display_end = min(len(content), end)

            for i in range(display_start, display_end):
                marker = ">> " if (i + 1) == line_num else "   "
                lines.append(f"{i + 1:4d} | {marker}{content[i].rstrip()}")

        return "\n".join(lines)
    except Exception:
        return None
