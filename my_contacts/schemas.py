from typing import Optional
from pydantic import BaseModel, EmailStr, PastDate, Field
from pydantic_extra_types.phone_numbers import PhoneNumber


class ContactModel(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr]
    phone_number: PhoneNumber
    birthday: Optional[PastDate]
    position: Optional[str]


class ContactResponse(ContactModel):
    id: int = 1

    class Config:
        from_attributes = True


class ContactUpdate(BaseModel):
    email: Optional[EmailStr]
    phone_number: Optional[PhoneNumber]
    position: Optional[str]


class UserModel(BaseModel):
    username: str = Field(min_length=4, max_length=50)
    user_email: EmailStr = Field(max_length=50)
    password: str = Field(min_length=8, max_length=20)


class UserResponse(BaseModel):
    username: str
    user_email: str
    detail: str = "User successfully created"

    class Config:
        from_attributes = True


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
