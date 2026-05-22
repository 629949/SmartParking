from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('park/', views.request_parking, name='request_parking'),
    path('session/<uuid:session_id>/', views.session_detail, name='session_detail'),
    path('checkout/<uuid:session_id>/', views.checkout, name='checkout'),
    path('receipt/<str:receipt_number>/', views.receipt_detail, name='receipt_detail'),
    path('receipt/<str:receipt_number>/download/', views.download_receipt, name='download_receipt'),
    path('sessions/', views.my_sessions, name='my_sessions'),
    path('api/slots/', views.api_slots_status, name='api_slots_status'),
    path('api/iot/callback/', views.api_iot_callback, name='api_iot_callback'),
]
