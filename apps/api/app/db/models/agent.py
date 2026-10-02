import uuid
from enum import Enum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, IdMixin, TenantMixin, TimestampMixin


class AdapterType(str, Enum):
    HTTP_JSON = "http_json"
    OPENAI_COMPAT = "openai_compat"
    WEBSOCKET = "websocket"
    MOCK = "mock"


class Agent(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "agents"

    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    intended_use: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone_guidelines: Mapped[str | None] = mapped_column(Text, nullable=True)
    prohibited_behaviours: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    languages: Mapped[list[str]] = mapped_column(JSONB, default=lambda: ["en"], nullable=False)
    adapter_type: Mapped[str] = mapped_column(String(50), default=AdapterType.HTTP_JSON.value, nullable=False)
    adapter_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    version_label: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)

    knowledge_docs: Mapped[list["KnowledgeDoc"]] = relationship("KnowledgeDoc", back_populates="agent", cascade="all, delete-orphan")


class KnowledgeDoc(Base, IdMixin, TimestampMixin):
    __tablename__ = "knowledge_docs"

    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="processed", nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="knowledge_docs")
    chunks: Mapped[list["KnowledgeChunk"]] = relationship("KnowledgeChunk", back_populates="doc", cascade="all, delete-orphan")


class KnowledgeChunk(Base, IdMixin, TimestampMixin):
    __tablename__ = "knowledge_chunks"

    doc_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_docs.id", ondelete="CASCADE"), index=True, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)

    doc: Mapped["KnowledgeDoc"] = relationship("KnowledgeDoc", back_populates="chunks")
