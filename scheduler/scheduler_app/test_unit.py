from typing import Any, Union

from django.forms.models import model_to_dict
from django.http.response import HttpResponseForbidden
from django.test import Client, TestCase

from .classes import courses, permissions, sections, users
from .models import Account, Course, CourseMembership, Section

# Model methods

class AccountTest(TestCase):
    def test_matchName(self):
        name = "Jimothy"
        a = Account(name=name)
        self.assertEqual(name, a.__str__(), "Account name fails to equal entered name")

class CourseTest(TestCase):
    def test_matchName(self):
        name = "CS 361"
        c = Course(name=name)
        self.assertEqual(name, c.__str__(), "Course name fails to equal entered name")

class SectionTest(TestCase):
    def test_matchName(self):
        s = Section(num=902)
        self.assertEqual("902", s.__str__(), "Section name fails to equal entered number")

# Classes

# Courses

class ListCoursesTest(TestCase):
    def setUp(self):
        self.accessible_course = Course.objects.create(name="CS 361")
        self.inaccessible_course = Course.objects.create(name="CS -666")
        self.user = Account.objects.create(role=Account.Role.TA)
        CourseMembership.objects.create(account=self.user, course=self.accessible_course)
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
    
    def test_userAccess(self):
        user_courses = courses.get(self.user)
        self.assertEqual([self.accessible_course], user_courses, "Get courses function fails to return correct courses for user")
    
    def test_supervisorAccess(self):
        supervisor_courses = courses.get(self.supervisor)
        self.assertIn(self.accessible_course, supervisor_courses, "Get courses function fails to include accessible course for supervisor")
        self.assertIn(self.inaccessible_course, supervisor_courses, "Get courses function does not include inaccessible course for supervisor")

class CreateCourseTest(TestCase):
    def setUp(self):
        self.user = Account.objects.create(role=Account.Role.TA)
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
        self.course = Course.objects.create(name="CS 361")
    
    def test_blankName(self):
        blank_name = ""
        errors = courses.create(blank_name)
        self.assertEqual(1, len(errors), "Course creation function fails to check for empty name")
        self.assertEqual(0, courses.count(blank_name), "Course creation function creates course with blank name")

    def test_duplicateName(self):
        errors = courses.create(self.course.name)
        self.assertEqual(1, len(errors), "Course creation function fails to check for duplicate name")
        self.assertEqual(1, courses.count(self.course.name), "Course creation function creates course with duplicate name")
    
    def test_createsCourse(self):
        name = "New Course"
        errors = courses.create(name)
        self.assertEqual(0, len(errors), "Course creation function outputs error with valid arguments")
        self.assertEqual(1, courses.count(name), "Course creation function fails to create course")

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
    
    def test_blankNum(self):
        blank_num = ""
        errors = sections.create(self.accessible_course, blank_num)
        self.assertEqual(1, len(errors), "Section creation function fails to produce an error when asked to create a section with a blank number")
        self.assertEqual(0, sections.count(blank_num), "Section creation function creates a section with a blank number")
    
    def test_duplicateNum(self):
        errors = sections.create(self.accessible_course, self.section.num)
        self.assertEqual(1, len(errors), "Section creation function fails to produce an error when asked to create a section with a duplicate number")
        self.assertEqual(1, sections.count(self.section.num), "Section creation function creates a section with a duplicate number")
    
    def test_createsSection(self):
        num = "002"
        errors = sections.create(self.accessible_course, num)
        self.assertEqual(0, len(errors), "Section creation function fails to create valid section without errors")
        self.assertEqual(1, sections.count(num), "Section creation function fails to create valid section")

class DeleteCourseTest(TestCase):
    def setUp(self):
        self.course = Course.objects.create(name="CS 361")
    
    def test_deletesCourse(self):
        courses.delete(self.course)
        self.assertEqual(0, courses.count(self.course.name), "Course deletion function fails to delete course")

class EditCourseTest(TestCase):
    def setUp(self):
        self.name = "CS 395"
        self.course = Course.objects.create(name=self.name)
        self.other_course = Course.objects.create(name="Yeah")
    
    def test_emptyName(self):
        errors = courses.edit(self.course, {})
        self.assertEqual(1, len(errors), "Course edit function allows blank name for course")
        self.assertEqual(self.name, self.course.name, "Course edit function changes course name to blank")
    
    def test_duplicateName(self):
        errors = courses.edit(self.course, {"name": self.other_course.name})
        self.assertEqual(1, len(errors), "Course edit function allows duplicate name for course")
        self.assertEqual(self.name, self.course.name, "Course edit function duplicates course name")
    
    def test_editsCourse(self):
        name = "CS 520"
        errors = courses.edit(self.course, {"name": name})
        self.assertEqual(0, len(errors), "Course edit function produces errors for valid name edit")
        self.assertEqual(name, self.course.name, "Course edit function fails to perform valid name edit")

