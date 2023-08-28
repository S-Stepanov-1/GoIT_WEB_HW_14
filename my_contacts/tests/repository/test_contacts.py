import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock

from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from my_contacts.database.models import User, Contact
from my_contacts.schemas import ContactModel, ContactUpdate
from my_contacts.repository.contacts import (get_contact, get_contacts, create_contact, delete_contact,
                                             put_update_contact, patch_update_contact,
                                             search_contacts, get_upcoming_birthdays,
                                             )


class TestContactsRepository(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_get_contacts_success(self):
        limit = 10
        skip = 0
        expected_contacts = [Contact(), Contact(), Contact()]
        self.session.query().filter_by().offset().limit().all.return_value = expected_contacts
        result = await get_contacts(skip=skip, limit=limit, user=self.user, db=self.session)
        self.assertEqual(result, expected_contacts)

    async def test_get_contacts_empty(self):
        limit = 10
        skip = 0
        expected_contacts = []
        self.session.query().filter_by().offset().limit().all.return_value = expected_contacts
        result = await get_contacts(skip=skip, limit=limit, user=self.user, db=self.session)
        self.assertEqual(result, expected_contacts)

    async def test_get_contact_success(self):
        contact_id = 1
        expected_contact = Contact(id=contact_id, user_id=self.user.id)
        self.session.query(Contact).filter(Contact.id == contact_id,
                                           Contact.user_id == self.user.id).first.return_value = expected_contact
        result = await get_contact(contact_id=contact_id, user=self.user, db=self.session)
        self.assertEqual(result, expected_contact)

    async def test_get_contact_not_found(self):
        contact_id = 1
        expected_contact = None
        self.session.query(Contact).filter(Contact.id == contact_id,
                                           Contact.user_id == self.user.id).first.return_value = expected_contact
        result = await get_contact(contact_id=contact_id, user=self.user, db=self.session)
        self.assertEqual(result, expected_contact)

    async def test_create_contact_success(self):
        contact_data = ContactModel(
            first_name="Bill",
            last_name="Rodgers",
            email="bill@example.com",
            phone_number="+380501234567",
            birthday=None,
            position=None)
        created_contact = Contact(**contact_data.model_dump(), user=self.user)

        self.session.add.return_value = None
        self.session.commit.return_value = None
        self.session.refresh.return_value = created_contact
        result = await create_contact(body=contact_data, user=self.user, db=self.session)

        self.assertEqual(result.first_name, created_contact.first_name)
        self.assertEqual(result.last_name, created_contact.last_name)
        self.assertEqual(result.email, created_contact.email)
        self.assertEqual(result.phone_number, created_contact.phone_number)
        self.assertEqual(result.birthday, created_contact.birthday)
        self.assertEqual(result.position, created_contact.position)

    async def test_create_contact_duplicated_email(self):
        contact_data = ContactModel(
            first_name="Bill",
            last_name="Johnson",
            email="bill@example.com",
            phone_number="+380501234589",
            birthday=None,
            position=None)
        error = IntegrityError(None, None, None, None)
        error.orig = "Duplicate fields: email"

        self.session.add.side_effect = error
        self.session.commit.return_value = None
        self.session.rollback.return_value = None

        with self.assertRaises(HTTPException) as context:
            await create_contact(body=contact_data, user=self.user, db=self.session)
        self.assertEqual(context.exception.status_code, status.HTTP_409_CONFLICT)

    async def test_create_contact_duplicated_phone_number(self):
        contact_data = ContactModel(
            first_name="Bill",
            last_name="Rodgers",
            email="bill@example.com",
            phone_number="+380501234567",
            birthday=None,
            position=None)
        error = IntegrityError(None, None, None, None)
        error.orig = "Duplicate fields: phone_number"

        self.session.add.side_effect = error
        self.session.commit.return_value = None
        self.session.rollback.return_value = None

        with self.assertRaises(HTTPException) as context:
            await create_contact(body=contact_data, user=self.user, db=self.session)
        self.assertEqual(context.exception.status_code, status.HTTP_409_CONFLICT)

    async def test_delete_contact_success(self):
        contact_id = 1
        contact = Contact(id=contact_id, user_id=self.user.id)
        self.session.query(Contact).filter(Contact.id == contact_id,
                                           Contact.user_id == self.user.id).first.return_value = contact
        expected_result = await delete_contact(contact_id=contact_id, user=self.user, db=self.session)
        self.assertEqual(expected_result, f"{contact.first_name} {contact.last_name} was deleted")

    async def test_delete_contact_not_found(self):
        contact_id = 1
        self.session.query(Contact).filter(Contact.id == contact_id,
                                           Contact.user_id == self.user.id).first.return_value = None
        expected_result = await delete_contact(contact_id=contact_id, user=self.user, db=self.session)
        self.assertIsNone(expected_result)

    async def test_put_update_contact_success(self):
        contact_id = 1
        contact_data = ContactModel(
            first_name="Updated First Name",
            last_name="Updated Last Name",
            email="updated@example.com",
            phone_number="+380501234567",
            birthday=None,
            position="Updated Position")
        contact = Contact(id=contact_id, user_id=self.user.id)
        self.session.query(Contact).filter(Contact.id == contact_id,
                                           Contact.user_id == self.user.id).first.return_value = contact

        updated_contact = await put_update_contact(contact_id=contact_id, body=contact_data, user=self.user,
                                                   db=self.session)

        self.assertEqual(updated_contact.first_name, contact_data.first_name)
        self.assertEqual(updated_contact.last_name, contact_data.last_name)
        self.assertEqual(updated_contact.email, contact_data.email)
        self.assertEqual(updated_contact.phone_number, contact_data.phone_number)
        self.assertEqual(updated_contact.birthday, contact_data.birthday)
        self.assertEqual(updated_contact.position, contact_data.position)

    async def test_patch_update_contact_success(self):
        contact_id = 1
        contact_data = ContactUpdate(
            email="new_email@example.com",
            phone_number="+380507892301",
            position="Updated Position"
        )
        contact = Contact(id=contact_id, user_id=self.user.id)
        self.session.query(Contact).filter(Contact.id == contact_id,
                                           Contact.user_id == self.user.id).first.return_value = contact
        updated_contact = await patch_update_contact(contact_id=contact_id, body=contact_data, user=self.user,
                                                     db=self.session)
        self.assertEqual(updated_contact.email, contact_data.email)
        self.assertEqual(updated_contact.phone_number, contact_data.phone_number)
        self.assertEqual(updated_contact.position, contact_data.position)

    async def test_search_contacts_success(self):
        q = "John"
        limit = 10
        skip = 0
        expected_result = [Contact(), Contact(), Contact()]

        db_query_mock = MagicMock()
        db_query_mock.filter.return_value.offset.return_value.limit.return_value.all.return_value = expected_result

        self.session.query.return_value = db_query_mock

        result = await search_contacts(q=q, skip=skip, limit=limit, user=self.user, db=self.session)
        self.assertEqual(result, expected_result)

    async def test_search_contacts_not_found(self):
        q = "Bob"
        limit = 10
        skip = 0
        expected_result = None

        db_query_mock = MagicMock()
        db_query_mock.filter.return_value.offset.return_value.limit.return_value.all.return_value = expected_result

        self.session.query.return_value = db_query_mock

        result = await search_contacts(q=q, skip=skip, limit=limit, user=self.user, db=self.session)
        self.assertEqual(result, expected_result)

    async def test_get_upcoming_birthdays(self):
        contact_1 = Contact(birthday=date.today() + timedelta(days=5))
        contact_2 = Contact(birthday=date.today() + timedelta(days=10))

        self.session.query().filter_by().all.return_value = [contact_1, contact_2]
        days = 12
        result = await get_upcoming_birthdays(days=days, user=self.user, db=self.session)

        self.assertIn(contact_1, result)
        self.assertIn(contact_2, result)

    async def test_get_upcoming_birthdays_not_found(self):
        contact1 = Contact(birthday=date.today() - timedelta(days=25))
        expected_result = None
        self.session.query().filter_by().all.return_value = [contact1]
        days = 12
        result = await get_upcoming_birthdays(days=days, user=self.user, db=self.session)

        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()
