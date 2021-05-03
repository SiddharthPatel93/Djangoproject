from django.test import Client, TestCase

from .classes import permissions
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