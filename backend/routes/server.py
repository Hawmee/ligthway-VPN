from flask import jsonify, Blueprint
import os
from config.settings import WIREGUARD_PATH
from services.config_service import ConfigService
from utils.helpers import list_existing_peers

server_bp = Blueprint('server', __name__)

@server_bp.route("/")
def home():
    return jsonify({"status": "Backend OK", "wireguard_config": WIREGUARD_PATH})

@server_bp.route("/server-info", methods=["GET"])
def server_info():
    """Check server configuration and public key"""
    try:
        public_key_path = os.path.join(WIREGUARD_PATH, "server", "publickey-server")
        server_conf_path = os.path.join(WIREGUARD_PATH, "wg_confs", "wg0.conf")
        
        public_key_exists = os.path.exists(public_key_path)
        config_exists = os.path.exists(server_conf_path)
        
        server_public_key = ConfigService.get_server_public_key()
        
        # Count existing peers
        existing_peers = len(list_existing_peers(WIREGUARD_PATH))
        
        return jsonify({
            "server_public_key": server_public_key,
            "publickey_server_exists": public_key_exists,
            "wg0_conf_exists": config_exists,
            "existing_peers_count": existing_peers,
            "wireguard_path": WIREGUARD_PATH
        })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500