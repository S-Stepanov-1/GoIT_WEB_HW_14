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
    TEMPLATE_FOLDER=Path(__file__).parent.parent.parent / "templates",
)


async def send_email(email_address: EmailStr, username: str, host: str):
    """
        The send_email function sends an email to the user with a link that they can click on to verify their email address.
        The function takes in three parameters:
            -email_address: The user's email address, which is used as the recipient of the message.
            -username: The username of the user, which is used in both the subject line and body of the message.
            -host: The hostname (or IP) where this service is running, which will be included in a link that users can click on
                   to verify their account.

        :param email_address: EmailStr: Validate the email address
        :param username: str: Pass the username to the email template
        :param host: str: Pass the host url to the template
        :return: A coroutine object
    """
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
    """
        The send_reset_password_email function sends an email to the user with a link to reset their password.
        The function takes in three arguments:
            - email_address: The user's email address, which is used as the recipient of the message.
            - username: The username of the account that requested a password reset. This is included in
                        the body of the message so that users can be sure they are requesting a password
                        reset for their own account and not someone else's. It also helps prevent phishing attacks,
                        since it makes it harder for attackers to impersonate other users by sending them fake emails
                        from our service asking

        :param email_address: EmailStr: Validate the email address
        :param username: str: Send the username to the email template
        :param host: str: Create the link to reset the password
        :return: A token_verification object
    """
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
    """
        The send_success_changed_email function sends an email to the user's email address
            with a message that their password has been changed.

        :param email_address: EmailStr: Validate the email address
        :param username: str: Send the username to the email template
        :param host: str: Pass the hostname of the server to the email template
        :return: A coroutine
    """
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
