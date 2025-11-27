from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outreachReport import OutreachReport
from app.models.user import User, UserRole
from app.schemas.report_schema import ReportCreate, ReportUpdate


class ReportService:
    """Business logic for CRUD operations on outreach reports."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_reports(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
    ) -> List[OutreachReport]:
        """Return reports scoped by user role."""
        query = select(OutreachReport).order_by(desc(OutreachReport.date))

        if current_user.role != UserRole.admin:
            query = query.where(OutreachReport.evangelist_id == current_user.id)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_report(
        self,
        report_in: ReportCreate,
        current_user: User,
    ) -> OutreachReport:
        """Create a report owned by the current user."""
        report = OutreachReport(
            **report_in.model_dump(),
            evangelist_id=current_user.id,
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def update_report(
        self,
        report: OutreachReport,
        report_update: ReportUpdate,
    ) -> OutreachReport:
        """Apply partial updates to an existing report."""
        update_data = report_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(report, field, value)

        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def delete_report(self, report: OutreachReport) -> None:
        """Delete a report."""
        await self.db.delete(report)
        await self.db.commit()

    async def get_report_by_id(
        self,
        report_id: UUID,
        current_user: User,
    ) -> OutreachReport:
        """
        Fetch a report and ensure visibility rules.
        Useful when a route wants to bypass dependency injection.
        """
        result = await self.db.execute(
            select(OutreachReport).where(OutreachReport.id == report_id)
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if current_user.role == UserRole.admin:
            return report

        if report.evangelist_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own reports",
            )
        return report

