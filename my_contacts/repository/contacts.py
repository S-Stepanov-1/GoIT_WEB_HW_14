from typing import List, Type
from datetime import date, timedelta

from fastapi import HTTPException, status

from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from my_contacts.database.models import Contact, User
from my_contacts.schemas import ContactModel, ContactUpdate


async def get_contacts(skip: int, limit: int, user: User, db: Session) -> list[Type[Contact]]:
    """
        The get_contacts function returns a list of contacts for the user.

        :param skip: int: Skip a certain number of contacts in the database
        :param limit: int: Limit the number of contacts returned
        :param user: User: Get the user_id from the logged in user
        :param db: Session: Pass the database session to the function
        :return: A list of contact objects
    """
    return db.query(Contact).filter_by(user_id=user.id).offset(skip).limit(limit).all()


async def get_contact(contact_id: int, user: User, db: Session) -> Type[Contact] | None:
    """
        The get_contact function takes in a contact_id and user object, and returns the Contact object with that id.
        If no such contact exists, it returns None.

        :param contact_id: int: Identify the contact in the database
        :param user: User: Get the user_id from the database
        :param db: Session: Access the database
        :return: A contact object or none
    """
    contact = db.query(Contact).filter(and_(Contact.user_id == user.id, Contact.id == contact_id)).first()
    if contact:
        return contact


async def create_contact(body: ContactModel, user: User, db: Session) -> Contact:
    """
        The create_contact function creates a new contact in the database.

        :param body: ContactModel: Validate the incoming data
        :param user: User: Get the user id of the logged in user
        :param db: Session: Access the database
        :return: A contact object
    """
    try:
        contact = Contact(**body.model_dump(), user=user)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact

    except IntegrityError as err:
        db.rollback()

        if "duplicate key" in str(err):
            duplicate_fields = []
            if db.query(Contact).filter_by(email=contact.email).first():
                duplicate_fields.append("email")
            if db.query(Contact).filter_by(phone_number=contact.phone_number).first():
                duplicate_fields.append("phone_number")

            if duplicate_fields:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail=f"Duplicate fields: {', '.join(duplicate_fields)}")

        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Data already exist")


async def delete_contact(contact_id: int, user: User, db: Session):
    """
        The delete_contact function deletes a contact from the database.
            Args:
                contact_id (int): The id of the contact to be deleted.
                user (User): The user who is deleting the contact. This is used to ensure that only contacts belonging
                    to this particular user are deleted, and not all contacts with this id in general.

        :param contact_id: int: Specify the id of the contact to be deleted
        :param user: User: Get the user_id from the token
        :param db: Session: Access the database and delete the contact
        :return: A string with the name of the deleted contact
    """
    contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    if contact:
        db.delete(contact)
        db.commit()
        return f"{contact.first_name} {contact.last_name} was deleted"


async def put_update_contact(contact_id: int, body: ContactModel, user: User, db: Session) -> Type[Contact]:
    """
        The put_update_contact function updates a contact in the database.
            Args:
                contact_id (int): The id of the contact to update.
                body (ContactModel): The updated information for the specified contact.

        :param contact_id: int: Find the contact in the database
        :param body: ContactModel: Pass in the json data that is sent to the api
        :param user: User: Ensure that only the user who created the contact can update it
        :param db: Session: Connect to the database
        :return: The contact that has been updated
    """
    contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone_number = body.phone_number
        contact.birthday = body.birthday
        contact.position = body.position

        db.commit()
        db.refresh(contact)

        return contact


async def patch_update_contact(contact_id: int, body: ContactUpdate, user: User, db: Session) -> Type[Contact]:
    """
        The patch_update_contact function updates a contact in the database.
            Args:
                contact_id (int): The id of the contact to update.
                body (ContactUpdate): The updated information for the specified contact.
                user (User): The user who is making this request, used to verify that they are authorized to make this change.

        :param contact_id: int: Identify the contact to be deleted
        :param body: ContactUpdate: Get the data from the request body
        :param user: User: Get the user id from the token
        :param db: Session: Connect to the database
        :return: A contact object
    """
    contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    if contact:
        contact.email = body.email or contact.email
        contact.phone_number = body.phone_number or contact.phone_number
        contact.position = body.position or contact.position

        db.commit()
        return contact


async def search_contacts(q: str, skip: int, limit: int, user: User, db: Session) -> List[Type[Contact]]:
    """
        The search_contacts function searches for contacts in the database.
            Args:
                q (str): The search query.
                skip (int): Number of contacts to be skipped.
                limit (int): Number of contacts to be returned.

        :param q: str: Search for a contact in the database
        :param skip: int: Skip the first n contacts
        :param limit: int: Limit the number of results returned
        :param user: User: Get the user's id from the database
        :param db: Session: Access the database
        :return: A list of contacts
    """
    required_contacts = db.query(Contact).filter(
        and_(Contact.user_id == user.id,
             func.lower(Contact.first_name).like(f"%{q.lower()}%"),
             func.lower(Contact.last_name).like(f"%{q.lower()}%"),
             func.lower(Contact.email).like(f"%{q.lower()}%"))
    ).offset(skip).limit(limit).all()

    if required_contacts:
        return required_contacts


async def get_upcoming_birthdays(days: int, user: User, db: Session) -> List[Type[Contact]]:
    """
        The get_upcoming_birthdays function returns a list of contacts whose birthdays are within the next 'days' days.

        :param days: int: Determine how many days in the future we want to look for birthdays
        :param user: User: Get the user's id from the database
        :param db: Session: Connect to the database
        :return: A list of contacts with upcoming birthdays
    """
    upcoming_birthdays = []

    today = date.today()
    end_date = today + timedelta(days=days)

    all_contacts = db.query(Contact).filter_by(user_id=user.id).all()
    for contact in all_contacts:
        if end_date >= contact.birthday.replace(year=today.year) > today:  # birthdays in this year
            upcoming_birthdays.append(contact)

        if end_date >= contact.birthday.replace(year=today.year + 1) > today:  # birthdays in the next year
            upcoming_birthdays.append(contact)

    if upcoming_birthdays:
        return upcoming_birthdays
