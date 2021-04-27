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
    password = models.CharField(max_length=MAX_LENGTH)
    phone = models.CharField(max_length=MAX_LENGTH)
    address = models.CharField(max_length=MAX_LENGTH)
    office_hours = models.CharField(max_length=MAX_LENGTH)

    def __str__(self):
        return self.name

class Course(models.Model):
    name = models.CharField(max_length=MAX_LENGTH)
    # String through parameter is necessary due to mutual dependency of classes
    members = models.ManyToManyField(Account, through="CourseMembership", related_name="courses")

    def __str__(self):
        return self.name

class CourseMembership(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    grader = models.BooleanField(default=False)

class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    num = models.CharField(max_length=MAX_LENGTH)
    members = models.ManyToManyField(Account, related_name="sections")

    def __str__(self):
        return str(self.num)