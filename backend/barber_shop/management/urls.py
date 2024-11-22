# management/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('update_profile/', views.update_profile, name='update_profile'),
    path('add_barber/', views.add_barber, name='add_barber'),
    path('generate_ticket/', views.generate_ticket, name='generate_ticket'),
    path('complete_attendance/', views.complete_attendance, name='complete_attendance'),
    path('remove_client_from_barber/', views.remove_client_from_barber, name='remove_client_from_barber'),
    path('reassign_client_to_queue/', views.reassign_client_to_queue, name='reassign_client_to_queue'),
    path('remove_client_from_queue/', views.remove_client_from_queue, name='remove_client_from_queue'),
    path('edit_barber/', views.edit_barber, name='edit_barber'),
    path('toggle_barber_status/', views.toggle_barber_status, name='toggle_barber_status'),
    path('close_day/', views.close_day, name='close_day'),
    path('get_barbers_and_clients/', views.get_barbers_and_clients, name='get_barbers_and_clients'),
    path('get_clients_in_queue/', views.get_clients_in_queue, name='get_clients_in_queue'),
    path('get_attendance_log/', views.get_attendance_log, name='get_attendance_log'),
    path('client/<int:client_id>/', views.get_client_by_id, name='get_client_by_id'),
    path('barber/<int:barber_id>/', views.get_barber_by_id, name='get_barber_by_id'),
]
