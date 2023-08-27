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
    contact = await contacts.get_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.get("/upcoming_birthdays/", response_model=List[ContactResponse],
            dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def get_upcoming_birthdays(days: int = Query(7, description="Upcoming birthdays in the next 7 days"),
                                 current_user: User = Depends(auth_service.get_current_user),
                                 db: Session = Depends(get_db)):
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
    return await contacts.create_contact(body, current_user, db)


@router.delete("/{contact_id}", dependencies=[Depends(RateLimiter(times=15, seconds=60))])
async def delete_contact(contact_id: int,
                         current_user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
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
    contact = await contacts.patch_update_contact(contact_id, body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact
