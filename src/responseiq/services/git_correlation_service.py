"""
git_correlation_service.py — P3: Change-to-Incident Correlation

Answers the question:
  "What changed in the last N commits that most likely caused this incident?"

The service operates in two modes:
  - heuristic  (no LLM key required): symbol/filename matching against git log
  - llm        (requires OpenAI key): compact diff sent to LLM for causal reasoning

CorrelationResult is attached to RemediationRecommendation so the suspect commit
surfaces in the UI, in generated PR bodies, and in the forensic audit trail.

State-machine position:
  Detect → Context → **Reason (P3 correlation here)** → Policy → Execute → Learn
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from responseiq.config.settings import settings
from responseiq.utils.git_utils import GitClient
from responseiq.utils.log_scrubber import scrub
from responseiq.utils.logger import logger

# ---------------------------------------------------------------------------
# Maximum diff characters we will send to the LLM (keeps cost predictable)
# ---------------------------------------------------------------------------
_MAX_DIFF_CHARS = 4000
_MAX_LOG_CHARS = 2000


# ---------------------------------------------------------------------------
# Result schema
# ---------------------------------------------------------------------------


@dataclass
class CorrelationResult:
    """
    Output of GitCorrelationService.correlate().

    Fields
    ------
    suspect_commit      : Human-readable  "<sha7> <subject>"  or None.
    suspect_commit_sha  : Full SHA of the suspect commit, or None.
    confidence_score    : 0.0–1.0 confidence that this commit caused the incident.
    suspect_files       : Source files changed in the suspect commit that overlap
                          with incident symbols.
    correlated_symbols  : Symbols (function names, module paths, class names)
                          extracted from the log that matched the diff.
    diff_summary        : One-paragraph human-readable explanation (from LLM) or
                          a heuristic summary string.
    lookback_hours      : The git log window that was searched.
    method              : "heuristic" | "llm" — which resolution path was used.
    rationale           : Why this commit was selected.
    no_recent_commits   : True when the git log window was empty (nothing to correlate).
    """

    suspect_commit: Optional[str] = None
    suspect_commit_sha: Optional[str] = None
    confidence_score: float = 0.0
    suspect_files: List[str] = field(default_factory=list)
    correlated_symbols: List[str] = field(default_factory=list)
    diff_summary: str = ""
    lookback_hours: int = 24
    method: str = "heuristic"
    rationale: str = ""
    no_recent_commits: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Symbol extraction helpers
# ---------------------------------------------------------------------------

# Patterns that commonly appear in Python / generic stack traces / log lines
_SYMBOL_PATTERNS = [
    re.compile(r'File "([^"]+\.py)"'),  # Python file paths
    re.compile(r"in ([a-zA-Z_][a-zA-Z0-9_.]{2,})"),  # "in function_name"
    re.compile(r"([a-zA-Z_][a-zA-Z0-9_]{2,}Error)"),  # FooError exception types
    re.compile(r"module '([a-zA-Z0-9_.]+)'"),  # module 'name'
    re.compile(r"ImportError.*'([a-zA-Z0-9_.]+)'"),  # ImportError 'pkg'
    re.compile(r"([a-zA-Z_][a-zA-Z0-9_]{2,})\(\)"),  # function_call()
    re.compile(r"class ([A-Z][a-zA-Z0-9_]+)"),  # class ClassName
]


def _extract_symbols(text: str) -> List[str]:
    """Extract candidate identifiers from log text / stack trace."""
    symbols: set[str] = set()
    for pattern in _SYMBOL_PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group(1)
            # Normalise: strip leading path components to get bare filename
            parts = raw.replace("\\", "/").split("/")
            symbols.add(parts[-1].replace(".py", ""))
            if len(parts) > 1:
                symbols.add(parts[-1])  # keep last segment as-is
    # Remove very short tokens (noise)
    return [s for s in symbols if len(s) >= 3]


# ---------------------------------------------------------------------------
# Git log parsing helpers
# ---------------------------------------------------------------------------

_COMMIT_LINE_RE = re.compile(r"^([0-9a-f]{7,40})\s(.+)$", re.MULTILINE)
_FILE_IN_LOG_RE = re.compile(r"^(\S.*\.(py|js|ts|go|java|rb|rs|cpp|c|h))\s*$", re.MULTILINE)


def _parse_log_entries(log_output: str) -> List[Dict[str, Any]]:
    """
    Parse `git log --oneline --name-only` output into a list of dicts:
      {"sha": str, "subject": str, "files": List[str]}
    """
    entries: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    for line in log_output.splitlines():
        line = line.strip()
        if not line:
            continue
        commit_match = _COMMIT_LINE_RE.match(line)
        if commit_match:
            if current:
                entries.append(current)
            current = {"sha": commit_match.group(1), "subject": commit_match.group(2), "files": []}
        elif current and "." in line and not line.startswith("diff") and not line.startswith("---"):
            current["files"].append(line)

    if current:
        entries.append(current)
    return entries


# ---------------------------------------------------------------------------
# Core service
# ---------------------------------------------------------------------------


class GitCorrelationService:
    """
    Correlates the most recent git commits in a repository against an incident
    log to identify the suspect change that triggered the incident.
    """

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path(".")
        self._client = GitClient(cwd=self.repo_path)

    async def correlate(
        self,
        log_text: str,
        lookback_hours: int = 24,
    ) -> CorrelationResult:
        """
        Main entry point.  Returns a CorrelationResult with the most likely
        suspect commit and a confidence score.

        Steps
        -----
        1. Validate that the directory is a git repo (graceful no-op if not).
        2. Extract symbols from the incident log.
        3. Fetch recent git log entries.
        4. If no recent commits → mark no_recent_commits and return.
        5. Heuristic scoring: match symbols against changed filenames.
        6. If LLM available: send compact diff to LLM for causal reasoning.
        7. Return CorrelationResult.
        """
        result = CorrelationResult(lookback_hours=lookback_hours)

        # --- 1. Validate git repo ---
        head = self._client.run_with_output(["rev-parse", "--git-dir"])
        if not head:
            logger.debug("GitCorrelationService: not a git repo or git not available — skipping")
            result.rationale = "Repository not available or not a git repo."
            return result

        # --- 2. Extract symbols ---
        symbols = _extract_symbols(log_text)
        result.correlated_symbols = symbols
        logger.debug(f"GitCorrelationService: extracted symbols: {symbols}")

        # --- 3. Fetch recent log entries ---
        log_output = self._client.get_log_entries(since_hours=lookback_hours)
        if not log_output or not log_output.strip():
            result.no_recent_commits = True
            result.rationale = f"No commits found in the last {lookback_hours} hours."
            logger.info(f"GitCorrelationService: no commits in last {lookback_hours}h")
            return result

        # --- 5. Heuristic scoring ---
        entries = _parse_log_entries(log_output)
        if not entries:
            result.no_recent_commits = True
            result.rationale = "Could not parse git log output."
            return result

        best_entry, best_score, best_files = self._heuristic_score(entries, symbols, log_text)

        if best_entry:
            result.suspect_commit = f"{best_entry['sha']} {best_entry['subject']}"
            result.suspect_commit_sha = best_entry["sha"]
            result.suspect_files = best_files
            result.confidence_score = min(best_score / 10.0, 0.75)  # cap heuristic at 0.75
            result.method = "heuristic"
            result.rationale = f"Heuristic match: {len(best_files)} changed file(s) overlap with incident symbols."
            result.diff_summary = f"Commit {result.suspect_commit} changed: {', '.join(best_files[:5])}" + (
                " and more." if len(best_files) > 5 else "."
            )

        # --- 6. LLM upgrade (if key available) ---
        if settings.openai_api_key:
            try:
                result = await self._llm_correlate(log_text, log_output, result, lookback_hours)
            except Exception as exc:
                logger.warning(f"GitCorrelationService LLM path failed: {exc} — keeping heuristic result")

        return result

    # ------------------------------------------------------------------
    # Heuristic scorer
    # ------------------------------------------------------------------

    @staticmethod
    def _heuristic_score(
        entries: List[Dict[str, Any]],
        symbols: List[str],
        log_text: str,
    ) -> tuple[Optional[Dict[str, Any]], float, List[str]]:
        """
        Score each commit entry by how many changed filenames / subjects overlap
        with the extracted symbols.  Also scores direct keyword matches in log_text.
        """
        best_entry: Optional[Dict[str, Any]] = None
        best_score = 0.0
        best_files: List[str] = []

        log_lower = log_text.lower()

        for entry in entries:
            score = 0.0
            matched_files: List[str] = []

            for f in entry.get("files", []):
                basename = Path(f).stem.lower()
                # Direct symbol match
                for sym in symbols:
                    if sym.lower() in basename or basename in sym.lower():
                        score += 3.0
                        matched_files.append(f)
                        break
                # Keyword match: does the log text mention this filename?
                if Path(f).name.lower() in log_lower:
                    score += 2.0
                    if f not in matched_files:
                        matched_files.append(f)

            # Bonus: subject line mentions a symbol
            subject_lower = entry.get("subject", "").lower()
            for sym in symbols:
                if sym.lower() in subject_lower:
                    score += 1.5

            if score > best_score:
                best_score = score
                best_entry = entry
                best_files = matched_files

        return best_entry, best_score, best_files

    # ------------------------------------------------------------------
    # LLM correlator
    # ------------------------------------------------------------------

    async def _llm_correlate(
        self,
        log_text: str,
        log_output: str,
        heuristic_result: CorrelationResult,
        lookback_hours: int,
    ) -> CorrelationResult:
        """
        Send a compact diff + incident log to the LLM and request a structured
        CorrelationResult.  Returns an updated result, or the original if LLM fails.
        """
        api_key = settings.openai_api_key.get_secret_value()  # type: ignore[union-attr]

        # Scrub PII before sending to LLM
        safe_log, _ = scrub(log_text)

        # Truncate diff / log for token efficiency
        diff_text = self._client.get_recent_diff(since_hours=lookback_hours) or ""
        safe_diff, _ = scrub(diff_text[:_MAX_DIFF_CHARS])
        safe_log_summary = safe_log[:_MAX_LOG_CHARS]

        if not safe_diff.strip():
            # No patch data — keep heuristic result
            return heuristic_result

        prompt = (
            "You are a senior SRE analyzing an incident. "
            "Below is a recent git diff (the last 24 hours of commits) and an incident log.\n\n"
            f"INCIDENT LOG:\n{safe_log_summary}\n\n"
            f"RECENT GIT DIFF:\n{safe_diff}\n\n"
            "Identify the single commit most likely to have caused this incident.\n"
            "Return ONLY a JSON object with these keys:\n"
            "  suspect_commit_sha  (string: the 7-char short SHA, or null)\n"
            "  suspect_commit      (string: '<sha7> <commit subject>', or null)\n"
            "  confidence_score    (number: 0.0–1.0)\n"
            "  suspect_files       (array of strings: changed files implicated)\n"
            "  diff_summary        (string: one paragraph explaining the causal link)\n"
            "  rationale           (string: concise explanation)\n"
            "Do NOT add markdown. Output only valid JSON."
        )

        payload = {
            "model": settings.llm_fast_model,
            "messages": [
                {"role": "system", "content": "You are a concise, JSON-only SRE incident analyst."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 600,
        }

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
            )

        if response.status_code != 200:
            logger.warning(f"GitCorrelationService LLM call failed: HTTP {response.status_code}")
            return heuristic_result

        content = response.json()["choices"][0]["message"]["content"]
        try:
            data: Dict[str, Any] = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("GitCorrelationService: LLM returned non-JSON — keeping heuristic result")
            return heuristic_result

        llm_result = CorrelationResult(
            suspect_commit=data.get("suspect_commit") or heuristic_result.suspect_commit,
            suspect_commit_sha=data.get("suspect_commit_sha") or heuristic_result.suspect_commit_sha,
            confidence_score=float(data.get("confidence_score", heuristic_result.confidence_score)),
            suspect_files=data.get("suspect_files") or heuristic_result.suspect_files,
            correlated_symbols=heuristic_result.correlated_symbols,
            diff_summary=data.get("diff_summary", ""),
            lookback_hours=lookback_hours,
            method="llm",
            rationale=data.get("rationale", ""),
            no_recent_commits=heuristic_result.no_recent_commits,
        )
        logger.info(
            f"GitCorrelationService LLM result: suspect={llm_result.suspect_commit} "
            f"confidence={llm_result.confidence_score:.2f}"
        )
        return llm_result
