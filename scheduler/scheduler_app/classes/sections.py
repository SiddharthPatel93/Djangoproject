from ..models import Course, Section

def count(num: str) -> int:
    return Section.objects.filter(num=num).count()

def create(course: Course, num: str) -> list[str]:
    errors = []

    if not num:
        errors.append("Please enter the section number!")
    elif Section.objects.filter(course=course.pk, num=num).exists():
        errors.append("Please enter a number not taken by an existing section in this course!")
    
    if not errors:
        Section.objects.create(course=course, num=num)

    return errors

def delete(section: Section):
    section.delete()