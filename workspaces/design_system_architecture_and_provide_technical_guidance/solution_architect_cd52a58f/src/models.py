from django.db import models

class Task(models.Model):
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=50, default='pending')
    dependencies = models.ManyToManyField('self', symmetrical=False, blank=True)

    def __str__(self): return self.name