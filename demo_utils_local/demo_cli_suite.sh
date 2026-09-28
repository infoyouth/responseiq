#!/bin/bash
set -e

# 1. Check CLI help is clean and fast
start=$(date +%s%3N)
uv run responseiq -h > cli_help.txt 2>&1
end=$(date +%s%3N)
elapsed=$((end - start))
if grep -q "TrustGate" cli_help.txt; then
  echo "FAIL: Too noisy (TrustGate in help output)"
else
  echo "PASS: CLI help is clean"
fi
if [ $elapsed -gt 500 ]; then
  echo "FAIL: CLI help took too long (${elapsed}ms)"
else
  echo "PASS: CLI help is fast (${elapsed}ms)"
fi

# 2. Check version output
uv run responseiq --version

# 3. Dry-run shadow mode
uv run responseiq --mode shadow --debug > cli_shadow.txt 2>&1 || true
if grep -q "PluginError" cli_shadow.txt; then
  echo "FAIL: Plugin error in shadow mode"
else
  echo "PASS: Shadow mode runs"
fi

# 4. Plugin loading in scan mode
uv run responseiq --mode scan --debug | grep -q "Loading plugin: scan" && echo "PASS: Plugin loading message found" || echo "FAIL: Plugin loading message missing"

# 5. SRE-friendly: simulate plugin crash
uv run responseiq --mode scan --target /nonexistent 2> cli_crash.txt && echo "FAIL: Scan on nonexistent dir should fail" || echo "PASS: Nonzero exit on plugin crash"
