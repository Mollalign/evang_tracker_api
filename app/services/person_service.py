from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outreachReport import OutreachReport
from app.models.person import Person
from app.models.user import User, UserRole
from app.schemas.person_schema import PersonCreate, PersonUpdate


class PersonService:
    """Business logic for CRUD operations on people linked to reports."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_report_or_raise(self, report_id: UUID) -> OutreachReport:
        result = await self.db.execute(
            select(OutreachReport).where(OutreachReport.id == report_id)
        )
        report = result.scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report

    async def _ensure_report_access(
        self,
        report_id: UUID,
        current_user: User,
    ) -> OutreachReport:
        report = await self._get_report_or_raise(report_id)
        if current_user.role == UserRole.admin:
            return report
        if report.evangelist_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own reports",
            )
        return report

    async def _get_person_or_raise(self, person_id: UUID) -> Person:
        result = await self.db.execute(
            select(Person).where(Person.id == person_id)
        )
        person = result.scalar_one_or_none()
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        return person

    async def ensure_person_access(
        self,
        person_id: UUID,
        current_user: User,
    ) -> Person:
        """Return person if user has access via associated report."""
        person = await self._get_person_or_raise(person_id)
        await self._ensure_report_access(person.report_id, current_user)
        return person

    async def list_people(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Person]:
        query = select(Person).join(OutreachReport)
        if current_user.role != UserRole.admin:
            query = query.where(OutreachReport.evangelist_id == current_user.id)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_person(
        self,
        person_in: PersonCreate,
        current_user: User,
    ) -> Person:
        await self._ensure_report_access(person_in.report_id, current_user)
        person = Person(**person_in.model_dump())
        self.db.add(person)
        await self.db.commit()
        await self.db.refresh(person)
        return person

    async def update_person(
        self,
        person_id: UUID,
        person_update: PersonUpdate,
        current_user: User,
    ) -> Person:
        person = await self.ensure_person_access(person_id, current_user)
        if person_update.report_id:
            await self._ensure_report_access(person_update.report_id, current_user)

        update_data = person_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(person, field, value)

        self.db.add(person)
        await self.db.commit()
        await self.db.refresh(person)
        return person

    async def delete_person(
        self,
        person_id: UUID,
        current_user: User,
    ) -> None:
        person = await self.ensure_person_access(person_id, current_user)
        await self.db.delete(person)
        await self.db.commit()

