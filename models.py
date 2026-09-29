from sqlalchemy import Boolean, Column, Integer, String
from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    terms_accepted = Column(Boolean, nullable=False, default=False)
    terms_version = Column(String, nullable=False, default="1.0")
    terms_accepted_at = Column(DateTime(timezone=True), server_default=func.now())


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


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

    created_at = Column(DateTime(timezone=True), server_default=func.now())