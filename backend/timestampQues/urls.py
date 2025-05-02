from django.urls import path
from .views import generate_practice_questions, user_video_inputs

urlpatterns = [
    path('process/', generate_practice_questions, name='video-process'),
    path('my-videos/', user_video_inputs, name='user-video-inputs'),
]
