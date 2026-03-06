#!/usr/bin/env bash
# samples/demo.sh — ResponseIQ "Wow" demo
#
# Run this script to see a real bug detected, diagnosed, and remediated
# in under 60 seconds. No API key required.
#
# Usage:
#   chmod +x samples/demo.sh
#   ./samples/demo.sh
#
# Options:
#   --fix        Also run --mode fix after the scan
#   --explain    Add --explain to the fix run (writes REASONING.md)
#   --no-color   Disable ANSI output

set -euo pipefail

# ── Colour helpers ──────────────────────────────────────────────────────────
if [ -t 1 ] && [[ "${NO_COLOR:-}" == "" ]] && [[ "${1:-}" != "--no-color" ]]; then
  BOLD="\033[1m"; DIM="\033[2m"; CYAN="\033[36m"
  GREEN="\033[32m"; YELLOW="\033[33m"; RED="\033[31m"; RESET="\033[0m"
else
  BOLD=""; DIM=""; CYAN=""; GREEN=""; YELLOW=""; RED=""; RESET=""
fi

# ── Argument parsing ─────────────────────────────────────────────────────────
RUN_FIX=0
RUN_EXPLAIN=0
for arg in "$@"; do
  case "$arg" in
    --fix)     RUN_FIX=1 ;;
    --explain) RUN_FIX=1; RUN_EXPLAIN=1 ;;
    --no-color) ;;
    *) echo "Unknown option: $arg"; exit 1 ;;
  esac
done

# ── Banner ───────────────────────────────────────────────────────────────────
echo
echo -e "${BOLD}${CYAN}  ╔═══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}  ║   ResponseIQ — AI-Native Self-Healing Infra Demo  ║${RESET}"
echo -e "${BOLD}${CYAN}  ╚═══════════════════════════════════════════════════╝${RESET}"
echo
echo -e "${DIM}  What you are about to see:${RESET}"
echo -e "${DIM}  1. A real Python service with 3 injected production bugs${RESET}"
echo -e "${DIM}  2. ResponseIQ detecting them from a live crash log${RESET}"
echo -e "${DIM}  3. The Trust Gate evaluating each fix${RESET}"
echo -e "${DIM}  4. A fully explainable REASONING audit trail (with --explain)${RESET}"
echo

# ── Locate script root ───────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CRASH_LOG="$SCRIPT_DIR/crash.log"
BUGGY_SVC="$SCRIPT_DIR/buggy_service.py"

# ── Guard: log file must exist ────────────────────────────────────────────────
if [[ ! -f "$CRASH_LOG" ]]; then
  echo -e "${RED}  ✗  $CRASH_LOG not found.${RESET}"
  echo "     Run from the repo root: ./samples/demo.sh"
  exit 1
fi

# ── Guard: responseiq must be installed ──────────────────────────────────────
if ! command -v responseiq &>/dev/null; then
  echo -e "${YELLOW}  ⚠  responseiq not found in PATH.${RESET}"
  echo -e "     Install it with:  ${CYAN}pip install responseiq${RESET}"
  echo -e "     Or from source:   ${CYAN}cd $REPO_ROOT && uv sync && source .venv/bin/activate${RESET}"
  exit 1
fi

# ── Show the injected bugs in buggy_service.py ────────────────────────────────
echo -e "${BOLD}  The Bugs (samples/buggy_service.py)${RESET}"
echo -e "  ${DIM}────────────────────────────────────────────────────${RESET}"
echo -e "  ${YELLOW}BUG 1${RESET}  line 36 — ${CYAN}user[\"email\"].lower()${RESET} — KeyError for OAuth users"
echo -e "  ${YELLOW}BUG 2${RESET}  line 43 — ${CYAN}_request_log.append(...)${RESET} — unbounded growth, OOM"
echo -e "  ${YELLOW}BUG 3${RESET}  line 48 — ${CYAN}sum(...) / _request_count${RESET} — ZeroDivisionError race"
echo
echo -e "  ${DIM}These are real, runnable Python bugs, not mocked fixtures.${RESET}"
echo

# ── Crash log preview ─────────────────────────────────────────────────────────
echo -e "${BOLD}  The Crash Log (samples/crash.log) — first 8 lines${RESET}"
echo -e "  ${DIM}────────────────────────────────────────────────────${RESET}"
head -8 "$CRASH_LOG" | while IFS= read -r line; do
  echo -e "  ${DIM}$line${RESET}"
done
echo

# ── Step 1: Scan ──────────────────────────────────────────────────────────────
echo -e "${BOLD}  Step 1/$(( RUN_FIX == 1 ? 2 : 1 )) — Scan${RESET}"
echo -e "  ${DIM}$ responseiq --mode scan --target samples/crash.log${RESET}"
echo

SCAN_START="$SECONDS"
responseiq --mode scan --target "$CRASH_LOG"
SCAN_ELAPSED=$(( SECONDS - SCAN_START ))

echo
echo -e "  ${GREEN}✔  Scan complete in ${SCAN_ELAPSED}s${RESET}"
echo

# ── Step 2: Fix (optional) ────────────────────────────────────────────────────
if [[ "$RUN_FIX" == "1" ]]; then
  EXPLAIN_FLAG=""
  if [[ "$RUN_EXPLAIN" == "1" ]]; then
    EXPLAIN_FLAG="--explain"
  fi

  echo -e "${BOLD}  Step 2/2 — Fix${RESET}"
  echo -e "  ${DIM}$ responseiq --mode fix --target samples/crash.log $EXPLAIN_FLAG${RESET}"
  echo

  FIX_START="$SECONDS"
  # shellcheck disable=SC2086
  responseiq --mode fix --target "$CRASH_LOG" $EXPLAIN_FLAG
  FIX_ELAPSED=$(( SECONDS - FIX_START ))

  echo
  echo -e "  ${GREEN}✔  Fix complete in ${FIX_ELAPSED}s${RESET}"

  if [[ "$RUN_EXPLAIN" == "1" ]] && [[ -f "REASONING.md" ]]; then
    echo
    echo -e "  ${CYAN}  Audit log written → $(pwd)/REASONING.md${RESET}"
    echo -e "  ${DIM}  (commit this alongside the patch for SOC2 / post-incident review)${RESET}"
  fi
  echo
fi

# ── Footer ────────────────────────────────────────────────────────────────────
echo -e "  ${DIM}────────────────────────────────────────────────────${RESET}"
echo
echo -e "${BOLD}  What's next?${RESET}"
echo
echo -e "  ${CYAN}  responseiq init${RESET}                       # interactive LLM + policy setup"
echo -e "  ${CYAN}  responseiq --mode shadow --target ./logs/ --shadow-report${RESET}"
echo -e "                                          # MTTR projection — no changes applied"
echo -e "  ${CYAN}  responseiq --mode fix --target ./logs/ --explain${RESET}"
echo -e "                                          # fix + full REASONING.md audit log"
echo
echo -e "${DIM}  Docs:   https://github.com/infoyouth/responseiq${RESET}"
echo -e "${DIM}  PyPI:   pip install responseiq${RESET}"
echo
