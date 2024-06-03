
from django.db import models

class Project(models.Model):
    id = int
    title = models.TextField()
    description = models.TextField()
    alert = models.TextField()
    other = models.TextField()

    def __str__(self):
        return f"Id: {self.id} | Title: {self.title} | Description: {self.description}"
