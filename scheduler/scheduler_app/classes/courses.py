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

def assigninstructor(course:Course, user:Account)->list[str]:
    errors = []
    if not course:
        errors.append("Please choose a course")
    if not user:
        errors.append("Please enter a user")
    if len(errors) > 0:
        return errors
    if user.get_role() == 1:
        coursemembers = course.members.all()
        old_instructor = list(coursemembers.filter(role=Account.Role.INSTRUCTOR))
        if len(old_instructor) is not 0:
            errors.append(" An instructor has already been assigned to this Course")

        else:
            new_assignment = CourseMembership.objects.create(account=user, course=course)
            new_assignment.save()
            errors.append("Successfully added INSTRUCTOR to course")
        return errors
    elif user.get_role() == 2:
        alreadyassigned = course.members.all()
        alreadyassigned2= list(alreadyassigned.filter(email=user.get_email()))
        if len(alreadyassigned2) is not 0:
            errors.append("this TA has already been assigned to this course")
            return errors
        else:
            newTA = CourseMembership.objects.create(account=user, course=course)
            newTA.save()
            errors.append("Successfully added TA to course")
        return errors
    else:
        errors.append("User is a supervisor")
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