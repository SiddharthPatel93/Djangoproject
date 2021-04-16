from django.db import models

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

class Course(models.Model):
    name = models.CharField(max_length=MAX_LENGTH)
    members = models.ManyToManyField(to=Account, related_name="courses")

    def __str__(self):
        return self.name

class Section(models.Model):
    course = models.ForeignKey(to=Course, on_delete=models.CASCADE)
    num = models.IntegerField()
    # String through parameter is necessary due to mutual dependency of classes
    members = models.ManyToManyField(to=Account, through="SectionMembership")

    def __str__(self):
        return str(self.num)

class SectionMembership(models.Model):
    account = models.ForeignKey(to=Account, on_delete=models.CASCADE)
    section = models.ForeignKey(to=Section, on_delete=models.CASCADE)
    grader = models.BooleanField(default=False)