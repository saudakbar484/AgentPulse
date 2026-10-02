import uuid
from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, IdMixin, TimestampMixin


class MetricDefinition(Base, IdMixin, TimestampMixin):
    __tablename__ = "metric_definitions"

    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)  # Nullable for built-in
    key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # rule, llm
    rubric: Mapped[str] = mapped_column(Text, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    is_blocking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)


class Evaluation(Base, IdMixin, TimestampMixin):
    __tablename__ = "evaluations"

    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    turn_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("turns.id", ondelete="CASCADE"), nullable=True)
    metric_key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    metric_version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    verdict: Mapped[str] = mapped_column(String(50), nullable=False)  # pass, fail, unsure
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)  # { turn: idx, quote: str, verified: bool }
    judge_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="evaluations")


class HumanLabel(Base, IdMixin, TimestampMixin):
    __tablename__ = "human_labels"

    evaluation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)  # pass, fail
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class CalibrationReport(Base, IdMixin, TimestampMixin):
    __tablename__ = "calibration_reports"

    metric_key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    judge_model: Mapped[str] = mapped_column(String(100), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    cohen_kappa: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    confusion_matrix: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
