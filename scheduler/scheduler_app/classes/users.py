from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from ..models import Account


def get(requester: Account) -> list[Account]:

    return list(Account.objects.all())
    return list(requester.users.all())

def create(details: dict) -> list[str]:
    errors = []

    if not (name := details.get("name", "")):
        errors.append("Please enter a name!")
    if not (role := details.get("role", "")):
        errors.append("Please enter a role!")
    else:
        try:
            role = Account.Role(int(role))
        except ValueError:
            errors.append("Please enter a valid role!")
    if not (email := details.get("email", "")):
        errors.append("Please enter an email!")
    elif Account.objects.filter(email=email).exists():
        errors.append("Please enter an unused email!")
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors.append("Please enter a valid email!")
    if not (password := details.get("password", "")):
        errors.append("Please enter a password!")
    
    if not errors:
        Account.objects.create(
            name=name,
            role=role,
            email=email,
            password=password,
            phone=details.get("phone", ""),
            address=details.get("address", ""),
            office_hours=details.get("office_hours", ""),
        )
    
    return errors

def delete(account: int) -> bool:
    """
    Attempt to delete a user.
    Return True if successful, False if not.
    """

def edit(requester: Account, account: Account, details: dict) -> list[str]:
    errors = []

    account.name = details.get("name", account.name)
    if (role := details.get("role", "")):
        if requester.pk != account.pk:
            account.role = Account.Role(int(role))
        else:
            errors.append("A user cannot change their own role")
    if (email := details.get("email", "")):
        if email != account.email and Account.objects.filter(email=email).exists():
            errors.append("Please enter an unused email!")
        else:
            try:
                validate_email(email)
                account.email = email
            except ValidationError:
                errors.append("Please enter a valid email!")
    account.password = details.get("password", account.password)
    account.phone = details.get("phone", account.phone)
    account.address = details.get("address", account.address)
    account.office_hours = details.get("office_hours", account.office_hours)

    if not errors:
        account.save()
    
    return errors