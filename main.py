"""
DualSense PC Mapper v0.3
========================
Free & open-source PS5 controller mapper for Windows.
Reads your DualSense and emulates an Xbox 360 controller.

Usage:
    python main.py              Start mapping with current config
    python main.py --gui        Launch GUI with controller visualization
    python main.py --test       Test mode (show raw inputs)
    python main.py --config     Configure button remapping & dead zones
    python main.py --show       Show current config

Requirements:
    pip install hidapi vgamepad
"""

import sys
import time
import os
from dualsense import DualSense
from xbox_mapper import XboxMapper
from config import load_config, save_config, print_config, interactive_remap, interactive_deadzone

LOGO = r"""
  ____              _ ____
 |  _ \ _   _  __ _| / ___|  ___ _ __  ___  ___
 | | | | | | |/ _` | \___ \ / _ \ '_ \/ __|/ _ \
 | |_| | |_| | (_| | |___) |  __/ | | \__ \  __/
 |____/ \__,_|\__,_|_|____/ \___|_| |_|___/\___|
          PC Mapper v0.3 | Free & Open Source
  github.com/chinsovandara/dualsense-pc-mapper
"""


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def run_test_mode():
    """Test mode: show live controller inputs without Xbox emulation."""
    print(LOGO)
    print("  [TEST MODE] Showing raw DualSense inputs.\n")

    ds = DualSense()

    print("  Scanning for DualSense controllers...")
    controllers = DualSense.find_controllers()

    if not controllers:
        print("\n  No DualSense controller found!")
        print("    - Connect via USB cable, or")
        print("    - Pair via Bluetooth in Windows Settings")
        print("\n  Press Enter to exit...")
        input()
        return

    print(f"  Found {len(controllers)} controller(s)\n")
    ds.connect(controllers[0])
    print("\n  Reading inputs... Press Ctrl+C to stop.\n")
    time.sleep(0.5)
    clear_screen()

    try:
        while True:
            if ds.read():
                sys.stdout.write("\033[H")
                pad = " " * 20
                print(f"  DualSense PC Mapper - TEST MODE{pad}")
                print(f"  {'=' * 42}{pad}")
                for row in str(ds.state).split("\n"):
                    print(f"{row}{pad}")
                print(f"  {'=' * 42}{pad}")
                print(f"\n  Press Ctrl+C to stop.{pad}")
                sys.stdout.flush()
            time.sleep(0.008)
    except KeyboardInterrupt:
        print("\n\n  Stopped.")
    finally:
        ds.disconnect()


def run_config():
    """Interactive configuration mode."""
    print(LOGO)
    print("  [CONFIG MODE] Set up your controller.\n")

    config = load_config()
    print_config(config)

    while True:
        print("  Options:")
        print("    1. Remap buttons")
        print("    2. Adjust dead zones")
        print("    3. Show current config")
        print("    4. Reset to defaults")
        print("    5. Save and exit")
        print()

        choice = input("  Choose (1-5): ").strip()

        if choice == "1":
            config = interactive_remap(config)
        elif choice == "2":
            config = interactive_deadzone(config)
        elif choice == "3":
            print_config(config)
        elif choice == "4":
            from config import DEFAULT_CONFIG
            config = DEFAULT_CONFIG.copy()
            print("\n  Reset to defaults.\n")
        elif choice == "5":
            save_config(config)
            print("  Done! Run 'python main.py' to use your config.\n")
            break
        else:
            print("  Invalid choice.\n")


def run_mapper():
    """Main mode: map DualSense to virtual Xbox controller."""
    config = load_config()

    print(LOGO)
    print("  [MAPPER MODE] DualSense -> Xbox 360\n")

    ds = DualSense()
    mapper = XboxMapper(config)

    print("  Scanning for DualSense controllers...")
    controllers = DualSense.find_controllers()

    if not controllers:
        print("\n  No DualSense controller found!")
        print("    - Connect via USB cable, or")
        print("    - Pair via Bluetooth in Windows Settings")
        print("\n  Press Enter to exit...")
        input()
        return

    print(f"  Found {len(controllers)} controller(s)")
    ds.connect(controllers[0])

    print()
    mapper.start()

    # Show active config summary
    custom_maps = [
        f"{ds_btn}->{xbox_btn}"
        for ds_btn, xbox_btn in config.get("button_map", {}).items()
        if xbox_btn and config.get("button_map", {}).get(ds_btn) != {
            "cross": "A", "circle": "B", "square": "X", "triangle": "Y",
            "l1": "LB", "r1": "RB", "l3": "LS", "r3": "RS",
            "share": "BACK", "options": "START", "ps_button": "GUIDE",
        }.get(ds_btn)
    ]

    print()
    print("  " + "=" * 42)
    print("    Mapping is ACTIVE!")
    print("    Your DualSense now works as Xbox 360.")
    print(f"    Dead zones: L={config.get('deadzone_left', 0.08):.0%} R={config.get('deadzone_right', 0.08):.0%}")
    if custom_maps:
        print(f"    Custom remaps: {', '.join(custom_maps)}")
    print("    Press Ctrl+C to stop.")
    print("  " + "=" * 42 + "\n")

    poll_count = 0
    try:
        while True:
            if ds.read():
                mapper.update(ds.state)
                poll_count += 1

                if poll_count % 250 == 0:
                    active_buttons = []
                    for btn in ["cross", "circle", "square", "triangle",
                                "l1", "r1", "share", "options"]:
                        if getattr(ds.state, btn):
                            active_buttons.append(btn.upper())

                    status = ", ".join(active_buttons) if active_buttons else "idle"
                    sys.stdout.write(f"\r  Status: {status:<40}")
                    sys.stdout.flush()

            time.sleep(0.004)
    except KeyboardInterrupt:
        print("\n\n  Shutting down...")
    finally:
        mapper.stop()
        ds.disconnect()
        print("  Thanks for using DualSense PC Mapper!")


def main():
    if "--gui" in sys.argv:
        from gui import launch_gui
        launch_gui()
    elif "--test" in sys.argv:
        run_test_mode()
    elif "--config" in sys.argv:
        run_config()
    elif "--show" in sys.argv:
        config = load_config()
        print(LOGO)
        print_config(config)
    else:
        run_mapper()


if __name__ == "__main__":
    main()
