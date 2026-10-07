#!/usr/bin/env bash
# Rebuild the four production environments on ICE from exact heck freezes (ops/ice/locks/venv-*.txt).
# Never modifies an existing env: refuses if the target dir exists. Run on a login node with internet.
# Usage: source sites/ice.env && bash ops/ice/build_envs.sh [atlas-031-clean magpie transport covariates]
# Afterwards each env's `pip freeze --all` must equal its lock (checked at the end; mismatch = FAIL, keep the env for inspection).
set -euo pipefail
: "${WS:?source sites/ice.env}" "${ICE_PYTHON:?set ICE_PYTHON (Python 3.11.5)}"
envs=("$@"); [[ $# -eq 0 ]] && envs=(atlas-031-clean magpie transport covariates)
unset PIP_INDEX_URL PIP_EXTRA_INDEX_URL PIP_CONFIG_FILE
status=0
for e in "${envs[@]}"; do
  dest="$WS/.venv-$e"; lock="$WS/ops/ice/locks/venv-$e.txt"
  [[ -f "$lock" ]] || { echo "no lock $lock"; exit 1; }
  if [[ -e "$dest" ]]; then echo "== $e: exists, skipping build (verify only)"; else
    echo "== $e: building $dest from $lock"
    "$ICE_PYTHON" -m venv "$dest"
    "$dest/bin/python" -m pip install --quiet --upgrade "pip==$(grep -E '^pip==' "$lock" | cut -d= -f3)"
    # git+ lines (speculators @ 261a82dd) need git; everything else is exact == pins from PyPI.
    PIP_CONFIG_FILE=/dev/null "$dest/bin/python" -m pip install --no-cache-dir --index-url https://pypi.org/simple -r "$lock"
  fi
  "$dest/bin/python" -m pip check || status=1
  if diff <(grep -v '^#' "$lock" | sort) <("$dest/bin/python" -m pip freeze --all | sed -e 's#^speculators @ .*#SPEC#' -e 's#^hs-connectors @ .*#HSC#' | sort) \
        | grep -v -e 'speculators @' -e 'hs-connectors @' -e '^[<>] SPEC$' -e '^[<>] HSC$' | grep -q '^[<>]'; then
    echo "  FAIL: $e freeze differs from lock:"; diff <(grep -v '^#' "$lock" | sort) <("$dest/bin/python" -m pip freeze --all | sort) | head -20; status=1
  else echo "  PASS: $e matches lock"; fi
done
sha=$(sha256sum "$WS/atlas/env/requirements.lock" | cut -d' ' -f1)
[[ "$sha" == deb579cd2b5e2bd95524ef136cc7230d56e83c10ca6b77d7ec1a200cf10c5a08 ]] && echo "engine lock sha256 OK ($sha)" || { echo "engine lock sha256 MISMATCH"; status=1; }
exit $status
