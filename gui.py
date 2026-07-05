"""
DualSense PC Mapper GUI v0.3
Visual controller interface with live input display and profile management.
Uses tkinter (built-in, no extra install needed).
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import math
import json
import os
from dualsense import DualSense
from xbox_mapper import XboxMapper
from config import (
    load_config, save_config, print_config,
    DEFAULT_CONFIG, DS_BUTTONS, XBOX_TARGETS,
    DEFAULT_BUTTON_MAP,
)

PROFILES_DIR = "profiles"


class ControllerCanvas(tk.Canvas):
    """Draws a live visualization of the DualSense controller."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#1a1a2e", highlightthickness=0, **kwargs)
        self.state = None

    def update_state(self, state):
        self.state = state
        self.draw()

    def draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            return

        cx, cy = w // 2, h // 2
        s = self.state

        # Controller body
        self.create_rounded_rect(cx - 180, cy - 100, cx + 180, cy + 100, 30, fill="#2d2d44", outline="#3d3d5c", width=2)

        # Left stick
        lx_off = (s.left_stick_x * 18) if s else 0
        ly_off = (s.left_stick_y * 18) if s else 0
        self.create_oval(cx - 120 - 22, cy - 20 - 22, cx - 120 + 22, cy - 20 + 22, fill="#1a1a2e", outline="#3d3d5c", width=2)
        self.create_oval(
            cx - 120 + lx_off - 14, cy - 20 + ly_off - 14,
            cx - 120 + lx_off + 14, cy - 20 + ly_off + 14,
            fill="#4a6fa5" if not (s and s.l3) else "#6aef8a", outline="#5a8fbf", width=2
        )

        # Right stick
        rx_off = (s.right_stick_x * 18) if s else 0
        ry_off = (s.right_stick_y * 18) if s else 0
        self.create_oval(cx + 60 - 22, cy + 20 - 22, cx + 60 + 22, cy + 20 + 22, fill="#1a1a2e", outline="#3d3d5c", width=2)
        self.create_oval(
            cx + 60 + rx_off - 14, cy + 20 + ry_off - 14,
            cx + 60 + rx_off + 14, cy + 20 + ry_off + 14,
            fill="#4a6fa5" if not (s and s.r3) else "#6aef8a", outline="#5a8fbf", width=2
        )

        # D-Pad
        dpad_cx, dpad_cy = cx - 60, cy + 30
        dpad_dirs = {
            "Up": (0, -14), "Down": (0, 14), "Left": (-14, 0), "Right": (14, 0),
            "Up-Right": (14, -14), "Up-Left": (-14, -14),
            "Down-Right": (14, 14), "Down-Left": (-14, 14),
        }
        # Draw D-Pad cross
        self.create_rectangle(dpad_cx - 6, dpad_cy - 18, dpad_cx + 6, dpad_cy + 18, fill="#2a2a3e", outline="#3d3d5c")
        self.create_rectangle(dpad_cx - 18, dpad_cy - 6, dpad_cx + 18, dpad_cy + 6, fill="#2a2a3e", outline="#3d3d5c")

        if s and s.dpad in dpad_dirs:
            dx, dy = dpad_dirs[s.dpad]
            self.create_oval(dpad_cx + dx - 5, dpad_cy + dy - 5, dpad_cx + dx + 5, dpad_cy + dy + 5, fill="#6aef8a")

        # Face buttons
        btn_cx, btn_cy = cx + 120, cy - 20
        btn_layout = {
            "triangle": (0, -18, "#59c19c"),
            "cross": (0, 18, "#6a8fdf"),
            "circle": (18, 0, "#df6a6a"),
            "square": (-18, 0, "#c77dba"),
        }
        for btn, (bx, by, color) in btn_layout.items():
            is_pressed = s and getattr(s, btn, False)
            fill = color if is_pressed else "#2a2a3e"
            outline_c = color if is_pressed else "#3d3d5c"
            self.create_oval(
                btn_cx + bx - 10, btn_cy + by - 10,
                btn_cx + bx + 10, btn_cy + by + 10,
                fill=fill, outline=outline_c, width=2
            )
            labels = {"triangle": "\u25B3", "cross": "\u2715", "circle": "\u25CB", "square": "\u25A1"}
            self.create_text(btn_cx + bx, btn_cy + by, text=labels[btn], fill="#fff" if is_pressed else "#555", font=("Arial", 8))

        # Shoulder buttons
        l1_color = "#6aef8a" if s and s.l1 else "#2a2a3e"
        r1_color = "#6aef8a" if s and s.r1 else "#2a2a3e"
        self.create_rounded_rect(cx - 160, cy - 105, cx - 80, cy - 88, 6, fill=l1_color, outline="#3d3d5c", width=1)
        self.create_text(cx - 120, cy - 96, text="L1", fill="#fff", font=("Arial", 8, "bold"))
        self.create_rounded_rect(cx + 80, cy - 105, cx + 160, cy - 88, 6, fill=r1_color, outline="#3d3d5c", width=1)
        self.create_text(cx + 120, cy - 96, text="R1", fill="#fff", font=("Arial", 8, "bold"))

        # Triggers (bars)
        l2_val = s.l2_trigger if s else 0
        r2_val = s.r2_trigger if s else 0
        # L2
        self.create_rounded_rect(cx - 160, cy - 125, cx - 80, cy - 110, 4, fill="#1a1a2e", outline="#3d3d5c", width=1)
        if l2_val > 0.01:
            bar_w = int(l2_val * 78)
            self.create_rounded_rect(cx - 159, cy - 124, cx - 159 + bar_w, cy - 111, 3, fill="#e76f51", outline="")
        self.create_text(cx - 120, cy - 117, text=f"L2 {l2_val:.0%}", fill="#fff", font=("Arial", 7))
        # R2
        self.create_rounded_rect(cx + 80, cy - 125, cx + 160, cy - 110, 4, fill="#1a1a2e", outline="#3d3d5c", width=1)
        if r2_val > 0.01:
            bar_w = int(r2_val * 78)
            self.create_rounded_rect(cx + 81, cy - 124, cx + 81 + bar_w, cy - 111, 3, fill="#e76f51", outline="")
        self.create_text(cx + 120, cy - 117, text=f"R2 {r2_val:.0%}", fill="#fff", font=("Arial", 7))

        # System buttons
        share_color = "#6aef8a" if s and s.share else "#2a2a3e"
        options_color = "#6aef8a" if s and s.options else "#2a2a3e"
        ps_color = "#4a6fa5" if s and s.ps_button else "#2a2a3e"
        touchpad_color = "#6aef8a" if s and s.touchpad else "#2a2a3e"

        self.create_oval(cx - 40 - 7, cy - 55 - 7, cx - 40 + 7, cy - 55 + 7, fill=share_color, outline="#3d3d5c")
        self.create_text(cx - 40, cy - 42, text="Share", fill="#888", font=("Arial", 6))

        self.create_oval(cx + 40 - 7, cy - 55 - 7, cx + 40 + 7, cy - 55 + 7, fill=options_color, outline="#3d3d5c")
        self.create_text(cx + 40, cy - 42, text="Options", fill="#888", font=("Arial", 6))

        self.create_oval(cx - 7, cy + 65 - 7, cx + 7, cy + 65 + 7, fill=ps_color, outline="#3d3d5c")
        self.create_text(cx, cy + 80, text="PS", fill="#888", font=("Arial", 6))

        # Touchpad
        self.create_rounded_rect(cx - 30, cy - 75, cx + 30, cy - 55, 6, fill=touchpad_color, outline="#3d3d5c", width=1)
        self.create_text(cx, cy - 65, text="Touchpad", fill="#888" if not (s and s.touchpad) else "#fff", font=("Arial", 7))

        # Connection status
        if s:
            self.create_oval(cx + 155, cy + 85, cx + 165, cy + 95, fill="#4aea8b", outline="")
            self.create_text(cx + 145, cy + 90, text="Connected", fill="#4aea8b", font=("Arial", 8), anchor="e")

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)


