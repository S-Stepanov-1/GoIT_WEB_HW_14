import os
import cloudinary
import cloudinary.uploader

from fastapi import APIRouter, Depends, UploadFile, File, Request, HTTPException, status, BackgroundTasks, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from my_contacts.database.db_connect import get_db
from my_contacts.database.models import User
from my_contacts.schemas import UserResponse
from my_contacts.repository import users as repository_users
from my_contacts.services.auth import auth_service
from my_contacts.services import send_email

load_dotenv()

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

router = APIRouter(prefix="/users", tags=["users"])

templates_dir = os.path.abspath("../../templates")
templates = Jinja2Templates(directory="templates")


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar_user(file: UploadFile = File(),
                             current_user: User = Depends(auth_service.get_current_user),
                             db: Session = Depends(get_db)):
    """Update user avatar"""
    uploaded_file_info = cloudinary.uploader \
        .upload(file.file, public_id=f"My Contacts App/{current_user.username}", overwrite=True)

    avatar_url = cloudinary.CloudinaryImage(f"My Contacts App/{current_user.username}") \
        .build_url(width=300, height=300, crop="fill", version=uploaded_file_info.get('version'))

    await repository_users.update_avatar(current_user.user_email, avatar_url, db)

    response_message = "Avatar successfully updated"
    user_response = UserResponse(username=current_user.username,
                                 user_email=current_user.user_email,
                                 detail=response_message)
    return user_response


@router.post("/forgot_password")
async def forgot_password(request: Request, background_tasks: BackgroundTasks, user_email: str,
                          db: Session = Depends(get_db)):
    user = await repository_users.get_user_by_email(user_email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"An unexpected error occurred.")

    background_tasks.add_task(send_email.send_reset_password_email, user_email, user.username, request.base_url)
    return {"user_email": user.user_email,
            "detail": "Check your email for reset password."}


@router.get("/reset_password/{token}")
async def reset_password(token: str, request: Request, db: Session = Depends(get_db)):
    try:
        email = await auth_service.get_email_from_token(token)
        user = await repository_users.get_user_by_email(email, db)
        return templates.TemplateResponse("reset_password.html", {"request": request, "user": user, "token": token})
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Incorrect token.")


@router.post("/reset_password/{token}", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def reset_password_post(token: str,
                              request: Request,
                              background_tasks: BackgroundTasks,
                              new_password: str = Form(...),
                              db: Session = Depends(get_db)):

    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    new_password = await auth_service.get_password_hash(new_password)

    await repository_users.change_password(user, new_password, db)
    background_tasks.add_task(send_email.send_success_changed_email, email, user.username, request.base_url)

    response_data = {
        "username": user.username,
        "user_email": email,
        "detail": "Password was changed successfully"
    }

    return UserResponse(**response_data)
