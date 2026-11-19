from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from models import RefreshToken
from security import (
    generate_refresh_token,
    hash_refresh_token,
    generate_token_family_id
)

def create_refresh_token(
    db: Session,
    user_id: int,
    family_id: str | None = None
):

    # 1. Generate original refresh token
    raw_token = generate_refresh_token()

    # 2. Hash the token
    token_hash = hash_refresh_token(raw_token)

    # 3. Generate family ID for new sessions
    if family_id is None:
        family_id = generate_token_family_id()

    # 4. Set expiration
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # 5. Create database record
    db_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        family_id=family_id,
        expires_at=expires_at
    )

    # 6. Save to database session
    db.add(db_token)
    db.flush()

    # 7. Return original token
    return raw_token