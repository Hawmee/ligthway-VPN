from flask import Blueprint, jsonify, request
from services.prometheus_service import PrometheusService

metrics_bp = Blueprint('metrics', __name__, url_prefix='/api/metrics')

@metrics_bp.route('/summary', methods=['GET'])
def get_summary():
    """Récupère le résumé global du VPN"""
    try:
        summary = PrometheusService.get_summary()
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metrics_bp.route('/peers', methods=['GET'])
def get_all_peers_metrics():
    """Récupère les métriques de base pour tous les peers"""
    try:
        peers = PrometheusService.get_all_peers_metrics()
        return jsonify({
            'peers': peers,
            'count': len(peers)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metrics_bp.route('/peers/active', methods=['GET'])
def get_active_peers():
    """Récupère uniquement les peers actifs"""
    try:
        active_peers = PrometheusService.get_active_peers()
        return jsonify({
            'active_peers': active_peers,
            'count': len(active_peers)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metrics_bp.route('/peer/<public_key>', methods=['GET'])
def get_peer_stats(public_key):
    """Récupère les statistiques complètes d'un peer spécifique"""
    try:
        stats = PrometheusService.get_peer_stats(public_key)
        
        if stats is None:
            return jsonify({'error': 'Peer not found or no metrics available'}), 404
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metrics_bp.route('/bandwidth', methods=['GET'])
def get_bandwidth():
    """Récupère la bande passante actuelle de tous les peers"""
    try:
        bandwidth = PrometheusService.get_peer_bandwidth()
        
        if bandwidth is None:
            return jsonify({'error': 'No bandwidth data available'}), 404
        
        return jsonify({
            'bandwidth': bandwidth,
            'count': len(bandwidth) if isinstance(bandwidth, list) else 0
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metrics_bp.route('/peer/<public_key>/bandwidth', methods=['GET'])
def get_peer_bandwidth(public_key):
    """Récupère la bande passante actuelle d'un peer spécifique"""
    try:
        bandwidth = PrometheusService.get_peer_bandwidth(public_key)
        
        if bandwidth is None:
            return jsonify({'error': 'Peer not found or no bandwidth data available'}), 404
        
        return jsonify(bandwidth), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metrics_bp.route('/peer/<public_key>/history', methods=['GET'])
def get_peer_history(public_key):
    """Récupère l'historique de bande passante d'un peer"""
    try:
        # Récupérer le paramètre de durée (en heures, par défaut 1)
        duration_hours = request.args.get('hours', default=1, type=int)
        
        # Limiter la durée maximale à 24 heures
        if duration_hours > 24:
            duration_hours = 24
        
        history = PrometheusService.get_peer_history(public_key, duration_hours)
        
        if history is None:
            return jsonify({'error': 'Peer not found or no history available'}), 404
        
        return jsonify({
            'public_key': public_key,
            'duration_hours': duration_hours,
            'history': history,
            'data_points': len(history)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metrics_bp.route('/health', methods=['GET'])
def health_check():
    """Vérifie la santé de l'API et de Prometheus"""
    try:
        prometheus_healthy = PrometheusService.check_prometheus_health()
        
        return jsonify({
            'api_status': 'up',
            'prometheus_status': 'up' if prometheus_healthy else 'down',
            'prometheus_url': PrometheusService.query.__globals__['PROMETHEUS_URL']
        }), 200
    except Exception as e:
        return jsonify({
            'api_status': 'up',
            'prometheus_status': 'down',
            'error': str(e)
        }), 200