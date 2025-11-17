<<<<<<< HEAD
from flask import Flask
from routes.peers import peers_bp
from routes.server import server_bp
from routes.wireguard import wireguard_bp

def create_app():
    app = Flask(__name__)
=======
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import base64
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
import subprocess

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})
WIREGUARD_PATH = "/wireguard-config"

@app.route("/")
def home():
    return jsonify({"status": "Backend OK", "wireguard_config": WIREGUARD_PATH})

@app.route("/peers", methods=["GET"])
def list_peers():
    peers = []

    try:
        for f in os.listdir(WIREGUARD_PATH):
            full_path = os.path.join(WIREGUARD_PATH, f)

            # Only folders → each peer has a folder
            if os.path.isdir(full_path) and f not in ("server", "templates", "wg_confs"):
                
                config_file = os.path.join(full_path, f"peer.conf")

                # Try to read the config file
                conf_content = None
                ip_address = None

                if os.path.isfile(config_file):
                    with open(config_file, "r") as c:
                        conf_content = c.read()

                    # Extract IP from "Address = ..."
                    for line in conf_content.splitlines():
                        line = line.strip()
                        if line.startswith("Address"):
                            ip_address = line.split("=", 1)[1].strip().split("/")[0]
                            break

                peers.append({
                    "name": f,
                    "ip": ip_address,
                })

        return jsonify(peers)

    except FileNotFoundError:
        return jsonify({"error": "WireGuard config directory not found"}), 500

def generate_wireguard_keys():
    """Generate WireGuard private and public keys"""
    private_key = x25519.X25519PrivateKey.generate()
>>>>>>> f0f6c70ad4350fe8d89e274aea4fbe9515f1f31c
    
    # Register blueprints
    app.register_blueprint(server_bp)
    app.register_blueprint(peers_bp)
    app.register_blueprint(wireguard_bp)
    
    return app
