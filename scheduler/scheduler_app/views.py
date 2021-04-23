from django.shortcuts import redirect, render

from .models import Account

def login(request):
    if request.method == "GET":
        return render(request, "login.html")
    
    errors = []
    
    if not (email := request.POST.get("email", "")):
        errors.append("Please enter an email!")
    if not (password := request.POST.get("password", "")):
        errors.append("Please enter a password!")

    if errors:
        return render(request, "login.html", {"errors": errors}, status=400)

    try:
        a = Account.objects.get(email=email)

        if a.check_password(password):
            request.session["account"] = a.id
            return redirect("/")
    except Account.DoesNotExist:
        pass

    return render(request, "login.html", {"errors": ["Wrong email or password!"]}, status=401)