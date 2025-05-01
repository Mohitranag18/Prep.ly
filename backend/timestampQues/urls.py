from django.urls import path
from .views import video_process_view

urlpatterns = [
    path('process/', video_process_view, name='video-process'),
]
