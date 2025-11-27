from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.person import Person
from app.schemas.person_schema import PersonCreate, PersonUpdate, PersonResponse
from app.services.person_service import PersonService

router = APIRouter()

def get_person_service(db: AsyncSession = Depends(get_db)) -> PersonService:
    return PersonService(db)

async def verify_person_ownership(
    person_id: UUID,
    current_user: User,
    service: PersonService = Depends(get_person_service),
) -> Person:
    """
    Verify user owns the person (via report) or is admin.
    """
    return await service.ensure_person_access(person_id, current_user)

@router.get("/", response_model=List[PersonResponse])
async def list_people(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
):
    """
    List people.
    - Admins see all people.
    - Evangelists see only people from their reports.
    """
    return await service.list_people(current_user, skip, limit)

@router.post("/", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(
    person_in: PersonCreate,
    current_user: User = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
):
    """
    Create a new person.
    Verifies that the user owns the report they are adding the person to.
    """
    return await service.create_person(person_in, current_user)

@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
):
    """
    Get a specific person.
    """
    return await service.ensure_person_access(person_id, current_user)

@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: UUID,
    person_update: PersonUpdate,
    current_user: User = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
):
    """
    Update a person.
    """
    return await service.update_person(person_id, person_update, current_user)

@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
):
    """
    Delete a person.
    """
    await service.delete_person(person_id, current_user)
