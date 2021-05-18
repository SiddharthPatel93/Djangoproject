from django.forms.models import model_to_dict
from django.http.response import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views import View

from .classes import courses, permissions, sections, users
from .classes.permissions import check_permissions
from .models import Account, Course, Section

class HomepageView(View):
    @check_permissions(check_supervisor=False)
    def get(self, request, requester: Account):
        return render(request, "homepage.html", {
            "user": requester,
        })

class LoginView(View):
    def get(self, request):
        if "account" in request.session:
            return redirect("/")
        
        return render(request, "login.html", {"nav": True})
    
    def post(self, request):
        if "account" in request.session:
            return redirect("/")
        
        errors, invalid_login = permissions.login_with_details(request, request.POST)

        if not errors:
            request.session["account"] = Account.objects.get(
                email=request.POST["email"],
                password=request.POST["password"],
            ).pk
            return redirect("/")

        return render(request, "login.html", {
            "nav": True,
            "errors": errors,
        }, status=401 if invalid_login else 400)


class LogoutView(View):
    def post(self, request):
        if "account" in request.session:
            del request.session["account"]

        return redirect("/login/")


class ListUsersView(View):
    def get(self, request):
        """Render template of all users as a list."""

        if "account" not in request.session:
            return redirect("/login/")

        requester = Account.objects.get(pk=request.session["account"])

        return render(request, "users_list.html", {
            "users": [{"pk": user.pk, "name": user.name} \
                      for user in users.get(requester)],
            "supervisor": requester.role == Account.Role.SUPERVISOR,
            "members": [{"pk": member.pk, "name": member.name} \
                        for course in courses.get(requester) \
                        for member in course.members.all()],
        })


class DeleteUserView(View):
    def post(self, request, account: int):
        """
        Attempt to delete the specified user.
        Redirect to /users/ after, potentially with error.
        """
        @check_permissions()
        def post(self, *args, account=0):
            try:
                account = Account.objects.get(pk=account)
            except Account.DoesNotExist:
                raise Http404("User does not exist")

            users.delete(account)

            return redirect("/users/")


class ViewUserView(View):
    @check_permissions(check_supervisor=False)
    def get(self, request, requester: Account, account=0):
        try:
            account = Account.objects.get(pk=account)
        except Account.DoesNotExist:
            raise Http404("User does not exist")

        return render(request, "user.html", {
            "roles": Account.Role.choices,
            "own_profile": account.pk == request.session["account"],
            "supervisor": requester.role == Account.Role.SUPERVISOR,
            **model_to_dict(account),
        })

    @check_permissions(check_supervisor=False)
    def post(self, request, requester: Account, account=0):
        if requester.role != Account.Role.SUPERVISOR and account != requester.pk:
            return HttpResponseForbidden("You are not a supervisor.")

        try:
            account = Account.objects.get(pk=account)
        except Account.DoesNotExist:
            raise Http404("User does not exist")

        errors = users.edit(requester, account, request.POST)

        return render(request, "user.html", {
            "roles": Account.Role.choices,
            "errors": errors,
            "own_profile": account.pk == request.session["account"],
            "supervisor": requester.role == Account.Role.SUPERVISOR,
            **model_to_dict(account),
        }, status=400 if errors else 200)


class CreateUserView(View):
    @check_permissions()
    def get(self, request, *args):
        return render(request, "user_create.html", {"roles": Account.Role.choices})

    @check_permissions()
    def post(self, request, *args):
        if (errors := users.create(request.POST)):
            return render(request, "user_create.html", {
                "errors": errors,
                "roles": Account.Role.choices,
            }, status=400)
        else:
            return redirect("/users/?user_created=true")


