# core/models.py
from django.db import models

class VideoInput(models.Model):
    video_url = models.URLField()
    watched_till = models.IntegerField(help_text="In seconds")
    created_at = models.DateTimeField(auto_now_add=True)
