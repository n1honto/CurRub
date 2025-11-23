"""
Модуль криптографической защиты
"""
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import hashlib
import json


class CryptoService:
    """Сервис криптографической защиты"""
    
    @staticmethod
    def generate_key_pair():
        """Генерация пары ключей RSA"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    @staticmethod
    def sign_data(data: str, private_key) -> str:
        """Подписание данных электронной подписью"""
        signature = private_key.sign(
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature.hex()
    
    @staticmethod
    def verify_signature(data: str, signature: str, public_key) -> bool:
        """Проверка электронной подписи"""
        try:
            public_key.verify(
                bytes.fromhex(signature),
                data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    @staticmethod
    def hash_data(data: str) -> str:
        """Хеширование данных SHA-256"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def serialize_public_key(public_key) -> str:
        """Сериализация публичного ключа"""
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode()
    
    @staticmethod
    def deserialize_public_key(pem_str: str):
        """Десериализация публичного ключа"""
        return serialization.load_pem_public_key(
            pem_str.encode(),
            backend=default_backend()
        )

