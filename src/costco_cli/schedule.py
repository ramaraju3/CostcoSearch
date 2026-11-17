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


def install(hour, minute, weekday=None):
    """Run daily, or once a week when weekday (0 = Sunday ... 6) is given."""
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    cmd = _costco_command()
    plist = {
        "Label": LABEL,
        "ProgramArguments": cmd + ["daily"],
        "StartCalendarInterval": {"Hour": hour, "Minute": minute, **({"Weekday": weekday} if weekday is not None else {})},
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
    when = (f"{FULL_DAYS[t['Weekday'] % 7]}s" if "Weekday" in t else "Daily") + f" at {t['Hour']:02d}:{t['Minute']:02d}"
    loaded = subprocess.run(["launchctl", "list", LABEL], capture_output=True).returncode == 0
    return when, loaded
