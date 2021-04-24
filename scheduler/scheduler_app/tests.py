from unittest.mock import patch

from django.test import Client, TestCase
from passlib.hash import argon2

from .models import Account, Course, Section

# Models

class AccountTest(TestCase):
    def test_matchName(self):
        name = "Jimothy"
        a = Account(name=name)
        self.assertEqual(name, a.__str__(), "Account name does not equal entered name")

    def test_checkPassword(self):
        a = Account(password="$argon2id$v=19$m=102400,t=2,p=8$YSwlBOCc8z5HKAUAAIBw7g$YwFCp+9Vdrv+v6Dxd2FY7Q")
        self.assertTrue(a.check_password("right"), "Account says right password is wrong")
        self.assertFalse(a.check_password("wrong"), "Account says wrong password is right")
    
    def test_setPassword(self):
        a = Account()

        real_using = argon2.using
        with patch("passlib.hash.argon2.using", lambda: real_using(salt=b"himalayan")):
            a.set_password("right")
        
        self.assertEqual("$argon2id$v=19$m=102400,t=2,p=8$aGltYWxheWFu$1ah3MW6jG4JC7EvDBQD+hg", \
            a.password, "Account does not set password correctly")

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
            role=Account.Role.SUPERVISOR,
        )
        self.account.set_password(self.password)
        self.account.save()
    
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