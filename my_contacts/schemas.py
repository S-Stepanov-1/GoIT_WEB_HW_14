from typing import Optional
from pydantic import BaseModel, EmailStr, PastDate, Field
from pydantic_extra_types.phone_numbers import PhoneNumber


class ContactModel(BaseModel):
    """
    ContactModel represents the structure of contact information.

    Attributes:
        first_name (str): The first name of the contact.
        last_name (str): The last name of the contact.
        email (Optional[EmailStr]): The email address of the contact (optional).
        phone_number (PhoneNumber): The phone number of the contact.
        birthday (Optional[PastDate]): The birthday of the contact (optional).
        position (Optional[str]): The position of the contact (optional).
    """
    first_name: str
    last_name: str
    email: Optional[EmailStr]
    phone_number: PhoneNumber
    birthday: Optional[PastDate]
    position: Optional[str]


class ContactResponse(ContactModel):
    """
    ContactResponse represents the response structure for contact information.

    Attributes:
        id (int): The unique identifier of the contact.
    """
    id: int = 1

    class Config:
        from_attributes = True


class ContactUpdate(BaseModel):
    """
    ContactUpdate represents the structure for updating contact information.

    Attributes:
        email (Optional[EmailStr]): The updated email address (optional).
        phone_number (Optional[PhoneNumber]): The updated phone number (optional).
        position (Optional[str]): The updated position (optional).
    """
    email: Optional[EmailStr]
    phone_number: Optional[PhoneNumber]
    position: Optional[str]


class UserModel(BaseModel):
    """
    UserModel represents the structure of user information.

    Attributes:
        username (str): The username of the user.
        user_email (EmailStr): The email address of the user.
        password (str): The password of the user.
    """
    username: str = Field(min_length=4, max_length=50)
    user_email: EmailStr = Field(max_length=50)
    password: str = Field(min_length=8, max_length=20)


class UserResponse(BaseModel):
    """
    UserResponse represents the response structure for user information.

    Attributes:
        username (str): The username of the user.
        user_email (str): The email address of the user.
        detail (str): A detail message indicating the status (default is "User successfully created").
    """
    username: str
    user_email: str
    detail: str = "User successfully created"

    class Config:
        from_attributes = True


class TokenModel(BaseModel):
    """
    TokenModel represents the structure of authentication tokens.

    Attributes:
        access_token (str): The access token.
        refresh_token (str): The refresh token.
        token_type (str): The type of token (default is "bearer").
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
