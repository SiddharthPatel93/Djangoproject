from functools import wraps

from django.http.response import HttpResponseForbidden
from django.shortcuts import redirect
from django.test import Client

from ..models import Account

def check_permissions(check_supervisor=True):
    def wrap_view(func):
        @wraps(func)
        def perform_checks(self, request, *args, **kwargs):
            if "account" not in request.session:
                return redirect("/login/")
        
            requester = Account.objects.get(pk=request.session["account"])
            if check_supervisor and requester.role != Account.Role.SUPERVISOR:
                return HttpResponseForbidden("You are not a supervisor.")
            
            return func(self, request, requester, *args, **kwargs)
        
        return perform_checks
    
    return wrap_view

# https://docs.djangoproject.com/en/3.2/topics/testing/tools/#persistent-state
def login(client: Client, account: Account):
    if account.pk is None:
        raise ValueError("Cannot login with unsaved account")
    
    s = client.session
    s["account"] = account.pk
    s.save()