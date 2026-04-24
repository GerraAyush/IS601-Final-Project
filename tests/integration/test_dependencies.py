import pytest
import logging
from unittest.mock import patch, AsyncMock, MagicMock

from uuid import uuid4
from datetime import datetime, timezone
from fastapi import HTTPException, status

from app.auth.dependencies import get_current_user, get_current_active_user
from app.schemas.user import UserResponse
from app.models.user import User

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db_user(**overrides):
    """Return a mock SQLAlchemy User instance."""
    user = MagicMock(spec=User)
    user.id         = overrides.get("id",         uuid4())
    user.username   = overrides.get("username",   "testuser")
    user.email      = overrides.get("email",      "test@example.com")
    user.first_name = overrides.get("first_name", "Test")
    user.last_name  = overrides.get("last_name",  "User")
    user.is_active  = overrides.get("is_active",  True)
    user.is_verified = overrides.get("is_verified", True)
    user.created_at = overrides.get("created_at", datetime.now(timezone.utc))
    user.updated_at = overrides.get("updated_at", datetime.now(timezone.utc))
    return user


def _make_db(**overrides):
    """Return a mock DB session whose .query().filter().first() returns a user."""
    user = _make_db_user(**overrides)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user
    return db, user


def _make_payload(user_id=None, token_type="access", **extra):
    uid = str(user_id or uuid4())
    return {"sub": uid, "type": token_type, "jti": "abc123", **extra}


# ---------------------------------------------------------------------------
# get_current_user — happy path: valid token, user found in DB
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_valid_token_existing_user():
    """Valid token and existing DB user returns the User model instance."""
    db, user = _make_db()
    payload = _make_payload(user_id=user.id)

    with patch("app.auth.dependencies.decode_token", new_callable=AsyncMock, return_value=payload):
        result = await get_current_user(token="validtoken", db=db)

    assert result is user
    assert result.username == "testuser"
    assert result.email == "test@example.com"
    logger.info("valid token + existing user → returns DB User instance")


# ---------------------------------------------------------------------------
# get_current_user — invalid token (decode_token raises 401)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """decode_token raising HTTPException propagates as 401."""
    db, _ = _make_db()

    with patch(
        "app.auth.dependencies.decode_token",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="invalidtoken", db=db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"
    logger.info("invalid token → 401 propagated correctly")


# ---------------------------------------------------------------------------
# get_current_user — valid token but payload missing 'sub'
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_valid_token_incomplete_payload():
    """Payload with no 'sub' key raises 401."""
    db, _ = _make_db()
    payload_no_sub = {"type": "access", "jti": "xyz"}   # no "sub"

    with patch("app.auth.dependencies.decode_token", new_callable=AsyncMock, return_value=payload_no_sub):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="validtoken", db=db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"


# ---------------------------------------------------------------------------
# get_current_active_user — active user passes through
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_active_user_active():
    """Active user is returned unchanged."""
    db, user = _make_db(is_active=True)
    payload = _make_payload(user_id=user.id)

    with patch("app.auth.dependencies.decode_token", new_callable=AsyncMock, return_value=payload):
        current_user = await get_current_user(token="validtoken", db=db)

    active_user = await get_current_active_user(current_user=current_user)

    assert active_user is user
    assert active_user.is_active is True
    logger.info("active user passes get_current_active_user")


# ---------------------------------------------------------------------------
# get_current_active_user — inactive user raises 400
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_active_user_inactive():
    """Inactive user raises HTTP 400."""
    db, user = _make_db(is_active=False)
    payload = _make_payload(user_id=user.id)

    with patch("app.auth.dependencies.decode_token", new_callable=AsyncMock, return_value=payload):
        current_user = await get_current_user(token="validtoken", db=db)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(current_user=current_user)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Inactive user"


# ---------------------------------------------------------------------------
# get_current_user — sub present but user not in DB → 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_sub_only_dict():
    """'sub' in payload but user not found in DB raises 401."""
    user_id = uuid4()
    payload = _make_payload(user_id=user_id)

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None  # user not found

    with patch("app.auth.dependencies.decode_token", new_callable=AsyncMock, return_value=payload):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="anytoken", db=db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"
    logger.info("sub-only payload + missing DB user → 401")


# ---------------------------------------------------------------------------
# get_current_user — sub present, user found → returns User
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_uuid_return():
    """Valid sub + found DB user returns the User instance."""
    db, user = _make_db()
    payload = _make_payload(user_id=user.id)

    with patch("app.auth.dependencies.decode_token", new_callable=AsyncMock, return_value=payload):
        result = await get_current_user(token="anytoken", db=db)

    assert result is user
    assert result.is_active is True
    logger.info("valid sub + DB user found → returns User instance")


# ---------------------------------------------------------------------------
# get_current_user — unexpected exception from decode_token → 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_dict_no_username_no_sub():
    """Unexpected exception during decode_token is caught and re-raised as 401."""
    db, _ = _make_db()

    with patch(
        "app.auth.dependencies.decode_token",
        new_callable=AsyncMock,
        side_effect=Exception("unexpected error"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="anytoken", db=db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"


# ---------------------------------------------------------------------------
# get_current_user — RuntimeError from decode_token → 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_unexpected_token_data_type():
    """Any non-HTTPException raised during auth is caught and returned as 401."""
    db, _ = _make_db()

    with patch(
        "app.auth.dependencies.decode_token",
        new_callable=AsyncMock,
        side_effect=RuntimeError("unexpected type"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="anytoken", db=db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# get_current_user — DB query itself raises → 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_construction_exception():
    """Exception raised during DB lookup is caught and raised as 401."""
    user_id = uuid4()
    payload = _make_payload(user_id=user_id)

    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = Exception("db error")

    with patch("app.auth.dependencies.decode_token", new_callable=AsyncMock, return_value=payload):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="anytoken", db=db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# get_current_active_user — inactive user (built directly) raises 400
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_active_user_inactive_from_uuid_branch():
    """Inactive user passed directly to get_current_active_user raises 400."""
    inactive_user = _make_db_user(is_active=False)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(current_user=inactive_user)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Inactive user"
    logger.info("inactive user passed directly → 400 raised")
