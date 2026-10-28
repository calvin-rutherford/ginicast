"""Offline checks only: presence is never evidence of remote validity."""
import os
from importlib.metadata import PackageNotFoundError, version

from ginicast_data.registry import Registry

DEPENDENCIES = ("requests", "pandas", "PyYAML", "python-dotenv", "tenacity")


def check_offline() -> tuple[list[str], int]:
    messages = []
    failures = 0
    for dependency in DEPENDENCIES:
        try:
            messages.append(f"PASS dependency {dependency}: {version(dependency)}")
        except PackageNotFoundError:
            messages.append(f"FAIL dependency {dependency}: missing")
            failures += 1
    try:
        registry = Registry()
        messages.append(f"PASS config structure: {len(registry.get_all_metrics())} metrics, "
                        f"{len(registry.get_core_metrics())} core")
        messages.append("UNVERIFIED source series definitions, units, and data provenance")
    except Exception as exc:
        messages.append(f"FAIL config: {type(exc).__name__}")
        failures += 1
    for name, required in (("FRED_API_KEY", True), ("BLS_API_KEY", False)):
        present = bool(os.getenv(name)) and not os.getenv(name, "").startswith("your_")
        messages.append(f"INFO {name}: {'present' if present else 'absent or placeholder'} "
                        f"({'required for FRED pulls' if required else 'optional'}; validity unverified)")
    messages.append("UNVERIFIED remote credentials, network, API availability, and coverage; no requests made")
    messages.append("Offline checks completed; exit status covers config/dependencies only")
    return messages, 1 if failures else 0
