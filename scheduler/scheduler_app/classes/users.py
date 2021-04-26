from ..models import Account

def perform_create(details: dict) -> list[str]:
    pass

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
    
    return errors