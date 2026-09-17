from flask import Flask, jsonify
from datetime import datetime, timezone

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "project": "CloudGuard",
        "service": "Preview Environment Manager",
        "status": "running",
        "message": "CloudGuard is operational"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route("/environment")
def environment():
    return jsonify({
        "environment": "preview",
        "branch": "feature/demo",
        "commit": "local-dev",
        "status": "active",
        "expires_in": "60 minutes"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
