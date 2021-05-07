from functools import wraps
from typing import Tuple, Union

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpRequest
from django.http.response import HttpResponseForbidden
from django.shortcuts import redirect
from django.test import Client

from ..models import Account

LOGIN = redirect("/login/")

def check_permissions(check_supervisor=True):
    def wrap_view(func):
        @wraps(func)
        def perform_checks(self, request, *args, **kwargs):
            if "account" not in request.session:
                return LOGIN
            
            try:
                requester = Account.objects.get(pk=request.session["account"])
            except Account.DoesNotExist:
                return LOGIN
            
            if check_supervisor and requester.role != Account.Role.SUPERVISOR:
                return HttpResponseForbidden("You are not a supervisor.")
            
            return func(self, request, requester, *args, **kwargs)
        
        return perform_checks
    
    return wrap_view

# https://docs.djangoproject.com/en/3.2/topics/testing/tools/#persistent-state
def login(client: Union[Client, HttpRequest], account: Account):
    if account.pk is None:
        raise ValueError("Cannot login with unsaved account")
    
    s = client.session
    s["account"] = account.pk
    s.save()

def login_with_details(request: Union[Client, HttpRequest], details: dict[str, str]) -> Tuple[list[str], bool]:
    errors = []
    invalid_login = False

    if not (email := details.get("email", "")):
        errors.append("Please enter your email!")
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors.append("Please enter a valid email!")
    if not (password := details.get("password", "")):
        errors.append("Please enter your password!")
    
    if not errors:
        try:
            a = Account.objects.get(email=email, password=password)
            login(request, a)
        except Account.DoesNotExist:
            errors.append("Wrong email or password!")
            invalid_login = True
    
    return (errors, invalid_login)