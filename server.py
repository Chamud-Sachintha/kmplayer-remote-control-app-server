from flask import Flask, request, jsonify
from flask_cors import CORS
from pynput.keyboard import Controller, Key
import os
import platform

try:
    from monitorcontrol import get_monitors
    MONITORCONTROL_AVAILABLE = True
except ImportError:
    MONITORCONTROL_AVAILABLE = False

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

keyboard = Controller()

# Supported keys and commands
VALID_KEYS = {
    '[': '[',
    ']': ']',
    'pause': Key.space,
    'shutdown': 'shutdown'  # handled separately
}


@app.route('/')
def index():
    return jsonify({"status": "PC Key Server is running!"})

@app.route('/brightness', methods=['POST'])
def set_brightness():
    try:
        data = request.get_json(force=True)
        value = int(data.get('value', 50))
        value = max(0, min(value, 100))  # clamp to 0–100
        system = platform.system()

        success = False

        # 🖥️ Try monitorcontrol first (for external monitors)
        if MONITORCONTROL_AVAILABLE:
            try:
                monitors = get_monitors()
                for m in monitors:
                    with m:
                        m.set_luminance(value)
                success = True
                print(f"Brightness set to {value}% via monitorcontrol")
            except Exception as e:
                print("monitorcontrol failed:", e)

        # 🪟 Windows fallback via WMI
        if not success and system == "Windows":
            ps_cmd = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{value})"
            os.system(f"powershell -Command \"{ps_cmd}\"")
            success = True

        # 🐧 Linux
        elif not success and system == "Linux":
            os.system(f"xrandr --output eDP-1 --brightness {value / 100}")
            success = True

        # 🍎 macOS
        elif not success and system == "Darwin":
            os.system(f"brightness {value / 100}")
            success = True

        if success:
            return jsonify({"status": "ok", "brightness": value}), 200
        else:
            return jsonify({"error": "No supported brightness method found"}), 500

    except Exception as e:
        print("Brightness error:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/key', methods=['POST'])
def press_key():
    try:
        data = request.get_json(force=True)
        key = data.get('key')

        if not key or key not in VALID_KEYS:
            return jsonify({"error": "Invalid or missing key"}), 400

        # Special shutdown command
        if key == 'shutdown':
            system = platform.system()
            if system == "Windows":
                os.system("shutdown /s /t 0")
            elif system == "Linux":
                os.system("shutdown now")
            elif system == "Darwin":  # macOS
                os.system("sudo shutdown -h now")
            return jsonify({"status": "shutting down"}), 200

        # Normal key press
        mapped_key = VALID_KEYS[key]
        keyboard.press(mapped_key)
        keyboard.release(mapped_key)

        print(f"Pressed: {key}")
        return jsonify({"status": "ok", "pressed": key}), 200

    except Exception as e:
        print("Error handling request:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Run on all interfaces so mobile can connect
    app.run(host="0.0.0.0", port=5000, debug=True)
