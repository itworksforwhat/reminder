from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models.user import User
from app.models.company import Company, CompanyMember, MemberRole
from app.utils.security import get_current_user

router = APIRouter(prefix="/companies", tags=["companies"])


class MemberInviteRequest(BaseModel):
    email: EmailStr
    role: str = "member"


class UpdateMemberRoleRequest(BaseModel):
    role: str


class MemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    role: str
    joined_at: str

    model_config = {"from_attributes": True}


class CompanyDetailResponse(BaseModel):
    id: UUID
    name: str
    business_number: str | None
    owner_id: UUID
    created_at: str
    member_count: int

    model_config = {"from_attributes": True}


@router.get("", response_model=list[CompanyDetailResponse])
async def list_my_companies(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 사용자가 소속된 회사 목록을 조회합니다."""
    result = await db.execute(
        select(CompanyMember).where(CompanyMember.user_id == user.id)
    )
    memberships = result.scalars().all()

    companies = []
    for membership in memberships:
        company = membership.company
        companies.append(CompanyDetailResponse(
            id=company.id,
            name=company.name,
            business_number=company.business_number,
            owner_id=company.owner_id,
            created_at=company.created_at.isoformat(),
            member_count=len(company.members),
        ))
    return companies


@router.get("/{company_id}/members", response_model=list[MemberResponse])
async def list_members(
    company_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """회사의 멤버 목록을 조회합니다."""
    await _check_member(db, user.id, company_id)

    result = await db.execute(
        select(CompanyMember).where(CompanyMember.company_id == company_id)
    )
    members = result.scalars().all()

    return [
        MemberResponse(
            id=m.id,
            user_id=m.user_id,
            user_name=m.user.name,
            user_email=m.user.email,
            role=m.role.value if isinstance(m.role, MemberRole) else m.role,
            joined_at=m.joined_at.isoformat(),
        )
        for m in members
    ]


@router.post("/{company_id}/members", response_model=MemberResponse, status_code=201)
async def invite_member(
    company_id: UUID,
    data: MemberInviteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """회사에 멤버를 초대합니다. OWNER 또는 ADMIN만 가능합니다."""
    membership = await _check_member(db, user.id, company_id)

    role_val = membership.role.value if isinstance(membership.role, MemberRole) else membership.role
    if role_val not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can invite members",
        )

    # 초대할 사용자 조회
    result = await db.execute(select(User).where(User.email == data.email))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found with this email",
        )

    # 이미 멤버인지 확인
    existing = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == target_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this company",
        )

    try:
        member_role = MemberRole(data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {[r.value for r in MemberRole]}",
        )

    new_member = CompanyMember(
        company_id=company_id,
        user_id=target_user.id,
        role=member_role,
    )
    db.add(new_member)
    await db.flush()

    return MemberResponse(
        id=new_member.id,
        user_id=target_user.id,
        user_name=target_user.name,
        user_email=target_user.email,
        role=member_role.value,
        joined_at=new_member.joined_at.isoformat(),
    )


@router.put("/{company_id}/members/{member_id}", response_model=MemberResponse)
async def update_member_role(
    company_id: UUID,
    member_id: UUID,
    data: UpdateMemberRoleRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """멤버의 역할을 변경합니다."""
    membership = await _check_member(db, user.id, company_id)
    role_val = membership.role.value if isinstance(membership.role, MemberRole) else membership.role
    if role_val not in ("owner", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    result = await db.execute(
        select(CompanyMember).where(CompanyMember.id == member_id, CompanyMember.company_id == company_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    try:
        target.role = MemberRole(data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {[r.value for r in MemberRole]}",
        )

    await db.flush()
    return MemberResponse(
        id=target.id,
        user_id=target.user_id,
        user_name=target.user.name,
        user_email=target.user.email,
        role=target.role.value if isinstance(target.role, MemberRole) else target.role,
        joined_at=target.joined_at.isoformat(),
    )


@router.delete("/{company_id}/members/{member_id}", status_code=204)
async def remove_member(
    company_id: UUID,
    member_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """멤버를 회사에서 제거합니다."""
    membership = await _check_member(db, user.id, company_id)
    role_val = membership.role.value if isinstance(membership.role, MemberRole) else membership.role
    if role_val not in ("owner", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    result = await db.execute(
        select(CompanyMember).where(CompanyMember.id == member_id, CompanyMember.company_id == company_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    target_role = target.role.value if isinstance(target.role, MemberRole) else target.role
    if target_role == "owner":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the owner")

    await db.delete(target)
    await db.flush()


async def _check_member(db: AsyncSession, user_id: UUID, company_id: UUID) -> CompanyMember:
    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.user_id == user_id,
            CompanyMember.company_id == company_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this company")
    return member
