"""ECDSA key management and signing for evidence receipts."""
import base64
import hashlib
import os
from pathlib import Path

import boto3
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils


KEYS_DIR = Path(__file__).resolve().parent.parent.parent / "keys"


class KeyManager:
    """Manages ECDSA P-256 keys for signing evidence receipts."""

    def __init__(self, private_key=None, public_key=None, key_id: str = "", *, kms_key_id: str = "") -> None:
        self._private_key = private_key
        self._public_key = public_key
        self.key_id = key_id
        self._kms_key_id = kms_key_id
        self._kms_client = None
        if kms_key_id:
            self._kms_client = boto3.client("kms")

    @classmethod
    def from_kms(cls, key_id: str) -> "KeyManager":
        """Create a KeyManager backed by AWS KMS."""
        return cls(key_id=key_id, kms_key_id=key_id)

    @classmethod
    def generate_dev_key(cls) -> "KeyManager":
        """Generate a new ECDSA P-256 key pair and save to backend/keys/."""
        KEYS_DIR.mkdir(parents=True, exist_ok=True)

        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        # Save private key PEM
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        (KEYS_DIR / "dev_private.pem").write_bytes(private_pem)

        # Save public key PEM
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        (KEYS_DIR / "dev_public.pem").write_bytes(public_pem)

        # Compute key_id as SHA-256 fingerprint of public DER, first 16 hex chars
        public_der = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        key_id = hashlib.sha256(public_der).hexdigest()[:16]

        return cls(private_key=private_key, public_key=public_key, key_id=key_id)

    @classmethod
    def load_private_key(cls, path: str | Path) -> "KeyManager":
        """Load a private key from PEM file and derive the public key."""
        pem_bytes = Path(path).read_bytes()
        private_key = serialization.load_pem_private_key(pem_bytes, password=None)
        public_key = private_key.public_key()

        public_der = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        key_id = hashlib.sha256(public_der).hexdigest()[:16]

        return cls(private_key=private_key, public_key=public_key, key_id=key_id)

    @classmethod
    def load_public_key(cls, path: str | Path) -> "KeyManager":
        """Load a public key from PEM file (verify-only)."""
        pem_bytes = Path(path).read_bytes()
        public_key = serialization.load_pem_public_key(pem_bytes)

        public_der = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        key_id = hashlib.sha256(public_der).hexdigest()[:16]

        return cls(public_key=public_key, key_id=key_id)

    def sign(self, data_hex: str) -> str:
        """Sign the hex string bytes with ECDSA-SHA256, return base64-encoded signature."""
        if self._kms_client:
            response = self._kms_client.sign(
                KeyId=self._kms_key_id,
                Message=data_hex.encode("utf-8"),
                MessageType="RAW",
                SigningAlgorithm="ECDSA_SHA_256",
            )
            return base64.b64encode(response["Signature"]).decode("utf-8")
        if self._private_key is None:
            raise ValueError("No private key loaded")
        signature = self._private_key.sign(
            data_hex.encode("utf-8"),
            ec.ECDSA(hashes.SHA256()),
        )
        return base64.b64encode(signature).decode("utf-8")

    def verify_signature(self, data_hex: str, signature_b64: str) -> bool:
        """Verify a signature. Returns True if valid, False otherwise."""
        if self._kms_client:
            try:
                response = self._kms_client.verify(
                    KeyId=self._kms_key_id,
                    Message=data_hex.encode("utf-8"),
                    MessageType="RAW",
                    Signature=base64.b64decode(signature_b64),
                    SigningAlgorithm="ECDSA_SHA_256",
                )
                return response["SignatureValid"]
            except Exception:
                return False
        if self._public_key is None:
            raise ValueError("No public key loaded")
        try:
            signature = base64.b64decode(signature_b64)
            self._public_key.verify(
                signature,
                data_hex.encode("utf-8"),
                ec.ECDSA(hashes.SHA256()),
            )
            return True
        except Exception:
            return False
