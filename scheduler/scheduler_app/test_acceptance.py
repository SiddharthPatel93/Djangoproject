from bs4 import BeautifulSoup
from django.db.models import Model
from django.forms.models import model_to_dict
from django.test import Client, TestCase

from .classes import permissions
from .models import Account, Course, CourseMembership, Section

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
        
        self.assertEqual([("/login/", 302)], logged_in.redirect_chain, "Logout page fails to redirect user to login page")
        self.assertEqual(logged_in.redirect_chain, logged_out.redirect_chain,
            "Logout fails to produce equal redirects for logged-in and logged-out accounts")
        self.assertNotIn("account", self.client.session, "Logout fails to erase session account")

class ListUsersTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.route = "/users/"
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
        self.instructor = Account.objects.create(role=Account.Role.INSTRUCTOR)
        self.ta = Account.objects.create(role=Account.Role.TA)
        self.test_course = Course.objects.create(name="CS 361")
        CourseMembership.objects.create(account=self.ta, course=self.test_course)
        CourseMembership.objects.create(account=self.instructor, course=self.test_course)
    
    def test_permissions(self):
        r = self.client.get(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "GETing users list while logged out fails to redirect to login page")

        permissions.login(self.client, self.ta)
        r = self.client.get(self.route)
        self.assertEqual(200, r.status_code, "GETing users list while logged in fails to load with status code 200")

    def test_supervisorAccess(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.get(self.route)
        self.assertTrue(r.context["supervisor"], "Users list fails to show management tools for supervisor")
        self.assertEqual(3, len(r.context["users"]), "Users list fails to show all users for supervisor")
    
    def test_userAccess(self):
        permissions.login(self.client, self.ta)
        r = self.client.get(self.route)
        self.assertFalse(r.context["supervisor"], "Users list shows management tools for user")
        self.assertEqual(2, len(r.context["members"]), "Users list fails to show only course members for user")
        self.assertEqual(3, len(r.context["users"]), "Users list fails to show all users for user")

def assert_field_accessibility(self: TestCase, user: Account, route: str, model: Model, case: str, hidden: list[str], readonly: list[str]):
    permissions.login(self.client, user)
    soup = BeautifulSoup(self.client.get(route).content, "lxml")
    fields = [field for field in model_to_dict(model) if field not in ["id", "members"]]

    for field in [f for f in fields if f not in hidden]:
        self.assertIsNotNone(soup.select_one(f"*[name={field}]"), f"Field {field} is not present when viewing {case}")
    for field in hidden:
        self.assertIsNone(soup.select_one(f"*[name={field}]"), f"Field {field} is present when viewing {case}")
    for field in [f for f in fields if f not in readonly]:
        self.assertIsNone(soup.select_one(f"*[name={field}][readonly], *[name={field}][disabled]"), f"Field {field} is readonly when viewing {case}")
    for field in readonly:
        self.assertIsNotNone(soup.select_one(f"*[name={field}][readonly], *[name={field}][disabled]"), f"Field {field} is not readonly when viewing {case}")

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
        self.assertEqual([("/login/", 302)], r.redirect_chain, "GETing user create page fails to redirect to login page when logged out")
        r = self.client.post(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "POSTing user create page fails to redirect to login page when logged out")

        permissions.login(self.client, self.user)
        r = self.client.get(self.route)
        self.assertEqual(403, r.status_code, "GETing user create page fails to load with status code 403 as user")
        r = self.client.post(self.route)
        self.assertEqual(403, r.status_code, "POSTing user create page fails to load with status code 403 as user")

        permissions.login(self.client, self.supervisor)
        r = self.client.get(self.route)
        self.assertEqual(200, r.status_code, "GETing create page fails to load with status code 200 as supervisor")
        r = self.client.post(self.route)
        self.assertEqual(400, r.status_code, "POSTing create page fails to load with status code 400 as supervisor")
    
    def test_fieldAccessibility(self):
        assert_field_accessibility(self, self.supervisor, self.route, self.supervisor, "create user page as supervisor", [], [])
    
    def test_rolesList(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.get(self.route)
        self.assertIn("roles", r.context, "GETing user creation page fails to include roles list")
        r = self.client.post(self.route)
        self.assertIn("roles", r.context, "POSTing user creation page fails to include roles list")
    
    def test_errorVisibility(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route)
        self.assertEqual(400, r.status_code, "User creation with error fails to load with status code 400")
        self.assertLess(0, len(r.context["errors"]), "User creation page fails to show errors")
    
    def test_createUser(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route, {
            "name": "name",
            "role": Account.Role.SUPERVISOR,
            "email": "c@c.com",
            "password": "password",
        }, follow=True)
        self.assertEqual([("/users/?user_created=true", 302)], r.redirect_chain, "Successful user creation fails to redirect to users page with flag set")

class ViewUserTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.route = "/users"

        self.user = Account.objects.create(
            name="TA",
            role=Account.Role.TA,
            email="ta@ta.ta",
            password="ta",
            phone="ta",
            address="ta",
            office_hours="ta",
            skills="ta",
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
            skills="supervisor",
        )
        self.supervisor_route = f"{self.route}/{self.supervisor.pk}/"
    
    def test_permissions(self):
        r = self.client.get(self.user_route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "Logged-out user is not redirected to login page when accessing user view page")

        permissions.login(self.client, self.user)
        r = self.client.get(self.user_route)
        self.assertEqual(200, r.status_code, "GETing own user view page as user fails to load with status code 200")
        r = self.client.post(self.user_route)
        self.assertEqual(200, r.status_code, "POSTing own user view page as user fails to load with status code 200")
        r = self.client.get(self.supervisor_route)
        self.assertEqual(200, r.status_code, "GETing other user view page as user fails to load with status code 200")
        r = self.client.post(self.supervisor_route)
        self.assertEqual(403, r.status_code, "POSTing other user view page as user fails to load with status code 403")
        
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.supervisor_route)
        self.assertEqual(200, r.status_code, "POSTing own user view page as supervisor fails to load with status code 200")
    
    def test_fieldAccessibility(self):
        assert_field_accessibility(self, self.user, self.user_route, self.user, "own profile as user", [], ["role"])
        assert_field_accessibility(self, self.user, self.supervisor_route, self.user, "other profile as user", ["password", "skills", "phone", "address"], ["name", "role", "email", "office_hours"])
        assert_field_accessibility(self, self.supervisor, self.user_route, self.supervisor, "other profile as supervisor", [], [])
        assert_field_accessibility(self, self.supervisor, self.supervisor_route, self.supervisor, "own profile as supervisor", [], ["role"])
    
    def test_rolesList(self):
        permissions.login(self.client, self.user)
        r = self.client.get(self.user_route)
        self.assertIn("roles", r.context, "GETing user view page fails to include roles list")
        r = self.client.post(self.user_route)
        self.assertIn("roles", r.context, "POSTing user view page fails to include roles list")
    
    def test_displayErrors(self):
        permissions.login(self.client, self.user)
        data = {
            "role": Account.Role.INSTRUCTOR.value,
            "email": "invalid",
        }
        r = self.client.post(self.user_route, data)
        self.assertEqual(2, len(r.context["errors"]), "Editing own profile with invalid info fails to produce errors")
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

class DeleteUserTest(TestCase):
    def setUp(self):
        """Create test accounts and client."""
        self.client = Client()
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
        self.instructor = Account.objects.create(role=Account.Role.INSTRUCTOR)
        self.ta = Account.objects.create(role=Account.Role.TA)
        self.route_base = "/users/{}/delete/"
        self.route = self.route_base.format(self.ta.pk)
    
    def test_deleteExistentUser(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route, follow=True)
        self.assertEqual([("/users/", 302)], r.redirect_chain,
                         "Deleting user as supervisor fails to redirect to users list")
        self.assertNotIn(self.ta.pk, [user["pk"] for user in r.context["users"]],
                         "Deleting user as supervisor fails to delete user")

    def test_deleteNeedsSupervisor(self):
        permissions.login(self.client, self.instructor)
        r = self.client.post(self.route)
        self.assertEqual(403, r.status_code, "Deleting user as an instructor fails to load with status code 403")
    
    def test_deleteNonexistentUser(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route_base.format(999), follow=True)
        self.assertEqual(404, r.status_code, "Deleting nonexistent user fails to load with status code 404")

class ListCoursesTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.route = "/courses/"

        self.accessible_course = Course.objects.create(name="CS 361")
        self.inaccessible_course = Course.objects.create(name="CS -666")
        self.user = Account.objects.create(role=Account.Role.TA)
        CourseMembership.objects.create(account=self.user, course=self.accessible_course)
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
    
    def test_login(self):
        r = self.client.get(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "Courses list fails to redirect to login page when logged out")
        permissions.login(self.client, self.user)
        self.assertEqual(200, r.status_code, "Courses list fails to load with status code 200 when logged in")
    
    def test_userAccess(self):
        permissions.login(self.client, self.user)
        r = self.client.get(self.route)
        self.assertEqual(1, len(r.context["courses"]), "Courses list fails to include correct courses for user")
        self.assertFalse(r.context["supervisor"], "Courses list shows management tools for user")
    
    def test_supervisorAccess(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.get(self.route)
        self.assertEqual(2, len(r.context["courses"]), "Courses list fails to include correct courses for supervisor")
        self.assertTrue(r.context["supervisor"], "Courses list fails to show management tools for supervisor")

class CreateCourseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.route = "/courses/create/"
        
        self.user = Account.objects.create(role=Account.Role.TA)
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
        self.existing_course = Course.objects.create(name="CS 361")
    
    def test_needLogin(self):
        r = self.client.get(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "GETing course creation page fails to redirect to login page when logged out")
        r = self.client.post(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "POSTing course creation page fails to redirect to login page when logged out")
        
        permissions.login(self.client, self.user)
        r = self.client.get(self.route)
        self.assertEqual(403, r.status_code, "GETing course creation page as user fails to load with status code 403")
        r = self.client.post(self.route)
        self.assertEqual(403, r.status_code, "POSTing course creation page as user fails to load with status code 403")
        
        permissions.login(self.client, self.supervisor)
        r = self.client.get(self.route)
        self.assertEqual(200, r.status_code, "GETing course creation as supervisor fails to load with status code 200")
        r = self.client.post(self.route)
        self.assertEqual(400, r.status_code, "POSTing course creation as supervisor fails to load with status code 400")
    
    def test_errorVisibility(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route, {"name": ""})
        self.assertEqual(400, r.status_code, "Creating course with invalid name fails to load with status code 400")
        self.assertEqual(1, len(r.context["errors"]), "Creating course with invalid name fails to display errors")
    
    def test_courseCreation(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route, {"name": "CS 395"}, follow=True)
        self.assertEqual([("/courses/?course_created=true", 302)], r.redirect_chain, "Creating course with valid name fails to redirect to courses page")
        self.assertEqual(2, len(r.context["courses"]), "Creating course with valid name fails to create course")

class ViewCourseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.route = "/courses"

        self.accessible_course = Course.objects.create(name="CS 361")
        self.accessible_route = f"{self.route}/{self.accessible_course.pk}/"
        self.section = Section.objects.create(course=self.accessible_course, num="001")
        self.inaccessible_course = Course.objects.create(name="CS -999")
        self.inaccessible_route = f"{self.route}/{self.inaccessible_course.pk}/"
        self.user = Account.objects.create(role=Account.Role.TA)
        CourseMembership.objects.create(account=self.user, course=self.accessible_course)
        self.instructor = Account.objects.create(role=Account.Role.INSTRUCTOR)
        CourseMembership.objects.create(account=self.instructor, course=self.accessible_course)
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
    
    def test_nonexistentCourse(self):
        permissions.login(self.client, self.user)
        r = self.client.get(f"{self.route}/999/")
        self.assertEqual(404, r.status_code, "Nonexistent course fails to load with status code 404")
    
    def test_needLogin(self):
        r = self.client.get(self.accessible_route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "GETing course page while logged out fails to redirect to login page")
        r = self.client.post(self.accessible_route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "POSTing course page while logged out fails to redirect to login page")

        permissions.login(self.client, self.user)
        r = self.client.get(self.accessible_route)
        self.assertEqual(200, r.status_code, "GETing accessible course page fails to load with status code 200 as user")
        self.assertFalse(r.context["supervisor"], "Course page shows management tools for user")
        r = self.client.post(self.accessible_route)
        self.assertEqual(403, r.status_code, "POSTing accessible course page fails to load with status code 403 as user")
        r = self.client.get(self.inaccessible_route)
        self.assertEqual(403, r.status_code, "GETing inaccessible course page fails to load with status code 403 as user")
        r = self.client.post(self.inaccessible_route)
        self.assertEqual(403, r.status_code, "POSTing inaccessible course page fails to load with status code 403 as user")

        permissions.login(self.client, self.supervisor)
        r = self.client.get(self.accessible_route)
        self.assertEqual(200, r.status_code, "GETing accessible course page fails to load with status code 200 as supervisor")
        self.assertTrue(r.context["supervisor"], "Course page shows management tools for supervisor")
        r = self.client.post(self.accessible_route)
        self.assertEqual(400, r.status_code, "POSTing accessible course page fails to load with status code 400 as supervisor")
        r = self.client.get(self.inaccessible_route)
        self.assertEqual(200, r.status_code, "GETing inaccessible course page fails to load with status code 200 as supervisor")
        r = self.client.post(self.inaccessible_route)
        self.assertEqual(400, r.status_code, "POSTing inaccessible course page fails to load with status code 400 as supervisor")
    
    def test_loadsCourseData(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.get(self.accessible_route)
        self.assertEqual(self.accessible_course, r.context["course"], "Course page fails to load course info")
        self.assertEqual(1, r.context["sections"].count(), "Course page fails to load course sections")
        self.assertEqual(self.instructor, r.context["instructor"], "Course page fails to load instructor")
        self.assertEqual(1, r.context["tas"].count(), "Course page fails to load TAs")

    def test_errorVisibility(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.accessible_route)
        self.assertEqual(1, len(r.context["errors"]), "Errors are not visible on course page")
    
    def test_createSection(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.accessible_route, {"num": "002"})
        self.assertEqual(200, r.status_code, "Course page fails to load with status code 200 after creating valid section")
        self.assertEqual(2, r.context["sections"].count(), "Course page fails to create valid course section")

class DeleteCourseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(name="CS 361")
        self.route_base = "/courses/{}/delete/"
        self.route = self.route_base.format(self.course.pk)

        self.user = Account.objects.create(role=Account.Role.TA)
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
    
    def test_needsSupervisor(self):
        r = self.client.post(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "Deleting course while logged out fails to redirect to login page")
        
        permissions.login(self.client, self.user)
        r = self.client.post(self.route)
        self.assertEqual(403, r.status_code, "Deleting course as user fails to load with status code 403")
    
    def test_courseExists(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route_base.format(999))
        self.assertEqual(404, r.status_code, "Deleting nonexistent course fails to load with status code 404")
    
    def test_deletesCourse(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route, follow=True)
        self.assertEqual([("/courses/", 302)], r.redirect_chain, "Deleting course as supervisor fails to redirect to courses list")
        self.assertNotIn(self.course.pk, [course["pk"] for course in r.context["courses"]], "Deleting course as supervisor fails to delete course")

class EditCourseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.route_base = "/courses/{}/edit/"
        self.course = Course.objects.create(name="CS 361")
        self.route = self.route_base.format(self.course.pk)

        self.user = Account.objects.create(role=Account.Role.TA)
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
    
    def test_needsSupervisor(self):
        r = self.client.get(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "GETing course edit page while logged out fails to redirect to login page")
        r = self.client.post(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "POSTing course edit page while logged out fails to redirect to login page")

        permissions.login(self.client, self.user)
        r = self.client.get(self.route)
        self.assertEqual(403, r.status_code, "GETing course edit page as user fails to load with status code 403")
        r = self.client.post(self.route)
        self.assertEqual(403, r.status_code, "POSTing course edit page as user fails to load with status code 403")

        permissions.login(self.client, self.supervisor)
        r = self.client.get(self.route)
        self.assertEqual(200, r.status_code, "GETing course edit page as supervisor fails to load with status code 200")
        r = self.client.post(self.route)
        self.assertEqual(400, r.status_code, "POSTing course edit page as supervisor fails to load with status code 400")
    
    def test_courseExists(self):
        permissions.login(self.client, self.supervisor)
        route = self.route_base.format(666)
        r = self.client.get(route)
        self.assertEqual(404, r.status_code, "GETing nonexistent course edit page fails to load with status code 404")
        r = self.client.post(route)
        self.assertEqual(404, r.status_code, "POSTing nonexistent course edit page fails to load with status code 404")
    
    def test_fieldAccessibility(self):
        assert_field_accessibility(self, self.supervisor, self.route, self.course, "course edit page", [], [])
    
    def test_fieldsFilledIn(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.get(self.route)
        self.assertEqual(self.course, r.context["course"], "Course edit page fails to include course in context")
    
    def test_errorVisibility(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route)
        self.assertEqual(1, len(r.context["errors"]), "Course edit page fails to display errors")
    
    def test_editsCourse(self):
        permissions.login(self.client, self.supervisor)
        name = "CS 666"
        r = self.client.post(self.route, {"name": name}, follow=True)
        self.assertEqual([(f"/courses/{self.course.pk}/", 302)], r.redirect_chain, "Performing valid course name edit fails to redirect to courses list")
        del self.course.name
        self.assertEqual(name, self.course.name, "Performing valid course name edit fails to change course name")

class DeleteSectionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(name="CS 361")
        self.section = Section.objects.create(course=self.course)
        self.route_base = "/courses/{}/sections/{}/delete/"
        self.route = self.route_base.format(self.course.pk, self.section.pk)

        self.user = Account.objects.create(role=Account.Role.TA)
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
    
    def test_needsSupervisor(self):
        r = self.client.post(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "Deleting section while logged out fails to redirect to login")
        
        permissions.login(self.client, self.user)
        r = self.client.post(self.route)
        self.assertEqual(403, r.status_code, "Deleting section while user fails to load with status code 403")
    
    def test_sectionExists(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route_base.format(self.course.pk, 999))
        self.assertEqual(404, r.status_code, "Deleting nonexistent section fails to load with status code 404")
    
    # These tests are separate because running them in the same function deletes the section before the secondd one
    def test_deletesSectionWithCorrectCourse(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route, follow=True)
        self.assertEqual([(f"/courses/{self.course.pk}/", 302)], r.redirect_chain, "Deleting valid section with correct course as supervisor fails to redirect to course page")
        self.assertNotIn(self.course, r.context["sections"], "Deleting valid section with incorrect course as supervisor fails to delete section")
    
    def test_deletesSectionWithIncorrectCourse(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route_base.format(999, self.section.pk), follow=True)
        self.assertEqual([(f"/courses/{self.course.pk}/", 302)], r.redirect_chain, "Deleting valid section with correct course as supervisor fails to redirect to course page")
        self.assertNotIn(self.course, r.context["sections"], "Deleting valid section with incorrect course as supervisor fails to delete section")