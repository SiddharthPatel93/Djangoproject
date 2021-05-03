from typing import Union

from bs4 import BeautifulSoup
from django.forms.models import model_to_dict
from django.test import Client, TestCase

from .classes import courses, permissions, sections, users
from .models import Account, Course, CourseMembership, Section

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

        permissions.login(self.client, self.account)
        r = self.client.get(self.route, follow=True)
        self.assertEqual([("/courses/", 302)], r.redirect_chain, "Login page does not redirect to dashboard when logged in")
    
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
        self.assertEqual("/courses/", r.headers["Location"], "Successful login does not redirect to course dashboard")
        self.assertIn("account", self.client.session, "Successful login does not add account to session")
        self.assertEqual(self.account.pk, self.client.session["account"], "Successful login adds wrong account to session")

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

class ListUsersTest(TestCase):
    def test_listUsers(self):
        """
        Check if all users are being populated in the view.
        Setup function not included since this is the only case with users I can think of.

        You can add users here: http://127.0.0.1:8000/admin/scheduler_app/account/add/

        Check:
        - Permissions (see lines 99-102 for how to set account manually. check if it fails with nonexistent account #)
        """

class DeleteUserTest(TestCase):
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
    
    def get_user(self, user_details: dict) -> Union[Account, None]:
        try:
            return Account.objects.get(email=user_details["email"])
        except (Account.DoesNotExist, Account.MultipleObjectsReturned):
            return None
    
    def test_unitMissingFields(self):
        errors = users.create({})
        self.assertEqual(4, len(errors), "User create function does not return errors for missing fields")
    
    def test_unitValidateEmail(self):
        user_details = {
            "name": "user",
            "role": Account.Role.TA,
            "email": "bad",
            "password": "password",
        }
        errors = users.create(user_details)
        self.assertEqual(1, len(errors), "User create function does not validate format of email")
        self.assertIsNone(self.get_user(user_details), "User create function creates user with bad email")
        user_details["email"] = "a@a.com"
        errors = users.create(user_details)
        self.assertEqual(1, len(errors), "User create function does not validate availability of email")
        self.assertIsNotNone(self.get_user(user_details), "User create function creates user with taken email")
    
    def test_unitCreateUser(self):
        user_details = {
            "name": "name",
            "role": Account.Role.TA,
            "email": "c@c.com",
            "password": "password",
        }
        errors = users.create(user_details)
        self.assertEqual(0, len(errors), "User create function produces errors when ignoring optional fields")
        account = self.get_user(user_details)
        self.assertIsNotNone(account, "User create function does not create user")
        
        user_details = {
            **user_details,
            "email": "d@d.com",
            "phone": "phone",
            "address": "address",
            "office_hours": "office_hours",
        }
        errors = users.create(user_details)
        account = self.get_user(user_details)
        data = model_to_dict(account)
        for field, value in user_details.items():
            self.assertEqual(value, data[field], f"User create function does not assign field {field}")
    
    def test_pagePermissions(self):
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
        })
        self.assertEqual(302, r.status_code, "Successful user creation does not load with status code 302")
        self.assertEqual("/users/?user_created=true", r.headers["Location"], "Successful user creation does not redirect to users page with flag set")

class ListCoursesTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.route = "/courses/"

        self.accessible_course = Course.objects.create(name="CS 361")
        self.inaccessible_course = Course.objects.create(name="CS -666")
        self.user = Account.objects.create(role=Account.Role.TA)
        CourseMembership.objects.create(account=self.user, course=self.accessible_course)
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
    
    def test_unitUserAccess(self):
        user_courses = courses.get(self.user)
        self.assertEqual([self.accessible_course], user_courses, "Get courses function does not return correct courses for user")
    
    def test_unitSupervisorAccess(self):
        supervisor_courses = courses.get(self.supervisor)
        self.assertIn(self.accessible_course, supervisor_courses, "Get courses function does not include accessible course for supervisor")
        self.assertIn(self.inaccessible_course, supervisor_courses, "Get courses function does nnot include inaccessible course for supervisor")
    
    def test_login(self):
        r = self.client.get(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "Courses list does not redirect to login page when logged out")
        permissions.login(self.client, self.user)
        self.assertEqual(200, r.status_code, "Courses list does not load with status code 200 when logged in")
    
    def test_userAccess(self):
        permissions.login(self.client, self.user)
        r = self.client.get(self.route)
        self.assertEqual(1, len(r.context["courses"]), "Courses list does not include correct courses for user")
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
    
    def get_courses(self, name: str) -> int:
        return Course.objects.filter(name=name).count()
    
    def test_unitValidateName(self):
        bad_name = ""
        errors = courses.create(bad_name)
        self.assertEqual(1, len(errors), "Course creation function fails to check for empty name")
        self.assertEqual(0, self.get_courses(bad_name), "Course creation function creates course with blank name")

        bad_name = "CS 361"
        errors = courses.create(bad_name)
        self.assertEqual(1, len(errors), "Course creation function fails to check for duplicate name")
        self.assertEqual(1, self.get_courses(bad_name), "Course creation function creates course with duplicate name")
    
    def test_unitCreatesCourse(self):
        name = "New Course"
        errors = courses.create(name)
        self.assertEqual(0, len(errors), "Course creation function outputs error with valid arguments")
        self.assertLess(0, Course.objects.filter(name=name).count(), "Course creation function fails to create course")
    
    def test_needLogin(self):
        r = self.client.get(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "GETing course creation page does not redirect to login page when logged out")
        r = self.client.post(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "POSTing course creation page does not redirect to login page when logged out")
        
        permissions.login(self.client, self.user)
        r = self.client.get(self.route)
        self.assertEqual(403, r.status_code, "GETing ccourse creation page is not forbidden to unprivileged user")
        r = self.client.post(self.route)
        self.assertEqual(403, r.status_code, "POSTing course creation page is not forbidden to unprivileged user")
        
        permissions.login(self.client, self.supervisor)
        r = self.client.get(self.route)
        self.assertEqual(200, r.status_code, "GETing course creation is not accessible to supervisor")
        r = self.client.post(self.route)
        self.assertEqual(401, r.status_code, "POSTing course creation is not accessible to supervisor")
    
    def test_errorVisibility(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route, {"name": ""})
        self.assertEqual(401, r.status_code, "Creating course with invalid name fails to load with status code 401")
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
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
    
    def get_sections(self, num: str) -> int:
        return Section.objects.filter(num=num).count()
    
    def test_unitEmptyNum(self):
        num = ""
        errors = sections.create(self.accessible_course, num)
        self.assertEqual(1, len(errors), "Section creation function fails to produce an error when asked to create a section with a blank number")
        self.assertEqual(0, self.get_sections(num), "Section creation function creates a section with a blank number")
    
    def test_unitDuplicateNum(self):
        errors = sections.create(self.accessible_course, self.section.num)
        self.assertEqual(1, len(errors), "Section creation function fails to produce an error when asked to create a section with a duplicate number")
        self.assertEqual(1, self.get_sections(self.section.num), "Section creation function creates a section with a duplicate number")
    
    def test_unitCreatesSection(self):
        num = "002"
        errors = sections.create(self.accessible_course, num)
        self.assertEqual(0, len(errors), "Section creation function fails to create valid section without errors")
        self.assertEqual(1, self.get_sections(num), "Section creation function fails to create valid section")
    
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
        self.assertEqual(401, r.status_code, "POSTing accessible course page fails to load with status code 401 as supervisor")
        r = self.client.get(self.inaccessible_route)
        self.assertEqual(200, r.status_code, "GETing inaccessible course page fails to load with status code 200 as supervisor")
        r = self.client.post(self.inaccessible_route)
        self.assertEqual(401, r.status_code, "POSTing inaccessible course page fails to load with status code 401 as supervisor")
    
    def test_loadsCourseData(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.get(self.accessible_route)
        self.assertEqual(self.accessible_course, r.context["course"], "Course page fails to load course info")
        self.assertEqual(1, r.context["sections"].count(), "Course page fails to load course sections")

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
    
    def test_unitDeletesCourse(self):
        courses.delete(self.course)
        self.assertEqual(0, Course.objects.filter(name=self.course.name).count(), "Course deletion function fails to delete course")
    
    def test_needsSupervisor(self):
        r = self.client.post(self.route, follow=True)
        self.assertEqual([("/login/", 302)], r.redirect_chain, "Deleting course while logged out fails to redirect to login")
        
        permissions.login(self.client, self.user)
        r = self.client.post(self.route)
        self.assertEqual(403, r.status_code, "Deleting course while user fails to load with status code 403")
    
    def test_courseExists(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route_base.format(999))
        self.assertEqual(404, r.status_code, "Deleting nonexistent course fails to load with status code 404")
    
    def test_deletesCourse(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route, follow=True)
        self.assertEqual([("/courses/", 302)], r.redirect_chain, "Deleting course while supervisor fails to redirect to courses list")
        self.assertNotIn(self.course.pk, [course["pk"] for course in r.context["courses"]], "Deleting course while supervisor fails to delete course")

class DeleteSectionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(name="CS 361")
        self.section = Section.objects.create(course=self.course)
        self.route_base = "/courses/{}/sections/{}/delete/"
        self.route = self.route_base.format(self.course.pk, self.section.pk)

        self.user = Account.objects.create(role=Account.Role.TA)
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
    
    def test_unitDeletesSection(self):
        sections.delete(self.section)
        self.assertEqual(0, Section.objects.filter(pk=self.section.pk).count(), "Section deletion function fails to delete section")
    
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
    
    def test_deletesSectionWithCorrectCourse(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route, follow=True)
        self.assertEqual([(f"/courses/{self.course.pk}/", 302)], r.redirect_chain, f"Deleting valid section with correct course while supervisor fails to redirect to course page")
        self.assertNotIn(self.course.pk, [section.pk for section in r.context["sections"]], f"Deleting valid section with correct course while supervisor fails to delete section")
    
    def test_deletesSectionWithIncorrectCourse(self):
        permissions.login(self.client, self.supervisor)
        r = self.client.post(self.route, follow=True)
        self.assertEqual([(f"/courses/{self.course.pk}/", 302)], r.redirect_chain, f"Deleting valid section with incorrect course while supervisor fails to redirect to course page")
        self.assertNotIn(self.course.pk, [section.pk for section in r.context["sections"]], f"Deleting valid section with incorrect course while supervisor fails to delete section")