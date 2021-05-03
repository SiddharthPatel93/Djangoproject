from bs4 import BeautifulSoup
from django.forms.models import model_to_dict
from django.test import Client, TestCase

from .classes import permissions
from .models import Account

class ViewUserTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.route = "/users"

        self.user = Account.objects.create(
            name="TA",
            role=Account.Role.TA,
            email="ta@ta.ta",
            password="TA",
            phone="TA",
            address="TA",
            office_hours="TA",
        )
        self.user_route = f"{self.route}/{self.user.pk}/"
        self.supervisor = Account.objects.create(
            name="Supervisor",
            role=Account.Role.SUPERVISOR,
            email="supervisor@supervisor.supervisor",
            password="supervisor",
            phone="supervisor",
            address="supervisor",
            office_hours="supervisor",
        )
        self.supervisor_route = f"{self.route}/{self.supervisor.pk}/"
    
    def test_permissions(self):
        r = self.client.get(self.user_route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "Logged-out user is not redirected to login page when accessing user view page")

        permissions.login(self.client, self.user)
        r = self.client.get(self.user_route)
        self.assertEqual(200, r.status_code, "GETing own user view page as user does not load with status code 200")
        r = self.client.post(self.user_route)
        self.assertEqual(401, r.status_code, "POSTing own user view page as user does not load with status code 401")
        r = self.client.get(self.supervisor_route)
        self.assertEqual(200, r.status_code, "GETing other user view page as user does not load with status code 200")
        r = self.client.post(self.supervisor_route)
        self.assertEqual(403, r.status_code, "POSTing other user view page as user does not load with status code 403")
        
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.supervisor_route)
        self.assertEqual(401, r.status_code, "POSTing own user view page as supervisor does not load with status code 401")
    
    def test_fieldAccessibility(self):
        permissions.login(self.client, self.user)
        soup = BeautifulSoup(self.client.get(self.user_route).content, "lxml")
        for field in ["name", "role", "email", "password", "phone", "address", "office_hours"]:
            self.assertIsNotNone(soup.find(attrs={"name": field}), f"Field {field} is not present in user view page")
        for field in ["name", "email", "password", "phone", "address", "office_hours"]:
            self.assertNotIn("readonly", soup.find(attrs={"name": field}), f"Field {field} is readonly when viewing own profile as user")
        for field in ["role"]:
            self.assertIn("readonly", soup.find(attrs={"name": field}), f"Field {field} is not readonly when viewing own profile as user")
        soup = BeautifulSoup(self.client.get(self.supervisor_route).content, "lxml")
        for field in ["name", "role", "email", "password", "phone", "address", "office_hours"]:
            self.assertIn("readonly", soup.find(attrs={"name": field}), f"Field {field} is not readonly when viewing other profile as user")

        permissions.login(self.client, self.supervisor_route)
        soup = BeautifulSoup(self.client.get(self.user_route).content, "lxml")
        for field in ["name", "role", "email", "password", "phone", "address", "office_hours"]:
            self.assertNotIn("readonly", soup.find(attrs={"name": field}), f"Field {field} is readonly when viewing other profile as supervisor")
        soup = BeautifulSoup(self.client.get(self.supervisor_route).content, "lxml")
        for field in ["name", "email", "password", "phone", "address", "office_hours"]:
            self.assertNotIn("readonly", soup.find(attrs={"name": field}), f"Field {field} is readonly when viewing own profile as supervisor")
        for field in ["role"]:
            self.assertIn("readonly", soup.find(attrs={"name": field}), f"Field {field} is not readonly when viewing own profile as supervisor")
    
    def test_displayErrors(self):
        permissions.login(self.client, self.user)
        data = {
            "role": Account.Role.INSTRUCTOR.value,
            "email": "invalid",
        }
        r = self.client.post(self.user_route, data)
        self.assertEqual(2, len(r.context["errors"]), "Editing own profile with invalid info does not produce errors")
        for field, value in data.items():
            self.assertNotEqual(value, r.context[field], f"Editing own profile with invalid info changes field {field}")
    
    def test_changeUserInfo(self):
        permissions.login(self.client, self.user)
        supervisor_info = model_to_dict(self.supervisor)
        del supervisor_info["id"]
        supervisor_info["email"] = "changed@supervisor.supervisor"
        del supervisor_info["role"]
        r = self.client.post(self.user_route, supervisor_info)
        self.assertEqual(200, r.status_code, "User cannot change own info")
        for field, value in supervisor_info.items():
            self.assertEqual(value, r.context[field], f"Field {field} is not changed when editing own info as user")
        self.assertTrue(r.context["updated"], "Updated message not shown to user")
        r = self.client.post(self.supervisor_route, supervisor_info)
        self.assertEqual(403, r.status_code, "User can change info of supervisor")

        permissions.login(self.client, self.supervisor)
        supervisor_info["role"] = Account.Role.INSTRUCTOR.value
        supervisor_info["email"] = "changed@ta.ta"
        r = self.client.post(self.user_route, supervisor_info)
        self.assertEqual(200, r.status_code, "Supervisor cannot change user info")
        for field, value in supervisor_info.items():
            self.assertEqual(value, r.context[field], f"Field {field} is not changed when editing other user info as supervisor")
        user_info = model_to_dict(self.user)
        del user_info["id"]
        del user_info["role"]
        r = self.client.post(self.supervisor_route, user_info)
        self.assertEqual(200, r.status_code, "Supervisor cannot change own info")
        for field, value in user_info.items():
            self.assertEqual(value, r.context[field], f"Field {field} is not changed when editing own info as supervisor")