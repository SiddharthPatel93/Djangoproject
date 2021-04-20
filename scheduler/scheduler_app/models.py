from django.db import models
from passlib.hash import argon2

MAX_LENGTH = 1023

class Account(models.Model):
    class Role(models.IntegerChoices):
        SUPERVISOR = 0, "Supervisor"
        INSTRUCTOR = 1, "Instructor"
        TA = 2, "TA"

    name = models.CharField(max_length=MAX_LENGTH)
    role = models.IntegerField(choices=Role.choices)
    email = models.EmailField()
    # Argon2id password hash. Security is important even for school projects
    # More info: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
    password = models.CharField(max_length=MAX_LENGTH)
    phone = models.CharField(max_length=MAX_LENGTH)
    address = models.CharField(max_length=MAX_LENGTH)
    office_hours = models.CharField(max_length=MAX_LENGTH)


    def __str__(self):
        return self.name
    
    def check_password(self, password: str) -> bool:
        return argon2.verify(password, self.password)

    def set_password(self, password: str):
        self.password = argon2.using().hash(password)

    def set_email(self):
        email = self.email

    def get_email(self):
        return self.email

    def set_role(self):
        role = self.role

    def get_role(self):
        return self.role

    def set_phone(self):
        phone = self.phone

    def get_phone(self):
        return self.phone

    def set_address(self):
        address = self.address

    def get_address(self):
        return self.address

    def set_office_hours(self):
        office_hours = self.office_hours

    def get_office_hours(self):
        return self.office_hours

class Course(models.Model):
    name = models.CharField(max_length=MAX_LENGTH)
    members = models.ManyToManyField(Account, through="CourseMembership")

    def __str__(self):
        return self.name

class CourseMembership(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    grader = models.BooleanField(default=False)

class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    num = models.IntegerField()
    # String through parameter is necessary due to mutual dependency of classes
    members = models.ManyToManyField(Account, related_name="sections")

    def __str__(self):
        return str(self.num)