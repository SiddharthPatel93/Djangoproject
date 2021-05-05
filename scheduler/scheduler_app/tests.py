from typing import Union

from bs4 import BeautifulSoup
from django.forms.models import model_to_dict
from django.test import Client, TestCase

from .classes import courses, permissions, sections, users
from .models import Account, Course, CourseMembership, Section

# Views

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