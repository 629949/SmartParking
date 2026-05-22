from django.urls import path
from . import views
urlpatterns = [
    path('control/', views.iot_control, name='iot_control'),
]
