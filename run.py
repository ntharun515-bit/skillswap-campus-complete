"""Entry point to run SkillSwap with SocketIO."""
from backend.app import app
from backend.extensions import socketio

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True, allow_unsafe_werkzeug=True)
