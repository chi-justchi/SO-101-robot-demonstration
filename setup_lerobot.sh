#!/bin/bash

# ─────────────────────────────────────────────
# LeRobot SO-101 Setup Script (WSL2 / Linux)
# Run: bash setup_lerobot.sh
# ─────────────────────────────────────────────

ask() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP $1: $2"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Command: $3"
    echo ""
    read -p "Run this step? [y/n/q(quit)]: " choice
    case "$choice" in
        y|Y) return 0 ;;
        q|Q) echo "Exiting."; exit 0 ;;
        *) echo "Skipped."; return 1 ;;
    esac
}

# ── STEP 1: Create conda environment ──────────
if ask 1 "Create conda environment (python 3.12)" "conda create -n lerobot python=3.12 -y"; then
    conda create -n lerobot python=3.12 -y
fi

# ── STEP 2: Activate environment ──────────────
if ask 2 "Activate lerobot environment" "conda activate lerobot"; then
    # NOTE: 'conda activate' only works in interactive shells.
    # After this script, you must run: conda activate lerobot
    # The rest of this script assumes the env is active.
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate lerobot
    echo "✓ Environment activated for this script session."
    echo ""
    echo "  IMPORTANT: After this script ends, run:"
    echo "    conda activate lerobot"
    echo "  in your terminal before continuing."
fi

# ── STEP 3: Install lerobot with feetech ──────
if ask 3 "Install lerobot[feetech] via pip" 'pip install "lerobot[feetech]"'; then
    pip install "lerobot[feetech]"
fi

# ── STEP 4: Download Miniforge (WSL2/Linux) ───
if ask 4 "Download Miniforge installer (skip if conda already works)" 'wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"'; then
    wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
fi

# ── STEP 5: Run Miniforge installer ───────────
if ask 5 "Run Miniforge installer (skip if conda already works)" "bash Miniforge3-\$(uname)-\$(uname -m).sh"; then
    bash Miniforge3-$(uname)-$(uname -m).sh
fi

# ── STEP 6: Install ffmpeg via conda ──────────
if ask 6 "Install ffmpeg from conda-forge" "conda install ffmpeg -c conda-forge"; then
    conda install ffmpeg -c conda-forge -y
fi

# ── STEP 7: Clone lerobot repo ────────────────
if ask 7 "Clone lerobot from HuggingFace GitHub" "git clone https://github.com/huggingface/lerobot.git"; then
    git clone https://github.com/huggingface/lerobot.git
fi

# ── STEP 8: Install lerobot in editable mode ──
if ask 8 "Install lerobot in editable mode (from cloned repo)" "cd lerobot && pip install -e ."; then
    cd lerobot
    pip install -e .
    cd ..
fi

# ── STEP 9: Install lerobot via pip ───────────
if ask 9 "Install lerobot via pip (standalone)" "pip install lerobot"; then
    pip install lerobot
fi

# ── STEP 10: Find available ports ─────────────
if ask 10 "Find available serial ports for your robot" "lerobot-find-port"; then
    lerobot-find-port
fi

# ── NOTE: Steps 11-15 use Mac-style port names (/dev/tty.usbmodem...)
# On WSL2/Linux, your ports will look like: /dev/ttyUSB0 or /dev/ttyACM0
# Run 'lerobot-find-port' first (step 10) to find the correct port names.
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "NOTE: The next steps use example port names."
echo "Replace the port values with what 'lerobot-find-port' showed you."
echo "On WSL2/Linux, ports look like: /dev/ttyUSB0 or /dev/ttyACM0"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── STEP 11: Setup follower motor ─────────────
if ask 11 "Setup motors for FOLLOWER arm" \
"lerobot-setup-motors --robot.type=so101_follower --robot.port=/dev/tty.usbmodem5C4C1271441"; then
    read -p "Enter FOLLOWER port (e.g. /dev/ttyUSB0): " FOLLOWER_PORT
    lerobot-setup-motors \
        --robot.type=so101_follower \
        --robot.port="$FOLLOWER_PORT"
fi

# ── STEP 12: Setup leader motor ───────────────
if ask 12 "Setup motors for LEADER arm" \
"lerobot-setup-motors --teleop.type=so101_leader --teleop.port=/dev/tty.usbmodem5C4C1266591"; then
    read -p "Enter LEADER port (e.g. /dev/ttyUSB1): " LEADER_PORT
    lerobot-setup-motors \
        --teleop.type=so101_leader \
        --teleop.port="$LEADER_PORT"
fi

# ── STEP 13: Calibrate follower ───────────────
if ask 13 "Calibrate FOLLOWER arm" \
"lerobot-calibrate --robot.type=so101_follower --robot.port=<port> --robot.id=my_awesome_follower_arm"; then
    read -p "Enter FOLLOWER port: " FOLLOWER_PORT
    lerobot-calibrate \
        --robot.type=so101_follower \
        --robot.port="$FOLLOWER_PORT" \
        --robot.id=my_awesome_follower_arm
fi

# ── STEP 14: Calibrate leader ─────────────────
if ask 14 "Calibrate LEADER arm" \
"lerobot-calibrate --teleop.type=so101_leader --teleop.port=<port> --teleop.id=my_awesome_leader_arm"; then
    read -p "Enter LEADER port: " LEADER_PORTpyhot
    lerobot-calibrate \
        --teleop.type=so101_leader \
        --teleop.port="$LEADER_PORT" \
        --teleop.id=my_awesome_leader_arm
fi

# ── STEP 15: Teleoperate ──────────────────────
if ask 15 "Start teleoperation" "lerobot-teleoperate ..."; then
    read -p "Enter FOLLOWER port: " FOLLOWER_PORT
    read -p "Enter LEADER port: " LEADER_PORT
    lerobot-teleoperate \
        --robot.type=so101_follower \
        --robot.port="$FOLLOWER_PORT" \
        --robot.id=my_awesome_follower_arm \
        --teleop.type=so101_leader \
        --teleop.port="$LEADER_PORT" \
        --teleop.id=my_awesome_leader_arm
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Setup script complete."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
