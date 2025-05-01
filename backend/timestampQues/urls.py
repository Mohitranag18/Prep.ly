from django.urls import path
from .views import generate_practice_questions

urlpatterns = [
    path('process/', generate_practice_questions, name='video-process'),
]
