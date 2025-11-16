from flask import Blueprint, jsonify
from ..db import check_db_health # Import the new function

bp = Blueprint("health", __name__)

@bp.route("/health", methods=["GET"])
def health():
    if check_db_health():
        return jsonify({"status": "ok", "database": "reachable"}), 200

    else:
        return jsonify({"status": "unhealthy", "database": "unreachable"}), 503
