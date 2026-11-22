"""Tests for ECDSA key management and signing."""
from app.evidence.signing import KeyManager


class TestKeyGeneration:
    def test_generate_dev_key(self):
        """Key generation produces a KeyManager with a key_id."""
        km = KeyManager.generate_dev_key()
        assert km.key_id
        assert len(km.key_id) == 16

    def test_sign_and_verify_roundtrip(self):
        """Signed data verifies correctly with the same key."""
        km = KeyManager.generate_dev_key()
        data = "abcdef1234567890"
        signature = km.sign(data)
        assert km.verify_signature(data, signature) is True

    def test_tampered_data_fails_verification(self):
        """Modified data does not verify against original signature."""
        km = KeyManager.generate_dev_key()
        data = "original_data_hash"
        signature = km.sign(data)
        assert km.verify_signature("tampered_data_hash", signature) is False

    def test_wrong_key_fails_verification(self):
        """Signature from one key does not verify with a different key."""
        km1 = KeyManager.generate_dev_key()
        km2 = KeyManager.generate_dev_key()
        data = "some_receipt_root_hash"
        signature = km1.sign(data)
        assert km2.verify_signature(data, signature) is False


class TestKeyPersistence:
    def test_load_private_key(self, tmp_path):
        """Saved key can be loaded back and used for signing."""
        from app.evidence.signing import KEYS_DIR

        km = KeyManager.generate_dev_key()
        loaded = KeyManager.load_private_key(KEYS_DIR / "dev_private.pem")
        assert loaded.key_id == km.key_id

        data = "test_data"
        sig = loaded.sign(data)
        assert loaded.verify_signature(data, sig) is True

    def test_load_public_key_verify_only(self):
        """Public key can verify but cannot sign."""
        from app.evidence.signing import KEYS_DIR
        import pytest

        km = KeyManager.generate_dev_key()
        pub_km = KeyManager.load_public_key(KEYS_DIR / "dev_public.pem")
        assert pub_km.key_id == km.key_id

        data = "test_data"
        sig = km.sign(data)
        assert pub_km.verify_signature(data, sig) is True

        with pytest.raises(ValueError, match="No private key"):
            pub_km.sign(data)
