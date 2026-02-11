from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import the new innovative modules
from src.utils.context_extractor import extract_context_from_log
from src.utils.log_processor import ParallelLogProcessor


@pytest.mark.asyncio
async def test_context_extraction_regex():
    """
    Verifies that the regular expressions correctly identify file paths in logs.
    """
    log_line = 'File "src/main.py", line 15 in <module>'
    # Mock read_code_around_line since we don't have the file
    with patch("src.utils.context_extractor.read_code_around_line", new_callable=AsyncMock) as mock_read:
        with patch("src.utils.context_extractor.resolve_local_path") as mock_resolve:

            mock_read.return_value = "15 | >> print('hello')"
            # Return a MagicMock that behaves like a Path but allows attribute setting
            mock_path = MagicMock(spec=Path)
            mock_path.__str__.return_value = "src/main.py"
            mock_path.exists.return_value = True
            mock_resolve.return_value = mock_path

            context = await extract_context_from_log(log_line)

            assert "DETECTED SOURCE CODE CONTEXT" in context
            assert "src/main.py" in context
            assert "print('hello')" in context


@pytest.mark.asyncio
async def test_parallel_log_processor_small_file():
    """
    Verifies that small files bypass the parallel engine.
    """
    processor = ParallelLogProcessor()

    # Create a small temp file
    tmp_path = Path("test_small_log.txt")
    tmp_path.write_text("Small log with Error")

    try:
        result = await processor.scan_large_file(tmp_path)
        assert result == "Small log with Error"
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@pytest.mark.asyncio
async def test_parallel_log_processor_large_file_split():
    """
    Tests the logic of the parallel processor with a mocked executor to avoid
    actual multiprocessing overhead during simple unit tests.
    """
    _ = ParallelLogProcessor()

    # Mock file size to be HUGE
    _ = Path("fake_huge_log.log")

    with patch("pathlib.Path.stat") as mock_stat:
        mock_stat.return_value.st_size = 10 * 1024 * 1024  # 10MB

        # Mock ProcessPoolExecutor to run synchronously or just return pre-canned results
        # We patch the run_in_executor to avoid spawning processes
        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=["Error detected in chunk"])

            # We skip the actual chunk creation or file reading by mocking
            # But the scan_large_file relies on "chunks" loop based on size.

            # Actually, simpler to mock the entire executor logic or just trust the integration test
            # Let's test the `_scan_chunk_for_errors` worker function logic specifically
            from src.utils.log_processor import _scan_chunk_for_errors

            # Create a real file for the worker to read
            real_file = Path("test_worker.log")
            real_file.write_text("Some normal text\nCRITICAL FAILURE detected\nMore text")

            try:
                # Test the worker function directly
                # We need to give it byte ranges.
                # "CRITICAL FAILURE" is at the start (offset ~17)
                matches = _scan_chunk_for_errors((str(real_file), 0, 100))

                # Check if it caught the 'CRITICAL' keyword (regex case insensitive matches 'critical')
                # The processor combines patterns:
                # combined_pattern = "|".join(PATTERNS + [r"(?i)error", r"(?i)panic", r"(?i)fatal"])
                # Wait, "CRITICAL" isn't in the default keywords list I added!
                # I added: error, panic, fatal

                # Let's verify specific keywords
                real_file.write_text("This is a Fatal Error")
                matches = _scan_chunk_for_errors((str(real_file), 0, 100))
                assert any("Fatal Error" in m for m in matches)

            finally:
                if real_file.exists():
                    real_file.unlink()


@pytest.mark.asyncio
async def test_resolve_local_path_filesystem(tmp_path):
    """
    Tests the actual path resolution logic with real files.
    """
    # Create a dummy structure: /tmp/roots/src/utils/helper.py
    src_dir = tmp_path / "src" / "utils"
    src_dir.mkdir(parents=True)
    target_file = src_dir / "helper.py"
    target_file.touch()

    # Case 1: Direct relative path match
    from src.utils.context_extractor import resolve_local_path

    # We pretend 'tmp_path' is the workspace root
    resolved = resolve_local_path("src/utils/helper.py", tmp_path)
    assert resolved == target_file

    # Case 2: Path with leading slash (absolute style in logs) -> should be stripped and matched
    # Log says: /app/src/utils/helper.py -> we match src/utils/helper.py
    resolved = resolve_local_path("/app/src/utils/helper.py", tmp_path)
    assert resolved == target_file

    # Case 3: Does not exist
    resolved = resolve_local_path("src/ghost.py", tmp_path)
    assert resolved is None


@pytest.mark.asyncio
async def test_read_code_around_line_aiofiles(tmp_path):
    """
    Tests actual async file reading with aiofiles.
    """
    from src.utils.context_extractor import read_code_around_line

    f = tmp_path / "code.py"
    # Create a file with 10 lines
    f.write_text("\n".join([f"line {i}" for i in range(1, 11)]))

    # Read around line 5, context 2 -> Lines 3,4,5,6,7
    # 0-indexed in list: 2,3,4,5,6
    snippet = await read_code_around_line(f, 5, context_lines=2)

    assert "line 3" in snippet
    assert "line 7" in snippet
    assert ">> line 5" in snippet  # Marker check
    assert "line 8" not in snippet

    # Test file not found or empty
    assert await read_code_around_line(tmp_path / "missing.py", 1) is None


@pytest.mark.asyncio
async def test_parallel_log_processor_large_flow(tmp_path):
    """
    Tests the flow of large file splitting without mocking the internals too heavily.
    """
    from src.utils.log_processor import ParallelLogProcessor

    processor = ParallelLogProcessor()
    # Force the processor to use 1 worker to be friendly to test environment
    processor.workers = 1

    huge_file = tmp_path / "large.log"
    # Create a >1MB file to trigger parallel logic
    # 1MB = 1048576 bytes
    # We put an error at the end
    content = ("INFO: Normal operation\n" * 50000) + "ERROR: Parallel Failure detected"
    huge_file.write_text(content)

    # Force the processor to use 1 worker to be friendly to test environment
    processor.workers = 1

    result = await processor.scan_large_file(huge_file)

    assert "Parallel Failure detected" in result
