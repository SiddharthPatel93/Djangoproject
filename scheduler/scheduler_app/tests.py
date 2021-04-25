from django.forms.models import model_to_dict
from django.test import Client, TestCase

from .classes import users
from .models import Account, Course, Section

# Models

class AccountTest(TestCase):
    def test_matchName(self):
        name = "Jimothy"
        a = Account(name=name)
        self.assertEqual(name, a.__str__(), "Account name does not equal entered name")

class CourseTest(TestCase):
    def test_matchName(self):
        name = "CS 361"
        c = Course(name=name)
        self.assertEqual(name, c.__str__(), "Course name does not equal entered name")

class SectionTest(TestCase):
    def test_matchName(self):
        s = Section(num=902)
        self.assertEqual("902", s.__str__(), "Section name does not equal entered number")

# Views

class LoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.route = "/login/"
        self.email = "test@example.com"
        self.password = "test"
        self.account = Account(
            email=self.email,
            password=self.password,
            role=Account.Role.SUPERVISOR,
        )
    
    def test_loadLogin(self):
        r = self.client.get(self.route, follow=True)
        self.assertEqual(200, r.status_code, "Login page does not load with status code 200")
        self.assertEqual([], r.redirect_chain, "Login page redirects to another page")
        self.assertNotIn("account", self.client.session, "Login page adds account to session")
        self.assertIsNotNone(r.context, "Login page does not render template")
        self.assertNotIn("errors", r.context, "Login page includes errors list")
    
    def test_emptyLogin(self):
        for data in [{}, {"email": "", "password": ""}]:
            r = self.client.post(self.route, data, follow=True)
            self.assertEqual(400, r.status_code, f"Empty login with data {data} does not load with status code 400")
            self.assertEqual([], r.redirect_chain, f"Empty login with data {data} redirects to another page")
            self.assertNotIn("account", self.client.session, f"Empty login with data {data} adds account to session")
            self.assertIsNotNone(r.context, f"Empty login with data {data} does not render template")
            self.assertIn("errors", r.context, f"Empty login with data {data} does not include errors list")
            self.assertEqual(2, len(r.context["errors"]), f"Empty login with data {data} does not produce 2 errors for empty fields")

    def test_successfulLogin(self):
        r = self.client.post(self.route, {"email": self.email, "password": self.password})
        self.assertEqual(302, r.status_code, "Successful login does not load with status code 302")
        self.assertIn("Location", r.headers, "Successful login does not redirect")
        self.assertEqual("/", r.headers["Location"], "Successful login does not redirect to course dashboard")
        self.assertIn("account", self.client.session, "Successful login does not add account to session")
        self.assertEqual(self.account.id, self.client.session["account"], "Successful login adds wrong account to session")

    def test_failedLogin(self):
        previous_error = ""

        for data in [{"email": self.email, "password": "wrong"}, {"email": "does@not.exist", "password": self.password}]:
            r = self.client.post(self.route, data, follow=True)
            self.assertEqual(401, r.status_code, f"Failed login with data {data} does not load with status code 401")
            self.assertEqual([], r.redirect_chain, f"Failed login with data {data} redirects to another page")
            self.assertNotIn("account", self.client.session, f"Failed login {data} adds account to session")
            self.assertIsNotNone(r.context, f"Failed login with data {data} does not render template")
            self.assertIn("errors", r.context, f"Failed login with data {data} does not include errors list")
            self.assertEqual(1, len(r.context["errors"]), f"Failed login with data {data} does not produce 1 error for failed login")
            
            error = r.context["errors"][0]
            if previous_error:
                self.assertEqual(previous_error, error, "Errors for wrong username and wrong password are different")
            else:
                previous_error = error

class LogoutView(TestCase):
    def setUp(self):
        self.client = Client()
        self.route = "/logout/"
    
    def test_wrongMethod(self):
        r = self.client.get(self.route)
        self.assertEqual(405, r.status_code, "Making logout GET request does not load with status code 405")
        self.assertIn(b"history.back()", r.content, "Making logout GET request does not redirect user to previous page")
    
    def perform_logout(self):
        return self.client.post(self.route, follow=True)

    def test_loggedIn(self):
        logged_out = self.perform_logout()
        # https://docs.djangoproject.com/en/3.2/topics/testing/tools/#persistent-state
        s = self.client.session
        s["account"] = 1
        s.save()
        logged_in = self.perform_logout()
        
        self.assertLess(0, len(logged_in.redirect_chain), "Logout does not redirect user")
        self.assertEqual(logged_in.redirect_chain, logged_out.redirect_chain,
            "Logout does not produce equal redirects for logged-in and logged-out accounts")
        self.assertNotIn("account", self.client.session, "Logout does not erase session account")

