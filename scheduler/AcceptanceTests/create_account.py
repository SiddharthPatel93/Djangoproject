from unittest.mock import patch

from django.test import Client, TestCase
from passlib.hash import argon2
from classes.accountcreation import create_account
from scheduler_app.models import Account, Course, Section


class Account_creation(TestCase):
    def setUp(self):
        self.client = Client()
        self.supervisor = Account.object.create(name="Admin", email="123@gmail.com", password="password", role = Account.Role.SUPERVISOR)
        self.supervisor.set_password("password")
        self.supervisor.save()

    def test_account_creation_valid(self):
        response = self.client.post("/", {"email":self.supervisor.get_email(), "password":"password"}) #methods need to be implemented
        self.assertEqual(response.url,"/admin/") #admin page
        new_account =create_account(name="james", role=Account.Role.INSTRUCTOR,password="123")
        new_account.save()
        self.assertEqual(new_account,Account.objects.get(email=new_account.get_email()))