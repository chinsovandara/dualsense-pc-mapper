"""
Xbox Controller Emulator
Maps DualSense inputs to a virtual Xbox 360 controller using vgamepad.
"""

import vgamepad as vg
from dualsense import DualSenseState

# DualSense → Xbox button mapping
BUTTON_MAP = {
    "cross": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "circle": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "square": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    "triangle": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    "l1": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    "r1": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "l3": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    "r3": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    "share": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    "options": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    "ps_button": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
}

DPAD_MAP = {
    "Up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    "Down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    "Left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    "Right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    "Up-Right": [vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT],
    "Up-Left": [vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT],
    "Down-Right": [vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT],
    "Down-Left": [vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT],
}


class XboxMapper:
    """Maps DualSense state to a virtual Xbox 360 controller."""

    def __init__(self):
        self.gamepad = None
        self.deadzone = 0.08  # Ignore tiny stick movements

    def start(self):
        """Create the virtual Xbox controller."""
        self.gamepad = vg.VX360Gamepad()
        print("Virtual Xbox 360 controller created!")
        print("Windows should now see an Xbox controller.")
        return True

    def stop(self):
        """Remove the virtual controller."""
        if self.gamepad:
            self.gamepad.reset()
            self.gamepad.update()
            self.gamepad = None
            print("Virtual controller removed.")

    def apply_deadzone(self, value):
        """Apply deadzone to stick values. Input: -1 to 1, Output: -1 to 1."""
        if abs(value) < self.deadzone:
            return 0.0
        # Scale remaining range to full 0-1
        sign = 1 if value > 0 else -1
        return sign * (abs(value) - self.deadzone) / (1 - self.deadzone)

    def update(self, state: DualSenseState):
        """Push current DualSense state to the virtual Xbox controller."""
        if not self.gamepad:
            return

        # Reset all inputs
        self.gamepad.reset()

        # Map sticks (vgamepad expects -1.0 to 1.0 for X, -1.0 to 1.0 for Y)
        lx = self.apply_deadzone(state.left_stick_x)
        ly = self.apply_deadzone(-state.left_stick_y)  # Invert Y axis
        rx = self.apply_deadzone(state.right_stick_x)
        ry = self.apply_deadzone(-state.right_stick_y)  # Invert Y axis

        self.gamepad.left_joystick_float(x_value_float=lx, y_value_float=ly)
        self.gamepad.right_joystick_float(x_value_float=rx, y_value_float=ry)

        # Map triggers (0.0 to 1.0)
        self.gamepad.left_trigger_float(value_float=state.l2_trigger)
        self.gamepad.right_trigger_float(value_float=state.r2_trigger)

        # Map face + system buttons
        for ds_btn, xbox_btn in BUTTON_MAP.items():
            if getattr(state, ds_btn, False):
                self.gamepad.press_button(button=xbox_btn)

        # Map D-Pad
        dpad_val = DPAD_MAP.get(state.dpad)
        if dpad_val:
            if isinstance(dpad_val, list):
                for btn in dpad_val:
                    self.gamepad.press_button(button=btn)
            else:
                self.gamepad.press_button(button=dpad_val)

        # Send the update
        self.gamepad.update()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
