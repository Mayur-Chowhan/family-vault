from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class FamilyMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    role: str
    created_at: datetime
    user: UserResponse


class MediaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    album_id: int
    resource_type: str
    format: str
    bytes: int
    width: int | None
    height: int | None
    duration: float | None
    original_filename: str
    created_at: datetime
    url: str
    thumbnail_url: str
    download_url: str


class MediaListResponse(BaseModel):
    items: list[MediaResponse]
    total: int
    page: int
    page_size: int


class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = Field(default="member", pattern="^(admin|member)$")


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_id: int
    email: str
    role: str
    token: str
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime


class FamilyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class FamilyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class FamilyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    updated_at: datetime


class AlbumCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    visibility: str = Field(default="private", pattern="^(private|family|public)$")


class AlbumUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    visibility: str | None = Field(default=None, pattern="^(private|family|public)$")


class AlbumResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_id: int
    name: str
    visibility: str
    created_at: datetime
    updated_at: datetime