class UsersView(TestCase):
    def test_listUsers(self):
        """
        Check if all users are being populated in the view.
        Setup function not included since this is the only case with users I can think of.

        You can add users here: http://127.0.0.1:8000/admin/scheduler_app/account/add/

        Check:
        - Permissions (see lines 99-102 for how to set account manually. check if it fails with nonexistent account #)
        """

class DeleteView(TestCase):
    def setUp(self):
        """Create test accounts and client."""
    
    def test_deleteUserUnit(self):
        """
        Test users.perform_delete.

        Check:
        - If account exists
        """
    
    def test_deleteExistentUser(self):
        """
        Test if existent user gets deleted right with the view.

        Check:
        - Permissions
        - Lack of error message
        - Redirect
        - User actually deleted
        """
    
    def test_deleteNonexistentUser(self):
        """
        Test if nonexistent user fails to get deleted with the view.
        Use your discretion with implementing these last two.
        It is possible I am being anal with all possible cases.

        Check:
        - Permissions
        - Error message
        - Redirect
        - No extraneous deletion taking place
        """
    
    def test_deleteOwnUser(self):
        """
        Test if the user deleting a user can't delete themself with the view.

        Check same qualities as last one.
        """

class UserEditView(TestCase):
    def login(self, account):
        s = self.client.session
        s["account"] = account.id
        s.save()
    
    def setUp(self):
        self.client = Client()
        self.route = "/users/edit"

        self.user = Account.objects.create(
            name="TA",
            role=Account.Role.TA,
            email="ta@ta.ta",
            password="TA",
            phone="TA",
            address="TA",
            office_hours="TA",
        )
        self.user_route = f"{self.route}/{self.user.id}/"
        self.supervisor = Account.objects.create(
            name="Supervisor",
            role=Account.Role.SUPERVISOR,
            email="supervisor@supervisor.supervisor",
            password="supervisor",
            phone="supervisor",
            address="supervisor",
            office_hours="supervisor",
        )
        self.supervisor_route = f"{self.route}/{self.supervisor.id}/"

        self.login(self.supervisor)
    
    def test_unitEditsUser(self):
        data = {
            "name": "name",
            "role": Account.Role.INSTRUCTOR,
            "email": "email@email.email",
            "password": "password",
            "phone": "phone",
            "address": "address",
            "office_hours": "office_hours"
        }
        good_edit = users.perform_edit(self.supervisor, self.user, data)
        self.assertEqual(0, len(good_edit), "Making correct edit to user produces errors")
        
        for key, value in data.items():
            self.assertEqual(value, self.user[key], f"User edit function does not correctly change key {key}")
    
    def test_unitValidatesFields(self):
        role_edit = users.perform_edit(self.supervisor, self.supervisor, {
            "role": Account.Role.INSTRUCTOR,
        })
        self.assertEqual(1, len(role_edit), f"User edit function does not block supervisor editing own role")

        email_edit = users.perform_edit(self.supervisor, self.user, {
            "email": "bad_email",
        })
        self.assertEqual(1, len(email_edit), f"User edit function does not validate email field")
    
    def test_login(self):
        r = self.client.get(self.user_route, follow=True)
        self.assertEqual(["/login/", 302], r.redirect_chain, "Logged-out user edit page does not redirect to login")
    
    def test_nonexistentUser(self):
        r = self.client.get(f"{self.route}/999/")
        self.assertEqual(404, r.status_code, "User edit page of nonexistent user does not load with 404 status code")
    
    def test_userPermissions(self):
        self.login(self.user)
        r = self.client.get(self.supervisor_route)
        self.assertEqual(403, r.status_code, "User edit page of any user other than currently logged-in unprivileged user does not load with 403 status code")
    
    def test_existentUser(self):
        r = self.client.get(self.user_route)
        self.assertEqual(200, r.status_code, "User edit page of existent user does not load with status code 200")
        for key, value in model_to_dict(self.user).items():
            self.assertEqual(value, r.context[key], f"User edit page does not show field {key}")

    def test_roleVisibility(self):
        r = self.client.get(self.supervisor_route)
        self.assertNotIn("role", r.context, "User edit page for logged-in supervisor shows role selector")

        self.login(self.user)
        r = self.client.get(self.user_route)
        self.assertNotIn("role", r.context, "User edit page for logged-in user shows role selector")
    
    def test_editUser(self):
        data = {
            "name": "name",
            "email": "email@email.email",
            "password": "password",
            "phone": "phone",
            "address": "address",
            "office_hours": "office_hours",
        }
        r = self.client.post(self.user_route, data)

        for key, value in data:
            self.assertEqual(value, r.context[key], f"User edit page does not change field {key}")