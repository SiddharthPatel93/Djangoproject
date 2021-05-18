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
    errors = check_valid(section, user)
    if len(errors) == 0:
        section.ta = user
    else:
        return errors

def assign_section(section:Section, user:Account) -> list[str]:
    errors = []
    if user is None:
        errors.append("Enter a valid user")
    if section is None:
        errors.append("Enter a section")
    if user is not None:
        if user.get_role() == 0:
            errors.append("User is a supervisor, not a TA!")
        if user.get_role() == 1:
            errors.append("User is an instructor, not a TA!")
    if len(errors) != 0:
        return errors
    if section.ta is None:
        section.ta= user
        errors.append("successfully added TA")
    else:
        errors.append("could not assign TA to section")
    return errors



def check_valid(section: Section, user: Account) -> list[str]:
    errors = []
    if user is None:
        errors.append("Enter a valid user\n")
    if section is None:
        errors.append("Enter a section\n")
    if user is not None and user.get_role() is not Account.Role.TA:
        errors.append("User is not a TA!\n")
    if len(errors) != 0:
        return errors
    course = section.course
    try:
        ta1 = course.members.get(courses__coursemembership__account=user)
    except:
        errors.append("ta not assigned to this course\n")
        return errors
    ta = section.ta
    if ta is not None:
        errors.append("TA has already been assigned to this section\n")
        return errors
    return errors
