from flask import Flask, jsonify, request
from datetime import datetime, timezone, timedelta
import uuid

app = Flask(__name__)

# In-memory preview environment store
environments = {}

DEFAULT_TTL_MINUTES = 60


def cleanup_expired_environments():
    now = datetime.now(timezone.utc)
    expired_ids = []

    for environment_id, environment in environments.items():
        expires_at = datetime.fromisoformat(environment["expires_at"])

        if expires_at <= now:
            expired_ids.append(environment_id)

    for environment_id in expired_ids:
        environments.pop(environment_id, None)


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


@app.route("/environments", methods=["GET"])
def list_environments():
    cleanup_expired_environments()

    return jsonify({
        "count": len(environments),
        "environments": list(environments.values())
    })


@app.route("/environments", methods=["POST"])
def create_environment():
    cleanup_expired_environments()

    data = request.get_json(silent=True) or {}

    branch = data.get("branch", "feature/demo")
    commit = data.get("commit", "local-dev")

    ttl_minutes = data.get("ttl_minutes", DEFAULT_TTL_MINUTES)

    try:
        ttl_minutes = int(ttl_minutes)

        if ttl_minutes <= 0:
            raise ValueError

    except (TypeError, ValueError):
        return jsonify({
            "error": "ttl_minutes must be a positive integer"
        }), 400

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ttl_minutes)

    environment_id = str(uuid.uuid4())[:8]

    environment = {
        "id": environment_id,
        "environment": "preview",
        "status": "active",
        "branch": branch,
        "commit": commit,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "expires_in": f"{ttl_minutes} minutes"
    }

    environments[environment_id] = environment

    return jsonify(environment), 201


@app.route("/environments/<environment_id>", methods=["DELETE"])
def delete_environment(environment_id):
    cleanup_expired_environments()

    if environment_id not in environments:
        return jsonify({
            "error": "Environment not found"
        }), 404

    deleted = environments.pop(environment_id)

    return jsonify({
        "message": "Preview environment deleted",
        "environment": deleted
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
