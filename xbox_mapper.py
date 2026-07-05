"""
Xbox Controller Emulator v0.2
Maps DualSense inputs to a virtual Xbox 360 controller using vgamepad.
Now supports custom button remapping and per-stick dead zones.
"""

import vgamepad as vg
from dualsense import DualSenseState

# Xbox button name -> vgamepad constant
XBOX_BUTTON_LOOKUP = {
    "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    "LB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    "RB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "LS": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    "RS": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    "BACK": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    "START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    "GUIDE": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
    "DPAD_UP": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    "DPAD_DOWN": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    "DPAD_LEFT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    "DPAD_RIGHT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
}

DPAD_MAP = {
    "Up": ["DPAD_UP"],
    "Down": ["DPAD_DOWN"],
    "Left": ["DPAD_LEFT"],
    "Right": ["DPAD_RIGHT"],
    "Up-Right": ["DPAD_UP", "DPAD_RIGHT"],
    "Up-Left": ["DPAD_UP", "DPAD_LEFT"],
    "Down-Right": ["DPAD_DOWN", "DPAD_RIGHT"],
    "Down-Left": ["DPAD_DOWN", "DPAD_LEFT"],
}


class XboxMapper:
    """Maps DualSense state to a virtual Xbox 360 controller."""

    def __init__(self, config=None):
        self.gamepad = None
        self.config = config or {}
        self.deadzone_left = self.config.get("deadzone_left", 0.08)
        self.deadzone_right = self.config.get("deadzone_right", 0.08)
        self.invert_left_y = self.config.get("invert_left_y", False)
        self.invert_right_y = self.config.get("invert_right_y", False)
        self.button_map = self.config.get("button_map", {})

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

    def apply_deadzone(self, value, deadzone):
        """Apply deadzone to stick values. Input: -1 to 1, Output: -1 to 1."""
        if abs(value) < deadzone:
            return 0.0
        sign = 1 if value > 0 else -1
        return sign * (abs(value) - deadzone) / (1 - deadzone)

    def press_xbox_button(self, xbox_name):
        """Press an Xbox button by its string name."""
        btn = XBOX_BUTTON_LOOKUP.get(xbox_name)
        if btn:
            self.gamepad.press_button(button=btn)

    def update(self, state: DualSenseState):
        """Push current DualSense state to the virtual Xbox controller."""
        if not self.gamepad:
            return

        # Reset all inputs
        self.gamepad.reset()

        # Map sticks with per-stick dead zones
        lx = self.apply_deadzone(state.left_stick_x, self.deadzone_left)
        ly = self.apply_deadzone(state.left_stick_y, self.deadzone_left)
        rx = self.apply_deadzone(state.right_stick_x, self.deadzone_right)
        ry = self.apply_deadzone(state.right_stick_y, self.deadzone_right)

        # Apply Y-axis inversion
        ly_mult = 1 if self.invert_left_y else -1
        ry_mult = 1 if self.invert_right_y else -1

        self.gamepad.left_joystick_float(x_value_float=lx, y_value_float=ly * ly_mult)
        self.gamepad.right_joystick_float(x_value_float=rx, y_value_float=ry * ry_mult)

        # Map triggers
        self.gamepad.left_trigger_float(value_float=state.l2_trigger)
        self.gamepad.right_trigger_float(value_float=state.r2_trigger)

        # Map buttons using custom remapping
        for ds_btn in ["cross", "circle", "square", "triangle",
                       "l1", "r1", "l3", "r3",
                       "share", "options", "ps_button", "touchpad"]:
            if getattr(state, ds_btn, False):
                xbox_target = self.button_map.get(ds_btn)
                if xbox_target:
                    self.press_xbox_button(xbox_target)

        # Map D-Pad (always direct, not remappable)
        dpad_buttons = DPAD_MAP.get(state.dpad, [])
        for btn_name in dpad_buttons:
            self.press_xbox_button(btn_name)

        # Send the update
        self.gamepad.update()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
