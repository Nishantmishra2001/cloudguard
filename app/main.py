from flask import Flask, jsonify, request, render_template
from datetime import datetime, timezone, timedelta
import uuid
import docker

app = Flask(__name__)

docker_client = docker.from_env()

environments = {}

DEFAULT_TTL_MINUTES = 60
PREVIEW_IMAGE = "cloudguard-preview:1.0"


def get_container_name(environment_id):
    return f"cloudguard-preview-{environment_id}"


def get_container_metrics(container):
    try:
        stats = container.stats(stream=False)

        cpu_stats = stats.get("cpu_stats", {})
        precpu_stats = stats.get("precpu_stats", {})

        cpu_delta = (
            cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        )

        system_delta = (
            cpu_stats.get("system_cpu_usage", 0)
            - precpu_stats.get("system_cpu_usage", 0)
        )

        online_cpus = cpu_stats.get("online_cpus", 1)

        if system_delta > 0 and cpu_delta >= 0:
            cpu_percent = (
                cpu_delta / system_delta
            ) * online_cpus * 100.0
        else:
            cpu_percent = 0.0

        memory_stats = stats.get("memory_stats", {})
        memory_usage = memory_stats.get("usage", 0)
        memory_limit = memory_stats.get("limit", 0)

        if memory_limit > 0:
            memory_percent = (
                memory_usage / memory_limit
            ) * 100.0
        else:
            memory_percent = 0.0

        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory_percent, 2),
            "memory_usage_mb": round(memory_usage / 1024 / 1024, 2),
            "memory_limit_mb": round(memory_limit / 1024 / 1024, 2)
        }

    except Exception:
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_usage_mb": 0,
            "memory_limit_mb": 0
        }


def cleanup_expired_environments():
    now = datetime.now(timezone.utc)
    expired_ids = []

    for environment_id, environment in list(environments.items()):
        expires_at = datetime.fromisoformat(environment["expires_at"])

        if expires_at <= now:
            expired_ids.append(environment_id)

    for environment_id in expired_ids:
        environment = environments.pop(environment_id, None)

        if environment:
            container_name = environment.get("container_name")

            if container_name:
                try:
                    container = docker_client.containers.get(container_name)
                    container.remove(force=True)
                except docker.errors.NotFound:
                    pass
                except Exception as error:
                    print(f"Cleanup error for {container_name}: {error}")


def build_environment_response(environment):
    result = dict(environment)

    container_name = environment.get("container_name")

    if container_name:
        try:
            container = docker_client.containers.get(container_name)

            result["container_status"] = container.status
            result["container_id"] = container.short_id

            metrics = get_container_metrics(container)
            result.update(metrics)

        except docker.errors.NotFound:
            result["container_status"] = "not_found"
            result["container_id"] = None
            result.update({
                "cpu_percent": 0,
                "memory_percent": 0,
                "memory_usage_mb": 0,
                "memory_limit_mb": 0
            })

        except Exception:
            result["container_status"] = "unknown"

    return result


@app.route("/")
def home():
    return render_template("index.html")


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
        "environments": [
            build_environment_response(environment)
            for environment in environments.values()
        ]
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

    container_name = get_container_name(environment_id)

    try:
        container = docker_client.containers.run(
            PREVIEW_IMAGE,
            name=container_name,
            detach=True,
            ports={
                "5000/tcp": None
            },
            labels={
                "cloudguard.environment": environment_id,
                "cloudguard.project": "CloudGuard"
            }
        )

        container.reload()

        port_info = container.attrs["NetworkSettings"]["Ports"]

        host_port = None

        if port_info.get("5000/tcp"):
            host_port = int(
                port_info["5000/tcp"][0]["HostPort"]
            )

    except Exception as error:
        return jsonify({
            "error": "Failed to create preview container",
            "details": str(error)
        }), 500

    environment = {
        "id": environment_id,
        "environment": "preview",
        "status": "active",
        "branch": branch,
        "commit": commit,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "expires_in": f"{ttl_minutes} minutes",
        "container_name": container_name,
        "container_id": container.short_id,
        "preview_port": host_port,
        "preview_url": f"http://localhost:{host_port}"
    }

    environments[environment_id] = environment

    return jsonify(
        build_environment_response(environment)
    ), 201


@app.route("/environments/<environment_id>", methods=["DELETE"])
def delete_environment(environment_id):
    cleanup_expired_environments()

    if environment_id not in environments:
        return jsonify({
            "error": "Environment not found"
        }), 404

    deleted = environments.pop(environment_id)

    container_name = deleted.get("container_name")

    if container_name:
        try:
            container = docker_client.containers.get(container_name)
            container.remove(force=True)

        except docker.errors.NotFound:
            pass

        except Exception as error:
            return jsonify({
                "error": "Environment record removed but container cleanup failed",
                "details": str(error)
            }), 500

    return jsonify({
        "message": "Preview environment deleted",
        "environment": deleted
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
