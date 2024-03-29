from ..models import Course, Section, Account, CourseMembership

def count(num: str) -> int:
    return Section.objects.filter(num=num).count()

def create(course: Course, num: str) -> list[str]:
    errors = []

    if not num:
        errors.append("Please enter the section number!")
    elif count(num):
        errors.append("Please enter a number not taken by an existing section in this course!")

    if not errors:
        Section.objects.create(course=course, num=num)

    return errors

def delete(section: Section):
    section.delete()


def assign(section: Section, user: Account) -> list[str]:
    errors = []

    if user is None:
        errors.append("Enter a valid user")
    else:
        if (role := user.get_role()) == Account.Role.SUPERVISOR:
            errors.append("User is a supervisor, not a TA!")
        elif role == Account.Role.INSTRUCTOR:
            errors.append("User is an instructor, not a TA!")
    if section is None:
        errors.append("Enter a section")
    else:
        try:
            if user.sections.count() >= CourseMembership.objects.get(course=section.course, account=user).sections:
                errors.append("User is assigned to too many sections!")
        except CourseMembership.DoesNotExist:
            pass
    
    if errors:
        return errors
    
    if section.ta is None:
        section.ta = user
        section.save()
    else:
        errors.append(f"{section.ta} already assigned to this section")
    
    return errors

def unassign(section: Section) -> bool:
    if section.ta:
        section.ta = None
        section.save()
        return True
    else:
        return False