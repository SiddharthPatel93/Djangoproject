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
    password = models.CharField(max_length=MAX_LENGTH)
    skills = models.CharField(max_length=MAX_LENGTH, blank=True, default="")
    phone = models.CharField(max_length=MAX_LENGTH, blank=True, default="")
    address = models.CharField(max_length=MAX_LENGTH, blank=True, default="")
    office_hours = models.CharField(max_length=MAX_LENGTH, blank=True, default="")

    def __str__(self):
        return self.name

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
    description = models.CharField(max_length=MAX_LENGTH, default="")
    # String through parameter is necessary due to mutual dependency of classes
    members = models.ManyToManyField(Account, through="CourseMembership", related_name="courses")

    def __str__(self):
        return self.name

class CourseMembership(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    grader = models.BooleanField(default=False)
    sections = models.IntegerField(default=1)

class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    num = models.CharField(max_length=MAX_LENGTH)
    ta = models.ForeignKey(Account, on_delete=models.SET_NULL, related_name="sections", null=True)

    def __str__(self):
        return str(self.num)