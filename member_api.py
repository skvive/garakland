"""Member-owned demo preferences for GARAKLAND.

Authenticated Neon Auth JWTs are signature-verified against this project's JWKS.
Never accept a user_id or email supplied in a browser request as authorization.
Coupon entries are DEMO bookmarks, not cash-value tickets or redemption rights.
"""
from __future__ import annotations
import json
import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from uuid import UUID

import jwt
from jwt import PyJWKClient

from db_adapter import DB_LOCK, db_connect

AUTH_PUBLIC = Path(__file__).resolve().parent / "auth" / "config.public.json"
DEMO_COUPONS = {"c-sea", "c-fruit", "c-meat", "c-kitchen"}
DEMO_STORES = {"demo-sea", "demo-fruit", "demo-meat", "demo-kitchen"}
ID_FORMAT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,79}$")


class MemberError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(message)


@lru_cache(maxsize=1)
def auth_url() -> str:
    configured = os.environ.get("GARAK_NEON_AUTH_URL", "").strip()
    if not configured:
        configured = json.loads(AUTH_PUBLIC.read_text("utf-8"))["authUrl"]
    if not configured.startswith("https://") or not configured.endswith("/auth"):
        raise RuntimeError("Invalid Neon Auth issuer URL")
    return configured.rstrip("/")


@lru_cache(maxsize=1)
def jwks_client() -> PyJWKClient:
    return PyJWKClient(auth_url() + "/.well-known/jwks.json", cache_jwk_set=True, lifespan=300)


def member_id(request) -> str:
    header = request.headers.get("Authorization", "")
    match = re.fullmatch(r"Bearer ([A-Za-z0-9._-]{32,12000})", header.strip())
    if not match:
        raise MemberError(401, "Google 또는 이메일 로그인 후 다시 시도해 주세요.")
    token = match.group(1)
    try:
        key = jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=["RS256", "ES256", "EdDSA"],
            issuer=auth_url(),
            options={"require": ["sub", "exp"], "verify_aud": False},
            leeway=30,
        )
        audience = claims.get("aud")
        if audience:
            values = [audience] if isinstance(audience, str) else audience
            if not isinstance(values, list) or not any(a in (auth_url(), "authenticated") for a in values):
                raise MemberError(401, "로그인 토큰의 사용 대상이 올바르지 않습니다.")
        identity = str(UUID(str(claims["sub"])))
        return identity
    except MemberError:
        raise
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise MemberError(401, "로그인 유효기간이 만료되었거나 인증이 올바르지 않습니다.")
    except Exception:
        # Fail closed if JWKS cannot be loaded. Never trust an unverified subject.
        raise MemberError(503, "인증 서버 연결을 확인할 수 없습니다. 잠시 후 다시 시도해 주세요.")


def setup() -> None:
    with DB_LOCK, db_connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS member_favorite_stores (
          user_id TEXT NOT NULL,
          store_id TEXT NOT NULL,
          created_at TEXT NOT NULL,
          PRIMARY KEY (user_id, store_id)
        );
        CREATE INDEX IF NOT EXISTS idx_member_favorites_user
          ON member_favorite_stores(user_id, created_at);
        CREATE TABLE IF NOT EXISTS member_demo_coupons (
          user_id TEXT NOT NULL,
          coupon_id TEXT NOT NULL,
          created_at TEXT NOT NULL,
          PRIMARY KEY (user_id, coupon_id)
        );
        CREATE INDEX IF NOT EXISTS idx_member_coupons_user
          ON member_demo_coupons(user_id, created_at);
        """)
        db.commit()


def read_state(user_id: str) -> dict:
    with DB_LOCK, db_connect() as db:
        favorites = [r["store_id"] for r in db.execute(
            "SELECT store_id FROM member_favorite_stores WHERE user_id=? ORDER BY created_at DESC, store_id",
            (user_id,),
        )]
        coupons = [r["coupon_id"] for r in db.execute(
            "SELECT coupon_id FROM member_demo_coupons WHERE user_id=? ORDER BY created_at DESC, coupon_id",
            (user_id,),
        )]
    return {"favorites": favorites, "coupons": coupons, "demoOnly": True}


def _valid_id(value: object) -> str:
    if not isinstance(value, str) or not ID_FORMAT.fullmatch(value):
        raise MemberError(400, "저장할 매장 또는 쿠폰 번호가 올바르지 않습니다.")
    return value


def _save_or_remove(user_id: str, path: str, body: dict) -> dict:
    target = "favorite" if path.endswith("/favorites") else "coupon"
    item_id = _valid_id(body.get("storeId") if target == "favorite" else body.get("couponId"))
    action = body.get("action")
    if action not in ("add", "remove"):
        raise MemberError(400, "저장 또는 삭제 동작을 선택해야 합니다.")
    if target == "coupon" and item_id not in DEMO_COUPONS:
        raise MemberError(404, "확인되지 않은 시연 쿠폰입니다.")
    table = "member_favorite_stores" if target == "favorite" else "member_demo_coupons"
    field = "store_id" if target == "favorite" else "coupon_id"
    with DB_LOCK, db_connect() as db:
        if target == "favorite" and item_id not in DEMO_STORES:
            exists = db.execute("SELECT id FROM stores WHERE id=?", (item_id,)).fetchone()
            if not exists:
                raise MemberError(404, "확인되지 않은 업소입니다.")
        if action == "add":
            db.execute(
                f"INSERT INTO {table} (user_id,{field},created_at) VALUES (?,?,?) "
                f"ON CONFLICT (user_id,{field}) DO NOTHING",
                (user_id, item_id, datetime.now(timezone.utc).isoformat()),
            )
        else:
            db.execute(
                f"DELETE FROM {table} WHERE user_id=? AND {field}=?",
                (user_id, item_id),
            )
        db.commit()
    return read_state(user_id)


def dispatch_get(request, path: str):
    if path != "/api/member/state":
        return False
    try:
        identity = member_id(request)
        return request.send_json(200, read_state(identity))
    except MemberError as err:
        return request.send_json(err.status, {"error": str(err)})
    except Exception:
        return request.send_json(503, {"error": "회원 데이터베이스에 연결할 수 없습니다."})


def dispatch_post(request, path: str, body: dict):
    if path not in ("/api/member/favorites", "/api/member/coupons"):
        return False
    try:
        identity = member_id(request)
        state = _save_or_remove(identity, path, body)
        return request.send_json(200, state)
    except MemberError as err:
        return request.send_json(err.status, {"error": str(err)})
    except Exception:
        return request.send_json(503, {"error": "회원 데이터를 저장하지 못했습니다."})
