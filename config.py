"""
Configuration Manager
Handles saving/loading button remaps, dead zones, and profiles as JSON.
"""

import json
import os

DEFAULT_CONFIG_PATH = "config.json"

# All remappable DualSense buttons
DS_BUTTONS = [
    "cross", "circle", "square", "triangle",
    "l1", "r1", "l3", "r3",
    "share", "options", "ps_button", "touchpad",
]

# All Xbox targets a button can map to
XBOX_TARGETS = [
    "A", "B", "X", "Y",
    "LB", "RB", "LS", "RS",
    "BACK", "START", "GUIDE",
    "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT",
]

# Default DualSense -> Xbox mapping
DEFAULT_BUTTON_MAP = {
    "cross": "A",
    "circle": "B",
    "square": "X",
    "triangle": "Y",
    "l1": "LB",
    "r1": "RB",
    "l3": "LS",
    "r3": "RS",
    "share": "BACK",
    "options": "START",
    "ps_button": "GUIDE",
    "touchpad": None,
}

DEFAULT_CONFIG = {
    "version": "0.2",
    "deadzone_left": 0.08,
    "deadzone_right": 0.08,
    "trigger_threshold": 0.0,
    "invert_left_y": False,
    "invert_right_y": False,
    "button_map": DEFAULT_BUTTON_MAP.copy(),
}


def load_config(path=DEFAULT_CONFIG_PATH):
    """Load config from JSON file. Returns default config if file doesn't exist."""
    if not os.path.exists(path):
        return DEFAULT_CONFIG.copy()

    try:
        with open(path, "r") as f:
            config = json.load(f)

        # Fill in any missing keys with defaults
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value

        # Fill in any missing button mappings
        for btn in DS_BUTTONS:
            if btn not in config["button_map"]:
                config["button_map"][btn] = DEFAULT_BUTTON_MAP.get(btn)

        return config

    except (json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Config file corrupted, using defaults. ({e})")
        return DEFAULT_CONFIG.copy()


def save_config(config, path=DEFAULT_CONFIG_PATH):
    """Save config to JSON file."""
    with open(path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Config saved to {path}")


def print_config(config):
    """Display current config in a readable format."""
    print("\n  Current Configuration")
    print("  " + "=" * 38)
    print(f"  Left stick deadzone:  {config['deadzone_left']:.0%}")
    print(f"  Right stick deadzone: {config['deadzone_right']:.0%}")
    print(f"  Trigger threshold:    {config['trigger_threshold']:.0%}")
    print(f"  Invert left Y:        {'Yes' if config['invert_left_y'] else 'No'}")
    print(f"  Invert right Y:       {'Yes' if config['invert_right_y'] else 'No'}")
    print()
    print("  Button Mapping:")
    print("  " + "-" * 38)
    print(f"  {'DualSense':<15} {'Xbox 360':<15}")
    print("  " + "-" * 38)
    for ds_btn, xbox_btn in config["button_map"].items():
        xbox_display = xbox_btn if xbox_btn else "(unmapped)"
        print(f"  {ds_btn:<15} {xbox_display:<15}")
    print()


def interactive_remap(config):
    """Interactive CLI for remapping buttons."""
    print("\n  Button Remapping")
    print("  " + "=" * 38)
    print("  Type the DualSense button to remap,")
    print("  then choose the Xbox target.")
    print("  Type 'done' when finished.\n")

    print("  DualSense buttons:", ", ".join(DS_BUTTONS))
    print("  Xbox targets:", ", ".join(XBOX_TARGETS))
    print()

    while True:
        ds_input = input("  DualSense button (or 'done'): ").strip().lower()

        if ds_input == "done":
            break

        if ds_input not in DS_BUTTONS:
            print(f"  Unknown button '{ds_input}'. Options: {', '.join(DS_BUTTONS)}")
            continue

        current = config["button_map"].get(ds_input, "None")
        print(f"  Currently mapped to: {current}")

        xbox_input = input("  New Xbox target (or 'none' to unmap): ").strip().upper()

        if xbox_input == "NONE":
            config["button_map"][ds_input] = None
            print(f"  {ds_input} -> unmapped\n")
        elif xbox_input in XBOX_TARGETS:
            config["button_map"][ds_input] = xbox_input
            print(f"  {ds_input} -> {xbox_input}\n")
        else:
            print(f"  Unknown target '{xbox_input}'. Options: {', '.join(XBOX_TARGETS)}")
            continue

    return config


def interactive_deadzone(config):
    """Interactive CLI for adjusting dead zones."""
    print("\n  Dead Zone Settings")
    print("  " + "=" * 38)
    print(f"  Current left stick:  {config['deadzone_left']:.0%}")
    print(f"  Current right stick: {config['deadzone_right']:.0%}")
    print()

    try:
        left = input("  New left deadzone (0-50, or Enter to keep): ").strip()
        if left:
            val = int(left) / 100.0
            if 0 <= val <= 0.5:
                config["deadzone_left"] = val
                print(f"  Left deadzone set to {val:.0%}")
            else:
                print("  Out of range, keeping current value.")

        right = input("  New right deadzone (0-50, or Enter to keep): ").strip()
        if right:
            val = int(right) / 100.0
            if 0 <= val <= 0.5:
                config["deadzone_right"] = val
                print(f"  Right deadzone set to {val:.0%}")
            else:
                print("  Out of range, keeping current value.")

    except ValueError:
        print("  Invalid input, keeping current values.")

    return config
