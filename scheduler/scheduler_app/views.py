from django.forms.models import model_to_dict
from django.http.response import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views import View

from .classes import users
from .models import Account

class LoginView(View):
    def get(self, request):
        return render(request, "login.html")
    
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
            pass

        return render(request, "login.html", {"errors": ["Wrong email or password!"]}, status=401)

class LogoutView(View):
    def get(self, request):
        return render(request, "back.html", status=405)

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
        
        errors = users.perform_edit(requester, account, request.POST)

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

        if (errors := users.perform_create(request.POST)):
            return render(request, "user_create.html", {"errors": errors}, status=401)
        else:
            return redirect("/users/?user_created=true")