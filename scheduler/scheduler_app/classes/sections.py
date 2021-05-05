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

def assign(section: Section, user: Account):
    if user or section is None or user.get_role() is not Account.Role.TA:
        raise ValueError
    ta = section.ta
    if ta is not None:
        return "Ta has already been assigned to this section"
    section.ta = user
    return section.ta
