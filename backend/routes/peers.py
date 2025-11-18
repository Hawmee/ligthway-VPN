from flask import jsonify, request, Blueprint
import threading
import os
import shutil
from config.settings import WIREGUARD_PATH
from services.key_service import KeyService
from services.config_service import ConfigService
from services.wireguard_service import WireGuardService
from services.prometheus_service import PrometheusService  # ← Nouveau
from utils.helpers import sanitize_peer_name, peer_exists, list_existing_peers

peers_bp = Blueprint('peers', __name__)

@peers_bp.route("/peers", methods=["GET"])
def list_peers():
    """List all existing peers with their metrics"""
    try:
        # Récupérer la liste des peers depuis la config
        peers = list_existing_peers(WIREGUARD_PATH)
        
        # Option pour désactiver les métriques via query param
        include_metrics = request.args.get('metrics', 'true').lower() == 'true'
        
        if not include_metrics:
            return jsonify(peers)
        
        # Enrichir chaque peer avec ses métriques Prometheus
        enriched_peers = []
        for peer in peers:
            peer_data = peer.copy()
            
            # Essayer de récupérer les métriques
            try:
                # Récupérer la clé publique du peer (à adapter selon votre structure)
                # Vous devrez peut-être lire le fichier de config pour obtenir la clé publique
                peer_public_key = get_peer_public_key(peer.get('name'))
                
                if peer_public_key:
                    # Récupérer les stats Prometheus
                    stats = PrometheusService.get_peer_stats(peer_public_key)
                    bandwidth = PrometheusService.get_peer_bandwidth(peer_public_key)
                    
                    if stats:
                        peer_data['metrics'] = {
                            'status': stats['status'],
                            'is_active': stats['is_active'],
                            'traffic': {
                                'sent_bytes': stats['sent_bytes'],
                                'received_bytes': stats['received_bytes'],
                                'total_bytes': stats['total_bytes'],
                                'sent_mb': stats['sent_mb'],
                                'received_mb': stats['received_mb'],
                                'total_mb': stats['total_mb']
                            },
                            'last_handshake': stats['last_handshake'],
                            'time_since_handshake': stats['time_since_handshake'],
                            'allowed_ips': stats['allowed_ips']
                        }
                    
                    if bandwidth:
                        peer_data['bandwidth'] = {
                            'sent_kbps': bandwidth['sent_kbps'],
                            'recv_kbps': bandwidth['recv_kbps'],
                            'sent_mbps': bandwidth['sent_mbps'],
                            'recv_mbps': bandwidth['recv_mbps']
                        }
            except Exception as e:
                # Si les métriques ne sont pas disponibles, continuer sans
                print(f"Warning: Could not fetch metrics for peer {peer.get('name')}: {e}")
                peer_data['metrics'] = None
                peer_data['bandwidth'] = None
            
            enriched_peers.append(peer_data)
        
        # Ajouter un résumé global
        try:
            summary = PrometheusService.get_summary()
        except Exception as e:
            print(f"Warning: Could not fetch summary: {e}")
            summary = None
        
        return jsonify({
            'peers': enriched_peers,
            'count': len(enriched_peers),
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
            "public_key": public_key,  # ← Ajouter la clé publique dans la réponse
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
    """Get the configuration file for a specific peer with metrics"""
    try:
        name = sanitize_peer_name(name)
        config_path = os.path.join(WIREGUARD_PATH, f"{name}.conf")
        
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        response_data = {
            "peer_name": name,
            "config": config_content
        }
        
        # Essayer d'ajouter les métriques si demandées
        include_metrics = request.args.get('metrics', 'false').lower() == 'true'
        
        if include_metrics:
            try:
                peer_public_key = get_peer_public_key(name)
                
                if peer_public_key:
                    stats = PrometheusService.get_peer_stats(peer_public_key)
                    bandwidth = PrometheusService.get_peer_bandwidth(peer_public_key)
                    history = PrometheusService.get_peer_history(peer_public_key, duration_hours=1)
                    
                    response_data['metrics'] = stats
                    response_data['bandwidth'] = bandwidth
                    response_data['history'] = history
            except Exception as e:
                print(f"Warning: Could not fetch metrics for peer {name}: {e}")
        
        return jsonify(response_data)
        
    except FileNotFoundError:
        return jsonify({"error": "Peer configuration not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@peers_bp.route("/peer/<name>/metrics", methods=["GET"])
def get_peer_metrics(name):
    """Get detailed metrics for a specific peer"""
    try:
        name = sanitize_peer_name(name)
        
        # Vérifier que le peer existe
        if not peer_exists(name, WIREGUARD_PATH):
            return jsonify({"error": f"Peer {name} not found"}), 404
        
        # Récupérer la clé publique du peer
        peer_public_key = get_peer_public_key(name)
        
        if not peer_public_key:
            return jsonify({"error": "Could not retrieve peer public key"}), 500
        
        # Récupérer les métriques
        stats = PrometheusService.get_peer_stats(peer_public_key)
        bandwidth = PrometheusService.get_peer_bandwidth(peer_public_key)
        
        # Récupérer l'historique (durée personnalisable via query param)
        duration_hours = request.args.get('hours', default=1, type=int)
        if duration_hours > 24:
            duration_hours = 24
        
        history = PrometheusService.get_peer_history(peer_public_key, duration_hours)
        
        if not stats:
            return jsonify({"error": "No metrics available for this peer"}), 404
        
        return jsonify({
            "peer_name": name,
            "public_key": peer_public_key,
            "stats": stats,
            "bandwidth": bandwidth,
            "history": {
                "duration_hours": duration_hours,
                "data_points": len(history) if history else 0,
                "data": history
            }
        })
        
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


# ===== HELPER FUNCTIONS =====

def get_peer_public_key(peer_name):
    """
    Récupère la clé publique d'un peer depuis sa configuration
    Vous devrez adapter cette fonction selon votre structure de fichiers
    """
    try:
        # Option 1: Lire depuis le fichier publickey-<peer>
        public_key_path = os.path.join(WIREGUARD_PATH, peer_name, f"publickey-{peer_name}")
        if os.path.exists(public_key_path):
            with open(public_key_path, 'r') as f:
                return f.read().strip()
        
        # Option 2: Lire depuis le fichier .conf du peer
        peer_conf_path = os.path.join(WIREGUARD_PATH, f"{peer_name}.conf")
        if os.path.exists(peer_conf_path):
            with open(peer_conf_path, 'r') as f:
                for line in f:
                    if line.strip().startswith('PublicKey'):
                        # Extraire la clé publique
                        return line.split('=')[1].strip()
        
        # Option 3: Lire depuis le wg0.conf du serveur
        server_conf_path = os.path.join(WIREGUARD_PATH, "wg_confs", "wg0.conf")
        if os.path.exists(server_conf_path):
            with open(server_conf_path, 'r') as f:
                lines = f.readlines()
                in_peer_section = False
                for i, line in enumerate(lines):
                    # Chercher le commentaire avec le nom du peer
                    if f"# {peer_name}" in line:
                        in_peer_section = True
                        continue
                    
                    # Si on est dans la section du peer, chercher la PublicKey
                    if in_peer_section and line.strip().startswith('PublicKey'):
                        return line.split('=')[1].strip()
                    
                    # Si on atteint une nouvelle section [Peer], arrêter
                    if in_peer_section and line.strip().startswith('[Peer]'):
                        break
        
        return None
        
    except Exception as e:
        print(f"Error getting public key for peer {peer_name}: {e}")
        return None