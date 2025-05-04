from django.urls import path
from . import views

urlpatterns = [
    path('question-papers/', views.question_paper_list_create, name='question-paper-list-create'),
    path('question-papers/<int:pk>/', views.question_paper_detail, name='question-paper-detail'),
]
