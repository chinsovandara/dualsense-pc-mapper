"""
DualSense Controller Reader
Handles USB/Bluetooth connection and input parsing for the PS5 DualSense controller.
"""

import hid
import time

# Sony DualSense identifiers
VENDOR_ID = 0x054C
PRODUCT_ID_DUALSENSE = 0x0CE6
PRODUCT_ID_DUALSENSE_EDGE = 0x0DF2

DPAD_DIRECTIONS = {
    0: "Up",
    1: "Up-Right",
    2: "Right",
    3: "Down-Right",
    4: "Down",
    5: "Down-Left",
    6: "Left",
    7: "Up-Left",
    8: "Released",
}


class DualSenseState:
    """Holds the current state of all DualSense inputs."""

    def __init__(self):
        # Sticks (0.0 to 1.0, 0.5 = center)
        self.left_stick_x = 0.5
        self.left_stick_y = 0.5
        self.right_stick_x = 0.5
        self.right_stick_y = 0.5

        # Triggers (0.0 to 1.0)
        self.l2_trigger = 0.0
        self.r2_trigger = 0.0

        # D-Pad
        self.dpad = "Released"

        # Face buttons
        self.cross = False
        self.circle = False
        self.square = False
        self.triangle = False

        # Shoulder buttons
        self.l1 = False
        self.r1 = False

        # Stick clicks
        self.l3 = False
        self.r3 = False

        # System buttons
        self.share = False
        self.options = False
        self.ps_button = False
        self.touchpad = False
        self.mute = False

    def __str__(self):
        pressed = []
        for btn in [
            "cross", "circle", "square", "triangle",
            "l1", "r1", "l3", "r3",
            "share", "options", "ps_button", "touchpad", "mute",
        ]:
            if getattr(self, btn):
                pressed.append(btn.upper())

        lines = [
            f"  L-Stick: ({self.left_stick_x:+.2f}, {self.left_stick_y:+.2f})",
            f"  R-Stick: ({self.right_stick_x:+.2f}, {self.right_stick_y:+.2f})",
            f"  L2: {self.l2_trigger:.2f}  R2: {self.r2_trigger:.2f}",
            f"  D-Pad: {self.dpad}",
            f"  Buttons: {', '.join(pressed) if pressed else 'None'}",
        ]
        return "\n".join(lines)


