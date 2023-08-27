import os
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr
from dotenv import load_dotenv

from my_contacts.services.auth import auth_service

load_dotenv()

user = os.environ.get("MAIL_USERNAME")
password = os.environ.get("MAIL_PASSWORD")
mail_from = os.environ.get("MAIL_FROM")
mail_server = os.environ.get("MAIL_SERVER")

conf = ConnectionConfig(
    MAIL_USERNAME=user,
    MAIL_PASSWORD=password,
    MAIL_FROM=mail_from,
    MAIL_PORT=465,
    MAIL_SERVER=mail_server,
    MAIL_FROM_NAME="Support Service",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent.parent/"templates",
)


async def send_email(email_address: EmailStr, username: str, host: str):
    try:
        token_verification = await auth_service.create_email_token({"sub": email_address})
        message = MessageSchema(
            subject="Email address confirmation",
            recipients=[email_address],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_signup.html")
    except ConnectionErrors as err:
        print(err)


async def send_reset_password_email(email_address: EmailStr, username: str, host: str):
    token_expire_seconds = 600
    try:
        token_verification = await auth_service.create_email_token({"sub": email_address},
                                                                   expires_delta=token_expire_seconds)
        message = MessageSchema(
            subject="Password reset",
            recipients=[email_address],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="send_email_reset.html")
    except ConnectionErrors as err:
        print(err)


async def send_success_changed_email(email_address: EmailStr, username: str, host: str):
    try:
        message = MessageSchema(
            subject="Password changed",
            recipients=[email_address],
            template_body={"host": host, "username": username},
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="info_email_reset_success.html")
    except ConnectionErrors as err:
        print(err)
