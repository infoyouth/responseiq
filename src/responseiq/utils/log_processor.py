import asyncio
import mmap
import os
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List, Tuple

# Context extractor patterns (shared)
from responseiq.utils.context_extractor import PATTERNS
from responseiq.utils.logger import logger

CHUNK_SIZE = 1024 * 1024 * 5  # 5MB chunks for parallel processing


def _scan_chunk_for_errors(args: Tuple[str, int, int]) -> List[str]:
    """
    CPU-Bound worker function (must be picklable for ProcessPool).
    Scans a specific byte range of a file for error patterns.
    """
    file_path, start_byte, end_byte = args
    matches = []

    # We extend the read slightly to catch patterns crossing chunk boundaries
    read_end = end_byte + 256

    try:
        with open(file_path, "r+b") as f:
            # Memory map the file (Zero-copy access)
            # PRO-TIP: mmap is faster than read() for random access or large files
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # Slice the mmap (this is virtually free, no data copy)
                # Ensure we fit within file bounds
                actual_end = min(read_end, mm.size())
                chunk_data = mm[start_byte:actual_end]

                # Decode strictly this chunk
                try:
                    text_chunk = chunk_data.decode("utf-8", errors="ignore")
                except Exception:
                    return []

                # Run Regex on just this slice
                # We are looking for "Error", "Panic", or specific stack trace patterns
                # Combine patterns for a single pass
                # Clean patterns of any existing flags to avoid warnings
                clean_patterns = [p for p in PATTERNS]
                keywords = [r"error", r"panic", r"fatal"]
                combined_pattern = "|".join(clean_patterns + keywords)

                # specific compilation with ignorecase
                regex = re.compile(combined_pattern, re.IGNORECASE)

                for match in regex.finditer(text_chunk):
                    # We found a hit. Let's capture the line context around it via simple
                    # newline search
                    # Map match.start() back to file offset if needed, but here we just
                    # return the snippet
                    span_start = max(0, match.start() - 100)
                    span_end = min(len(text_chunk), match.end() + 200)
                    matches.append(text_chunk[span_start:span_end].strip())

    except Exception:  # noqa: S110
        # Silently fail in worker to avoid crashing main loop
        pass

    return matches


class ParallelLogProcessor:
    def __init__(self):
        # determine core count
        self.workers = min(os.cpu_count() or 4, 8)

    async def scan_large_file(self, file_path: Path) -> str:
        """
        Orchestrates the parallel scanning of a large file.
        Returns a summarized string of 'interesting' parts (Errors + Stack Traces).
        """
        file_size = file_path.stat().st_size

        # Strategy: If small, read directly. If large, map-reduce.
        if file_size < 1024 * 1024:  # 1MB
            # Fast path
            async with asyncio.Lock():  # Just to be safe if reused
                return file_path.read_text(errors="ignore")[:50000]  # Safe cap

        logger.info(
            f"Processing large log {file_path.name} ({file_size / 1024 / 1024:.2f}MB) with {self.workers} cores."
        )

        # 1. Create chunks
        chunks = []
        for i in range(0, file_size, CHUNK_SIZE):
            chunks.append((str(file_path), i, min(i + CHUNK_SIZE, file_size)))

        # 2. Scatter (Run in parallel processes)
        loop = asyncio.get_running_loop()
        extracted_snippets = []

        with ProcessPoolExecutor(max_workers=self.workers) as pool:
            # asyncio.gather doesn't work directly with ProcessPool map, so we wrap it
            # We use run_in_executor for each chunk submission
            futures = [loop.run_in_executor(pool, _scan_chunk_for_errors, chunk) for chunk in chunks]

            # 3. Gather
            results = await asyncio.gather(*futures)

            for res in results:
                extracted_snippets.extend(res)

        # 4. Reduce (Deduplicate and Summary)
        # Limit to top 10 findings to not overwhelm the LLM
        unique_snippets = list(set(extracted_snippets))[:15]

        logger.info(f"Parallel scan found {len(unique_snippets)} distinct issues via regex.")
        return "\n...\n".join(unique_snippets)
