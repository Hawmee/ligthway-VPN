from flask import jsonify, Blueprint
from services.wireguard_service import WireGuardService

wireguard_bp = Blueprint('wireguard', __name__)

@wireguard_bp.route("/reload-wireguard", methods=["POST"])
def reload_wireguard():
    """Manually reload WireGuard configuration"""
    success, message = WireGuardService.restart_wireguard_container()
    if success:
        return jsonify({"message": message})
    else:
        return jsonify({"error": message}), 500