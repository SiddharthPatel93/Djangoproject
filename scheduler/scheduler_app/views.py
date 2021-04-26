from django.forms.models import model_to_dict
from django.http.response import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views import View

from .classes import courses, users
from .models import Account

class LoginView(View):
    def get(self, request):
        if "account" in request.session:
            return redirect("/")
        
        return render(request, "login.html", {"nav": True})
    
    def post(self, request):
        errors = []
        
        if not (email := request.POST.get("email", "")):
            errors.append("Please enter an email!")
        if not (password := request.POST.get("password", "")):
            errors.append("Please enter a password!")

        if errors:
            return render(request, "login.html", {"errors": errors}, status=400)

        try:
            a = Account.objects.get(email=email, password=password)
            request.session["account"] = a.id
            return redirect("/")
        except Account.DoesNotExist:
            return render(request, "login.html", {"nav": True, "errors": ["Wrong email or password!"]}, status=401)

class LogoutView(View):
    def post(self, request):
        if "account" in request.session:
            del request.session["account"]
        
        return redirect("/login/")

class ViewUsersView(View):
    def get(self, request):
        """Render template of all users as a list."""

class DeleteUserView(View):
    def post(self, request, account: int):
        """
        Attempt to delete the specified user.
        Redirect to /users/ after, potentially with error.
        """

class EditUserView(View):
    def get(self, request, account=0):
        if "account" not in request.session:
            return redirect("/login/")
        
        requester = Account.objects.get(pk=request.session["account"])
        if requester.role != Account.Role.SUPERVISOR and account != requester.id:
            return HttpResponseForbidden("You are not a supervisor.")

        try:
            account = Account.objects.get(pk=account)
        except Account.DoesNotExist:
            raise Http404("User does not exist")

        data = model_to_dict(account)
        if account.id == requester.id and "role" in data:
            del data["role"]
        
        return render(request, "user_edit.html", {"roles": Account.Role.choices, **data})

    def post(self, request, account=0):
        if "account" not in request.session:
            return redirect("/login/")
        
        requester = Account.objects.get(pk=request.session["account"])
        if requester.role != Account.Role.SUPERVISOR and account != requester.id:
            return HttpResponseForbidden("You are not a supervisor.")

        try:
            account = Account.objects.get(pk=account)
        except Account.DoesNotExist:
            raise Http404("User does not exist")
        
        errors = users.edit(requester, account, request.POST)

        data = model_to_dict(account)
        if account.id == requester.id and "role" in data:
            del data["role"]
        data["errors"] = errors
        
        return render(request, "user_edit.html", {"roles": Account.Role.choices, "updated": len(errors) == 0, **data}, status=200 if not errors else 401)

class CreateUserView(View):
    def get(self, request):
        if "account" not in request.session:
            return redirect("/login/")
        
        requester = Account.objects.get(pk=request.session["account"])
        if requester.role != Account.Role.SUPERVISOR:
            return HttpResponseForbidden("You are not a supervisor.")
        
        return render(request, "user_create.html", {"roles": Account.Role.choices})

    def post(self, request):
        if "account" not in request.session:
            return redirect("/login/")
        
        requester = Account.objects.get(pk=request.session["account"])
        if requester.role != Account.Role.SUPERVISOR:
            return HttpResponseForbidden("You are not a supervisor.")

        if (errors := users.create(request.POST)):
            return render(request, "user_create.html", {"errors": errors}, status=401)
        else:
            return redirect("/users/?user_created=true")

class ViewCoursesView(View):
    def get(self, request):
        if "account" not in request.session:
            return redirect("/login/")
        
        requester = Account.objects.get(pk=request.session["account"])

        return render(request, "courses.html", {
            "courses": [{ "pk": course.pk, "name": course.name, "members": course.members.count()} \
                for course in courses.get(requester)],
            "supervisor": requester.role == Account.Role.SUPERVISOR,
        })

class CreateCourseView(View):
    def get(self, request):
        if "account" not in request.session:
            return redirect("/login/")
        
        requester = Account.objects.get(pk=request.session["account"])
        if requester.role != Account.Role.SUPERVISOR:
            return HttpResponseForbidden("You are not a supervisor.")
        
        return render(request, "course_create.html")

    def post(self, request):
        if "account" not in request.session:
            return redirect("/login/")
        
        requester = Account.objects.get(pk=request.session["account"])
        if requester.role != Account.Role.SUPERVISOR:
            return HttpResponseForbidden("You are not a supervisor.")
        
        errors = courses.create(request.POST.get("name", ""))

        if errors:
            return render(request, "course_create.html", {"errors": errors}, status=401)
        else:
            return redirect("/courses/?course_created=true")