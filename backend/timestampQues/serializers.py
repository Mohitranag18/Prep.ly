# core/serializers.py
from rest_framework import serializers
from .models import VideoInput

class VideoInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoInput
        fields = '__all__'
