from bs4 import BeautifulSoup
from django.forms.models import model_to_dict
from django.test import Client, TestCase

from .classes import permissions
from .models import Account

class LoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.route = "/login/"
        self.homepage = "/"
        self.account = Account.objects.create(
            email="email@email.email",
            password="password",
            role=Account.Role.SUPERVISOR,
        )
    
    def test_loggedOut(self):
        r = self.client.get(self.route, follow=True)
        self.assertEqual(200, r.status_code, "Login page fails to load with status code 200")
        self.assertNotIn("account", self.client.session, "Loading login page adds account to session")
        self.assertNotIn("errors", r.context, "Loading login page includes errors list")

    def test_loggedIn(self):
        permissions.login(self.client, self.account)
        r = self.client.get(self.route, follow=True)
        self.assertEqual([(self.homepage, 302)], r.redirect_chain, "GETing login page when logged in fails to redirect to homepage")
        self.assertEqual(self.account.pk, self.client.session["account"], "GETing login page when logged in removes account session")
        r = self.client.post(self.route, follow=True)
        self.assertEqual([(self.homepage, 302)], r.redirect_chain, "POSTing login page when logged in fails to redirect to homepage")
        self.assertEqual(self.account.pk, self.client.session["account"], "POSTing login page when logged in removes account session")
    
    def test_displaysErrors(self):
        r = self.client.post(self.route, {})
        self.assertEqual(400, r.status_code, "Blank login fails to load with status code 400")
        self.assertEqual(2, len(r.context["errors"]), "Bad login fails to display errors")
        r = self.client.post(self.route, {"email": self.account.email, "password": "wrong"})
        self.assertEqual(401, r.status_code, "Incorrect login fails to load with status code 401")

    def test_successfulLogin(self):
        r = self.client.post(self.route, model_to_dict(self.account), follow=True)
        self.assertEqual([(self.homepage, 302)], r.redirect_chain, "Successful login fails to redirect to homepage")
        self.assertEqual(self.account.pk, self.client.session["account"], "Successful login fails to login to account")

class LogoutTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.route = "/logout/"
        self.account = Account.objects.create(role=Account.Role.TA)
    
    def perform_logout(self):
        return self.client.post(self.route, follow=True)

    def test_performsLogout(self):
        logged_out = self.perform_logout()
        permissions.login(self.client, self.account)
        logged_in = self.perform_logout()
        
        self.assertEqual([("/login/", 302)], logged_in.redirect_chain, "Logout page does not redirect user to login page")
        self.assertEqual(logged_in.redirect_chain, logged_out.redirect_chain,
            "Logout does not produce equal redirects for logged-in and logged-out accounts")
        self.assertNotIn("account", self.client.session, "Logout does not erase session account")

class CreateUserTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.route = "/users/create/"
        self.user = Account.objects.create(
            email="a@a.com",
            role=Account.Role.TA,
        )
        self.supervisor = Account.objects.create(
            email="b@b.com",
            role=Account.Role.SUPERVISOR,
        )
    
    def test_permisssions(self):
        r = self.client.get(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "GETing user create page does not redirect to login page when logged out")
        r = self.client.post(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "POSTing user create page does not redirect to login page when logged out")

        permissions.login(self.client, self.user)
        r = self.client.get(self.route)
        self.assertEqual(403, r.status_code, "GETing user create page does not load with status code 403 when unprivileged user")
        r = self.client.post(self.route)
        self.assertEqual(403, r.status_code, "POSTing user create page does not load with status code 403 when unprivileged user")

        permissions.login(self.client, self.supervisor)
        r = self.client.get(self.route)
        self.assertEqual(200, r.status_code, "GETing create page does not load with status code 200 when supervisor")
        r = self.client.post(self.route)
        self.assertEqual(401, r.status_code, "POSTing create page does not load with status code 401 when supervisor")
    
    def test_errorVisibility(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route)
        self.assertEqual(401, r.status_code, "User creation with error does not load with status code 401")
        self.assertLess(0, len(r.context["errors"]), "User create page does not show errors")
    
    def test_createUser(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route, {
            "name": "name",
            "role": Account.Role.SUPERVISOR,
            "email": "c@c.com",
            "password": "password",
        }, follow=True)
        self.assertEqual([("/users/?user_created=true", 302)], r.redirect_chain, "Successful user creation does not redirect to users page with flag set")

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