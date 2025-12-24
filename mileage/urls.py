from django.urls import path
from .views import submit_mileage, dashboard, edit_mileage, change_status

urlpatterns = [
    path('submit/', submit_mileage, name='submit'),
    path('dashboard/', dashboard, name='dashboard'),
    path('edit/<int:record_id>/', edit_mileage, name='edit_mileage'),
    path('change-status/<int:record_id>/', change_status, name='change_status'),
]
