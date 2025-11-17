import os
import subprocess
import docker
from config.settings import WIREGUARD_PATH, DOCKER_CONTAINER_NAME, SERVER_CONFIG_PATH

class WireGuardService:
    # Initialiser le client Docker
    _docker_client = docker.from_env()

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
            # Utiliser l'API Docker pour exécuter la commande dans le conteneur
            container = WireGuardService._docker_client.containers.get(DOCKER_CONTAINER_NAME)
            result = container.exec_run(
                ["wg", "syncconf", "wg0", "/config/wg_confs/wg0.conf"]
            )
            
            if result.exit_code == 0:
                print("WireGuard configuration reloaded successfully")
            else:
                print(f"Warning: Could not reload WireGuard config automatically: {result.output.decode()}")
                
        except docker.errors.NotFound:
            print(f"Error: Container {DOCKER_CONTAINER_NAME} not found")
        except docker.errors.APIError as e:
            print(f"Error with Docker API: {e}")
        except Exception as e:
            print(f"Unexpected error reloading WireGuard config: {e}")

    @staticmethod
    def restart_wireguard_container():
        """Restart the entire WireGuard container using Docker Python SDK"""
        try:
            # Récupérer le conteneur
            container = WireGuardService._docker_client.containers.get(DOCKER_CONTAINER_NAME)
            
            # Redémarrer le conteneur
            container.restart(timeout=30)
            
            return True, "WireGuard container restarted successfully"
            
        except docker.errors.NotFound:
            return False, f"WireGuard container '{DOCKER_CONTAINER_NAME}' not found"
        except docker.errors.APIError as e:
            return False, f"Docker API error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
            
    @staticmethod
    def remove_peer_from_server_config(peer_name):
        """Remove peer configuration from server's wg0.conf"""
        try:
            server_config_path = os.path.join(WIREGUARD_PATH, SERVER_CONFIG_PATH)
            
            # Vérifier si le fichier existe
            if not os.path.exists(server_config_path):
                return False, f"Server configuration file not found: {server_config_path}"
            
            # Lire le contenu actuel du fichier
            with open(server_config_path, 'r') as f:
                lines = f.readlines()
            
            # Trouver et supprimer la section [Peer] correspondante
            new_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Vérifier si c'est le début d'une section [Peer] avec le bon nom
                if line.strip().startswith('[Peer]'):
                    # Regarder les lignes suivantes pour trouver le commentaire avec le nom du peer
                    peer_section_start = i
                    peer_comment_found = False
                    
                    # Avancer jusqu'à la prochaine section [Peer] ou fin du fichier
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().startswith('['):
                        # Vérifier si cette ligne contient le commentaire avec le nom du peer
                        if f"# {peer_name}" in lines[j]:
                            peer_comment_found = True
                            break
                        j += 1
                    
                    # Si on a trouvé le peer, sauter toute cette section
                    if peer_comment_found:
                        # Trouver la fin de cette section [Peer]
                        k = j + 1
                        while k < len(lines) and not lines[k].strip().startswith('['):
                            k += 1
                        # Sauter toute la section
                        i = k
                        continue
                    else:
                        # Ce n'est pas le bon peer, garder cette section
                        new_lines.append(line)
                        i += 1
                else:
                    # Ce n'est pas une section [Peer], garder la ligne
                    new_lines.append(line)
                    i += 1
            
            # Réécrire le fichier sans la section du peer
            with open(server_config_path, 'w') as f:
                f.writelines(new_lines)
            
            # Recharger la configuration WireGuard
            WireGuardService.reload_wireguard_config()
            
            return True, f"Peer {peer_name} removed from server configuration"
            
        except Exception as e:
            return False, f"Error removing peer from server config: {str(e)}"