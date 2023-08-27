from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from my_contacts.database.db_connect import get_db
from my_contacts.database.models import User
from my_contacts.repository import contacts
from my_contacts.schemas import ContactResponse, ContactModel, ContactUpdate
from my_contacts.services.auth import auth_service

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=List[ContactResponse],
            description="No more than 15 requests per minute",
            dependencies=[Depends(RateLimiter(times=15, seconds=60))]
            )
async def read_contacts(query: str = Query(None, description="Search by name, last name, or email"),
                        skip: int = Query(0, description="Number of records to skip"),
                        limit: int = Query(10, description="Number of records to retrieve"),
                        current_user: User = Depends(auth_service.get_current_user),
                        db: Session = Depends(get_db)):
    """
        The read_contacts function is used to retrieve a list of contacts from the database.
        The function can be called with or without a query parameter, which will search for contacts by name, last name, or email.
        If no query parameter is provided then all contacts are returned in the response body.

        :param query: str: Search for contacts by name, last name, or email
        :param description: Describe the endpoint in the openapi documentation
        :param last name: Search for contacts by last name
        :param or email&quot;): Describe the query parameter in the swagger documentation
        :param skip: int: Skip a number of records in the database
        :param description: Provide a description of the endpoint
        :param limit: int: Limit the number of records returned by the function
        :param description: Provide a description of the endpoint in the openapi documentation
        :param current_user: User: Get the user id from the jwt token
        :param db: Session: Pass the database session to the function
        :return: A list of contacts
    """
    if query:
        contact_list = await contacts.search_contacts(query, skip, limit, current_user, db)
    else:
        contact_list = await contacts.get_contacts(skip, limit, current_user, db)

    if len(contact_list) != 0:
        return contact_list
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No contacts were found")


@router.get("/{contact_id}", response_model=ContactResponse, dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def read_contact(contact_id: int,
                       current_user: User = Depends(auth_service.get_current_user),
                       db: Session = Depends(get_db)):
    """
        The read_contact function is used to retrieve a single contact from the database.
        It takes in an integer representing the ID of the contact, and returns a Contact object.

        :param contact_id: int: Specify the contact to be read
        :param current_user: User: Get the current user from the auth_service
        :param db: Session: Get a database session
        :return: A contact object
    """
    contact = await contacts.get_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.get("/upcoming_birthdays/", response_model=List[ContactResponse],
            dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def get_upcoming_birthdays(days: int = Query(7, description="Upcoming birthdays in the next 7 days"),
                                 current_user: User = Depends(auth_service.get_current_user),
                                 db: Session = Depends(get_db)):
    """
        The get_upcoming_birthdays function returns a list of contacts with upcoming birthdays.

        :param days: int: Specify the number of days in advance to get upcoming birthdays
        :param description: Describe the parameter in the api documentation
        :param current_user: User: Get the current user from the auth_service
        :param db: Session: Get a database session
        :return: A list of contacts
    """
    upcoming_birthdays = await contacts.get_upcoming_birthdays(days, current_user, db)
    if upcoming_birthdays:
        return upcoming_birthdays
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contacts not found")


@router.post("/", response_model=ContactResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def create_contact(body: ContactModel,
                         current_user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    """
        The create_contact function creates a new contact in the database.
            The function takes a ContactModel object as input, which is validated by pydantic.
            The current_user is retrieved from the auth_service and passed to contacts.create_contact().


        :param body: ContactModel: Define the type of data that is expected in the request body
        :param current_user: User: Get the user id of the current logged in user
        :param db: Session: Pass the database session to the function
        :return: The created contact
    """
    return await contacts.create_contact(body, current_user, db)


@router.delete("/{contact_id}", dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def delete_contact(contact_id: int,
                         current_user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    """
        The delete_contact function deletes a contact from the database.
            It takes in an integer representing the id of the contact to be deleted,
            and returns a dictionary containing information about that contact.

        :param contact_id: int: Specify the id of the contact to be deleted
        :param current_user: User: Get the current user's id
        :param db: Session: Pass the database session to the function
        :return: A contact object
    """
    contact = await contacts.delete_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOT FOUND"
        )

    return contact


@router.put("/{contact_id}", response_model=ContactResponse,
            dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def put_update_contact(body: ContactModel,
                             contact_id: int,
                             current_user: User = Depends(auth_service.get_current_user),
                             db: Session = Depends(get_db)):
    """
        The put_update_contact function updates a contact in the database.
            The function takes three parameters:
                body: A ContactModel object containing the new information for the contact.
                contact_id: An integer representing the id of an existing contact to be updated.
                current_user (optional): A User object representing a user who is logged into this application and has been authenticated by FastAPI's auth middleware, which uses JWT tokens to authenticate users and verify their identity. This parameter is optional because it will only be used if you are using authentication in your application, which you can enable or disable by setting AUTHENTICATION

        :param body: ContactModel: Pass the contact data to be updated
        :param contact_id: int: Specify the id of the contact to be deleted
        :param current_user: User: Access the current user's information
        :param db: Session: Pass the database session to the function
        :return: The updated contact
    """
    contact = await contacts.put_update_contact(contact_id, body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.patch("/{contact_id}", response_model=ContactResponse,
              dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def patch_update_contact(body: ContactUpdate,
                               contact_id: int,
                               current_user: User = Depends(auth_service.get_current_user),
                               db: Session = Depends(get_db)):
    """
        The patch_update_contact function updates a contact in the database.
            The function takes in a ContactUpdate object, which is defined as follows:

        :param body: ContactUpdate: Get the data from the request body
        :param contact_id: int: Get the contact id from the url
        :param current_user: User: Get the current user from the auth_service
        :param db: Session: Pass the database session to the function
        :return: A contact object
    """
    contact = await contacts.patch_update_contact(contact_id, body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact
