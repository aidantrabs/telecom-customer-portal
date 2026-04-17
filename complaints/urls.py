from django.urls import path

from . import views

app_name = 'complaints'

urlpatterns = [
    path('new/', views.new_complaint, name='new'),
]
