import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, IdMixin, TimestampMixin


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Run(Base, IdMixin, TimestampMixin):
    __tablename__ = "runs"

    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False)
    suite_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suites.id", ondelete="CASCADE"), index=True, nullable=False)
    agent_version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=RunStatus.QUEUED.value, index=True, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)  # models, concurrency, budget, seed
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verdict: Mapped[str | None] = mapped_column(String(50), nullable=True)  # PASS, FAIL
    score_overall: Mapped[float | None] = mapped_column(Float, nullable=True)

    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="run", cascade="all, delete-orphan")


class Conversation(Base, IdMixin, TimestampMixin):
    __tablename__ = "conversations"

    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), index=True, nullable=False)
    scenario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False)
    termination_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)  # goal_reached, give_up, max_turns, error
    latency_ms_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped["Run"] = relationship("Run", back_populates="conversations")
    scenario: Mapped["Scenario"] = relationship("Scenario")
    turns: Mapped[list["Turn"]] = relationship("Turn", back_populates="conversation", cascade="all, delete-orphan", order_by="Turn.idx")
    evaluations: Mapped[list["Evaluation"]] = relationship("Evaluation", back_populates="conversation", cascade="all, delete-orphan")


class Turn(Base, IdMixin, TimestampMixin):
    __tablename__ = "turns"

    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, agent, system, tool
    content: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="turns")

    __table_args__ = (
        Index("ix_turns_conv_idx", "conversation_id", "idx", unique=True),
    )
