from ..models import Account, Course

def get(requester: Account) -> list[Course]:
    if requester.role == Account.Role.SUPERVISOR:
        return list(Course.objects.all())
    
    return list(requester.courses.all())

def create(name: str) -> list[str]:
    if not name:
        return ["Please enter the course name!"]
    elif Course.objects.filter(name=name).exists():
        return ["Please enter a name not taken by an existing course!"]
    
    Course.objects.create(name=name)
    return []

def delete(course: Course):
    pass