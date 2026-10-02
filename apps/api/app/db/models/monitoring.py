import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, IdMixin, TimestampMixin


class Trace(Base, IdMixin, TimestampMixin):
    __tablename__ = "traces"

    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="api", nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    redacted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sampled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ingested", nullable=False)

    turns: Mapped[list["TraceTurn"]] = relationship("TraceTurn", back_populates="trace", cascade="all, delete-orphan", order_by="TraceTurn.idx")


class TraceTurn(Base, IdMixin, TimestampMixin):
    __tablename__ = "trace_turns"

    trace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("traces.id", ondelete="CASCADE"), index=True, nullable=False)
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    trace: Mapped["Trace"] = relationship("Trace", back_populates="turns")


class Monitor(Base, IdMixin, TimestampMixin):
    __tablename__ = "monitors"

    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    metrics: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    sampling_rate: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    baseline_ref: Mapped[str] = mapped_column(String(100), default="trailing_7d", nullable=False)
    rules: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="monitor", cascade="all, delete-orphan")


class MonitorWindow(Base, IdMixin, TimestampMixin):
    __tablename__ = "monitor_windows"

    monitor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("monitors.id", ondelete="CASCADE"), index=True, nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metric_key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mean_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fail_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    stats: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class Alert(Base, IdMixin, TimestampMixin):
    __tablename__ = "alerts"

    monitor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("monitors.id", ondelete="CASCADE"), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="warning", nullable=False)  # info, warning, critical
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open", index=True, nullable=False)  # open, acknowledged, resolved
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    monitor: Mapped["Monitor"] = relationship("Monitor", back_populates="alerts")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="alert", cascade="all, delete-orphan")


class Notification(Base, IdMixin, TimestampMixin):
    __tablename__ = "notifications"

    alert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # slack, email, webhook
    status: Mapped[str] = mapped_column(String(50), default="sent", nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    alert: Mapped["Alert"] = relationship("Alert", back_populates="notifications")
