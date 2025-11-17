import base64
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

class KeyService:
    @staticmethod
    def generate_wireguard_keys():
        """Generate WireGuard private and public keys"""
        private_key = x25519.X25519PrivateKey.generate()
        
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        private_key_b64 = base64.b64encode(private_bytes).decode('utf-8')
        public_key_b64 = base64.b64encode(public_bytes).decode('utf-8')
        
        return private_key_b64, public_key_b64

    @staticmethod
    def generate_preshared_key():
        """Generate a preshared key (symmetric)"""
        psk = x25519.X25519PrivateKey.generate()
        psk_bytes = psk.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        return base64.b64encode(psk_bytes).decode('utf-8')