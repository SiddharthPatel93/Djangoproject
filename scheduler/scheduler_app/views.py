from django.shortcuts import redirect, render
from django.views import View

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
        pass

    def post(self, request, account=0):
        pass