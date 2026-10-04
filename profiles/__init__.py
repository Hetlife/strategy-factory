"""Asset-class profiles for factory.py (CE-1-02).

A profile is a JSON file profiles/<name>.json holding the universe, benchmark,
calendar flag, cost/tax constants and state dir for one asset class. factory.py
selects one with the FACTORY_PROFILE environment variable (default
"equity_nse", which reproduces the pre-profile behaviour exactly).

The equity_nse profile must NEVER carry rules, ladder or cost_per_side: those
financial risk parameters stay literals in factory.py. Other profiles may carry
such keys as inert proposals; nothing here reads them.
"""
import json
import os

DEFAULT_PROFILE = "equity_nse"
FORBIDDEN_EQUITY_KEYS = ("rules", "ladder", "cost_per_side")
_HERE = os.path.dirname(os.path.abspath(__file__))


class ProfileError(ValueError):
    """Unknown, unreadable or invalid profile."""


def check_equity_forbidden_keys(profile):
    bad = sorted(k for k in profile if str(k).lower() in FORBIDDEN_EQUITY_KEYS)
    if bad:
        raise ProfileError(
            f"profile '{DEFAULT_PROFILE}' must not carry {bad}: RULES, LADDER "
            f"and COST_PER_SIDE are financial parameters that stay literal "
            f"in factory.py")


def load_profile(name, profiles_dir=None):
    """Return the profile dict for `name`, or raise ProfileError."""
    if not isinstance(name, str) or not name or os.sep in name or name.startswith("."):
        raise ProfileError(f"invalid profile name {name!r}")
    path = os.path.join(profiles_dir or _HERE, name + ".json")
    if not os.path.isfile(path):
        raise ProfileError(f"unknown profile '{name}': no file {path}")
    try:
        with open(path) as fh:
            profile = json.load(fh)
    except (OSError, ValueError) as e:
        raise ProfileError(f"cannot read profile '{name}' ({path}): {e}") from e
    if not isinstance(profile, dict):
        raise ProfileError(f"profile '{name}' must be a JSON object")
    if name == DEFAULT_PROFILE:
        check_equity_forbidden_keys(profile)
    return profile
