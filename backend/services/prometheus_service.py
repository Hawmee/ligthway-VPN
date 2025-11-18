import requests
from datetime import datetime
from config.settings import PROMETHEUS_URL

class PrometheusService:
    """Service pour interagir avec Prometheus"""
    
    @staticmethod
    def query(query):
        """Exécute une requête PromQL instantanée"""
        try:
            response = requests.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={'query': query},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying Prometheus: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def query_range(query, start, end, step='15s'):
        """Exécute une requête PromQL sur une plage de temps"""
        try:
            response = requests.get(
                f"{PROMETHEUS_URL}/api/v1/query_range",
                params={
                    'query': query,
                    'start': start,
                    'end': end,
                    'step': step
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying Prometheus range: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_all_peers_metrics():
        """Récupère toutes les métriques pour tous les peers"""
        query = 'wireguard_sent_bytes_total'
        result = PrometheusService.query(query)
        
        if 'error' in result or result.get('status') != 'success':
            return []
        
        peers = []
        for metric in result['data']['result']:
            peer = {
                'public_key': metric['metric'].get('public_key', ''),
                'interface': metric['metric'].get('interface', ''),
                'allowed_ips': metric['metric'].get('allowed_ips', ''),
                'sent_bytes': int(metric['value'][1])
            }
            peers.append(peer)
        
        return peers
    
    @staticmethod
    def get_peer_stats(public_key):
        """Récupère les statistiques complètes d'un peer"""
        # Données envoyées
        sent_query = f'wireguard_sent_bytes_total{{public_key="{public_key}"}}'
        sent_result = PrometheusService.query(sent_query)
        
        # Données reçues
        recv_query = f'wireguard_received_bytes_total{{public_key="{public_key}"}}'
        recv_result = PrometheusService.query(recv_query)
        
        # Dernier handshake
        handshake_query = f'wireguard_latest_handshake_seconds{{public_key="{public_key}"}}'
        handshake_result = PrometheusService.query(handshake_query)
        
        # Vérifier les erreurs
        if ('error' in sent_result or 'error' in recv_result or 
            sent_result.get('status') != 'success'):
            return None
        
        # Extraction des données
        sent_bytes = 0
        recv_bytes = 0
        handshake_ts = 0
        allowed_ips = ""
        interface = ""
        
        if sent_result['data']['result']:
            sent_bytes = int(sent_result['data']['result'][0]['value'][1])
            allowed_ips = sent_result['data']['result'][0]['metric'].get('allowed_ips', '')
            interface = sent_result['data']['result'][0]['metric'].get('interface', '')
        
        if recv_result['data']['result']:
            recv_bytes = int(recv_result['data']['result'][0]['value'][1])
        
        if handshake_result['data']['result']:
            handshake_ts = int(handshake_result['data']['result'][0]['value'][1])
        
        # Calcul du statut (actif si handshake < 3 minutes)
        current_time = datetime.now().timestamp()
        is_active = (current_time - handshake_ts) < 180 if handshake_ts > 0 else False
        
        # Calculer le temps depuis le dernier handshake
        time_since_handshake = None
        if handshake_ts > 0:
            seconds_since = int(current_time - handshake_ts)
            if seconds_since < 60:
                time_since_handshake = f"{seconds_since}s"
            elif seconds_since < 3600:
                time_since_handshake = f"{seconds_since // 60}m {seconds_since % 60}s"
            else:
                hours = seconds_since // 3600
                minutes = (seconds_since % 3600) // 60
                time_since_handshake = f"{hours}h {minutes}m"
        
        stats = {
            'public_key': public_key,
            'interface': interface,
            'allowed_ips': allowed_ips,
            'sent_bytes': sent_bytes,
            'received_bytes': recv_bytes,
            'total_bytes': sent_bytes + recv_bytes,
            'sent_mb': round(sent_bytes / 1024 / 1024, 2),
            'received_mb': round(recv_bytes / 1024 / 1024, 2),
            'total_mb': round((sent_bytes + recv_bytes) / 1024 / 1024, 2),
            'last_handshake_timestamp': handshake_ts,
            'last_handshake': datetime.fromtimestamp(handshake_ts).isoformat() if handshake_ts > 0 else None,
            'time_since_handshake': time_since_handshake,
            'is_active': is_active,
            'status': 'active' if is_active else 'inactive'
        }
        
        return stats
    
    @staticmethod
    def get_peer_bandwidth(public_key=None):
        """Récupère la bande passante actuelle (bytes/sec sur 5 minutes)"""
        # Si un public_key est spécifié, filtrer pour ce peer
        if public_key:
            sent_rate_query = f'rate(wireguard_sent_bytes_total{{public_key="{public_key}"}}[5m])'
            recv_rate_query = f'rate(wireguard_received_bytes_total{{public_key="{public_key}"}}[5m])'
        else:
            sent_rate_query = 'rate(wireguard_sent_bytes_total[5m])'
            recv_rate_query = 'rate(wireguard_received_bytes_total[5m])'
        
        sent_rate = PrometheusService.query(sent_rate_query)
        recv_rate = PrometheusService.query(recv_rate_query)
        
        if 'error' in sent_rate or 'error' in recv_rate:
            return None if public_key else []
        
        bandwidth_list = []
        
        if sent_rate['data']['result']:
            for metric in sent_rate['data']['result']:
                peer_key = metric['metric']['public_key']
                sent_bps = float(metric['value'][1])
                
                # Trouver le taux de réception correspondant
                recv_bps = 0
                if recv_rate['data']['result']:
                    for recv_metric in recv_rate['data']['result']:
                        if recv_metric['metric']['public_key'] == peer_key:
                            recv_bps = float(recv_metric['value'][1])
                            break
                
                bandwidth_list.append({
                    'public_key': peer_key,
                    'sent_bytes_per_sec': round(sent_bps, 2),
                    'recv_bytes_per_sec': round(recv_bps, 2),
                    'total_bytes_per_sec': round(sent_bps + recv_bps, 2),
                    'sent_kbps': round(sent_bps / 1024, 2),
                    'recv_kbps': round(recv_bps / 1024, 2),
                    'sent_mbps': round(sent_bps * 8 / 1024 / 1024, 3),
                    'recv_mbps': round(recv_bps * 8 / 1024 / 1024, 3)
                })
        
        # Si on cherche un peer spécifique, retourner uniquement ses données
        if public_key:
            for bw in bandwidth_list:
                if bw['public_key'] == public_key:
                    return bw
            return None
        
        return bandwidth_list
    
    @staticmethod
    def get_active_peers():
        """Récupère uniquement les peers actifs (handshake < 3 minutes)"""
        query = '(time() - wireguard_latest_handshake_seconds) < 180'
        result = PrometheusService.query(query)
        
        if 'error' in result or result.get('status') != 'success':
            return []
        
        active_peers = []
        for metric in result['data']['result']:
            active_peers.append({
                'public_key': metric['metric'].get('public_key', ''),
                'interface': metric['metric'].get('interface', ''),
                'allowed_ips': metric['metric'].get('allowed_ips', '')
            })
        
        return active_peers
    
    @staticmethod
    def get_summary():
        """Récupère un résumé global du VPN"""
        # Nombre total de peers
        total_peers_query = 'count(wireguard_sent_bytes_total)'
        total_peers_result = PrometheusService.query(total_peers_query)
        
        # Peers actifs
        active_peers_query = 'count((time() - wireguard_latest_handshake_seconds) < 180)'
        active_peers_result = PrometheusService.query(active_peers_query)
        
        # Total données envoyées
        total_sent_query = 'sum(wireguard_sent_bytes_total)'
        total_sent_result = PrometheusService.query(total_sent_query)
        
        # Total données reçues
        total_recv_query = 'sum(wireguard_received_bytes_total)'
        total_recv_result = PrometheusService.query(total_recv_query)
        
        # Bande passante actuelle totale
        total_bandwidth_sent_query = 'sum(rate(wireguard_sent_bytes_total[5m]))'
        total_bandwidth_sent_result = PrometheusService.query(total_bandwidth_sent_query)
        
        total_bandwidth_recv_query = 'sum(rate(wireguard_received_bytes_total[5m]))'
        total_bandwidth_recv_result = PrometheusService.query(total_bandwidth_recv_query)
        
        # Extraction des valeurs
        total_peers = 0
        active_peers = 0
        total_sent_bytes = 0
        total_recv_bytes = 0
        bandwidth_sent = 0
        bandwidth_recv = 0
        
        if total_peers_result.get('status') == 'success' and total_peers_result['data']['result']:
            total_peers = int(total_peers_result['data']['result'][0]['value'][1])
        
        if active_peers_result.get('status') == 'success' and active_peers_result['data']['result']:
            active_peers = int(active_peers_result['data']['result'][0]['value'][1])
        
        if total_sent_result.get('status') == 'success' and total_sent_result['data']['result']:
            total_sent_bytes = int(total_sent_result['data']['result'][0]['value'][1])
        
        if total_recv_result.get('status') == 'success' and total_recv_result['data']['result']:
            total_recv_bytes = int(total_recv_result['data']['result'][0]['value'][1])
        
        if total_bandwidth_sent_result.get('status') == 'success' and total_bandwidth_sent_result['data']['result']:
            bandwidth_sent = float(total_bandwidth_sent_result['data']['result'][0]['value'][1])
        
        if total_bandwidth_recv_result.get('status') == 'success' and total_bandwidth_recv_result['data']['result']:
            bandwidth_recv = float(total_bandwidth_recv_result['data']['result'][0]['value'][1])
        
        summary = {
            'total_peers': total_peers,
            'active_peers': active_peers,
            'inactive_peers': max(0, total_peers - active_peers),
            'total_sent_bytes': total_sent_bytes,
            'total_received_bytes': total_recv_bytes,
            'total_sent_gb': round(total_sent_bytes / 1024 / 1024 / 1024, 2),
            'total_received_gb': round(total_recv_bytes / 1024 / 1024 / 1024, 2),
            'total_traffic_gb': round((total_sent_bytes + total_recv_bytes) / 1024 / 1024 / 1024, 2),
            'current_bandwidth_sent_mbps': round(bandwidth_sent * 8 / 1024 / 1024, 3),
            'current_bandwidth_recv_mbps': round(bandwidth_recv * 8 / 1024 / 1024, 3),
            'current_bandwidth_total_mbps': round((bandwidth_sent + bandwidth_recv) * 8 / 1024 / 1024, 3)
        }
        
        return summary
    
    @staticmethod
    def get_peer_history(public_key, duration_hours=1):
        """Récupère l'historique de bande passante d'un peer"""
        import time
        
        end = int(time.time())
        start = end - (duration_hours * 3600)
        
        # Historique d'envoi
        sent_query = f'rate(wireguard_sent_bytes_total{{public_key="{public_key}"}}[5m])'
        sent_result = PrometheusService.query_range(sent_query, start, end, '1m')
        
        # Historique de réception
        recv_query = f'rate(wireguard_received_bytes_total{{public_key="{public_key}"}}[5m])'
        recv_result = PrometheusService.query_range(recv_query, start, end, '1m')
        
        if 'error' in sent_result or 'error' in recv_result:
            return None
        
        history = []
        
        # Traiter les données d'envoi
        sent_data = {}
        if sent_result.get('status') == 'success' and sent_result['data']['result']:
            for value in sent_result['data']['result'][0]['values']:
                timestamp = value[0]
                sent_data[timestamp] = float(value[1])
        
        # Traiter les données de réception
        recv_data = {}
        if recv_result.get('status') == 'success' and recv_result['data']['result']:
            for value in recv_result['data']['result'][0]['values']:
                timestamp = value[0]
                recv_data[timestamp] = float(value[1])
        
        # Combiner les données
        all_timestamps = sorted(set(list(sent_data.keys()) + list(recv_data.keys())))
        
        for ts in all_timestamps:
            sent_bps = sent_data.get(ts, 0)
            recv_bps = recv_data.get(ts, 0)
            
            history.append({
                'timestamp': ts,
                'datetime': datetime.fromtimestamp(ts).isoformat(),
                'sent_bytes_per_sec': round(sent_bps, 2),
                'recv_bytes_per_sec': round(recv_bps, 2),
                'sent_kbps': round(sent_bps / 1024, 2),
                'recv_kbps': round(recv_bps / 1024, 2),
                'sent_mbps': round(sent_bps * 8 / 1024 / 1024, 3),
                'recv_mbps': round(recv_bps * 8 / 1024 / 1024, 3)
            })
        
        return history
    
    @staticmethod
    def check_prometheus_health():
        """Vérifie la santé de Prometheus"""
        try:
            response = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=5)
            return response.status_code == 200
        except:
            return False