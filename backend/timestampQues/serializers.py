from rest_framework import serializers
from .models import VideoInput

class VideoInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoInput
        fields = ['id', 'video_url', 'watched_till', 'created_at']
        read_only_fields = ['id', 'created_at']

