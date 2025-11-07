#!/usr/bin/env python3
"""
Security utilities: encrypted secrets storage, MFA (optional), and file encryption.
- Derives a symmetric key from owner passphrase (scrypt) and uses Fernet (AES128 in CBC? Actually Fernet AES128-CBC + HMAC) via cryptography.
- Stores secrets in ai_data/security/keystore.json (salt + encrypted blobs).
- Provides MFA via pyotp when available.
"""
import os
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any

CRYPTO_AVAILABLE = False
PYOTP_AVAILABLE = False

try:
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    from cryptography.hazmat.backends import default_backend
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except Exception:
    CRYPTO_AVAILABLE = False

try:
    import pyotp
    PYOTP_AVAILABLE = True
except Exception:
    PYOTP_AVAILABLE = False

class SecurityError(Exception):
    pass

class SecurityManager:
    def __init__(self, data_dir: str = "ai_data/security"):
        self.dir = Path(data_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.keystore_path = self.dir / "keystore.json"
        self._fernet: Optional[Fernet] = None
        self._state: Dict[str, Any] = {}

    def _derive_key(self, passphrase: str, salt: bytes) -> bytes:
        if not CRYPTO_AVAILABLE:
            raise SecurityError("cryptography is required: pip install cryptography pyotp")
        kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1, backend=default_backend())
        key = kdf.derive(passphrase.encode('utf-8'))
        return base64.urlsafe_b64encode(key)

    def unlock_or_create(self, passphrase: str) -> bool:
        """Unlock existing keystore or create a new one.
        Returns True if created new, False if unlocked existing.
        """
        created = False
        if self.keystore_path.exists():
            with open(self.keystore_path, 'r', encoding='utf-8') as f:
                self._state = json.load(f)
        else:
            self._state = {
                "version": 1,
                "salt": base64.b64encode(os.urandom(16)).decode('ascii'),
                "device_token": base64.urlsafe_b64encode(os.urandom(18)).decode('ascii'),
                "secrets": {},
                "mfa": {"enabled": False, "secret_enc": None},
                "created_at": __import__('datetime').datetime.utcnow().isoformat(),
            }
            created = True
            with open(self.keystore_path, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, indent=2)
        key = self._derive_key(passphrase, base64.b64decode(self._state["salt"]))
        self._fernet = Fernet(key)
        return created

    def _save(self):
        with open(self.keystore_path, 'w', encoding='utf-8') as f:
            json.dump(self._state, f, indent=2)

    def device_token(self) -> str:
        return self._state.get("device_token", "")

    def set_secret(self, name: str, value: str) -> None:
        if not self._fernet:
            raise SecurityError("keystore is locked")
        token = self._fernet.encrypt(value.encode('utf-8')).decode('ascii')
        self._state.setdefault("secrets", {})[name] = token
        self._save()

    def get_secret(self, name: str) -> Optional[str]:
        if not self._fernet:
            raise SecurityError("keystore is locked")
        token = self._state.get("secrets", {}).get(name)
        if not token:
            return None
        try:
            return self._fernet.decrypt(token.encode('ascii')).decode('utf-8')
        except Exception:
            return None

    def delete_secret(self, name: str) -> bool:
        if name in self._state.get("secrets", {}):
            del self._state["secrets"][name]
            self._save()
            return True
        return False

    def list_secrets(self):
        return list(self._state.get("secrets", {}).keys())

    def enable_mfa(self) -> Optional[Dict[str, str]]:
        if not PYOTP_AVAILABLE:
            # still create container for backup codes even without TOTP
            self._state['mfa'] = {"enabled": False, "secret_enc": None, "backup_codes": []}
            self._save()
            return None
        secret = pyotp.random_base32()
        enc = self._fernet.encrypt(secret.encode('utf-8')).decode('ascii')
        # generate 10 backup codes
        import secrets
        codes = [secrets.token_hex(4) for _ in range(10)]
        enc_codes = [self._fernet.encrypt(c.encode('utf-8')).decode('ascii') for c in codes]
        self._state['mfa'] = {"enabled": True, "secret_enc": enc, "backup_codes": enc_codes}
        self._save()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name="Saraphina Owner", issuer_name="Saraphina")
        return {"secret": secret, "provisioning_uri": uri, "backup_codes": codes}

    def mfa_enabled(self) -> bool:
        m = self._state.get('mfa', {})
        return bool(m.get('enabled')) and bool(m.get('secret_enc'))

    def verify_mfa(self, code: str) -> bool:
        # Try TOTP first
        if PYOTP_AVAILABLE and self.mfa_enabled():
            try:
                enc = self._state['mfa']['secret_enc']
                secret = self._fernet.decrypt(enc.encode('ascii')).decode('utf-8')
                totp = pyotp.TOTP(secret)
                if bool(totp.verify(code, valid_window=1)):
                    return True
            except Exception:
                pass
        # Fallback to backup codes
        try:
            bcodes = self._state.get('mfa', {}).get('backup_codes', [])
            for i, enc in enumerate(list(bcodes)):
                try:
                    plain = self._fernet.decrypt(enc.encode('ascii')).decode('utf-8')
                    if code == plain:
                        # consume code
                        del self._state['mfa']['backup_codes'][i]
                        self._save()
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def encrypt_file(self, src: str, dest: str) -> str:
        if not self._fernet:
            raise SecurityError("keystore is locked")
        data = Path(src).read_bytes()
        enc = self._fernet.encrypt(data)
        out = Path(dest)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(enc)
        return str(out)

    def decrypt_file(self, src: str, dest: str) -> str:
        if not self._fernet:
            raise SecurityError("keystore is locked")
        data = Path(src).read_bytes()
        dec = self._fernet.decrypt(data)
        out = Path(dest)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(dec)
        return str(out)

    def generate_owner_keys(self) -> Optional[Dict[str, str]]:
        """Generate Ed25519 keypair and store in keystore if absent. Returns pubkey."""
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives import serialization
        except Exception:
            return None
        existing = self.get_secret('owner_privkey') if self._fernet else None
        if existing:
            return {"owner_pubkey": self.get_secret('owner_pubkey') or ''}
        priv = Ed25519PrivateKey.generate()
        priv_pem = priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        pub = priv.public_key()
        pub_pem = pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        self.set_secret('owner_privkey', priv_pem)
        self.set_secret('owner_pubkey', pub_pem)
        return {"owner_pubkey": pub_pem}

    def sign_bytes(self, data: bytes) -> Optional[str]:
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives import serialization
            import base64
            pem = self.get_secret('owner_privkey')
            if not pem:
                return None
            priv = serialization.load_pem_private_key(pem.encode('utf-8'), password=None)
            sig = priv.sign(data)
            return base64.b64encode(sig).decode('ascii')
        except Exception:
            return None

    def verify_signature(self, data: bytes, signature_b64: str, pubkey_pem: Optional[str] = None) -> bool:
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            from cryptography.hazmat.primitives import serialization
            import base64
            pub_pem = pubkey_pem or self.get_secret('owner_pubkey') or ''
            if not pub_pem:
                return False
            pub = serialization.load_pem_public_key(pub_pem.encode('utf-8'))
            pub.verify(base64.b64decode(signature_b64), data)
            return True
        except Exception:
            return False

    def rekey(self, new_passphrase: str) -> None:
        """Re-encrypt keystore with a new passphrase and fresh salt."""
        if not self._fernet:
            raise SecurityError("keystore is locked")
        # Decrypt all secrets with old key
        secrets_plain: Dict[str, str] = {}
        for k, token in self._state.get('secrets', {}).items():
            try:
                secrets_plain[k] = self._fernet.decrypt(token.encode('ascii')).decode('utf-8')
            except Exception:
                secrets_plain[k] = ''
        # Decrypt MFA secret if present
        mfa_enc = (self._state.get('mfa') or {}).get('secret_enc')
        mfa_plain = None
        if mfa_enc:
            try:
                mfa_plain = self._fernet.decrypt(mfa_enc.encode('ascii')).decode('utf-8')
            except Exception:
                mfa_plain = None
        # Decrypt backup codes
        bcodes = (self._state.get('mfa') or {}).get('backup_codes', [])
        bcodes_plain = []
        for enc in bcodes:
            try:
                bcodes_plain.append(self._fernet.decrypt(enc.encode('ascii')).decode('utf-8'))
            except Exception:
                pass
        # Generate new salt and key
        new_salt = os.urandom(16)
        new_key = self._derive_key(new_passphrase, new_salt)
        new_fernet = Fernet(new_key)
        # Update state
        self._state['salt'] = base64.b64encode(new_salt).decode('ascii')
        # Re-encrypt secrets
        self._state['secrets'] = {k: new_fernet.encrypt(v.encode('utf-8')).decode('ascii') for k, v in secrets_plain.items()}
        if mfa_plain is not None:
            self._state.setdefault('mfa', {})['secret_enc'] = new_fernet.encrypt(mfa_plain.encode('utf-8')).decode('ascii')
        if bcodes_plain:
            self._state.setdefault('mfa', {})['backup_codes'] = [new_fernet.encrypt(c.encode('utf-8')).decode('ascii') for c in bcodes_plain]
        self._fernet = new_fernet
        self._save()
