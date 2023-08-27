import os
from typing import Optional

from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from dotenv import load_dotenv

from my_contacts.database.db_connect import get_db
from my_contacts.repository import users as repository_users


load_dotenv()

secret_key = os.environ.get("SECRET_KEY")
algorithm = os.environ.get("ALGORITHM")


class Auth:
    """
        Auth class for handling authentication and token generation.

        Attributes:
            pwd_context (CryptContext): Password hashing context.
            SECRET_KEY (str): Secret key for token generation.
            ALGORITHM (str): Token encoding algorithm.
            oauth2_scheme (OAuth2PasswordBearer): OAuth2 password bearer scheme.
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = secret_key
    ALGORITHM = algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    async def verify_password(self, plain_password, hashed_password):
        """
            The verify_password method takes a plain-text password and a hashed password
            and returns True if the passwords match, False otherwise. The method uses the
            passlib library to verify that the hash matches what is stored in our database.

            :param self: Represent the instance of the class
            :param plain_password: Store the password that is entered by the user
            :param hashed_password: Compare the hashed password stored in the database with the plain text password entered by a user
            :return: True if the plain password matches the hashed password, and false otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    async def get_password_hash(self, password: str):
        """
            The get_password_hash method takes a password as input and returns the hashed version of that password.
            The hashing algorithm used is PBKDF2, which is considered secure for most applications.

            :param self: Represent the instance of the class
            :param password: str: Pass in the password that is to be hashed
            :return: A password hash
        """
        return self.pwd_context.hash(password)

    async def create_email_token(self, data: dict, expires_delta: Optional[float] = None):
        """
            The create_email_token method takes in a dictionary of data and an optional expires_delta parameter.
            The method then creates a token that will expire after the specified time period. The token is created using
            the JWT library, which uses the SECRET_KEY and ALGORITHM to create the token.

            :param self: Access the class attributes and methods
            :param data: dict: Pass in the data that will be encoded into the token
            :param expires_delta: Optional[float]: Set the expiration time of the token
            :return: A token that is encoded using the json web token (jwt) standard
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=5)

        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        """
            The get_email_from_token method takes a token as an argument and returns the email address associated with that token.
            The method uses the jwt library to decode the token, which is then used to return the email address.

            :param self: Refer to the current object
            :param token: str: Pass in the token that is sent to the user's email
            :return: The email address of the user who is trying to log in
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")

    # define a method to generate a new access token
    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
            The create_access_token method creates a new access token.
                Args:
                    data (dict): A dictionary containing the claims to be encoded in the JWT.
                    expires_delta (Optional[float]): An optional parameter specifying how long, in seconds,
                        the access token should last before expiring. If not specified, it defaults to 20 minutes.

            :param self: Refer to the instance of the class
            :param data: dict: Pass in the data that will be encoded into the jwt
            :param expires_delta: Optional[float]: Set the expiration time of the access token
            :return: A jwt token that is encoded with the data passed in as a parameter
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=20)

        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    # define a method to generate a new refresh token
    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
            The create_refresh_token method creates a refresh token for the user.
                Args:
                    data (dict): A dictionary containing the user's id and username.
                    expires_delta (Optional[float]): The number of seconds until the token expires, defaults to None.

            :param self: Represent the instance of the class
            :param data: dict: Pass the user_id and username of the user to be encoded
            :param expires_delta: Optional[float]: Set the time until the refresh token expires
            :return: A refresh token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=5)

        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    # define a method to decode a refresh_token
    async def decode_refresh_token(self, refresh_token: str):
        """
            The decode_refresh_token method is used to decode the refresh token.
            It takes in a refresh_token as an argument and returns the email of the user if successful.
            If it fails, it raises an HTTPException with status code 401 (Unauthorized) and detail message &quot;Could not validate credentials&quot;.


            :param self: Represent the instance of the class
            :param refresh_token: str: Pass in the refresh token that was sent to the client
            :return: The email of the user if the refresh token is valid
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "refresh_token":
                email = payload["sub"]
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid scope for token")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
            The get_current_user method is a dependency that will be used in the
                protected endpoints. It takes a token as an argument and returns the user
                if it's valid, otherwise raises an HTTPException with status code 401.

            :param self: Represent the instance of a class
            :param token: str: Get the token from the authorization header
            :param db: Session: Get the database session
            :return: A user object that is stored in the database
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials for this user",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "access_token":
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = await repository_users.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception
        return user


auth_service = Auth()
