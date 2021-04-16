from django.test import TestCase

from .models import Account, Course, Section

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
        num = 902
        s = Section(num=num)
        self.assertEqual(str(num), s.__str__(), "Section name does not equal entered number")