from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.api.dependencies import get_current_user, verify_report_ownership
from app.models.user import User
from app.models.outreachReport import OutreachReport
from app.schemas.report_schema import ReportCreate, ReportUpdate, ReportResponse
from app.services.report_service import ReportService

router = APIRouter()


def get_report_service(db: AsyncSession = Depends(get_db)) -> ReportService:
    return ReportService(db)

@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    """
    List reports.
    - Admins see all reports.
    - Evangelists see only their own reports.
    """
    return await service.list_reports(current_user, skip, limit)

@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_in: ReportCreate,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    """
    Create a new outreach report.
    """
    return await service.create_report(report_in, current_user)

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report: OutreachReport = Depends(verify_report_ownership)
):
    """
    Get a specific report by ID.
    Access is controlled by verify_report_ownership dependency.
    """
    return report

@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_update: ReportUpdate,
    report: OutreachReport = Depends(verify_report_ownership),
    service: ReportService = Depends(get_report_service),
):
    """
    Update a report.
    Access is controlled by verify_report_ownership dependency.
    """
    return await service.update_report(report, report_update)

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report: OutreachReport = Depends(verify_report_ownership),
    service: ReportService = Depends(get_report_service),
):
    """
    Delete a report.
    Access is controlled by verify_report_ownership dependency.
    """
    await service.delete_report(report)
