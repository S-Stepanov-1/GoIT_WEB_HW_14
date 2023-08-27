from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer

from my_contacts.database.db_connect import get_db
from my_contacts.repository import users as repository_users
from my_contacts.schemas import UserModel, UserResponse, TokenModel
from my_contacts.services.auth import auth_service

from my_contacts.services.send_email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def register_user(request: Request,
                        background_tasks: BackgroundTasks,
                        body: UserModel = Depends(),
                        db: Session = Depends(get_db)):
    """
        The register_user function creates a new user in the database.
            It takes a UserModel object as input, which is validated by pydantic.
            The password is hashed using Argon2 and stored in the database.
            A confirmation email is sent to the user's email address.

        :param request: Request: Get the base_url of the request
        :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
        :param body: UserModel: Get the user's information from the request body
        :param db: Session: Get the database session
        :return: A dictionary with two keys: user and detail
    """
    exist_user = await repository_users.get_user_by_email(body.user_email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )
    body.password = await auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_email, new_user.user_email, new_user.username, request.base_url)
    return {"user": [new_user.username, new_user.user_email],
            "detail": "User successfully created. Check your email for confirmation."}


@router.post("/login", response_model=TokenModel, status_code=status.HTTP_201_CREATED)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
        The login function is used to authenticate a user.
            It takes in the username and password of the user, and returns an access token if successful.
            The access token can be used to make authenticated requests.

        :param body: OAuth2PasswordRequestForm: Get the username and password from the request body
        :param db: Session: Get the database session from the dependency
        :return: A token and a refresh token
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None or not await auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please confirm your account"
        )
    access_token = await auth_service.create_access_token(data={"sub": user.user_email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.user_email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.get("/refresh_token")
async def get_refresh_token(credentials: HTTPAuthorizationCredentials = Security(security),
                            db: Session = Depends(get_db)):
    """
        The get_refresh_token function is used to refresh the access token.
        It takes in a refresh token and returns a new access token and a new refresh token.
        The function first decodes the given refresh_token, then checks if it matches with the user's stored one.
        If they match, it creates two new tokens (access &amp; refresh) for that user.

        :param credentials: HTTPAuthorizationCredentials: Get the token from the request header
        :param db: Session: Get the database session
        :return: A new access token and a new refresh token
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)

    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    new_access_token = await auth_service.create_access_token(data={"sub": email})
    new_refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, new_refresh_token, db)
    return {"new_access_token": new_access_token, "refresh_token": new_refresh_token}


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
        The confirmed_email function is used to confirm a user's email address.
            It takes the token from the URL and uses it to get the user's email address.
            Then, it checks if that user exists in our database and if they have already confirmed their email.
            If not, then we update their record in our database with a confirmation of their email.

        :param token: str: Get the token from the url
        :param db: Session: Get the database session
        :return: A message that the email is confirmed
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification error",
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Your email is confirmed"}
