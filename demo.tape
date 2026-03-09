# demo.tape — VHS terminal recording script for ResponseIQ
#
# Regenerate the animated GIF:
#   go install github.com/charmbracelet/vhs@latest
#   vhs demo.tape
#
# Pre-requisites (one-time setup before recording):
#   Create the instant-replay wrapper so VHS uses pre-captured output
#   instead of waiting ~30 s for a live LLM call:
#
#   cat > /tmp/responseiq-demo-replay << 'WRAP'
#   #!/usr/bin/env bash
#   cat /home/shital/git/responseiq/demo_utils_local/demo_output.txt
#   WRAP
#   chmod +x /tmp/responseiq-demo-replay
#
#   To refresh captured output (requires Ollama running with llama3.2):
#     python -m responseiq.cli demo 2>/dev/null \
#       | tee demo_utils_local/demo_output.txt
#
# Commit demo.gif along with any tape changes.

Output demo.gif

Set FontSize 14
Set Width 1200
Set Height 700
Set Theme "Dracula"
Set Shell "bash"
Set Padding 20
Env PATH "/home/shital/git/responseiq/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Env PS1 "$ "
Env PROMPT_COMMAND ""

# ── Setup ──────────────────────────────────────────────────────────────────
Type "cd /home/shital/git/responseiq"
Enter
Sleep 200ms
Type "clear"
Enter
Sleep 200ms

# ── Install (shown for first-time visitors) ────────────────────────────────
Type "pip install responseiq --quiet && responseiq --version"
Sleep 300ms
Enter
Sleep 1s

Type "clear"
Enter
Sleep 200ms

# ── Main hook: responseiq demo ─────────────────────────────────────────────
Hide
Type "alias responseiq-demo-replay='/tmp/responseiq-demo-replay'; responseiq() { responseiq-demo-replay; }"
Enter
Sleep 100ms
Show

Type "responseiq demo"
Sleep 500ms
Enter

# Scan output appears
Sleep 3s

# Fix output + REASONING.md line appear
Sleep 3s

# Final "Demo complete" + pipe suggestions
Sleep 2s

# ── Pipe mode teaser ───────────────────────────────────────────────────────
Sleep 1s
Type "cat samples/crash.log | responseiq --mode scan --target - 2>/dev/null"
Sleep 500ms
Enter
Sleep 2s

# ── End ────────────────────────────────────────────────────────────────────
Sleep 3s
