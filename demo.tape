# demo.tape — VHS terminal recording script for ResponseIQ
#
# Regenerate the animated GIF:
#   brew install vhs          # macOS
#   go install github.com/charmbracelet/vhs@latest   # Go
#   vhs demo.tape
#
# Pre-requisites (one-time setup before recording):
#   1. Create instant-replay wrapper (uses pre-captured real Ollama output):
#      cat > /tmp/responseiq << 'WRAP'
#      #!/usr/bin/env bash
#      case "$*" in
#        *scan*) cat /home/shital/git/responseiq/demo_utils_local/scan_output.txt ;;
#        *fix*)  cat /home/shital/git/responseiq/demo_utils_local/fix_output.txt ;;
#        *)      exec /home/shital/git/responseiq/.venv/bin/responseiq "$@" ;;
#      esac
#      WRAP
#      chmod +x /tmp/responseiq
#
#   2. To refresh captured output (requires Ollama running with llama3.2):
#      See demo_utils_local/README.md
#
# Commit the resulting demo.gif along with any tape changes.

Output demo.gif

Set FontSize 14
Set Width 1200
Set Height 620
Set Theme "Dracula"
Set Shell "bash"
Set Padding 20
Env PATH "/tmp:/home/shital/git/responseiq/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Env PS1 "$ "
Env PROMPT_COMMAND ""

# ── Setup ──────────────────────────────────────────────────────────────────
Type "cd /home/shital/git/responseiq"
Enter
Sleep 300ms
Type "clear"
Enter
Sleep 300ms

# ── Step 0: Version check ───────────────────────────────────────────────────
Type "responseiq --version"
Enter
Sleep 1s

# ── Step 1: Scan ─────────────────────────────────────────────────────────────
Type "responseiq --mode scan --target ./samples/crash.log 2>/dev/null"
Sleep 500ms
Enter
Sleep 2s

# ── Step 2: Fix ──────────────────────────────────────────────────────────────
Type "responseiq --mode fix --target ./fixtures/fixture_high.json 2>/dev/null"
Sleep 500ms
Enter
Sleep 2s

# ── End ─────────────────────────────────────────────────────────────────────
Sleep 2s
