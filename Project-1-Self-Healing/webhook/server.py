import urllib.error
import urllib.request
import json
import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from unittest import result

from flask import Flask, jsonify, request

app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLAYBOOK = PROJECT_ROOT / "ansible" / "recover.yml"
INVENTORY = PROJECT_ROOT / "ansible" / "inventory.ini"
AUDIT_FILE = PROJECT_ROOT / "webhook" / "logs" / "recovery-audit.jsonl"
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

audit_lock = threading.Lock()


def write_audit(event, **details):
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        **details
    }

    with audit_lock:
        with AUDIT_FILE.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record) + "\n")

APP_HEALTH_URL = "http://127.0.0.1:3005/health"


def application_is_healthy():
    try:
        with urllib.request.urlopen(APP_HEALTH_URL, timeout=3) as response:
            data = json.load(response)
            return response.status == 200 and data.get("status") == "UP"
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return False

WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN")
COOLDOWN_SECONDS = 120

last_recovery = 0.0
recovery_running = False
lock = threading.Lock()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("selfhealing-webhook")


@app.get("/health")
def health():
    return jsonify({"status": "UP"})


@app.post("/alert")
def receive_alert():
    global last_recovery, recovery_running

    if not WEBHOOK_TOKEN:
        return jsonify({"error": "Webhook token not configured"}), 503

    supplied_token = request.authorization.password if request.authorization and request.authorization.type.lower() == "basic" else ""

    import hmac
    if not hmac.compare_digest(supplied_token, WEBHOOK_TOKEN):
        logger.warning("Rejected unauthorized webhook request")
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON payload"}), 400

    if payload.get("status") != "firing":
        return jsonify({"status": "ignored", "reason": "Alert is not firing"}), 200

    valid_alerts = [
        alert for alert in payload.get("alerts", [])
        if alert.get("status") == "firing"
        and alert.get("labels", {}).get("alertname") in {
            "SelfHealingAppUnhealthy",
            "SelfHealingAppDown"
        }
        and alert.get("labels", {}).get("service") == "selfhealing-app"
    ]

    if not valid_alerts:
        return jsonify({"status": "ignored", "reason": "No matching alerts"}), 200

    with lock:
        now = time.monotonic()

        if recovery_running:
            write_audit("recovery_ignored", reason="already_running")
            return jsonify({"status": "ignored", "reason": "Recovery already running"}), 200

        if now - last_recovery < COOLDOWN_SECONDS:
            write_audit("recovery_ignored", reason="cooldown_active")
            return jsonify({"status": "ignored", "reason": "Recovery cooldown active"}), 200

        recovery_running = True
        if application_is_healthy():
            write_audit(
                "recovery_ignored",
                reason="application_already_healthy"
            )

            return jsonify({
                "status": "ignored",
                "reason": "Application is already healthy"
            }), 200
        last_recovery = now

        write_audit(
            "recovery_accepted",
            service="selfhealing-app",
            alert_names=sorted({
                alert["labels"]["alertname"] for alert in valid_alerts
            })
        )

    def perform_recovery():
        global recovery_running

        try:
            logger.info("Starting Ansible recovery")

            result = subprocess.run(
                [
                    "ansible-playbook",
                    "-i",
                    str(INVENTORY),
                    str(PLAYBOOK)
                ],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=90,
                check=False
            )

            logger.info("Ansible return code: %s", result.returncode)
            logger.info("Ansible output:\n%s", result.stdout)

            if result.stderr:
                logger.warning("Ansible stderr:\n%s", result.stderr)

            if result.returncode == 0:
                logger.info("RECOVERY SUCCESSFUL")
                write_audit("recovery_completed", result="success", return_code=0)
            else:
                logger.error("RECOVERY FAILED")
                write_audit(
                    "recovery_completed",
                    result="failed",
                    return_code=result.returncode
                )

        except subprocess.TimeoutExpired:
            logger.error("RECOVERY TIMEOUT")
            write_audit("recovery_completed", result="timeout")

        except Exception:
            logger.exception("Unexpected recovery error")
            write_audit("recovery_completed", result="exception")

        finally:
            with lock:
                recovery_running = False

    threading.Thread(target=perform_recovery, daemon=True).start()

    return jsonify({
        "status": "accepted",
        "message": "Ansible recovery started"
    }), 202


if __name__ == "__main__":
    if not WEBHOOK_TOKEN:
        raise SystemExit("WEBHOOK_TOKEN environment variable is required")

    app.run(host="0.0.0.0", port=5000, debug=False)