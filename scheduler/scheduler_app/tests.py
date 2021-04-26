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
        self.account = Account.objects.create(
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

class UserEditTest(TestCase):
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
    
    def test_unitEditsUser(self):
        data = {
            "name": "name",
            "role": Account.Role.INSTRUCTOR,
            "password": "password",
            "phone": "phone",
            "address": "address",
            "office_hours": "office_hours",
        }
        good_edit = users.perform_edit(self.supervisor, self.user, data)
        self.assertEqual(0, len(good_edit), "Making correct edit to user produces errors")
        
        user = model_to_dict(self.user)
        del user["id"]
        del user["email"]
        for field, value in data.items():
            self.assertEqual(value, user[field], f"User edit function does not correctly change field {field}")
    
    def test_unitValidatesFields(self):
        role_edit = users.perform_edit(self.user, self.user, {
            "role": Account.Role.INSTRUCTOR.value,
        })
        self.assertEqual(1, len(role_edit), f"User edit function does not block user from editing own role")

        role_edit = users.perform_edit(self.supervisor, self.supervisor, {
            "role": Account.Role.INSTRUCTOR.value,
        })
        self.assertEqual(1, len(role_edit), "User edit function does not block supervisor from editing own role")

    def login(self, account):
        s = self.client.session
        s["account"] = account.id
        s.save()
    
    def test_login(self):
        r = self.client.get(self.user_route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "Logged-out user is not redirected to login page when accessing user edit page")
    
    def test_userPermissions(self):
        self.login(self.user)
        r = self.client.get(self.user_route)
        self.assertEqual(200, r.status_code, "Unprivileged user cannot access own user edit page")
        r = self.client.get(self.supervisor_route)
        self.assertEqual(403, r.status_code, "Unprivileged user can access other user edit pages")
        
        self.login(self.supervisor)
        r = self.client.get(self.user_route)
        self.assertEqual(200, r.status_code, "Privileged user cannot access other user edit pages")
    
    def test_accessFields(self):
        self.login(self.user)
        r = self.client.get(self.user_route)
        for field in ["name", "password", "phone", "address", "office_hours"]:
            self.assertIn(field, r.context, f"Field {field} does not appear in own user edit page as user")
        self.assertNotIn("role", r.context, "Role appears in user edit page as user")

        self.login(self.supervisor)
        r = self.client.get(self.user_route)
        for field in ["name", "role", "password", "phone", "address", "office_hours"]:
            self.assertIn(field, r.context, f"Field {field} does not appear in other user edit page as supervisor")
        r = self.client.get(self.supervisor_route)
        for field in ["name", "password", "phone", "address", "office_hours"]:
            self.assertIn(field, r.context, f"Field {field} does not appear in own user edit page as supervisor")
        self.assertNotIn("role", r.context, "Role appears in own user edit page as supervisor")
    
    def test_displayErrors(self):
        self.login(self.user)
        r = self.client.post(self.user_route, {
            "role": Account.Role.INSTRUCTOR.value,
        })
        self.assertEqual(1, len(r.context["errors"]), "Editing own role does not produce error as user")

        self.login(self.supervisor)
        r = self.client.post(self.supervisor_route, {
            "role": Account.Role.INSTRUCTOR.value,
        })
        self.assertEqual(1, len(r.context["errors"]), "Editing own role does not produce error as supervisor")
    
    def test_changeUserInfo(self):
        self.login(self.user)
        supervisor_info = model_to_dict(self.supervisor)
        del supervisor_info["id"]
        del supervisor_info["role"]
        del supervisor_info["email"]
        r = self.client.post(self.user_route, supervisor_info)
        self.assertEqual(200, r.status_code, "User cannot change own info")
        for field, value in supervisor_info.items():
            self.assertEqual(value, r.context[field], f"Field {field} is not changed when editing own info as user")
        self.assertTrue(r.context["updated"], "Updated message not shown to user")
        r = self.client.post(self.supervisor_route, supervisor_info)
        self.assertEqual(403, r.status_code, "User can change info of supervisor")

        self.login(self.supervisor)
        supervisor_info["role"] = Account.Role.INSTRUCTOR.value
        r = self.client.post(self.user_route, supervisor_info)
        self.assertEqual(200, r.status_code, "Supervisor cannot change user info")
        for field, value in supervisor_info.items():
            self.assertEqual(value, r.context[field], f"Field {field} is not changed when editing other user info as supervisor")
        user_info = model_to_dict(self.user)
        del user_info["id"]
        del user_info["role"]
        del user_info["email"]
        r = self.client.post(self.supervisor_route, user_info)
        self.assertEqual(200, r.status_code, "Supervisor cannot change own info")
        for field, value in user_info.items():
            self.assertEqual(value, r.context[field], f"Field {field} is not changed when editing own info as supervisor")

class CreateUserTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.route = "/users/create/",
        self.user = Account.objects.create(
            email="a@a.com",
            role=Account.Role.TA,
        )
        self.supervisor = Account.objects.create(
            email="b@b.com",
            role=Account.Role.SUPERVISOR,
        )
    
    def test_unitMissingFields(self):
        errors = users.perform_create({})
        self.assertEqual(4, len(errors), "User create function does not return errors for missing fields")
    
    def test_unitValidateEmail(self):
        user_details = {
            "name": "user",
            "role": Account.Role.TA,
            "email": "bad",
            "password": "password",
        }
        errors = users.perform_create(user_details)
        self.assertEqual(1, len(errors), "User create function does not validate format of email")
        errors = users.perform_create({"email": "a@a.com", **user_details})
        self.assertEqual(1, len(errors), "User create function does not validate availability of email")
    
    def test_unitCreateUser(self):
        user_details = {
            "name": "name",
            "role": Account.Role.TA,
            "email": "a@a.com",
            "password": "password",
        }
        errors = users.perform_create(user_details)
        self.assertEqual(0, len(errors), "User create function produces errors when ignoring optional fields")
        account = Account.objects.get(email=user_details["email"])
        self.assertIsNotNone(account, "User create function does not create user")
        
        user_details = {
            "email": "b@b.com",
            "phone": "phone",
            "address": "address",
            "office_hours": "office_hours",
            **user_details,
        }
        errors = users.perform_create(user_details)
        account = Account.objects.get(email=user_details["email"])
        data = model_to_dict(account)
        for field, value in user_details.items():
            self.assertEqual(value, data[field], f"User create function does not assign field {field}")

    def login(self, account):
        s = self.client.session
        s["account"] = account.id
        s.save()
    
    def test_getPage(self):
        r = self.client.get(self.route)
        self.assertEqual(403, r.status_code, "User create page does not load with status code 403 when logged out")
        self.login(self.user)
        r = self.client.get(self.route)
        self.assertEqual(403, r.status_code, "User create page does not load with status code 403 when unprivileged user")
        self.login(self.supervisor)
        r = self.client.get(self.route)
        self.assertEqual(200, r.status_code, "User create page does not load with status code 200 when supervisor")
    
    def test_errorVisibility(self):
        r = self.client.post(self.route, {})
        self.assertEqual(401, r.status_code, "User creation with error does not load with status code 401")
        self.assertLess(0, r.context["errors"], "User create page does not show errors")
    
    def test_createUser(self):
        r = self.client.post(self.route, {
            "name": "name",
            "role": Account.Role.SUPERVISOR,
            "email": "c@c.com",
            "password": "password",
        }, follow=True)
        self.assertEqual([("/users/", 302)], r.redirect_chain, "Successful user creation does not redirect to users page")