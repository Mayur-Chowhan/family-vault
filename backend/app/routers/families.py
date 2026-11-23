from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user, require_membership
from app.models import Family, FamilyMember, User
from app.schemas import (
    FamilyCreate,
    FamilyMemberResponse,
    FamilyResponse,
    FamilyUpdate,
)

router = APIRouter(prefix="/api/v1/families", tags=["families"])
MANAGE_ROLES = {"owner", "admin"}


def require_family_role_dependency(allowed_roles: set[str]):
    async def dependency(
        family_id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> FamilyMember:
        member = await require_membership(family_id, user, db)
        if member.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role"
            )
        return member

    return dependency


manage_role = require_family_role_dependency(MANAGE_ROLES)


async def get_family_or_404(family_id: int, db: AsyncSession) -> Family:
    family = await db.get(Family, family_id)
    if family is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")
    return family


@router.post("", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def create_family(
    payload: FamilyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    family = Family(**payload.model_dump())
    db.add(family)
    await db.flush()
    db.add(FamilyMember(family_id=family.id, user_id=user.id, role="owner"))
    await db.commit()
    await db.refresh(family)
    return family


@router.get("", response_model=list[FamilyResponse])
async def list_families(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Family)
        .join(FamilyMember, FamilyMember.family_id == Family.id)
        .where(FamilyMember.user_id == user.id)
        .order_by(Family.id)
    )
    return result.scalars().all()


@router.get("/{family_id}", response_model=FamilyResponse)
async def get_family(
    family_id: int,
    membership: FamilyMember = Depends(require_membership),
    db: AsyncSession = Depends(get_db),
):
    return await get_family_or_404(family_id, db)


@router.patch("/{family_id}", response_model=FamilyResponse)
async def update_family(
    family_id: int,
    payload: FamilyUpdate,
    membership: FamilyMember = Depends(manage_role),
    db: AsyncSession = Depends(get_db),
):
    family = await get_family_or_404(family_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(family, field, value)
    await db.commit()
    await db.refresh(family)
    return family


@router.delete("/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family(
    family_id: int,
    membership: FamilyMember = Depends(manage_role),
    db: AsyncSession = Depends(get_db),
):
    family = await get_family_or_404(family_id, db)
    await db.delete(family)
    await db.commit()


@router.get("/{family_id}/members", response_model=list[FamilyMemberResponse])
async def list_members(
    family_id: int,
    membership: FamilyMember = Depends(require_membership),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FamilyMember)
        .options(selectinload(FamilyMember.user))
        .where(FamilyMember.family_id == family_id)
        .order_by(FamilyMember.id)
    )
    return result.scalars().all()


@router.delete("/{family_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    family_id: int,
    member_id: int,
    membership: FamilyMember = Depends(manage_role),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.id == member_id,
            FamilyMember.family_id == family_id,
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if target.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the owner"
        )
    await db.delete(target)
    await db.commit()
