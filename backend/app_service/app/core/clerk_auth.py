from httpx import AsyncClient
from jose import jwk, jwt, JWTError
from jose.constants import Algorithms
from fastapi import HTTPException, status
from app.config import settings

_jwks_cache: list[dict] | None = None


async def _fetch_jwks() -> list[dict]:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    if not settings.CLERK_ISSUER:
        return []
    try:
        async with AsyncClient() as client:
            resp = await client.get(f"{settings.CLERK_ISSUER}/.well-known/jwks.json", timeout=10)
            if resp.status_code == 200:
                _jwks_cache = resp.json().get("keys", [])
                return _jwks_cache
    except Exception:
        pass
    return []


async def verify_clerk_token(token: str) -> dict:
    jwks_keys = await _fetch_jwks()
    if not jwks_keys:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Clerk not configured")

    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    alg = unverified_header.get("alg", "RS256")

    key_data = None
    for k in jwks_keys:
        if k.get("kid") == kid:
            key_data = k
            break
    if not key_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid key ID")

    try:
        public_key = jwk.construct(key_data, algorithm=alg)
        payload = jwt.decode(token, public_key, algorithms=[alg], options={"verify_aud": False})
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Clerk token")
