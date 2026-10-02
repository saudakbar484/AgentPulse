import uuid
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, IdMixin, TenantMixin, TimestampMixin


class Persona(Base, IdMixin, TimestampMixin):
    __tablename__ = "personas"

    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)  # Nullable for built-in library
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    emotion: Mapped[str] = mapped_column(String(50), default="neutral", nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="en", nullable=False)
    traits: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    style_prompt: Mapped[str] = mapped_column(Text, nullable=False)


class Suite(Base, IdMixin, TimestampMixin):
    __tablename__ = "suites"

    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)
    thresholds: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    scenarios: Mapped[list["Scenario"]] = relationship("Scenario", back_populates="suite", cascade="all, delete-orphan")


class Scenario(Base, IdMixin, TimestampMixin):
    __tablename__ = "scenarios"

    suite_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suites.id", ondelete="CASCADE"), index=True, nullable=False)
    persona_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="SET NULL"), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    opening_message: Mapped[str] = mapped_column(Text, nullable=False)
    success_criteria: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    max_turns: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    origin: Mapped[str] = mapped_column(String(50), default="generated", nullable=False)  # generated, manual, trace
    embedding: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)

    suite: Mapped["Suite"] = relationship("Suite", back_populates="scenarios")
    persona: Mapped["Persona | None"] = relationship("Persona")
