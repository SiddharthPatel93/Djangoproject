from unittest.mock import patch

from django.test import TestCase
from passlib.hash import argon2

from .models import Account, Course, Section

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