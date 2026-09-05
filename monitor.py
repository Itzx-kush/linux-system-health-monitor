#!/usr/bin/env python3

import os
import shutil
import subprocess
import time
from datetime import datetime


CONFIG_PATH = "config/thresholds.conf"
LOG_PATH = "logs/system.log"
REPORT_PATH = "reports/health_report.txt"


def read_cpu_times():
    """Read aggregate CPU times from Linux /proc/stat."""

    with open("/proc/stat", "r") as file:
        line = file.readline()

    values = line.split()[1:]

    if len(values) < 8:
        raise RuntimeError("Unable to read CPU statistics.")

    values = [int(value) for value in values]

    user = values[0]
    nice = values[1]
    system = values[2]
    idle = values[3]
    iowait = values[4]
    irq = values[5]
    softirq = values[6]
    steal = values[7]

    idle_time = idle + iowait
    total_time = (
        user
        + nice
        + system
        + idle
        + iowait
        + irq
        + softirq
        + steal
    )

    return idle_time, total_time


def get_cpu_usage():
    """Calculate CPU utilization percentage using two CPU snapshots."""

    idle_1, total_1 = read_cpu_times()

    time.sleep(1)

    idle_2, total_2 = read_cpu_times()

    idle_difference = idle_2 - idle_1
    total_difference = total_2 - total_1

    if total_difference <= 0:
        return 0.0

    usage = (
        1 - (idle_difference / total_difference)
    ) * 100

    usage = max(0.0, min(100.0, usage))

    return round(usage, 2)


def get_memory_usage():
    """Calculate memory utilization percentage."""

    memory = {}

    with open("/proc/meminfo", "r") as file:
        for line in file:
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            memory[key] = int(value.strip().split()[0])

    total = memory.get("MemTotal")
    available = memory.get("MemAvailable")

    if total is None or available is None or total <= 0:
        raise RuntimeError("Unable to read memory statistics.")

    used = total - available
    usage = (used / total) * 100

    return round(usage, 2)


def get_disk_usage():
    """Calculate disk utilization percentage for the root filesystem."""

    usage = shutil.disk_usage("/")

    if usage.total <= 0:
        raise RuntimeError("Unable to read disk statistics.")

    percentage = (usage.used / usage.total) * 100

    return round(percentage, 2)


def get_process_count():
    """Count currently running Linux processes."""

    process_count = 0

    for entry in os.listdir("/proc"):
        if entry.isdigit():
            process_count += 1

    return process_count


def check_network():
    """Check network connectivity using a single ping request."""

    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", "8.8.8.8"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
            check=False,
        )

        return result.returncode == 0

    except FileNotFoundError:
        print("Warning: 'ping' command is not available.")
        return False

    except subprocess.TimeoutExpired:
        print("Warning: Network check timed out.")
        return False

    except OSError as error:
        print(f"Warning: Network check failed: {error}")
        return False


def load_thresholds():
    """Load monitoring thresholds from configuration."""

    thresholds = {
        "CPU_WARNING": 80.0,
        "MEMORY_WARNING": 80.0,
        "DISK_WARNING": 80.0,
    }

    try:
        with open(CONFIG_PATH, "r") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                if "=" not in line:
                    print(
                        f"Warning: Invalid configuration on line "
                        f"{line_number}: {line}"
                    )
                    continue

                key, value = line.split("=", 1)

                key = key.strip()
                value = value.strip()

                if key not in thresholds:
                    print(
                        f"Warning: Unknown configuration option "
                        f"'{key}' on line {line_number}."
                    )
                    continue

                try:
                    threshold = float(value)

                    if not 0 <= threshold <= 100:
                        print(
                            f"Warning: {key} must be between 0 and 100. "
                            f"Using default value {thresholds[key]}."
                        )
                        continue

                    thresholds[key] = threshold

                except ValueError:
                    print(
                        f"Warning: Invalid numeric value for {key} "
                        f"on line {line_number}. "
                        f"Using default value {thresholds[key]}."
                    )

    except FileNotFoundError:
        print(
            f"Warning: Configuration file not found: {CONFIG_PATH}. "
            "Using default thresholds."
        )

    except OSError as error:
        print(
            f"Warning: Could not read configuration file: {error}. "
            "Using default thresholds."
        )

    return thresholds


def get_status(value, threshold):
    """Return OK or WARNING based on a threshold."""

    if value >= threshold:
        return "WARNING"

    return "OK"


def write_log(cpu, memory, disk, processes, network):
    """Append current system health data to the log."""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    network_status = "Connected" if network else "Disconnected"

    log_entry = (
        f"{timestamp} | "
        f"CPU={cpu}% | "
        f"MEMORY={memory}% | "
        f"DISK={disk}% | "
        f"PROCESSES={processes} | "
        f"NETWORK={network_status}\n"
    )

    try:
        with open(LOG_PATH, "a") as file:
            file.write(log_entry)

    except OSError as error:
        print(f"Warning: Could not write log file: {error}")


def generate_report(
    cpu,
    memory,
    disk,
    processes,
    network,
    cpu_status,
    memory_status,
    disk_status,
):
    """Generate a human-readable system health report."""

    network_status = "Connected" if network else "Disconnected"

    statuses = [
        cpu_status,
        memory_status,
        disk_status,
    ]

    if not network:
        overall_status = "CRITICAL"
    elif "WARNING" in statuses:
        overall_status = "WARNING"
    else:
        overall_status = "HEALTHY"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = (
        "========================================\n"
        "       SYSTEM HEALTH REPORT\n"
        "========================================\n\n"
        f"Generated At        : {timestamp}\n\n"
        f"CPU Usage           : {cpu}% [{cpu_status}]\n"
        f"Memory Usage        : {memory}% [{memory_status}]\n"
        f"Disk Usage          : {disk}% [{disk_status}]\n"
        f"Running Processes   : {processes}\n"
        f"Network Connectivity: {network_status}\n\n"
        f"Overall Status      : {overall_status}\n"
    )

    try:
        with open(REPORT_PATH, "w") as file:
            file.write(report)

    except OSError as error:
        print(f"Warning: Could not generate report: {error}")


def main():
    """Run one complete system health monitoring cycle."""

    print("=" * 50)
    print("       LINUX SYSTEM HEALTH MONITOR")
    print("=" * 50)
    print()

    print("Collecting system information...")
    print()

    try:
        thresholds = load_thresholds()

        cpu = get_cpu_usage()
        memory = get_memory_usage()
        disk = get_disk_usage()
        processes = get_process_count()
        network = check_network()

        cpu_status = get_status(
            cpu,
            thresholds["CPU_WARNING"],
        )

        memory_status = get_status(
            memory,
            thresholds["MEMORY_WARNING"],
        )

        disk_status = get_status(
            disk,
            thresholds["DISK_WARNING"],
        )

        print(f"CPU Usage            : {cpu}% [{cpu_status}]")
        print(f"Memory Usage         : {memory}% [{memory_status}]")
        print(f"Disk Usage           : {disk}% [{disk_status}]")
        print(f"Running Processes    : {processes}")

        network_display = (
            "Connected [OK]"
            if network
            else "Disconnected [CRITICAL]"
        )

        print(
            f"Network Connectivity : "
            f"{network_display}"
        )

        write_log(
            cpu,
            memory,
            disk,
            processes,
            network,
        )

        generate_report(
            cpu,
            memory,
            disk,
            processes,
            network,
            cpu_status,
            memory_status,
            disk_status,
        )

    except (OSError, RuntimeError, ValueError) as error:
        print()
        print(f"ERROR: Monitoring failed: {error}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())