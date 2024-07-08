
from django.db import models

class Project(models.Model):
    id = int
    title = models.TextField()
    description = models.TextField()
    txt_1 = models.TextField(max_length=255, default='default_value')
    txt_2 = models.TextField(max_length=255, default='default_value')
    txt_3 = models.TextField(max_length=255, default='default_value')
    txt_4 = models.TextField(max_length=255, default='default_value')
    alert = models.TextField()
    other = models.TextField()

    def __str__(self):
        return f"Id: {self.id} | Title: {self.title} | Description: {self.description}"
