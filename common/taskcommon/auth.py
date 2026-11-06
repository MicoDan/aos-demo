"""Keycloak JWT validation shared by both APIs.

JWKS is fetched from an internal URL (cached, refreshed on unknown `kid` so key
rotation works) while `iss` is validated against the PUBLIC issuer URL.
Tokens are never logged or stored.
"""
import logging
import os
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

import jwt
from fastapi import HTTPException, Request
from jwt import PyJWKClient

log = logging.getLogger("auth")


class AuthError(Exception):
    """Token is invalid -> 401."""


class AuthUnavailable(Exception):
    """Could not fetch signing keys -> 503."""


@dataclass(frozen=True)
class User:
    sub: str
    username: Optional[str] = None


class JWTValidator:
    def __init__(
        self,
        issuer: str,
        jwks_url: Optional[str] = None,
        allowed_azp: Iterable[str] = (),
        key_resolver: Optional[Callable[[str], object]] = None,
        leeway: int = 5,
    ):
        self.issuer = issuer
        self.allowed_azp = {a for a in allowed_azp if a}
        self.leeway = leeway
        self._resolver = key_resolver
        # cache_jwk_set + refresh on kid miss (PyJWT does this) => rotation safe
        self._jwks = (
            PyJWKClient(jwks_url, cache_keys=True, cache_jwk_set=True, lifespan=300, timeout=5)
            if jwks_url
            else None
        )
        if not self._resolver and not self._jwks:
            raise ValueError("need jwks_url or key_resolver")

    def validate(self, token: str) -> dict:
        try:
            if self._resolver:
                key = self._resolver(token)
            else:
                key = self._jwks.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=self.issuer,
                leeway=self.leeway,
                options={"require": ["exp", "iss", "sub"], "verify_aud": False},
            )
        except jwt.PyJWKClientConnectionError as e:
            log.error("JWKS fetch failed: %s", e)
            raise AuthUnavailable() from e
        except jwt.PyJWTError as e:
            raise AuthError(type(e).__name__) from e
        if self.allowed_azp and claims.get("azp") not in self.allowed_azp:
            raise AuthError("azp not allowed")
        return claims


def validator_from_env() -> JWTValidator:
    return JWTValidator(
        issuer=os.environ["KEYCLOAK_ISSUER"],
        jwks_url=os.environ["KEYCLOAK_JWKS_URL"],
        allowed_azp=os.environ.get("ALLOWED_AZP", "").split(","),
    )


def get_current_user(request: Request) -> User:
    """FastAPI dependency: requires a valid Bearer token. `app.state.validator` must be set."""
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "Missing bearer token", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = request.app.state.validator.validate(token.strip())
    except AuthError as e:
        raise HTTPException(401, f"Invalid token ({e})", headers={"WWW-Authenticate": "Bearer"})
    except AuthUnavailable:
        raise HTTPException(503, "Identity provider unavailable")
    return User(sub=claims["sub"], username=claims.get("preferred_username"))
