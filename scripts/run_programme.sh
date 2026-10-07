#!/usr/bin/env bash
# docs/prereg_full_programme.md - every run in sequence (one at a time, to stay inside memory).
# Usage: PY=<python> bash scripts/run_programme.sh <logdir>
cd "$(dirname "$0")/.." || exit 1
PY=${PY:-python}
LOG=${1:-/tmp}
BOOKS=("BPHS" "Phaladeepika" "KP Readers" "KP modern" "Saravali" "Valens" "Lilly")
run() { echo "=== $(date +%H:%M) $*"; "$PY" scripts/run_bphs_engine.py --workers 4 --prereg docs/prereg_full_programme.md "$@" 2>&1 \
        | grep -E "phase 1 done|signal|PASS|per rule:|learned|written|Traceback|Error"; }

echo "=== $(date +%H:%M) N natal"
"$PY" scripts/run_natal.py --workers 4 2>&1 | grep -vE "^  [0-9]+/"

for b in "${BOOKS[@]}"; do run --sources "$b" --ratings AA; done                       # T1

LILLY_DIR_WINDOW=1.0 ASTRO_RUN_TAG=_window1 run --sources Lilly                          # T3
LILLY_KEY=ptolemy ASTRO_RUN_TAG=_ptolemy run --sources Lilly

for b in "${BOOKS[@]}"; do ASTRO_OFFSETS=half ASTRO_RUN_TAG=_halfyear run --sources "$b"; done   # T2

run --sources "BPHS,Phaladeepika,KP Readers,KP modern,Saravali,Valens,Lilly"           # T4

echo "=== $(date +%H:%M) programme done"
