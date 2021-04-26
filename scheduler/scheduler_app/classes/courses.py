from ..models import Account, Course

def create(name: str) -> list[str]:
    pass

def get_courses(requester: Account) -> list[Course]:
    if requester.role == Account.Role.SUPERVISOR:
        return list(Course.objects.all())
    
    return list(requester.courses.all())