class MappingFrame(ttk.Frame):
    """Panel for button remapping and dead zone controls."""

    def __init__(self, parent, config, on_config_change=None):
        super().__init__(parent)
        self.config = config
        self.on_config_change = on_config_change
        self.remap_vars = {}
        self.build_ui()

    def build_ui(self):
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Arial", 11, "bold"))

        # Dead zone controls
        dz_frame = ttk.LabelFrame(self, text="  Dead Zones  ", padding=10)
        dz_frame.pack(fill="x", padx=8, pady=(8, 4))

        ttk.Label(dz_frame, text="Left Stick:").grid(row=0, column=0, sticky="w", pady=2)
        self.left_dz = tk.IntVar(value=int(self.config["deadzone_left"] * 100))
        left_scale = ttk.Scale(dz_frame, from_=0, to=50, variable=self.left_dz, command=lambda v: self._on_dz_change())
        left_scale.grid(row=0, column=1, sticky="ew", padx=(5, 5))
        self.left_dz_label = ttk.Label(dz_frame, text=f"{self.left_dz.get()}%", width=5)
        self.left_dz_label.grid(row=0, column=2)

        ttk.Label(dz_frame, text="Right Stick:").grid(row=1, column=0, sticky="w", pady=2)
        self.right_dz = tk.IntVar(value=int(self.config["deadzone_right"] * 100))
        right_scale = ttk.Scale(dz_frame, from_=0, to=50, variable=self.right_dz, command=lambda v: self._on_dz_change())
        right_scale.grid(row=1, column=1, sticky="ew", padx=(5, 5))
        self.right_dz_label = ttk.Label(dz_frame, text=f"{self.right_dz.get()}%", width=5)
        self.right_dz_label.grid(row=1, column=2)

        dz_frame.columnconfigure(1, weight=1)

        # Button mapping
        map_frame = ttk.LabelFrame(self, text="  Button Mapping  ", padding=10)
        map_frame.pack(fill="both", expand=True, padx=8, pady=4)

        ttk.Label(map_frame, text="DualSense", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(map_frame, text="Xbox 360", font=("Arial", 9, "bold")).grid(row=0, column=1, sticky="w")

        xbox_options = ["(unmapped)"] + XBOX_TARGETS

        for i, ds_btn in enumerate(DS_BUTTONS):
            ttk.Label(map_frame, text=ds_btn).grid(row=i + 1, column=0, sticky="w", pady=1)

            current = self.config["button_map"].get(ds_btn)
            var = tk.StringVar(value=current if current else "(unmapped)")
            self.remap_vars[ds_btn] = var

            combo = ttk.Combobox(map_frame, textvariable=var, values=xbox_options, state="readonly", width=12)
            combo.grid(row=i + 1, column=1, sticky="w", pady=1, padx=(5, 0))
            combo.bind("<<ComboboxSelected>>", lambda e, b=ds_btn: self._on_remap(b))

        map_frame.columnconfigure(1, weight=1)

        # LED Color Control
        led_frame = ttk.LabelFrame(self, text="  LED Light Bar  ", padding=10)
        led_frame.pack(fill="x", padx=8, pady=4)

        # Color presets
        preset_frame = ttk.Frame(led_frame)
        preset_frame.pack(fill="x", pady=(0, 5))

        self.led_colors = [
            ("Blue", "#0000FF", 0, 0, 255),
            ("Red", "#FF0000", 255, 0, 0),
            ("Green", "#00FF00", 0, 255, 0),
            ("Purple", "#8000FF", 128, 0, 255),
            ("Cyan", "#00FFFF", 0, 255, 255),
            ("Orange", "#FF8000", 255, 128, 0),
            ("Pink", "#FF00AA", 255, 0, 170),
            ("White", "#FFFFFF", 255, 255, 255),
            ("Off", "#333333", 0, 0, 0),
        ]

        for i, (name, hex_color, r, g, b) in enumerate(self.led_colors):
            btn = tk.Button(preset_frame, bg=hex_color if name != "Off" else "#333",
                           width=2, height=1, relief="raised", bd=1,
                           command=lambda r=r, g=g, b=b, n=name: self._set_led(r, g, b, n))
            btn.grid(row=0, column=i, padx=1, pady=1)

        self.led_status = ttk.Label(led_frame, text="Color: Default", font=("Arial", 8))
        self.led_status.pack(anchor="w")

        # Custom RGB sliders
        custom_frame = ttk.Frame(led_frame)
        custom_frame.pack(fill="x", pady=(5, 0))

        self.led_r = tk.IntVar(value=0)
        self.led_g = tk.IntVar(value=0)
        self.led_b = tk.IntVar(value=255)

        for label, var, color in [("R", self.led_r, "#ff4444"), ("G", self.led_g, "#44ff44"), ("B", self.led_b, "#4444ff")]:
            row = ttk.Frame(custom_frame)
            row.pack(fill="x", pady=1)
            ttk.Label(row, text=label, width=2, font=("Arial", 8, "bold")).pack(side="left")
            ttk.Scale(row, from_=0, to=255, variable=var, command=lambda v: self._on_rgb_slide()).pack(side="left", fill="x", expand=True, padx=3)

        ttk.Button(custom_frame, text="Apply Custom Color", command=self._apply_custom_led).pack(fill="x", pady=(5, 0))

        self.on_led_change = None  # callback set by main GUI

        # Profile buttons
        prof_frame = ttk.Frame(self, padding=(8, 4))
        prof_frame.pack(fill="x")

        ttk.Button(prof_frame, text="Save Profile", command=self._save_profile).pack(side="left", padx=2)
        ttk.Button(prof_frame, text="Load Profile", command=self._load_profile).pack(side="left", padx=2)
        ttk.Button(prof_frame, text="Reset Defaults", command=self._reset_defaults).pack(side="left", padx=2)

    def _on_dz_change(self):
        self.config["deadzone_left"] = self.left_dz.get() / 100.0
        self.config["deadzone_right"] = self.right_dz.get() / 100.0
        self.left_dz_label.config(text=f"{self.left_dz.get()}%")
        self.right_dz_label.config(text=f"{self.right_dz.get()}%")
        if self.on_config_change:
            self.on_config_change(self.config)

    def _on_remap(self, ds_btn):
        val = self.remap_vars[ds_btn].get()
        self.config["button_map"][ds_btn] = None if val == "(unmapped)" else val
        if self.on_config_change:
            self.on_config_change(self.config)

    def _set_led(self, r, g, b, name="Custom"):
        self.led_r.set(r)
        self.led_g.set(g)
        self.led_b.set(b)
        self.led_status.config(text=f"Color: {name}")
        self.config["led_color"] = [r, g, b]
        if self.on_led_change:
            self.on_led_change(r, g, b)

    def _on_rgb_slide(self):
        pass  # Just updates vars, user clicks Apply

    def _apply_custom_led(self):
        r, g, b = self.led_r.get(), self.led_g.get(), self.led_b.get()
        self._set_led(r, g, b, f"#{r:02x}{g:02x}{b:02x}")

    def _save_profile(self):
        os.makedirs(PROFILES_DIR, exist_ok=True)
        path = filedialog.asksaveasfilename(
            initialdir=PROFILES_DIR,
            defaultextension=".json",
            filetypes=[("JSON Profile", "*.json")],
            title="Save Profile"
        )
        if path:
            self._sync_config()
            save_config(self.config, path)
            messagebox.showinfo("Saved", f"Profile saved to {os.path.basename(path)}")

    def _load_profile(self):
        os.makedirs(PROFILES_DIR, exist_ok=True)
        path = filedialog.askopenfilename(
            initialdir=PROFILES_DIR,
            filetypes=[("JSON Profile", "*.json")],
            title="Load Profile"
        )
        if path:
            self.config = load_config(path)
            self._refresh_ui()
            if self.on_config_change:
                self.on_config_change(self.config)
            messagebox.showinfo("Loaded", f"Profile loaded from {os.path.basename(path)}")

    def _reset_defaults(self):
        if messagebox.askyesno("Reset", "Reset all settings to defaults?"):
            self.config = DEFAULT_CONFIG.copy()
            self.config["button_map"] = DEFAULT_BUTTON_MAP.copy()
            self._refresh_ui()
            if self.on_config_change:
                self.on_config_change(self.config)

    def _sync_config(self):
        self.config["deadzone_left"] = self.left_dz.get() / 100.0
        self.config["deadzone_right"] = self.right_dz.get() / 100.0
        for ds_btn, var in self.remap_vars.items():
            val = var.get()
            self.config["button_map"][ds_btn] = None if val == "(unmapped)" else val

    def _refresh_ui(self):
        self.left_dz.set(int(self.config["deadzone_left"] * 100))
        self.right_dz.set(int(self.config["deadzone_right"] * 100))
        self.left_dz_label.config(text=f"{self.left_dz.get()}%")
        self.right_dz_label.config(text=f"{self.right_dz.get()}%")
        for ds_btn, var in self.remap_vars.items():
            val = self.config["button_map"].get(ds_btn)
            var.set(val if val else "(unmapped)")


class DualSenseGUI:
    """Main GUI application."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DualSense PC Mapper v0.3")
        self.root.geometry("820x520")
        self.root.configure(bg="#1a1a2e")
        self.root.minsize(700, 450)

        self.ds = None
        self.mapper = None
        self.config = load_config()
        self.running = False
        self.polling = False

        self.build_ui()

    def build_ui(self):
        # Top bar
        top = tk.Frame(self.root, bg="#0d1117", height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="🎮 DualSense PC Mapper", bg="#0d1117", fg="#f0f6fc",
                 font=("Arial", 14, "bold")).pack(side="left", padx=15, pady=10)

        self.status_label = tk.Label(top, text="⚪ Disconnected", bg="#0d1117", fg="#8b949e",
                                     font=("Arial", 10))
        self.status_label.pack(side="right", padx=15)

        # Main content
        content = tk.Frame(self.root, bg="#1a1a2e")
        content.pack(fill="both", expand=True, padx=5, pady=5)

        # Left: controller visualization
        left = tk.Frame(content, bg="#1a1a2e")
        left.pack(side="left", fill="both", expand=True)

        self.canvas = ControllerCanvas(left, width=420, height=300)
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # Control buttons
        btn_frame = tk.Frame(left, bg="#1a1a2e")
        btn_frame.pack(fill="x", padx=5, pady=5)

        self.connect_btn = tk.Button(btn_frame, text="Connect Controller", bg="#238636", fg="white",
                                      font=("Arial", 10, "bold"), relief="flat", padx=15, pady=5,
                                      command=self.toggle_connection, cursor="hand2")
        self.connect_btn.pack(side="left", padx=3)

        self.map_btn = tk.Button(btn_frame, text="Start Mapping", bg="#4361ee", fg="white",
                                  font=("Arial", 10, "bold"), relief="flat", padx=15, pady=5,
                                  command=self.toggle_mapping, state="disabled", cursor="hand2")
        self.map_btn.pack(side="left", padx=3)

        self.save_btn = tk.Button(btn_frame, text="Save Config", bg="#e76f51", fg="white",
                                   font=("Arial", 10, "bold"), relief="flat", padx=15, pady=5,
                                   command=self.save_current_config, cursor="hand2")
        self.save_btn.pack(side="right", padx=3)

        # Right: mapping panel (scrollable)
        right = tk.Frame(content, bg="#1a1a2e", width=280)
        right.pack(side="right", fill="y", padx=(0, 5))
        right.pack_propagate(False)

        self.mapping_panel = MappingFrame(right, self.config, on_config_change=self.on_config_change)
        self.mapping_panel.pack(fill="both", expand=True)
        self.mapping_panel.on_led_change = self.on_led_change

    def toggle_connection(self):
        if self.ds:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        try:
            self.ds = DualSense()
            controllers = DualSense.find_controllers()
            if not controllers:
                messagebox.showerror("Not Found", "No DualSense controller found!\n\nConnect via USB or pair via Bluetooth.")
                self.ds = None
                return

            self.ds.connect(controllers[0])
            self.status_label.config(text="🟢 Connected", fg="#4aea8b")
            self.connect_btn.config(text="Disconnect", bg="#e63946")
            self.map_btn.config(state="normal")

            # Start polling input
            self.polling = True
            self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self.poll_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect:\n{e}")
            self.ds = None

    def disconnect(self):
        self.polling = False
        if self.running:
            self.toggle_mapping()

        if self.ds:
            self.ds.disconnect()
            self.ds = None

        self.status_label.config(text="⚪ Disconnected", fg="#8b949e")
        self.connect_btn.config(text="Connect Controller", bg="#238636")
        self.map_btn.config(state="disabled")
        self.canvas.state = None
        self.canvas.draw()

    def toggle_mapping(self):
        if self.running:
            self.running = False
            if self.mapper:
                self.mapper.stop()
                self.mapper = None
            self.map_btn.config(text="Start Mapping", bg="#4361ee")
            self.status_label.config(text="🟢 Connected", fg="#4aea8b")
        else:
            try:
                self.mapper = XboxMapper(self.config)
                self.mapper.start()
                self.running = True
                self.map_btn.config(text="Stop Mapping", bg="#e63946")
                self.status_label.config(text="🟢 Mapping Active", fg="#4aea8b")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start mapping:\n{e}\n\nMake sure ViGEmBus is installed.")

    def _poll_loop(self):
        while self.polling and self.ds:
            try:
                if self.ds.read():
                    if self.running and self.mapper:
                        self.mapper.update(self.ds.state)
                    # Update canvas on main thread
                    self.root.after(0, self.canvas.update_state, self.ds.state)
            except Exception:
                self.root.after(0, self.disconnect)
                break
            time.sleep(0.008)

    def on_config_change(self, config):
        self.config = config
        if self.mapper:
            self.mapper.deadzone_left = config.get("deadzone_left", 0.08)
            self.mapper.deadzone_right = config.get("deadzone_right", 0.08)
            self.mapper.button_map = config.get("button_map", {})

    def on_led_change(self, r, g, b):
        """Send LED color to the controller."""
        if self.ds:
            self.ds.set_led_color(r, g, b)
    def save_current_config(self):
        self.mapping_panel._sync_config()
        save_config(self.config)
        messagebox.showinfo("Saved", "Config saved to config.json")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        self.polling = False
        if self.running and self.mapper:
            self.mapper.stop()
        if self.ds:
            self.ds.disconnect()
        self.root.destroy()


def launch_gui():
    app = DualSenseGUI()
    app.run()


if __name__ == "__main__":
    launch_gui()