class DualSense:
    """Manages connection and input reading from a DualSense controller."""

    def __init__(self):
        self.device = None
        self.is_bluetooth = False
        self.state = DualSenseState()

    @staticmethod
    def find_controllers():
        """Scan for connected DualSense controllers."""
        controllers = []
        for dev in hid.enumerate(VENDOR_ID):
            if dev["product_id"] in (PRODUCT_ID_DUALSENSE, PRODUCT_ID_DUALSENSE_EDGE):
                controllers.append(dev)
        return controllers

    def connect(self, device_info=None):
        """Connect to a DualSense controller."""
        if device_info is None:
            controllers = self.find_controllers()
            if not controllers:
                raise ConnectionError(
                    "No DualSense controller found!\n"
                    "Make sure your controller is:\n"
                    "  - Connected via USB cable, OR\n"
                    "  - Paired via Bluetooth in Windows settings"
                )
            device_info = controllers[0]

        self.device = hid.device()
        self.device.open_path(device_info["path"])

        # Detect connection type
        if device_info.get("interface_number", -1) == -1:
            self.is_bluetooth = True
        else:
            self.is_bluetooth = False

        self.device.set_nonblocking(True)

        model = "DualSense Edge" if device_info["product_id"] == PRODUCT_ID_DUALSENSE_EDGE else "DualSense"
        connection = "Bluetooth" if self.is_bluetooth else "USB"
        print(f"Connected to {model} via {connection}")

        return True

    def disconnect(self):
        """Disconnect from the controller."""
        if self.device:
            self.device.close()
            self.device = None
            print("Controller disconnected.")

    def read(self):
        """Read and parse the latest input report. Returns True if data was read."""
        if not self.device:
            return False

        data = self.device.read(78)
        if not data:
            return False

        # Bluetooth reports have a different offset
        offset = 1 if self.is_bluetooth else 0

        self._parse_report(data, offset)
        return True

    def _parse_report(self, data, offset):
        """Parse a raw input report into controller state."""
        s = self.state

        # Skip report ID (byte 0), data starts at byte 1
        base = offset + 1

        # Analog sticks - raw 0-255, convert to -1.0 to 1.0
        s.left_stick_x = round((data[base + 0] / 255.0) * 2 - 1, 3)
        s.left_stick_y = round((data[base + 1] / 255.0) * 2 - 1, 3)
        s.right_stick_x = round((data[base + 2] / 255.0) * 2 - 1, 3)
        s.right_stick_y = round((data[base + 3] / 255.0) * 2 - 1, 3)

        # Triggers - raw 0-255, convert to 0.0 to 1.0
        s.l2_trigger = round(data[base + 4] / 255.0, 3)
        s.r2_trigger = round(data[base + 5] / 255.0, 3)

        # Buttons byte 1 (base + 7)
        buttons1 = data[base + 7]

        # D-Pad is the lower 4 bits
        dpad_val = buttons1 & 0x0F
        s.dpad = DPAD_DIRECTIONS.get(dpad_val, "Released")

        # Face buttons are the upper 4 bits
        s.square = bool(buttons1 & 0x10)
        s.cross = bool(buttons1 & 0x20)
        s.circle = bool(buttons1 & 0x40)
        s.triangle = bool(buttons1 & 0x80)

        # Buttons byte 2 (base + 8)
        buttons2 = data[base + 8]
        s.l1 = bool(buttons2 & 0x01)
        s.r1 = bool(buttons2 & 0x02)
        s.share = bool(buttons2 & 0x10)
        s.options = bool(buttons2 & 0x20)
        s.l3 = bool(buttons2 & 0x40)
        s.r3 = bool(buttons2 & 0x80)

        # Buttons byte 3 (base + 9)
        buttons3 = data[base + 9]
        s.ps_button = bool(buttons3 & 0x01)
        s.touchpad = bool(buttons3 & 0x02)
        s.mute = bool(buttons3 & 0x04)

    def set_led_color(self, red, green, blue):
        """Set the light bar color (0-255 per channel). USB only."""
        if not self.device:
            return False

        if self.is_bluetooth:
            return self._set_led_bluetooth(red, green, blue)

        # USB output report: 48 bytes, report ID 0x02
        report = bytearray(48)
        report[0] = 0x02   # Report ID
        report[1] = 0xFF   # Flags 0: enable all features
        report[2] = 0x04   # Flags 1: enable lightbar
        report[45] = min(255, max(0, int(red)))
        report[46] = min(255, max(0, int(green)))
        report[47] = min(255, max(0, int(blue)))

        self.device.write(bytes(report))
        return True

    def _set_led_bluetooth(self, red, green, blue):
        """Set LED color over Bluetooth (different report format)."""
        try:
            report = bytearray(78)
            report[0] = 0x31   # BT report ID
            report[1] = 0x02   # Sequence tag
            report[2] = 0xFF   # Flags 0
            report[3] = 0x04   # Flags 1: lightbar
            report[46] = min(255, max(0, int(red)))
            report[47] = min(255, max(0, int(green)))
            report[48] = min(255, max(0, int(blue)))

            # Bluetooth needs CRC32 at the end
            import binascii
            crc = binascii.crc32(bytes(report[:-4]))
            report[-4:] = crc.to_bytes(4, byteorder="little")

            self.device.write(bytes(report))
            return True
        except Exception:
            return False

    def set_rumble(self, left_motor, right_motor):
        """Set rumble intensity (0-255 per motor). USB only for now."""
        if not self.device or self.is_bluetooth:
            return False

        report = bytearray(48)
        report[0] = 0x02
        report[1] = 0x03   # Flags 0: enable rumble motors
        report[2] = 0x00
        report[3] = min(255, max(0, int(right_motor)))
        report[4] = min(255, max(0, int(left_motor)))

        self.device.write(bytes(report))
        return True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.disconnect()