class ListCoursesView(View):
    @check_permissions(check_supervisor=False)
    def get(self, request, requester: Account):
        return render(request, "courses_list.html", {
            "courses": [{"pk": course.pk, "name": course.name} \
                        for course in courses.get(requester)],
            "supervisor": requester.role == Account.Role.SUPERVISOR,
            "instructors": [{"pk": instructor.pk, "name": instructor.name}\
                        for instructor in Account.objects.filter(role=Account.Role.INSTRUCTOR)],
            "TAs": [{"pk": TA.pk, "name": TA.name}\
                        for TA in Account.objects.filter(role=Account.Role.TA)],
        })

class CreateCourseView(View):
    @check_permissions()
    def get(self, request, *args):
        return render(request, "course_create.html")

    @check_permissions()
    def post(self, request, *args):
        errors = courses.create(request.POST.get("name", ""))

        if errors:
            return render(request, "course_create.html", {"errors": errors}, status=400)
        else:
            return redirect("/courses/?course_created=true")


class ViewCourseView(View):
    @check_permissions(check_supervisor=False)
    def get(self, request, requester: Account, course=0):
        try:
            course = Course.objects.get(pk=course)
        except Course.DoesNotExist:
            raise Http404("Course does not exist")

        supervisor = requester.role == Account.Role.SUPERVISOR
        instructor = requester.role == Account.Role.INSTRUCTOR

        if not supervisor and course not in courses.get(requester):
            return HttpResponseForbidden("You do not have access to this course.")

        return render(request, "course.html", {
            "TAs": course.members.filter(courses__coursemembership__account=Account.Role.TA),
            "course": course,
            "sections": course.sections.all(),
            "supervisor": supervisor,
            "instructor": instructor,
        })

    @check_permissions()
    def post(self, request, *args, course=0):
        try:
            course = Course.objects.get(pk=course)
        except Course.DoesNotExist:
            return Http404("Course does not exist")

        errors = sections.create(course, request.POST.get("num", ""))

        return render(request, "course.html", {
            "course": course,
            "sections": course.sections.all(),
            "errors": errors,
            "supervisor": True,
        }, status=400 if errors else 200)

class EditCourseView(View):
    @check_permissions()
    def get(self, request, *args, course=0):
        try:
            course = Course.objects.get(pk=course)
        except Course.DoesNotExist:
            raise Http404("Course does not exist")

        return render(request, "course_edit.html", {"course": course})

    @check_permissions()
    def post(self, request, *args, course=0):
        try:
            course = Course.objects.get(pk=course)
        except Course.DoesNotExist:
            raise Http404("Course does not exist")

        errors = courses.edit(course, request.POST)

        if errors:
            return render(request, "course_edit.html", {
                "course": course,
                "errors": errors,
            }, status=400)
        else:
            return redirect(f"/courses/{course.pk}/")


class DeleteCourseView(View):
    @check_permissions()
    def post(self, *args, course=0):
        try:
            course = Course.objects.get(pk=course)
        except Course.DoesNotExist:
            raise Http404("Course does not exist")

        courses.delete(course)

        return redirect("/courses/")


class DeleteSectionView(View):
    @check_permissions()
    def post(self, *args, section=0, **kwargs):
        try:
            section = Section.objects.get(pk=section)
        except Section.DoesNotExist:
            raise Http404("Section does not exist")

        sections.delete(section)

        return redirect(f"/courses/{section.course.pk}/")


class SectionAssignmentView(View):
    def get(self, request):
        if "account" not in request.session:
            return redirect("/login/")

        requester = Account.objects.get(pk=request.session["account"])

        if requester.role is not Account.Role.SUPERVISOR:
            return HttpResponseForbidden("You do not have access to this feature")

        if courses not in courses.get(requester):
            return HttpResponseForbidden("No courses available")

        return render(request, "course.html", {
            "instructors": [{"pk": user.pk, "name": user.name} \
                            for user in users.get(requester)],
            "TAs": users.get(Account.Role.TA)
        })

    def post(self, request):
        if "account" not in request.session:
            return redirect("/login/")

        requester = Account.objects.get(pk=request.session["account"])

        if requester.role is not Account.Role.SUPERVISOR:
            return HttpResponseForbidden("You do not have access to this feature")

        if courses not in courses.get(requester):
            return HttpResponseForbidden("No courses available")

        errors = Section.assignTA(courses.Course, courses.num, request.POST.get("name", ""))

        if errors:
            return render(request, "section_assignment.html", {"errors": errors}, status=401)
        else:
            return render(request, "course.html", {
                "instructors": Account.objects.filter(Account.Role.INSTRUCTOR),
                "TAs": users.get(Account.Role.TA)
            })


