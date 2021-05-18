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
        section.ta=user
        section.save()
        errors.append(f"Successfully added TA {user.name}")
    else:
        errors.append(f"{section.ta} already assigned to this section")
    return errors




