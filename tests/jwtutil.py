import time

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from taskcommon.auth import JWTValidator

ISSUER = "http://localhost:8080/realms/taskapp"
_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTHER = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def make_validator() -> JWTValidator:
    return JWTValidator(issuer=ISSUER, allowed_azp=["task-frontend"], key_resolver=lambda _t: _KEY.public_key())


def token(sub="user-1", iss=ISSUER, exp_in=300, azp="task-frontend", signing_key=None) -> str:
    now = int(time.time())
    claims = {"sub": sub, "iss": iss, "iat": now, "exp": now + exp_in, "azp": azp,
              "preferred_username": sub}
    return jwt.encode(claims, signing_key or _KEY, algorithm="RS256", headers={"kid": "test"})


def bad_signature_token(**kw) -> str:
    return token(signing_key=_OTHER, **kw)


def auth(sub="user-1", **kw) -> dict:
    return {"Authorization": f"Bearer {token(sub=sub, **kw)}"}
