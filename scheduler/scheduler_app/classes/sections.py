from ..models import Course, Section, Account


def create(course: Course, num: str) -> list[str]:
    if not num:
        return ["Please enter the section number!"]
    elif Section.objects.filter(course=course.pk, num=num).exists():
        return ["Please enter a number not taken by an existing section in this course!"]

    Section.objects.create(course=course, num=num)
    return []


def delete(section: Section):
    section.delete()


def assign(section: Section, user: Account) -> list[str]:
    errors = check_valid(section, user)
    if len(errors) == 0:
        section.ta = user
    else:
        return errors


def check_valid(section: Section, user: Account) -> list[str]:
    errors = []
    if user is None:
        errors.append("Enter a valid user\n")
    if section is None:
        errors.append("Enter a section\n")
    if user.get_role() is not Account.Role.TA:
        errors.append("User is not a TA!\n")
    course = section.course
    try:
        ta1 = course.members.get(user)
    except:
        errors.append("ta not assigned to this course\n")
        return errors
    ta = section.ta
    if ta is not None:
        errors.append("TA has already been assigned to this section\n")
        return errors
    return errors
