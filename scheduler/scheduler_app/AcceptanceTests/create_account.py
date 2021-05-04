from django.test import Client, TestCase
from scheduler_app.classes.accountcreation import create_account
from scheduler_app.models import Account


class Account_creation(TestCase):
    def setUp(self):
        self.client = Client()
        self.supervisor = Account.object.create(name="Admin", email="123@gmail.com", password="password", role = Account.Role.SUPERVISOR)
        self.supervisor.set_password("password")
        self.supervisor.save()

    def test_account_creation_valid(self):
        response = self.client.post("/", {"email":self.supervisor.get_email(), "password":"password"}) #methods need to be implemented
        self.assertEqual(response.url,"/admin/") #admin page
        new_account = create_account(name="james", role=Account.Role.INSTRUCTOR,email= "james@gmail.com",password="123")
        new_account.save()
        self.assertEqual(new_account,Account.objects.get(email=new_account.get_email()), "New account was not created")

    def test_account_creation_invalid(self):
        response = self.client.post("/", {"email":self.supervisor.get_email(), "password":"password"}) #methods need to be implemented
        self.assertEqual(response.url,"/admin/") #admin page
        new_account = create_account(name="supervisor2", role=Account.Role.SUPERVISOR, email= self.supervisor.get_email(),password="123")
        new_account.save()
        self.assertEqual(new_account,Account.objects.get(email=new_account.get_email()), "New account was created with same email as Supervisor")
