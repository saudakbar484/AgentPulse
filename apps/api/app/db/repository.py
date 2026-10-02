import uuid
from typing import Any, Generic, TypeVar
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, org_id: uuid.UUID, entity_id: uuid.UUID) -> ModelType | None:
        stmt = select(self.model).where(
            self.model.org_id == org_id,  # type: ignore[attr-defined]
            self.model.id == entity_id     # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        org_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> list[ModelType]:
        stmt = (
            select(self.model)
            .where(self.model.org_id == org_id)  # type: ignore[attr-defined]
            .limit(limit)
            .offset(offset)
            .order_by(self.model.created_at.desc())  # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, entity: ModelType) -> ModelType:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(
        self,
        org_id: uuid.UUID,
        entity_id: uuid.UUID,
        values: dict[str, Any]
    ) -> ModelType | None:
        stmt = (
            update(self.model)
            .where(
                self.model.org_id == org_id,  # type: ignore[attr-defined]
                self.model.id == entity_id     # type: ignore[attr-defined]
            )
            .values(**values)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, org_id: uuid.UUID, entity_id: uuid.UUID) -> bool:
        stmt = delete(self.model).where(
            self.model.org_id == org_id,  # type: ignore[attr-defined]
            self.model.id == entity_id     # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
