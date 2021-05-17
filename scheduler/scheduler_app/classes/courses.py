from ..models import Account, Course

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

def assigninstructor(course:Course, user:Account)->list[str]:
    errors = []
    if not course:
        errors.append("Please chose a course")
    if not user:
        errors.append("Please enter an instructor")
    old_instructor = course.members.filter(courses__coursemembership__account=Account.Role.INSTRUCTOR)
    if old_instructor is not None:
        errors.append("Instructor already assigned to this Course")
    if user.get_role() is not Account.Role.INSTRUCTOR:
        errors.append("User is NOT an instructor")
    if not errors:
        new_assignment = CourseMembership.objects.create(account=user, course=course)
        new_assignment.save()
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