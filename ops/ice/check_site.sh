#!/usr/bin/env bash
# Preflight for ICE: every site variable filled, paths writable, Slurm reachable, venvs/models present.
# Usage: source sites/ice.env && bash ops/ice/check_site.sh      (read-only; prints PASS/FAIL per item)
set -u
fail=0
ok()  { printf '  PASS  %s\n' "$1"; }
bad() { printf '  FAIL  %s\n' "$1"; fail=1; }
echo "== site variables"
for v in SITE WS HF_HOME ICE_PYTHON SLURM_ACCOUNT SLURM_PARTITION SLURM_GRES PAUSE_MARKER; do
  val=${!v:-}
  if [[ -z "$val" || "$val" == TODO* ]]; then bad "$v unset or TODO"; else ok "$v=$val"; fi
done
[[ "${SITE:-}" == ice ]] || bad "SITE must be ice (source sites/ice.env)"
echo "== paths"
[[ -d "${WS:-/nonexistent}/.git" ]] && ok "WS is a git clone" || bad "WS is not the repo clone"
for d in "$WS/artifacts" "$HF_HOME"; do mkdir -p "$d" 2>/dev/null && [[ -w "$d" ]] && ok "writable $d" || bad "not writable $d"; done
df -h "$WS" "$HF_HOME" 2>/dev/null | sed 's/^/    /'
[[ -e "$PAUSE_MARKER" ]] && echo "  NOTE  pause marker present: real launches refused" || ok "no pause marker"
echo "== python / git"
if [[ -x "${ICE_PYTHON:-}" ]]; then
  pv=$("$ICE_PYTHON" -c 'import sys;print(".".join(map(str,sys.version_info[:3])))')
  [[ "$pv" == 3.11.5 ]] && ok "ICE_PYTHON is 3.11.5" || echo "  WARN  ICE_PYTHON is $pv (heck uses 3.11.5; pins were frozen there)"
else bad "ICE_PYTHON not executable"; fi
(cd "$WS" && git fetch -q origin && [[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]) && ok "clone at origin/main" || echo "  WARN  clone not at origin/main"
echo "== slurm"
command -v sbatch >/dev/null && ok "sbatch found" || bad "sbatch not on PATH"
sinfo -h -p "${SLURM_PARTITION:-x}" -o '%P %a %D %G' 2>/dev/null | head -3 | sed 's/^/    /' || bad "sinfo failed for partition"
echo "== environments (ops/ice/build_envs.sh)"
for py in "$ATLAS_PY" "$MAGPIE_PY" "$TRANSPORT_PY" "$COVARIATES_PY"; do [[ -x "$py" ]] && ok "$py" || echo "  TODO  missing $py"; done
echo "== models (ops/ice/stage_models.py --check)"
[[ -x "${ATLAS_PY:-}" ]] && HF_HUB_OFFLINE=1 "$ATLAS_PY" "$WS/ops/ice/stage_models.py" --check --tier core 2>&1 | tail -3 | sed 's/^/    /'
echo; [[ $fail == 0 ]] && echo "SITE CHECK PASS" || { echo "SITE CHECK FAIL"; exit 1; }
