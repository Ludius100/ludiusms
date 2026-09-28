import shutil
import time
import urllib.request

from config import NAS_ROOT, SERVICE_STATUS_URLS


def cpu_snapshot():
    with open("/proc/stat") as f:
        parts = f.readline().split()[1:]

    values = list(map(int, parts))

    idle = values[3] + values[4]
    total = sum(values)

    return idle, total


def cpu_percent():
    idle1, total1 = cpu_snapshot()
    time.sleep(0.15)
    idle2, total2 = cpu_snapshot()

    idle_delta = idle2 - idle1
    total_delta = total2 - total1

    if total_delta == 0:
        return 0

    return round(
        100 * (1 - idle_delta / total_delta)
    )


def check_http(url):
    start = time.monotonic()

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "NAS-Dashboard/1.0"
            }
        )

        with urllib.request.urlopen(
            req,
            timeout=3
        ) as response:
            status = response.status

        latency = round(
            (time.monotonic() - start) * 1000
        )

        return {
            "online": 200 <= status < 500,
            "latency": latency
        }

    except Exception:
        return {
            "online": False,
            "latency": None
        }


def get_service_statuses():
    return {
        name: check_http(url)
        for name, url in SERVICE_STATUS_URLS.items()
    }


def get_system_stats():
    mem = {}

    with open("/proc/meminfo") as f:
        for line in f:
            key, value = line.split(":", 1)
            mem[key] = int(
                value.strip().split()[0]
            )

    ram_percent = round(
        (
            1 -
            mem["MemAvailable"] /
            mem["MemTotal"]
        ) * 100
    )

    with open("/proc/uptime") as f:
        uptime_seconds = int(
            float(f.read().split()[0])
        )

    disk = shutil.disk_usage(NAS_ROOT)

    disk_percent = round(
        disk.used / disk.total * 100
    )

    return {
        "cpu": cpu_percent(),
        "ram": ram_percent,
        "disk": disk_percent,
        "diskUsedGB": round(
            disk.used / 1024**3,
            1
        ),
        "diskTotalGB": round(
            disk.total / 1024**3,
            1
        ),
        "uptimeSeconds": uptime_seconds
    }