# Permissions

class PermissionsCheckerTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Account.objects.create(role=Account.Role.TA)
        self.supervisor = Account.objects.create(role=Account.Role.SUPERVISOR)
    
    @permissions.check_permissions(check_supervisor=False)
    def user_view(self, *args):
        pass

    @permissions.check_permissions()
    def supervisor_view(self, *args):
        pass
    
    def test_loggedOut(self):
        r = self.user_view(self.client)
        self.assertEqual("/login/", r.url, "Requesting check_permissions view while logged out fails to redirect to login page")
    
    def test_userAccessible(self):
        permissions.login(self.client, self.user)
        r = self.user_view(self.client)
        self.assertIsNone(r, "Requesting check_permissions view with check_supervisor=False as user fails to load successfully")
    
    def test_supervisorAccessible(self):
        permissions.login(self.client, self.user)
        r = self.supervisor_view(self.client)
        self.assertIsInstance(r, HttpResponseForbidden, "Requesting check_permissions view as user fails to load unsuccessfully")
        
        permissions.login(self.client, self.supervisor)
        r = self.supervisor_view(self.client)
        self.assertIsNone(r, "Requesting check_permissions view as supervisor fails to load successfully")
    
    def test_deletedAccount(self):
        permissions.login(self.client, self.user)
        self.user.delete()
        r = self.user_view(self.client)
        self.assertEqual("/login/", r.url, "Requesting check_permissions view when logged into deleted account fails to redirect to login page")

class LoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.existent_user = Account.objects.create(role=Account.Role.SUPERVISOR)
        self.nonexistent_user = Account(role=Account.Role.SUPERVISOR)
    
    def test_logsIn(self):
        permissions.login(self.client, self.existent_user)
        self.assertEqual(self.existent_user.pk, self.client.session["account"], "Session login function fails to login user")
    
    def test_nonexistentUser(self):
        with self.assertRaises(ValueError):
            permissions.login(self.client, self.nonexistent_user)
        self.assertNotIn("account", self.client.session, "Session login function logs in nonexistent user")

class DetailsLoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.account = Account.objects.create(
            role=Account.Role.SUPERVISOR,
            email="email@email.email",
            password="password",
        )
    
    def test_blankDetails(self):
        errors, invalid_login = permissions.login_with_details(self.client, {})
        self.assertEqual(2, len(errors), "Details login function fails to produce errors when given blank details")
        self.assertFalse(invalid_login, "Details login function says blank details are invalid login")
    
    def get_bad_password_errors(self):
        return permissions.login_with_details(self.client, {"email": self.account.email, "password": "wrong"})
    
    def test_emailValidation(self):
        invalid_email, invalid_login = permissions.login_with_details(self.client, {"email": "bad", "password": self.account.password})
        self.assertEqual(1, len(invalid_email), "Details login function fails to produce error when given invalid email")
        self.assertFalse(invalid_login, "Details login functions says invalid email is invalid login")
        bad_password = self.get_bad_password_errors()
        self.assertNotEqual(bad_password, invalid_email, "Details login function produces same error as bad password when given invalid email")
    
    def test_wrongDetails(self):
        nonexistent_account, invalid_login = permissions.login_with_details(self.client, {"email": "wrong@wrong.wrong", "password": self.account.password})
        self.assertEqual(1, len(nonexistent_account), "Details login function fails to produce error when given wrong details")
        self.assertTrue(invalid_login, "Details login function says nonexistent account is not invalid login")
        bad_password, invalid_login = self.get_bad_password_errors()
        self.assertNotIn("account", self.client.session, "Details login function logs in user with wrong password")
        self.assertEqual(nonexistent_account, bad_password, "Details login function fails to produce same error for wrong email and wrong password")
        self.assertTrue(invalid_login, "Details login function says bad password is not invalid login")
    
    def test_rightDetails(self):
        errors, invalid_login = permissions.login_with_details(self.client, model_to_dict(self.account))
        self.assertEqual(self.account.pk, self.client.session["account"], "Details login fails to log in user with right details")
        self.assertEqual(0, len(errors), "Details login function produces error when given right details")
        self.assertFalse(invalid_login, "Details login function says right details are invalid login")

# Users