class CourseAssignmentView(View):
    def get(self, request):
        if "account" not in request.session:
            return redirect("/login/")

        requester = Account.objects.get(pk=request.session["account"])

        if requester.role is not Account.Role.SUPERVISOR:
            return HttpResponseForbidden("You do not have access to this feature")

        if courses not in courses.get(requester):
            return HttpResponseForbidden("No courses available")

        return render(request, "user_course_assignment.html")

    def post(self, request):
        if "account" not in request.session:
            return redirect("/login/")

        requester = Account.objects.get(pk=request.session["account"])

        if requester.role is not Account.Role.SUPERVISOR:
            return HttpResponseForbidden("You do not have access to this feature")

        if courses not in courses.get(requester):
            return HttpResponseForbidden("No courses available")

        errors = courses.assign(courses.Course, courses.num, request.POST.get("name", ""))

        if errors:
            return render(request, "user_course_assignment.html", {"errors": errors}, status=401)
        else:
            return redirect("/course_assignment/")

class AssignToCourseview(View):
    @check_permissions()
    def get(self, request, requester: Account, course=0):
        try:
            course = Course.objects.get(pk=course)
        except Course.DoesNotExist:
            raise Http404("Course does not exist")

        return render(request, "user_course_assignment.html", {
            "course": course,
            "supervisor": requester.role == Account.Role.SUPERVISOR,
            "users": [{"pk": user.pk, "name": user.name, "role": user.get_role_display()} \
                            for user in Account.objects.exclude(role=Account.Role.SUPERVISOR)],
    })

    @check_permissions()
    def post(self, request, requester: Account, course=0):
        try:
            course = Course.objects.get(pk=course)
        except Course.DoesNotExist:
            raise Http404("Course does not exist")

        user_key = request.POST.get('user', "0")
        user = Account.objects.get(pk=user_key)
        errors = courses.assigninstructor(course, user)
        return render(request, "user_course_assignment.html", {
            "errors": errors,
            "course": course,
            "users": [{"pk": user.pk, "name": user.name, "role": user.get_role_display()} \
                      for user in Account.objects.exclude(role=Account.Role.SUPERVISOR)],

        })

class AssignToSectionView(View):
    @check_permissions()
    def get(self, request, requester: Account, course=0, section=0):
        try:
            section = Course.objects.get(pk=course)
        except Course.DoesNotExist:
            raise Http404("Course does not exist")

        return render(request, "user_course_assignment.html", {
            "course": course,
            "supervisor": requester.role == Account.Role.SUPERVISOR,
            "users": [{"pk": user.pk, "name": user.name, "role": user.get_role_display()} \
                            for user in Account.objects.exclude(role=Account.Role.SUPERVISOR)],
    })

    @check_permissions()
    def post(self, request, requester: Account, course=0):
        try:
            course = Course.objects.get(pk=course)
        except Course.DoesNotExist:
            raise Http404("Course does not exist")

        user_key = request.POST.get('user', "0")
        user = Account.objects.get(pk=user_key)
        errors = courses.assigninstructor(course, user)
        return render(request, "user_course_assignment.html", {
            "errors": errors,
            "course": course,
            "users": [{"pk": user.pk, "name": user.name, "role": user.get_role_display()} \
                      for user in Account.objects.exclude(role=Account.Role.SUPERVISOR)],

        })