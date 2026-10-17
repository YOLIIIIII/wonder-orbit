from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def now():
    return datetime.now(timezone.utc)


def uid():
    return str(uuid4())


class Timestamp:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Star(Timestamp, Base):
    __tablename__ = "stars"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(160))
    original_text: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80))
    tags: Mapped[list] = mapped_column(JSON, default=list)
    interest_reason: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(20))
    source_reference: Mapped[str | None] = mapped_column(Text)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer)
    estimated_budget: Mapped[float | None] = mapped_column(Float)
    energy_level: Mapped[str | None] = mapped_column(String(12))
    status: Mapped[str] = mapped_column(String(20), default="collected")


class Quest(Timestamp, Base):
    __tablename__ = "quests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    proposal_key: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    estimated_budget: Mapped[float | None] = mapped_column(Float)
    energy_level: Mapped[str] = mapped_column(String(12))
    steps: Mapped[list] = mapped_column(JSON)
    rationale: Mapped[str] = mapped_column(Text)
    uncertainties: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="accepted")


class QuestStar(Base):
    __tablename__ = "quest_stars"
    quest_id: Mapped[str] = mapped_column(ForeignKey("quests.id", ondelete="CASCADE"), primary_key=True)
    star_id: Mapped[str] = mapped_column(ForeignKey("stars.id", ondelete="RESTRICT"), primary_key=True)


class Reflection(Base):
    __tablename__ = "reflections"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    quest_id: Mapped[str] = mapped_column(ForeignKey("quests.id", ondelete="CASCADE"), unique=True)
    outcome: Mapped[str] = mapped_column(String(20))
    user_feedback: Mapped[str] = mapped_column(Text)
    liked_aspects: Mapped[list] = mapped_column(JSON)
    disliked_aspects: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class UserPreference(Timestamp, Base):
    __tablename__ = "user_preferences"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    explicit: Mapped[dict] = mapped_column(JSON, default=dict)
    candidates: Mapped[list] = mapped_column(JSON, default=list)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    request_key: Mapped[str] = mapped_column(String(100), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    request_type: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    model_name: Mapped[str] = mapped_column(String(120))
    mode: Mapped[str] = mapped_column(String(12))
    events: Mapped[list] = mapped_column(JSON, default=list)
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    elapsed_ms: Mapped[int | None] = mapped_column(Integer)
    error_type: Mapped[str | None] = mapped_column(String(80))
    summary: Mapped[str | None] = mapped_column(Text)
    decisions: Mapped[dict] = mapped_column(JSON, default=dict)
