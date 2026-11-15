from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.sql import func

import secrets,hashlib
import datetime as dt


from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    terms_accepted = Column(Boolean, nullable=False, default=False)
    terms_version = Column(String, nullable=False, default="1.0")
    terms_accepted_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=True)
    is_direct = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false"
    )


class RoomMember(Base):
    __tablename__ = "room_members"

    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        primary_key=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

REFRESH_TTL = dt.timedelta(days=7)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)