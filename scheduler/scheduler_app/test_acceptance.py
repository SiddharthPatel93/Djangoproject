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
        self.fields = ["name", "role", "email", "password", "phone", "address", "office_hours"]
    
    def test_permissions(self):
        r = self.client.get(self.user_route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "Logged-out user is not redirected to login page when accessing user view page")

        permissions.login(self.client, self.user)
        r = self.client.get(self.user_route)
        self.assertEqual(200, r.status_code, "GETing own user view page as user does not load with status code 200")
        r = self.client.post(self.user_route)
        self.assertEqual(200, r.status_code, "POSTing own user view page as user does not load with status code 200")
        r = self.client.get(self.supervisor_route)
        self.assertEqual(200, r.status_code, "GETing other user view page as user does not load with status code 200")
        r = self.client.post(self.supervisor_route)
        self.assertEqual(403, r.status_code, "POSTing other user view page as user does not load with status code 403")
        
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.supervisor_route)
        self.assertEqual(200, r.status_code, "POSTing own user view page as supervisor does not load with status code 200")
    
    def assert_accessibility_case(self, user: Account, route: str, case: str, hidden: list[str], readonly: list[str]):
        permissions.login(self.client, user)
        soup = BeautifulSoup(self.client.get(route).content, "lxml")

        for field in [f for f in self.fields if f not in hidden]:
            self.assertIsNotNone(soup.select_one(f"*[name={field}]"), f"Field {field} is not present when viewing {case}")
        for field in hidden:
            self.assertIsNone(soup.select_one(f"*[name={field}]"), f"Field {field} is present when viewing {case}")
        for field in [f for f in self.fields if f not in readonly]:
            self.assertIsNone(soup.select_one(f"*[name={field}][readonly], *[name={field}][disabled]"), f"Field {field} is readonly when viewing {case}")
        for field in readonly:
            self.assertIsNotNone(soup.select_one(f"*[name={field}][readonly], *[name={field}][disabled]"), f"Field {field} is not readonly when viewing {case}")
    
    def test_fieldAccessibility(self):
        self.assert_accessibility_case(self.user, self.user_route, "own profile as user", [], ["role"])
        self.assert_accessibility_case(self.user, self.supervisor_route, "other profile as user", ["password", "phone", "address"], ["name", "role", "email", "office_hours"])
        self.assert_accessibility_case(self.supervisor, self.user_route, "other profile as supervisor", [], [])
        self.assert_accessibility_case(self.supervisor, self.supervisor_route, "own profile as supervisor", [], ["role"])
    
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