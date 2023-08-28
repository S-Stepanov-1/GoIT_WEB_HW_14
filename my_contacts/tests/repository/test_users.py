import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from my_contacts.schemas import UserModel
from my_contacts.database.models import User
from my_contacts.repository.users import (get_user_by_email, create_user, delete_user, update_token,
                                          confirmed_email, update_avatar, change_password
                                          )


class TestUsersRepository(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.session = MagicMock(spec=Session)

    async def test_get_user_by_email(self):
        email = "test_mail@example.com"
        user = User(id=1, user_email=email)
        self.session.query().filter_by().first.return_value = user

        result = await get_user_by_email(email=email, db=self.session)
        self.assertEqual(result, user)

    async def test_get_user_by_email_nonexistent(self):
        user_email = "non_existent_mail@example.com"
        self.session.query().filter_by().first.return_value = None

        result = await get_user_by_email(email=user_email, db=self.session)
        self.assertIsNone(result)

    async def test_create_user(self):
        user_data = UserModel(username="fake_user", user_email="test@example.com", password="password123")
        new_user = User(id=1, user_email=user_data.user_email)
        self.session.add.return_value = None
        self.session.commit.return_value = None
        self.session.refresh.return_value = None

        result = await create_user(body=user_data, db=self.session)
        self.assertEqual(result.user_email, new_user.user_email)

    async def test_delete_user(self):
        user = User(id=1, user_email="test_mail@example.com")
        self.session.delete.return_value = None
        self.session.commit.return_value = None
        self.session.refresh.return_value = None

        await delete_user(user=user, db=self.session)
        self.assertEqual(self.session.delete.call_args[0][0], user)

    async def test_update_token(self):
        user = User(id=1, user_email="test_mail@example.com")
        token = "new_refresh_token"
        self.session.commit.return_value = None
        self.session.refresh.return_value = None

        await update_token(user=user, token=token, db=self.session)
        self.assertEqual(user.refresh_token, token)

    async def test_confirmed_email(self):
        user_email = "test_mail@example.com"
        user = User(id=1, user_email=user_email, confirmed=True)
        self.session.commit.return_value = None
        self.session.refresh.return_value = None

        await confirmed_email(email=user_email, db=self.session)
        self.assertTrue(user.confirmed)

    async def test_update_avatar(self):
        user_email = "test_mail@example.com"
        avatar_url = "https://fake.com/avatar.png"
        self.session.commit.return_value = None
        self.session.refresh.return_value = None

        updated_user = await update_avatar(email=user_email, avatar_url=avatar_url, db=self.session)
        self.assertEqual(updated_user.avatar_url, avatar_url)

    async def test_change_password(self):
        user_email = "test_mail@example.com"
        new_password = "new_password123"
        user = User(id=1, user_email=user_email, password="old_password123")
        self.session.commit.return_value = None
        self.session.refresh.return_value = None

        updated_user = await change_password(user=user, password=new_password, db=self.session)
        self.assertEqual(updated_user.password, new_password)


if __name__ == '__main__':
    unittest.main()
