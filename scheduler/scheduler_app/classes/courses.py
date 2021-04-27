from ..models import Account, Course, Section

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

def create_section(course: Course, num: str) -> list[str]:
    if not num:
        return ["Please enter the section number!"]
    elif Section.objects.filter(course=course.pk, num=num).exists():
        return ["Please enter a number not taken by an existing section in this course!"]
    
    Section.objects.create(course=course, num=num)
    return []