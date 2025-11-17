from flask import Flask
from routes.peers import peers_bp
from routes.server import server_bp
from routes.wireguard import wireguard_bp

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(server_bp)
    app.register_blueprint(peers_bp)
    app.register_blueprint(wireguard_bp)
    
    return app
