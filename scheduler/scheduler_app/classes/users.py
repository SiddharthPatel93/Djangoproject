from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from ..models import Account

def perform_create(details: dict) -> list[str]:
    errors = []

    if not details.get("name", ""):
        errors.append("Please enter a name!")
    if not details.get("role", ""):
        errors.append("Please enter a role!")
    if not details.get("email", ""):
        errors.append("Please enter an email!")
    elif Account.objects.filter(email=details["email"]).exists():
        errors.append("Please enter an unused email!")
    else:
        try:
            validate_email(details["email"])
        except ValidationError:
            errors.append("Please enter a valid email!")
    if not details.get("password", ""):
        errors.append("Please enter a password!")
    
    if not errors:
        Account.objects.create(
            name=details["name"],
            role=Account.Role(int(details["role"])),
            email=details["email"],
            password=details["password"],
            phone=details.get("phone", ""),
            address=details.get("address", ""),
            office_hours=details.get("office_hours", ""),
        )
    
    return errors

def perform_delete(account: int) -> bool:
    """
    Attempt to delete a user.
    Return True if successful, False if not.
    """

def perform_edit(requester: Account, account: Account, details: dict) -> list[str]:
    errors = []

    account.name = details.get("name", account.name)
    if "role" in details:
        if requester.id != account.id:
            account.role = Account.Role(int(details["role"]))
        else:
            errors.append("A user cannot change their own role")
    account.password = details.get("password", account.password)
    account.phone = details.get("phone", account.phone)
    account.address = details.get("address", account.address)
    account.office_hours = details.get("office_hours", account.office_hours)

    if not errors:
        account.save()
    
    return errors