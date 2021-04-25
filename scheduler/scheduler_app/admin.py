from django.contrib import admin

from .models import Account, Course, CourseMembership, Section

admin.site.register(Account)
admin.site.register(Course)
admin.site.register(CourseMembership)
admin.site.register(Section)