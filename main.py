"""
DualSense PC Mapper v0.1
========================
Free & open-source PS5 controller mapper for Windows.
Reads your DualSense and emulates an Xbox 360 controller.

Usage:
    python main.py          → Connect and start mapping
    python main.py --test   → Test mode (show inputs without Xbox emulation)

Requirements:
    pip install hidapi vgamepad
"""

import sys
import time
import os
from dualsense import DualSense
from xbox_mapper import XboxMapper

LOGO = r"""
╔══════════════════════════════════════════╗
║     🎮  DualSense PC Mapper  v0.1       ║
║     Free & Open Source                   ║
║     github.com/YOUR_USERNAME/ds-mapper   ║
╚══════════════════════════════════════════╝
"""


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def run_test_mode():
    """Test mode: show live controller inputs without Xbox emulation."""
    print(LOGO)
    print("[TEST MODE] Showing raw DualSense inputs.\n")

    ds = DualSense()

    # Scan for controllers
    print("Scanning for DualSense controllers...")
    controllers = DualSense.find_controllers()

    if not controllers:
        print("\n❌ No DualSense controller found!")
        print("   - Connect via USB cable, or")
        print("   - Pair via Bluetooth in Windows Settings")
        print("\nPress Enter to exit...")
        input()
        return

    print(f"✅ Found {len(controllers)} controller(s)\n")

    # Connect
    ds.connect(controllers[0])
    print("\nReading inputs... Press Ctrl+C to stop.\n")
    time.sleep(0.5)
    clear_screen()

    try:
        while True:
            if ds.read():
                # Move cursor to top-left and redraw
                sys.stdout.write("\033[H")
                line = "─" * 42
                pad = " " * 20  # pad to clear leftover characters
                print(f"  🎮 DualSense PC Mapper - TEST MODE{pad}")
                print(f"{line}{pad}")
                for row in str(ds.state).split("\n"):
                    print(f"{row}{pad}")
                print(f"{line}{pad}")
                print(f"\n  Press Ctrl+C to stop.{pad}")
                sys.stdout.flush()
            time.sleep(0.008)  # ~120Hz polling
    except KeyboardInterrupt:
        print("\n\nStopped.")
    finally:
        ds.disconnect()


def run_mapper():
    """Main mode: map DualSense to virtual Xbox controller."""
    print(LOGO)
    print("[MAPPER MODE] DualSense → Xbox 360 emulation.\n")

    ds = DualSense()
    mapper = XboxMapper()

    # Scan for controllers
    print("Scanning for DualSense controllers...")
    controllers = DualSense.find_controllers()

    if not controllers:
        print("\n❌ No DualSense controller found!")
        print("   - Connect via USB cable, or")
        print("   - Pair via Bluetooth in Windows Settings")
        print("\nPress Enter to exit...")
        input()
        return

    print(f"✅ Found {len(controllers)} controller(s)")

    # Connect DualSense
    ds.connect(controllers[0])

    # Create virtual Xbox controller
    print()
    mapper.start()

    print("\n" + "═" * 42)
    print("  Mapping is ACTIVE!")
    print("  Your DualSense now works as Xbox 360.")
    print("  Press Ctrl+C to stop.")
    print("═" * 42 + "\n")

    poll_count = 0
    try:
        while True:
            if ds.read():
                mapper.update(ds.state)
                poll_count += 1

                # Print status every ~2 seconds
                if poll_count % 250 == 0:
                    active_buttons = []
                    for btn in ["cross", "circle", "square", "triangle",
                                "l1", "r1", "share", "options"]:
                        if getattr(ds.state, btn):
                            active_buttons.append(btn.upper())

                    status = ", ".join(active_buttons) if active_buttons else "idle"
                    sys.stdout.write(f"\r  Status: {status:<40}")
                    sys.stdout.flush()

            time.sleep(0.004)  # ~250Hz polling for low latency
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        mapper.stop()
        ds.disconnect()
        print("Done. Thanks for using DualSense PC Mapper!")


def main():
    if "--test" in sys.argv:
        run_test_mode()
    else:
        run_mapper()


if __name__ == "__main__":
    main()
