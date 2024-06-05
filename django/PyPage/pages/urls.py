# pages/urls.py
from django.contrib.auth import views as auth_views
from django.urls import path
from pages import views

urlpatterns = [
    path("", views.home, name='home'),
    path("ach", views.ach, name='ach'),
    path("ach1", views.ach1, name='ach1'),
    path("ach2", views.ach2, name='ach2'),
    path("ach3", views.ach3, name='ach3'),
    path("ach4", views.ach4, name='ach4'),
]