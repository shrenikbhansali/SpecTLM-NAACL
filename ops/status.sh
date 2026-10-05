#!/usr/bin/env bash
# Operator status snapshot (MASTER §8.1 step 4).
# Usage: ops/status.sh [--no-gpu]
# Sections: pause marker, board (non-todo §4 rows on every branch), GPUs per
# node, disk, downloads, launched runs, recent failures.
set -uo pipefail

WS=${WS:-/home/heck2/sbhansali8/SpecTLM}
REPO=$(cd "$(dirname "$0")/.." && pwd)
PAUSE=${PAUSE_MARKER:-/home/heck2/sbhansali8/SpecTLM/tlm-spec-maintenance/EXPERIMENTS_PAUSED.json}
NODES=${NODES:-"heck-srv1 heck-srv2 heck-srv3 heck-srv4 heck-srv5 heck-srv6"}
HF_HOME=${HF_HOME:-/home/heck2/sbhansali8/HFcache}

hdr() { printf '\n=== %s ===\n' "$1"; }

echo "status @ $(TZ=America/New_York date '+%Y-%m-%d %H:%M %Z')"

hdr "pause marker"
if [[ -e $PAUSE ]]; then
  echo "PRESENT: $PAUSE ($(python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(d.get('status'),d.get('requested_at'))" "$PAUSE" 2>/dev/null))"
else
  echo "absent"
fi

hdr "board (non-todo rows, per branch)"
for br in $(git -C "$REPO" for-each-ref --format='%(refname:short)' refs/heads/); do
  git -C "$REPO" show "$br:MASTER.md" 2>/dev/null \
    | awk -F'|' -v br="$br" '/^## 4\./ {on=1} /^## 5\./ {on=0} on && /^\| (B|O|A|M|W|G|R|FIX)[0-9A-Z–-]* \|/ {
        st=$8; gsub(/^ +| +$/,"",st); if (st!="todo") {id=$2; gsub(/ /,"",id); who=$9; gsub(/^ +| +$/,"",who); printf "%-12s %-6s %-12s %s\n", br, id, st, who}}'
done | sort -k2,2 -k1,1 | uniq

hdr "git"
git -C "$REPO" log --all --since='6 hours ago' --format='%h %ad %an %d %s' --date=format:'%H:%M' | head -15

if [[ ${1:-} != --no-gpu ]]; then
  hdr "GPUs (used/total MiB, util%; * = other user's process)"
  for n in $NODES; do
    (
      out=$(timeout 25 ssh -o BatchMode=yes -o ConnectTimeout=8 -o LogLevel=ERROR "$n" '
        nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits | tr -d " " | tr "\n" ";"
        echo -n "|"
        for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader); do ps -o user= -p $p; done | sort | uniq -c | tr -s " " | tr "\n" ","
      ' 2>/dev/null | grep -v '^\*' | tail -1)
      if [[ -z $out ]]; then echo "$n: UNREACHABLE"; exit; fi
      gpus=${out%%|*}; users=${out#*|}
      free=$(tr ';' '\n' <<<"$gpus" | awk -F, 'NF==4 && $2<1000 {c++} END {print c+0}')
      printf '%-10s free=%s  %s  users:[%s]\n' "$n" "$free" "$(tr ';' '\n' <<<"$gpus" | awk -F, 'NF==4 {printf "%s:%s/%s,%s%% ", $1,$2,$3,$4}')" "$users"
    ) &
  done
  wait
fi

hdr "disk"
df -h /home/heck2 /nethome/sbhansali8 2>/dev/null | awk 'NR==1 || /heck2|nethome/'
quota -s 2>/dev/null | awk 'NR>2 && NF>=4 {print "nethome quota: used " $1 " soft " $2 " hard " $3}' | head -1
for d in "$WS/artifacts" "$HF_HOME/hub"; do
  [[ -d $d ]] && echo "$(timeout 60 du -sh "$d" 2>/dev/null | cut -f1)	$d"
done

hdr "downloads"
inc=$(timeout 60 find "$HF_HOME/hub" -name '*.incomplete' -mmin -30 2>/dev/null | wc -l)
echo "HF partial files touched in last 30 min: $inc"
for f in $(ls -t "$WS"/artifacts/atlas/*download*.log "$WS"/artifacts/atlas/*download*.jsonl "$WS"/artifacts/atlas/*/*download*.log 2>/dev/null | head -3); do
  echo "--- $f ($(wc -l <"$f") lines, modified $(date -r "$f" '+%H:%M'))"; tail -n 4 "$f" | cut -c1-200
done

hdr "launched runs (ops registry)"
python3 "$REPO/ops/launch.py" list --n 15 2>&1

hdr "recent failures (last 6 h)"
find "$WS/artifacts" -maxdepth 3 -name exit_code -mmin -360 2>/dev/null | while read -r f; do
  c=$(cat "$f"); [[ $c != 0 ]] && echo "exit $c: $(dirname "$f")"
done
find "$WS/artifacts" -maxdepth 3 \( -name '*.log' -o -name '*.err' \) -mmin -360 2>/dev/null \
  | xargs -r grep -lE 'Traceback|CUDA out of memory|Error:|NCCL' 2>/dev/null | head -10 | sed 's/^/errors in: /'
echo "(end)"
