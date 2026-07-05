# 🎮 DualSense PC Mapper

**Free & open-source PS5 DualSense controller mapper for Windows.**

Use your PS5 controller on any PC game — no paid apps needed.

## How It Works

This app reads your DualSense controller (USB or Bluetooth) and creates a virtual Xbox 360 controller that Windows recognizes natively. Every PC game that supports Xbox controllers will work with your DualSense.

### Button Mapping

| DualSense | Xbox 360 |
|-----------|----------|
| ✕ Cross | A |
| ○ Circle | B |
| □ Square | X |
| △ Triangle | Y |
| L1 / R1 | LB / RB |
| L2 / R2 | LT / RT |
| L3 / R3 | LS / RS |
| Share | Back |
| Options | Start |
| PS Button | Guide |
| D-Pad | D-Pad |
| Sticks | Sticks |

## Quick Start

### Requirements
- Windows 10/11
- Python 3.8+
- [ViGEmBus Driver](https://github.com/nefarius/ViGEmBus/releases) (required for virtual Xbox controller)

### Install

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/dualsense-pc-mapper.git
cd dualsense-pc-mapper

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
# Start mapping (DualSense → Xbox)
python main.py

# Test mode (see raw inputs without Xbox emulation)
python main.py --test
```

### Download .exe (No Python Needed)

Check the [Releases](https://github.com/YOUR_USERNAME/dualsense-pc-mapper/releases) page for a standalone .exe.

## Connecting Your Controller

**USB:** Just plug it in.

**Bluetooth:**
1. Hold the **Create** + **PS** buttons on your DualSense until the light bar flashes blue
2. Go to Windows Settings → Bluetooth → Add device
3. Select "Wireless Controller"

## Roadmap

- [x] v0.1 — Detect & connect DualSense (USB + Bluetooth)
- [x] v0.1 — Map all buttons, sticks, triggers to Xbox 360
- [ ] v0.2 — Custom button remapping
- [ ] v0.2 — Adjustable dead zones
- [ ] v0.3 — GUI with controller visualization
- [ ] v0.3 — Save/load profiles
- [ ] v0.4 — LED color control
- [ ] v1.0 — Full release with installer

## Why This Exists

Too many apps charge money for basic controller support. This project is 100% free, open source, and always will be.

## Contributing

Pull requests welcome! Check the [Issues](https://github.com/YOUR_USERNAME/dualsense-pc-mapper/issues) tab for things to work on.

## License

MIT License — do whatever you want with it.
