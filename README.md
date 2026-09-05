# Linux System Health & Monitoring Tool

A Linux system health monitoring utility built with Python and Bash.
The tool collects system metrics, checks configurable thresholds, records
monitoring results, generates health reports, and supports automated
periodic monitoring.

## Features

- CPU utilization monitoring
- Memory utilization monitoring
- Disk utilization monitoring
- Running process count
- Network connectivity check
- Configurable warning thresholds
- Warning and critical status detection
- Timestamped system logging
- Human-readable health reports
- Configuration validation and fallback defaults
- Bash-based automated monitoring cycles

## Technologies

- Python 3
- Bash
- Linux
- WSL2 / Ubuntu
- Git

## Project Structure

```text
linux-system-health-monitor/
├── config/
│   └── thresholds.conf
├── logs/
│   └── .gitkeep
├── reports/
│   └── .gitkeep
├── monitor.py
├── monitor.sh
├── .gitignore
└── README.md
