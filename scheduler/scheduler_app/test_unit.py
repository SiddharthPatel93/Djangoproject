from typing import Union

from django.forms.models import model_to_dict
from django.test import Client, TestCase

from .classes import permissions, users
from .models import Account, Course, Section

# Model methods

class AccountTest(TestCase):
    def test_matchName(self):
        name = "Jimothy"
        a = Account(name=name)
        self.assertEqual(name, a.__str__(), "Account name fails to equal entered name")

class CourseTest(TestCase):
    def test_matchName(self):
        name = "CS 361"
        c = Course(name=name)
        self.assertEqual(name, c.__str__(), "Course name fails to equal entered name")

class SectionTest(TestCase):
    def test_matchName(self):
        s = Section(num=902)
        self.assertEqual("902", s.__str__(), "Section name fails to equal entered number")

# Classes

# Permissions

class ClientLoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.existent_user = Account.objects.create(role=Account.Role.SUPERVISOR)
        self.nonexistent_user = Account(role=Account.Role.SUPERVISOR)
    
    def test_logsIn(self):
        self.assertNotIn("account", self.client.session, "Test client has account in session before login")
        permissions.login(self.client, self.existent_user)
        self.assertEqual(self.existent_user.pk, self.client.session["account"], "Login function fails to login user")
    
    def test_nonexistentUser(self):
        with self.assertRaises(ValueError):
            permissions.login(self.client, self.nonexistent_user)
        self.assertNotIn("account", self.client.session, "Login functions logs in nonexistent user")

class CreateUserTest(TestCase):
    def get_user(self, user_details: dict) -> Union[Account, None]:
        try:
            return Account.objects.get(email=user_details["email"])
        except (Account.DoesNotExist, Account.MultipleObjectsReturned):
            return None
    
    def test_missingFields(self):
        errors = users.create({})
        self.assertEqual(4, len(errors), "User create function fails to return errors for missing fields")
    
    def test_validateEmail(self):
        user_details = {
            "name": "user",
            "role": Account.Role.TA,
            "email": "bad",
            "password": "password",
        }
        errors = users.create(user_details)
        self.assertEqual(1, len(errors), "User create function fails to validate format of email")
        self.assertIsNone(self.get_user(user_details), "User create function creates user with bad email")
        user_details["email"] = "a@a.com"
        errors = users.create(user_details)
        self.assertEqual(1, len(errors), "User create function fails to validate availability of email")
        self.assertIsNotNone(self.get_user(user_details), "User create function creates user with taken email")
    
    def test_createUser(self):
        user_details = {
            "name": "name",
            "role": Account.Role.TA,
            "email": "c@c.com",
            "password": "password",
        }
        errors = users.create(user_details)
        self.assertEqual(0, len(errors), "User create function produces errors when ignoring optional fields")
        account = self.get_user(user_details)
        self.assertIsNotNone(account, "User create function fails to create user")
        
        user_details = {
            **user_details,
            "email": "d@d.com",
            "phone": "phone",
            "address": "address",
            "office_hours": "office_hours",
        }
        errors = users.create(user_details)
        account = self.get_user(user_details)
        data = model_to_dict(account)
        for field, value in user_details.items():
            self.assertEqual(value, data[field], f"User create function fails to assign field {field}")

class EditUserTest(TestCase):
    def setUp(self):
        self.user = Account.objects.create(
            name="TA",
            role=Account.Role.TA,
            email="ta@ta.ta",
            password="TA",
            phone="TA",
            address="TA",
            office_hours="TA",
        )
        self.supervisor = Account.objects.create(
            name="Supervisor",
            role=Account.Role.SUPERVISOR,
            email="supervisor@supervisor.supervisor",
            password="supervisor",
            phone="supervisor",
            address="supervisor",
            office_hours="supervisor",
        )
    
    def test_editsUser(self):
        data = {
            "name": "name",
            "role": Account.Role.INSTRUCTOR,
            "email": "email@email.email",
            "password": "password",
            "phone": "phone",
            "address": "address",
            "office_hours": "office_hours",
        }
        good_edit = users.edit(self.supervisor, self.user, data)
        self.assertEqual(0, len(good_edit), "Making correct edit to user produces errors")
        
        user = model_to_dict(self.user)
        del user["id"]
        for field, value in data.items():
            self.assertEqual(value, user[field], f"User edit function fails to correctly change field {field}")
    
    def test_rejectsOwnRole(self):
        role_edit = users.edit(self.user, self.user, {"role": Account.Role.INSTRUCTOR.value})
        self.assertEqual(1, len(role_edit), "User edit function fails to block user from editing own role")
    
    def test_acceptsInPlaceEmail(self):
        email_edit = users.edit(self.user, self.user, {"email": self.user.email})
        self.assertEqual(0, len(email_edit), "User edit function fails to replace user email with existing one")
    
    def test_checksValidEmail(self):
        email_edit = users.edit(self.user, self.user, {"email": "invalid"})
        self.assertEqual(1, len(email_edit), "User edit function fails to block user from changing email to invalid one")
    
    def test_checksDuplicateEmail(self):
        email_edit = users.edit(self.user, self.user, {"email": self.supervisor.email})
        self.assertEqual(1, len(email_edit), "User edit function fails to block user from changing email to duplicate one")
    