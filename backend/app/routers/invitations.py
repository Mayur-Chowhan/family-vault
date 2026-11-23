import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import FamilyInvitation, FamilyMember, User
from app.schemas import InvitationCreate, InvitationResponse

router = APIRouter(prefix="/api/v1", tags=["invitations"])


def is_expired(invitation: FamilyInvitation) -> bool:
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < datetime.now(timezone.utc)


@router.post(
    "/families/{family_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    family_id: int,
    payload: InvitationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await db.execute(
        select(FamilyMember).where(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == user.id,
        )
    )
    member = membership.scalar_one_or_none()
    if member is None or member.role not in {"owner", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner or admin only")

    existing_user = await db.execute(select(User).where(User.email == payload.email))
    if existing_user.scalar_one_or_none() is not None:
        already = await db.execute(
            select(FamilyMember)
            .join(User, FamilyMember.user_id == User.id)
            .where(
                FamilyMember.family_id == family_id,
                User.email == payload.email,
            )
        )
        if already.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member")

    invitation = FamilyInvitation(
        family_id=family_id,
        email=payload.email,
        role=payload.role,
        token=secrets.token_urlsafe(32),
        invited_by=user.id,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.invitation_expire_days),
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)
    return invitation


@router.get("/families/{family_id}/invitations", response_model=list[InvitationResponse])
async def list_invitations(
    family_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await db.execute(
        select(FamilyMember).where(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == user.id,
        )
    )
    member = membership.scalar_one_or_none()
    if member is None or member.role not in {"owner", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner or admin only")

    result = await db.execute(
        select(FamilyInvitation)
        .where(FamilyInvitation.family_id == family_id)
        .order_by(FamilyInvitation.id)
    )
    return result.scalars().all()


@router.get("/invitations/mine", response_model=list[InvitationResponse])
async def my_invitations(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(FamilyInvitation)
        .where(
            FamilyInvitation.email == user.email,
            FamilyInvitation.accepted_at.is_(None),
        )
        .order_by(FamilyInvitation.id)
    )
    return result.scalars().all()


@router.post("/invitations/{token}/accept", response_model=InvitationResponse)
async def accept_invitation(
    token: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FamilyInvitation).where(FamilyInvitation.token == token)
    )
    invitation = result.scalar_one_or_none()
    if invitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if invitation.accepted_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation already used")
    if is_expired(invitation):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation expired")
    if invitation.email != user.email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invitation is for a different email")

    existing = await db.execute(
        select(FamilyMember).where(
            FamilyMember.family_id == invitation.family_id,
            FamilyMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member")

    db.add(
        FamilyMember(
            family_id=invitation.family_id,
            user_id=user.id,
            role=invitation.role,
        )
    )
    invitation.accepted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(invitation)
    return invitation
