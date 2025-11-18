from flask import jsonify, request, Blueprint
import threading
import os
import shutil
from config.settings import WIREGUARD_PATH
from services.key_service import KeyService
from services.config_service import ConfigService
from services.wireguard_service import WireGuardService
from utils.helpers import sanitize_peer_name, peer_exists, list_existing_peers

peers_bp = Blueprint('peers', __name__)

@peers_bp.route("/peers", methods=["GET"])
def list_peers():
    """List all existing peers"""
    peers = list_existing_peers(WIREGUARD_PATH)
    return jsonify(peers)

@peers_bp.route("/add-peer", methods=["POST"])
def add_peer():
    """Add a new peer"""
    try:
        name = request.json.get("name")
        if not name:
            return jsonify({"error": "peer name required"}), 400
        
        # Clean the name
        name = sanitize_peer_name(name)
        
        # Check if peer already exists
        if peer_exists(name, WIREGUARD_PATH):
            return jsonify({"error": f"Peer {name} already exists"}), 400
        
        # Generate keys
        private_key, public_key = KeyService.generate_wireguard_keys()
        preshared_key = KeyService.generate_preshared_key()
        
        # Add peer to server configuration and get assigned IP
        peer_ip = WireGuardService.add_peer_to_server_config(name, public_key, preshared_key)
        
        # Create peer directory structure
        ConfigService.create_peer_directory_structure(name, private_key, public_key, preshared_key, peer_ip)
        
        # Create the .conf file for easy download
        ConfigService.create_peer_config_file(name, peer_ip, private_key, preshared_key)
        
        # Prepare response data first
        response_data = {
            "message": f"Peer {name} created successfully",
            "peer_name": name,
            "ip_address": peer_ip,
            "config_file": f"{name}.conf",
            "directory": name
        }
        
        # Start WireGuard restart in background thread
        def restart_wireguard_background():
            try:
                restart_success, restart_message = WireGuardService.restart_wireguard_container()
                if not restart_success:
                    print(f"Warning: {restart_message}")
                else:
                    print("WireGuard container restarted successfully")
            except Exception as e:
                print(f"Error restarting WireGuard container: {e}")
        
        # Start the background thread
        thread = threading.Thread(target=restart_wireguard_background)
        thread.daemon = True  # This ensures the thread won't prevent program exit
        thread.start()
        
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@peers_bp.route("/peer/<name>", methods=["GET"])
def get_peer_config(name):
    """Get the configuration file for a specific peer"""
    try:
        name = sanitize_peer_name(name)
        config_path = os.path.join(WIREGUARD_PATH, f"{name}.conf")
        
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        return jsonify({
            "peer_name": name,
            "config": config_content
        })
    except FileNotFoundError:
        return jsonify({"error": "Peer configuration not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@peers_bp.route("/peer/<name>", methods=["DELETE"])
def delete_peer(name):
    """Delete a peer configuration"""
    try:
        name = sanitize_peer_name(name)
        
        # Remove peer from server config first
        success, message = WireGuardService.remove_peer_from_server_config(name)
        if not success:
            return jsonify({"error": message}), 500
        
        # Remove peer directory
        peer_dir = os.path.join(WIREGUARD_PATH, name)
        if os.path.exists(peer_dir):
            shutil.rmtree(peer_dir)
        
        # Remove .conf file
        config_path = os.path.join(WIREGUARD_PATH, f"{name}.conf")
        if os.path.exists(config_path):
            os.remove(config_path)

        # Prepare response data
        response_data = {"message": f"Peer {name} deleted successfully"}
        
        # Start WireGuard restart in background thread
        def restart_wireguard_background():
            try:
                restart_success, restart_message = WireGuardService.restart_wireguard_container()
                if not restart_success:
                    print(f"Warning: {restart_message}")
                else:
                    print(f"WireGuard container restarted successfully after deleting peer {name}")
            except Exception as e:
                print(f"Error restarting WireGuard container: {e}")
        
        # Start the background thread
        thread = threading.Thread(target=restart_wireguard_background)
        thread.daemon = True  # This ensures the thread won't prevent program exit
        thread.start()
        
        return jsonify(response_data)
            
    except Exception as e:


        return jsonify({"error": str(e)}), 500

