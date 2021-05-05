from ..models import Course, Section

def count(num: str) -> int:
    return Section.objects.filter(num=num).count()

def create(course: Course, num: str) -> list[str]:
    if not num:
        return ["Please enter the section number!"]
    elif Section.objects.filter(course=course.pk, num=num).exists():
        return ["Please enter a number not taken by an existing section in this course!"]
    
    Section.objects.create(course=course, num=num)
    return []

def delete(section: Section):
    section.delete()