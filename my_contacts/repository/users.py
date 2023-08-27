from typing import Type

from sqlalchemy.orm import Session

from my_contacts.database.models import User
from my_contacts.schemas import UserModel


async def get_user_by_email(email: str, db: Session) -> Type[User]:
    """
        The get_user_by_email function takes in an email and a database session,
        and returns the user associated with that email. If no such user exists, it returns None.

        :param email: str: Specify the email address of the user we are trying to find
        :param db: Session: Pass the database session to the function
        :return: A user object
    """
    user = db.query(User).filter_by(user_email=email).first()
    if user:
        return user


async def create_user(body: UserModel, db: Session) -> User:
    """
        The create_user function creates a new user in the database.

        :param body: UserModel: Validate the request body
        :param db: Session: Connect to the database
        :return: A user object
    """
    new_user = User(**body.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def delete_user(user: User, db: Session) -> None:
    """
        The delete_user function deletes a user from the database.

        :param user: User: Specify the type of the user parameter
        :param db: Session: Pass the database session to the function
        :return: None, which is the default return value for functions that don't explicitly return a value
    """
    db.delete(user)
    db.commit()
    db.refresh(user)


async def update_token(user: Type[User], token: str | None, db: Session) -> None:
    """
        The update_token function updates the refresh token for a user.

        :param user: Type[User]: Specify the type of the user parameter
        :param token: str | None: Set the refresh token for a user
        :param db: Session: Pass the database session to the function
        :return: None, but it does update the user's refresh token in the database
    """
    user.refresh_token = token
    db.commit()
    db.refresh(user)


async def confirmed_email(email: str, db: Session) -> None:
    """
        The confirmed_email function takes in an email and a database session,
        and sets the confirmed field of the user with that email to True.


        :param email: str: Get the email of the user that needs to be confirmed
        :param db: Session: Pass the database session to the function
        :return: None
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()
    db.refresh(user)


async def update_avatar(email, avatar_url: str, db: Session) -> Type[User]:
    """
        The update_avatar function updates the avatar_url of a user in the database.

        :param email: Find the user in the database
        :param avatar_url: str: Specify the type of the parameter
        :param db: Session: Pass the database session to the function
        :return: The updated user
    """
    user = await get_user_by_email(email, db)
    user.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return user


async def change_password(user, password: str, db: Session) -> Type[User]:
    """
        The change_password function takes a user and password, then updates the user's password in the database.
            Args:
                user (User): The User object to update.
                password (str): The new plaintext password for this User.

        :param user: Identify the user whose password is being changed
        :param password: str: Pass in the new password to be set
        :param db: Session: Pass the database session to the function
        :return: The user object
    """
    user.password = password
    db.commit()
    db.refresh(user)
    return user
