#!/bin/bash
# Usage:
#   bash record.sh                          # uses task from record_config.yaml
#   bash record.sh "Pick up the cube"       # override task description
#   bash record.sh "Pick up the cube" --resume  # continue adding episodes to existing dataset

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$SCRIPT_DIR/record_config.yaml"

TASK=""
EXTRA_ARGS=()

for arg in "$@"; do
    if [[ "$arg" == --* ]]; then
        EXTRA_ARGS+=("$arg")
    elif [[ -z "$TASK" ]]; then
        TASK="$arg"
    fi
done

DATASET_ROOT="$(grep 'root:' "$CONFIG" | awk '{print $2}')"
VIZ_DIR="/mnt/d/SO_101_Robot/viz_output"
RRD_FILE="$VIZ_DIR/recording_$(date +%Y%m%d_%H%M%S).rrd"

CMD=(lerobot-record --config_path "$CONFIG"
    --display_data=true
    --display_save_path "$RRD_FILE"
)

if [[ -n "$TASK" ]]; then
    CMD+=(--dataset.single_task "$TASK")
fi

CMD+=("${EXTRA_ARGS[@]}")

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  LeRobot Record + Teleoperate"
echo "  Config : $CONFIG"
echo "  Task   : ${TASK:-"(from config)"}"
echo "  Extra  : ${EXTRA_ARGS[*]:-none}"
echo "  Local  : $DATASET_ROOT"
echo "  Viz    : $RRD_FILE"
echo "  Hub    : $(grep 'repo_id:' "$CONFIG" | awk '{print $2}')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exec "${CMD[@]}"
