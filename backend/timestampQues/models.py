from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class VideoInput(models.Model):
    video_url = models.URLField()
    watched_till = models.IntegerField(help_text="In seconds")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.owner.username}-{self.video_url}"
            self.slug = slugify(base)
        super().save(*args, **kwargs)
