from django.forms.models import model_to_dict
from django.test import Client, TestCase

from .classes import permissions, users
from .models import Account

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
    