"""Daily background sync via launchd."""
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

from . import config

LABEL = "com.github.mdkocher.costco-cli"
PLIST = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"


def _costco_command():
    exe = shutil.which("costco")
    if exe:
        return [exe]
    return [sys.executable, "-m", "costco_cli"]


def _job_env():
    """Environment for the launchd job. launchd starts it with almost nothing,
    so carry over this tool's own settings (data folder, browser path, ports)
    or the 07:00 run silently uses different ones than the shell that set it up."""
    env = {"PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"}
    env.update({k: v for k, v in os.environ.items() if k.startswith("COSTCO_CLI_")})
    return env


DAYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]  # launchd Weekday: 0 = Sunday
FULL_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def parse_slot(text):
    """'sat 09:00' -> (6, 9, 0); '07:00' -> (None, 7, 0) meaning every day."""
    parts = text.lower().split()
    day = None
    if len(parts) == 2:
        if parts[0][:3] not in DAYS:
            raise ValueError(f"unknown day {parts[0]!r}; use sun, mon, ... sat")
        day = DAYS.index(parts[0][:3])
    elif len(parts) != 1:
        raise ValueError(f"expected 'DAY HH:MM' or 'HH:MM', got {text!r}")
    hh, mm = (int(x) for x in parts[-1].split(":"))
    if not (0 <= hh < 24 and 0 <= mm < 60):
        raise ValueError(f"not a time of day: {parts[-1]!r}")
    return day, hh, mm


def _interval(day, hh, mm):
    return {"Hour": hh, "Minute": mm, **({"Weekday": day} if day is not None else {})}


def _describe(t):
    return (f"{FULL_DAYS[t['Weekday'] % 7]}s" if "Weekday" in t else "Daily") + f" at {t['Hour']:02d}:{t['Minute']:02d}"


def install(hour=None, minute=None, weekday=None, slots=None):
    """Run at each of slots [(weekday or None, hour, minute), ...]; weekday
    0 = Sunday, None = every day. hour/minute/weekday is the one-slot form."""
    slots = slots or [(weekday, hour, minute)]
    intervals = [_interval(*s) for s in slots]
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    cmd = _costco_command()
    plist = {
        "Label": LABEL,
        "ProgramArguments": cmd + ["daily"],
        "StartCalendarInterval": intervals[0] if len(intervals) == 1 else intervals,
        "StandardOutPath": str(config.LOG_DIR / "daily.log"),
        "StandardErrorPath": str(config.LOG_DIR / "daily.log"),
        "EnvironmentVariables": _job_env(),
    }
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["launchctl", "unload", str(PLIST)], check=False, capture_output=True)
    PLIST.write_bytes(plistlib.dumps(plist))
    subprocess.run(["launchctl", "load", str(PLIST)], check=True)
    return PLIST, " ".join(cmd + ["daily"])


def uninstall():
    if not PLIST.exists():
        return False
    subprocess.run(["launchctl", "unload", str(PLIST)], check=False, capture_output=True)
    PLIST.unlink()
    return True


def status():
    if not PLIST.exists():
        return None
    plist = plistlib.loads(PLIST.read_bytes())
    t = plist["StartCalendarInterval"]
    when = ", ".join(_describe(x) for x in (t if isinstance(t, list) else [t]))
    loaded = subprocess.run(["launchctl", "list", LABEL], capture_output=True).returncode == 0
    return when, loaded
