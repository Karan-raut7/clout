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
from sqlalchemy import UniqueConstraint,CheckConstraint

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





from sqlalchemy import UniqueConstraint, CheckConstraint

class DMThread(Base):
    __tablename__ = "dm_threads"

    id = Column(Integer, primary_key=True, index=True)
    user_a_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_b_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_a_id", "user_b_id", name="uq_dm_pair"),
        CheckConstraint("user_a_id < user_b_id", name="ck_dm_order"),
    )


class DMMessage(Base):
    __tablename__ = "dm_messages"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("dm_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    token_hash = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True
    )

    family_id = Column(
        String(36),
        nullable=False,
        index=True
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False
    )

    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    replaced_by_token_hash = Column(
        String(64),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )