import os

def sanitize_peer_name(name):
    """Clean the peer name to avoid path traversal"""
    return "".join(c for c in name if c.isalnum() or c in ('-', '_')).lower()

def peer_exists(peer_name, wireguard_path):
    """Check if a peer directory already exists"""
    peer_dir = os.path.join(wireguard_path, peer_name)
    return os.path.exists(peer_dir)

def list_existing_peers(wireguard_path):
    """List all existing peers"""
    peers = []
    try:
        for f in os.listdir(wireguard_path):
            if os.path.isdir(os.path.join(wireguard_path, f)) and f not in ['server', 'templates', 'wg_confs']:
                peers.append(f)
    except FileNotFoundError:
        pass
    return peers