class CreateUserTest(TestCase):
    def setUp(self):
        self.user_details = {
            "name": "user",
            "role": Account.Role.TA,
            "email": "a@a.com",
            "password": "password",
        }
    
    def get_user(self, user_details: dict[str, Any]) -> Union[Account, None]:
        try:
            return Account.objects.get(email=user_details["email"])
        except (Account.DoesNotExist, Account.MultipleObjectsReturned):
            return None
    
    def test_missingFields(self):
        errors = users.create({})
        self.assertEqual(4, len(errors), "User creation function fails to return errors for missing fields")
    
    def test_malformedRole(self):
        self.user_details["role"] = "nope"
        errors = users.create(self.user_details)
        self.assertEqual(1, len(errors), "User creation function fails to validate format of role")
    
    def test_invalidRole(self):
        self.user_details["role"] = "999"
        errors = users.create(self.user_details)
        self.assertEqual(1, len(errors), "User creation function fails to validate contents of role")
    
    def test_validateEmail(self):
        self.user_details["email"] = "bad"
        errors = users.create(self.user_details)
        self.assertEqual(1, len(errors), "User creation function fails to validate format of email")
        self.assertIsNone(self.get_user(self.user_details), "User creation function creates user with bad email")
    
    def test_duplicateEmail(self):
        users.create(self.user_details)
        errors = users.create(self.user_details)
        self.assertEqual(1, len(errors), "User creation function fails to validate availability of email")
        self.assertIsNotNone(self.get_user(self.user_details), "User creation function creates user with taken email")
    
    def test_createUser(self):
        user_details = {
            "name": "name",
            "role": Account.Role.TA,
            "email": "c@c.com",
            "password": "password",
        }
        errors = users.create(user_details)
        self.assertEqual(0, len(errors), "User creation function produces errors when ignoring optional fields")
        account = self.get_user(user_details)
        self.assertIsNotNone(account, "User creation function fails to create user")
        
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
            self.assertEqual(value, data[field], f"User creation function fails to assign field {field}")

class EditUserTest(TestCase):
    def setUp(self):
        self.user = Account.objects.create(
            name="TA",
            role=Account.Role.TA,
            email="ta@ta.ta",
            password="ta",
            skills="ta",
            phone="ta",
            address="ta",
            office_hours="ta",
        )
        self.supervisor = Account.objects.create(
            name="Supervisor",
            role=Account.Role.SUPERVISOR,
            email="supervisor@supervisor.supervisor",
            password="supervisor",
            skills="supervisor",
            phone="supervisor",
            address="supervisor",
            office_hours="supervisor",
        )
    
    def test_editsUser(self):
        data = {
            "name": "name",
            "role": Account.Role.INSTRUCTOR,
            "email": "email@email.email",
            "password": "password",
            "skills": "skills",
            "phone": "phone",
            "address": "address",
            "office_hours": "office_hours",
        }
        good_edit = users.edit(self.supervisor, self.user, data)
        self.assertEqual(0, len(good_edit), "Making correct edit to user produces errors")
        
        user = model_to_dict(self.user)
        del user["id"]
        for field, value in data.items():
            self.assertEqual(value, user[field], f"User edit function fails to correctly change field {field}")
    
    def test_rejectsOwnRole(self):
        role_edit = users.edit(self.user, self.user, {"role": Account.Role.INSTRUCTOR.value})
        self.assertEqual(1, len(role_edit), "User edit function fails to block user from editing own role")
    
    def test_acceptsInPlaceEmail(self):
        email_edit = users.edit(self.user, self.user, {"email": self.user.email})
        self.assertEqual(0, len(email_edit), "User edit function fails to replace user email with existing one")
    
    def test_checksValidEmail(self):
        email_edit = users.edit(self.user, self.user, {"email": "invalid"})
        self.assertEqual(1, len(email_edit), "User edit function fails to block user from changing email to invalid one")
    
    def test_checksDuplicateEmail(self):
        email_edit = users.edit(self.user, self.user, {"email": self.supervisor.email})
        self.assertEqual(1, len(email_edit), "User edit function fails to block user from changing email to duplicate one")

class DeleteUserTest(TestCase):
    def setUp(self):
        self.user = Account.objects.create(name="TA", role=Account.Role.TA)
    def test_deleteUser(self):
        self.assertEqual(1, users.count(self.user.name))
        users.delete(self.user)
        self.assertEqual(0, users.count(self.user.name), "User deletion function fails to delete user")

# Sections

class DeleteSectionTest(TestCase):
    def setUp(self):
        self.course = Course.objects.create(name="CS 361")
        self.section = Section.objects.create(course=self.course, num="902")
    
    def test_deletesSection(self):
        sections.delete(self.section)
        self.assertEqual(0, sections.count(self.section.num), "Section deletion function fails to delete section")