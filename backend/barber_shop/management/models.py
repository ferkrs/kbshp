# management/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('barber', 'Barber'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    def __str__(self):
        return self.username

class BarberProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    total_clients_attended = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.get_full_name()

class Client(models.Model):
    name = models.CharField(max_length=100)
    assigned_barber = models.ForeignKey(
        BarberProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clients_assigned'  # Asegúrate de que esto está definido
    )
    in_queue = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class AttendanceLog(models.Model):
    client_name = models.CharField(max_length=100)
    barber = models.ForeignKey(BarberProfile, on_delete=models.CASCADE)
    attended_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client_name} atendido por {self.barber.user.get_full_name()} a las {self.attended_at}"