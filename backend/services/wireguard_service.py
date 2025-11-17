import os
import subprocess
from config.settings import WIREGUARD_PATH, DOCKER_CONTAINER_NAME

class WireGuardService:
    @staticmethod
    def add_peer_to_server_config(peer_name, peer_public_key, preshared_key):
        """Add the peer to the server configuration"""
        try:
            server_conf_path = os.path.join(WIREGUARD_PATH, "wg_confs", "wg0.conf")
            
            # Calculate next available IP
            existing_peers = len([f for f in os.listdir(WIREGUARD_PATH) 
                                 if os.path.isdir(os.path.join(WIREGUARD_PATH, f)) and f not in ['server', 'templates', 'wg_confs']])
            peer_ip = f"192.0.0.{existing_peers + 2}"
            
            # Peer configuration to add to server
            peer_config = f"""
[Peer]
# {peer_name}
PublicKey = {peer_public_key}
PresharedKey = {preshared_key}
AllowedIPs = {peer_ip}/32
"""
            
            # Read current server config
            with open(server_conf_path, "r") as f:
                current_config = f.read()
            
            # Find the position to insert
            if current_config.strip().endswith(']'):
                lines = current_config.split('\n')
                new_lines = []
                for line in lines:
                    if line.strip() == ']' and peer_config not in current_config:
                        new_lines.append(peer_config)
                        new_lines.append(']')
                    else:
                        new_lines.append(line)
                new_config = '\n'.join(new_lines)
            else:
                new_config = current_config + peer_config
            
            # Write updated server configuration
            with open(server_conf_path, "w") as f:
                f.write(new_config)
            
            # Reload WireGuard configuration
            WireGuardService.reload_wireguard_config()
            
            return peer_ip
            
        except Exception as e:
            print(f"Error adding peer to server: {e}")
            return f"192.0.0.{existing_peers + 2}"

    @staticmethod
    def reload_wireguard_config():
        """Reload WireGuard configuration using syncconf"""
        try:
            subprocess.run([
                "docker", "exec", DOCKER_CONTAINER_NAME, 
                "wg", "syncconf", "wg0", 
                "/config/wg_confs/wg0.conf"
            ], check=True, capture_output=True, timeout=30)
            print("WireGuard configuration reloaded successfully")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not reload WireGuard config automatically: {e}")
            print("You may need to restart the WireGuard container manually")
        except subprocess.TimeoutExpired:
            print("Warning: WireGuard reload timed out")

    @staticmethod
    def restart_wireguard_container():
        """Restart the entire WireGuard container"""
        try:
            result = subprocess.run(
                ["docker", "restart", DOCKER_CONTAINER_NAME],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            return True, "WireGuard container restarted successfully"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to restart WireGuard: {e.stderr}"
        except subprocess.TimeoutExpired:
            return False, "WireGuard restart timed out"