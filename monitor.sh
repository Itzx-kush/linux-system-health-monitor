#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_DIR" || {
    echo "ERROR: Could not access project directory."
    exit 1
}

INTERVAL=60
RUNS=1

echo "========================================"
echo "       LINUX SYSTEM HEALTH MONITOR"
echo "========================================"
echo
echo "Project directory : $PROJECT_DIR"
echo "Interval           : ${INTERVAL}s"
echo "Monitoring cycles  : $RUNS"
echo

for ((cycle=1; cycle<=RUNS; cycle++))
do
    echo "----------------------------------------"
    echo "Monitoring cycle $cycle of $RUNS"
    echo "----------------------------------------"

    python3 monitor.py

    if [ $? -ne 0 ]; then
        echo
        echo "ERROR: Monitoring failed on cycle $cycle."
        exit 1
    fi

    if [ $cycle -lt $RUNS ]; then
        echo
        echo "Waiting ${INTERVAL} seconds..."
        sleep "$INTERVAL"
    fi
done

echo
echo "Monitoring completed successfully."