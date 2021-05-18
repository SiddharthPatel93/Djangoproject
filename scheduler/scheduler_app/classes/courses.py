from ..models import Account, Course, CourseMembership

def count(name: str) -> int:
    return Course.objects.filter(name=name).count()

def get(requester: Account) -> list[Course]:
    if requester.role == Account.Role.SUPERVISOR:
        return list(Course.objects.all())
    
    return list(requester.courses.all())

def create(name: str) -> list[str]:
    errors = []

    if not name:
        errors.append("Please enter the course name!")
    elif count(name):
        errors.append("Please enter a name not taken by an existing course!")
    
    if not errors:
        Course.objects.create(name=name)
    
    return errors

def delete(course: Course):
    course.delete()

def assign(course: Course, user: Account) -> list[str]:
    errors = []

    if not course:
        errors.append("Please choose a course")
    if not user:
        errors.append("Please enter a user")
    
    if errors:
        return errors
    
    if (role := user.get_role()) == Account.Role.SUPERVISOR:
        errors.append("User is a supervisor!")
    elif role == Account.Role.INSTRUCTOR \
            and (instructor := course.members.filter(role=Account.Role.INSTRUCTOR).first()):
        errors.append(f"Instructor {instructor.name} has already been assigned to this course!")
    elif course.members.filter(email=user.get_email()):
        errors.append(f"User {user.name} has already been assigned to this course!")
    else:
        CourseMembership.objects.create(account=user, course=course)
        errors.append(f"Successfully added user {user.name} to course!")
    
    return errors

def edit(course: Course, details: dict[str, str]) -> list[str]:
    errors = []

    if not (name := details.get("name", "")):
        errors.append("Please enter a name!")
    elif count(name):
        errors.append("Please enter a name not taken by an existing course!")
    else:
        course.name = name

    if not errors:
        course.save()

    return errors