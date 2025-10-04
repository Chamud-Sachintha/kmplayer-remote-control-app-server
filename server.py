from flask import Flask, request, jsonify
from flask_cors import CORS
from pynput.keyboard import Controller

app = Flask(__name__)
CORS(app)  # ✅ Enable CORS for all routes

keyboard = Controller()

@app.route('/')
def index():
    return "PC Key Server is running!"

@app.route('/key', methods=['POST'])
def press_key():
    data = request.get_json()
    key = data.get('key')

    if key not in ['[', ']']:
        return jsonify({"error": "Invalid key"}), 400

    keyboard.press(key)
    keyboard.release(key)
    print(f"Pressed: {key}")
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
