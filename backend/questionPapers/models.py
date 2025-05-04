from django.db import models

class University(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.university.name} - {self.name}"

class QuestionPaper(models.Model):
    SEMESTER_CHOICES = [(i, f"Semester {i}") for i in range(1, 9)]

    university = models.ForeignKey(University, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.IntegerField(choices=SEMESTER_CHOICES)

    year = models.PositiveIntegerField()
    subject = models.CharField(max_length=255)

    pdf_file = models.FileField(upload_to='question_papers/')
    parsed_text = models.TextField(blank=True, null=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('university', 'course', 'semester', 'year', 'subject')

    def __str__(self):
        return f"{self.university.name} - {self.course.name} - Sem {self.semester} - {self.year} - {self.subject}"
